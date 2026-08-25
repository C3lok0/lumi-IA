import io
import re
import time
import streamlit as st
from google import genai
from google.genai import types
from gtts import gTTS

# DICIONÁRIO DE EXPRESSÕES DA LUMI

EXPRESSOES_LUMI = {
    "neutro": "imagens/lumi_neutro.png",     # Aguardando ação do usuário
    "pensando": "imagens/lumi_pensando.gif", # Enquanto gera a resposta
    "feliz": "imagens/lumi_feliz.gif",       # Quando responde com sucesso
    "erro": "imagens/lumi_erro.png"          # Quando ocorre falha na API
}

# Configuração da página
st.set_page_config(page_title="LUMI", page_icon="🌟", layout="wide")

# Estado para controlar qual imagem exibir no canto da tela
if "expressao_atual" not in st.session_state:
    st.session_state.expressao_atual = EXPRESSOES_LUMI["neutro"]

st.title("🌟 LUMI - Inteligência Artificial")
st.caption("Desenvolvida por Marcelo e Isabelle | FATEC")

#CSS CUSTOMIZADO PARA FIXAR A LUMI NO CANTO INFERIOR DIREITO
st.markdown(
    """
    <style>
    /* Container fixo no canto inferior direito */
    .avatar-flutuante {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 999999;
        width: 150px; /* Ajuste o tamanho da personagem aqui */
        filter: drop-shadow(0px 4px 10px rgba(0, 0, 0, 0.3));
        pointer-events: none; /* Permite clicar o que estiver atrás da imagem se necessário */
    }
    .avatar-flutuante img {
        width: 100%;
        height: auto;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Renderiza a LUMI fixada no canto inferior direito
try:
    # Usamos o st.markdown para aplicar a classe CSS
    st.markdown(
        f'<div class="avatar-flutuante"><img src="{st.session_state.expressao_atual}"></div>',
        unsafe_allow_html=True
    )
except Exception:
    pass

# Função para converter texto em áudio
def gerar_audio(texto, lang_code='pt', tld='com.br'):
    texto_limpo = re.sub(r'[\*\_\#\`]', '', texto)
    tts = gTTS(text=texto_limpo, lang=lang_code, tld=tld)
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    return fp

# 1. Obter a chave dos Secrets
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error("⚠️ Chave 'GEMINI_API_KEY' não encontrada nos Secrets do Streamlit!")
    st.stop()

# 2. Inicializar cliente e sessão
if "client" not in st.session_state:
    st.session_state.client = genai.Client(api_key=API_KEY)

if "chat" not in st.session_state:
    instrucao_sistema = (
        "Você é a LUMI, uma inteligência artificial amigável e prestativa criada pelo Marcelo e pela Isabelle na FATEC. "
        "Apenas se identifique ou diga quem te criou CASO o usuário pergunte explicitamente sobre quem é você ou quem te criou. "
        "Nas conversas normais, responda diretamente à pergunta do usuário de forma educada, sem se apresentar a cada mensagem. "
        "Você também é capaz de analisar documentos, imagens e arquivos enviados pelos usuários. "
        "Responda de forma direta e sem incluir marcações de tempo ou legendas."
    )

    st.session_state.chat = st.session_state.client.chats.create(
        model="gemini-3.6-flash",
        config=types.GenerateContentConfig(
            system_instruction=instrucao_sistema
        )
    )

if "messages" not in st.session_state:
    st.session_state.messages = []

if "audio_counter" not in st.session_state:
    st.session_state.audio_counter = 0

if "prompt_sugerido" not in st.session_state:
    st.session_state.prompt_sugerido = None

if "ultimo_tempo" not in st.session_state:
    st.session_state.ultimo_tempo = 0.0

# 3. Barra lateral (Configurações, Métricas, Arquivos e Download)
with st.sidebar:
    st.header("Configurações da LUMI")
    falar_resposta = st.toggle("Ouvir respostas", value=True)
    
    idioma_voz = st.selectbox(
        "🎙️ Sotaque/Idioma da Voz:",
        ["Português (Brasil)", "Português (Portugal)", "Inglês (US)"]
    )
    
    lang_config = {'lang': 'pt', 'tld': 'com.br'}
    if idioma_voz == "Português (Portugal)":
        lang_config = {'lang': 'pt', 'tld': 'pt'}
    elif idioma_voz == "Inglês (US)":
        lang_config = {'lang': 'en', 'tld': 'com'}

    st.write("---")
    st.header("Painel de Métricas")
    col_m1, col_m2 = st.columns(2)
    col_m1.metric("Mensagens", len(st.session_state.messages))
    col_m2.metric("Última Resposta", f"{st.session_state.ultimo_tempo:.2f}s")

    st.write("---")
    st.header("Anexar Arquivo")
    uploaded_file = st.file_uploader(
        "Envie um PDF, Imagem ou Texto:", 
        type=["pdf", "png", "jpg", "jpeg", "txt", "csv"]
    )
    
    st.write("---")
    st.header("Opções da Conversa")
    
    if st.session_state.messages:
        historico_texto = "HISTÓRICO DE CONVERSA COM A LUMI (FATEC)\n" + "="*40 + "\n\n"
        for msg in st.session_state.messages:
            autor = "LUMI" if msg["role"] == "assistant" else "VOCÊ"
            historico_texto += f"[{autor}]: {msg['content']}\n\n"
        
        st.download_button(
            label="Baixar Conversa (.txt)",
            data=historico_texto,
            file_name="conversa_lumi.txt",
            mime="text/plain"
        )
    
    if st.button("Limpar Conversa"):
        st.session_state.messages = []
        st.session_state.audio_counter += 1
        st.session_state.prompt_sugerido = None
        st.session_state.ultimo_tempo = 0.0
        st.session_state.expressao_atual = EXPRESSOES_LUMI["neutro"]
        st.rerun()

# 4. Exibir Cards de Sugestão de Perguntas
if not st.session_state.messages:
    st.write("### 💡 Sugestões de perguntas para começar:")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🌟 Quem criou você?"):
            st.session_state.prompt_sugerido = "Quem criou você e para qual faculdade?"
        if st.button("📄 Como você me ajuda com arquivos?"):
            st.session_state.prompt_sugerido = "Quais tipos de arquivos posso te enviar e o que você consegue analisar neles?"
            
    with col2:
        if st.button("💻 O que é o modelo Gemini 3.6?"):
            st.session_state.prompt_sugerido = "Explique brevemente o que é o modelo de IA Gemini Flash."
        if st.button("🎓 Dicas para trabalhos acadêmicos"):
            st.session_state.prompt_sugerido = "Me dê 3 dicas rápidas para estruturar uma boa apresentação acadêmica."

# 5. Exibir histórico de mensagens
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if "audio" in message and message["audio"] is not None:
            st.audio(message["audio"], format="audio/mp3", autoplay=False)

# 6. Entradas do Usuário
st.write("---")
audio_input = st.audio_input(
    "🎤 Fale com a LUMI clicando no microfone:", 
    key=f"audio_input_{st.session_state.audio_counter}"
)
text_input = st.chat_input("Digite sua mensagem aqui...")

# Lógica de captura de prompt
prompt_envio = None
audio_bytes_envio = None
conteudos_para_envio = []

if uploaded_file is not None:
    file_bytes = uploaded_file.read()
    file_part = types.Part.from_bytes(
        data=file_bytes,
        mime_type=uploaded_file.type
    )
    conteudos_para_envio.append(file_part)

if audio_input is not None:
    audio_bytes_envio = audio_input.read()
    audio_part = types.Part.from_bytes(
        data=audio_bytes_envio,
        mime_type="audio/wav"
    )
    conteudos_para_envio.append(audio_part)
    conteudos_para_envio.append("Por favor, responda à minha fala no áudio e inicie a resposta indicando o que você entendeu que eu disse.")
elif text_input:
    conteudos_para_envio.append(text_input)
elif st.session_state.prompt_sugerido:
    conteudos_para_envio.append(st.session_state.prompt_sugerido)
    st.session_state.prompt_sugerido = None

# 7. Processamento e Resposta da LUMI
if conteudos_para_envio:
    inicio_tempo = time.time()
    
    # 💭 Muda para a expressão "pensando" no canto da tela
    st.session_state.expressao_atual = EXPRESSOES_LUMI["pensando"]

    mensagem_usuario = ""
    if uploaded_file is not None:
        mensagem_usuario += f"📎 *[Arquivo enviado: {uploaded_file.name}]*\n"
    
    if audio_bytes_envio:
        mensagem_usuario += "🎙️ *[Mensagem de áudio enviada]*"
    elif isinstance(conteudos_para_envio[0], str):
        mensagem_usuario += conteudos_para_envio[0]

    st.session_state.messages.append({
        "role": "user", 
        "content": mensagem_usuario,
        "audio": audio_bytes_envio
    })

    with st.chat_message("user"):
        st.write(mensagem_usuario)
        if audio_bytes_envio:
            st.audio(audio_bytes_envio)

    # Bloco da resposta
    try:
        response = st.session_state.chat.send_message(
            conteudos_para_envio if len(conteudos_para_envio) > 1 else conteudos_para_envio[0]
        )
        texto_resposta = re.sub(r'\d{2}:\d{2}', '', response.text)
        
        # 🌟 Resposta com sucesso: a LUMI fica FELIZ no canto da tela!
        st.session_state.expressao_atual = EXPRESSOES_LUMI["feliz"]
        
        with st.chat_message("assistant"):
            st.write(texto_resposta)
            
            audio_bytes = None
            if falar_resposta:
                audio_bytes = gerar_audio(
                    texto_resposta, 
                    lang_code=lang_config['lang'], 
                    tld=lang_config['tld']
                )
                st.audio(audio_bytes, format="audio/mp3", autoplay=True)

        st.session_state.ultimo_tempo = time.time() - inicio_tempo

        st.session_state.messages.append({
            "role": "assistant", 
            "content": texto_resposta,
            "audio": audio_bytes
        })
        
        if audio_bytes_envio:
            st.session_state.audio_counter += 1
            st.rerun()

    except Exception as e:
        # ⚠️ Erro na requisição: a LUMI fica com a expressão de ERRO!
        st.session_state.expressao_atual = EXPRESSOES_LUMI["erro"]
        
        with st.chat_message("assistant"):
            st.error(f"Erro ao processar resposta: {e}")
            
        st.session_state.messages.append({
            "role": "assistant", 
            "content": f"⚠️ Ocorreu um erro ao processar: {e}",
            "audio": None
        })
