import io
import re
import streamlit as st
from google import genai
from google.genai import types
from gtts import gTTS

# Configuração da página
st.set_page_config(page_title="LUMI", page_icon="🌟")
st.title("LUMI")
st.write("Converse com a LUMI, IA criada por Marcelo e Isabelle, para um trabalho da faculdade FATEC!")

# Função para converter texto da LUMI em áudio
def gerar_audio(texto):
    texto_limpo = re.sub(r'[\*\_\#\`]', '', texto)
    tts = gTTS(text=texto_limpo, lang='pt', tld='com.br')
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

# 3. Barra lateral (Configurações, Arquivos e Download)
with st.sidebar:
    st.header("Configurações")
    falar_resposta = st.toggle("🔊 Ouvir respostas da LUMI", value=True)
    
    st.write("---")
    st.header("Anexar Arquivo")
    uploaded_file = st.file_uploader(
        "Envie um PDF, Imagem ou Texto:", 
        type=["pdf", "png", "jpg", "jpeg", "txt", "csv"]
    )
    
    st.write("---")
    st.header("Opções da Conversa")
    
    # Gerar arquivo de texto com o histórico para download
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
    
    if st.button(" Limpar Conversa"):
        st.session_state.messages = []
        st.session_state.audio_counter += 1
        st.session_state.prompt_sugerido = None
        st.rerun()

# 4. Exibir Cards de Sugestão de Perguntas (Apenas se não houver mensagens no chat)
if not st.session_state.messages:
    st.write("### 💡 Sugestões de perguntas para começar:")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🌟 Quem criou você?"):
            st.session_state.prompt_sugerido = "Quem criou você e para qual faculdade?"
        if st.button("📄 Como você me ajuda com arquivos?"):
            st.session_state.prompt_sugerido = "Quais tipos de arquivos posso te enviar e o que você consegue analisar neles?"
            
    with col2:
        if st.button("💻 O que é o modelo Gemini 2.5?"):
            st.session_state.prompt_sugerido = "Explique brevemente o que é o modelo de IA Gemini 2.5 Flash."
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

# Lógica para captura do prompt (Digitado, Áudio ou Sugestão por botão)
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
elif text_input:
    conteudos_para_envio.append(text_input)
elif st.session_state.prompt_sugerido:
    conteudos_para_envio.append(st.session_state.prompt_sugerido)
    st.session_state.prompt_sugerido = None  # Limpa o estado após ler

# 7. Processamento e Resposta da LUMI
if conteudos_para_envio:
    mensagem_usuario = ""
    if uploaded_file is not None:
        mensagem_usuario += f"📎 *[Arquivo enviado: {uploaded_file.name}]*\n"
    
    if audio_bytes_envio:
        mensagem_usuario += "🎙️ *[Mensagem de áudio enviada]*"
    elif isinstance(conteudos_para_envio[-1], str):
        mensagem_usuario += conteudos_para_envio[-1]

    st.session_state.messages.append({
        "role": "user", 
        "content": mensagem_usuario,
        "audio": audio_bytes_envio
    })

    with st.chat_message("user"):
        st.write(mensagem_usuario)
        if audio_bytes_envio:
            st.audio(audio_bytes_envio)

    # Processa com a LUMI
    with st.chat_message("assistant"):
        try:
            response = st.session_state.chat.send_message(
                conteudos_para_envio if len(conteudos_para_envio) > 1 else conteudos_para_envio[0]
            )
            texto_resposta = re.sub(r'\d{2}:\d{2}', '', response.text)
            
            st.write(texto_resposta)
            
            audio_bytes = None
            if falar_resposta:
                audio_bytes = gerar_audio(texto_resposta)
                st.audio(audio_bytes, format="audio/mp3", autoplay=True)

            st.session_state.messages.append({
                "role": "assistant", 
                "content": texto_resposta,
                "audio": audio_bytes
            })
            
            if audio_bytes_envio:
                st.session_state.audio_counter += 1
                st.rerun()

        except Exception as e:
            st.error(f"Erro ao processar mensagem ou arquivo: {e}")
