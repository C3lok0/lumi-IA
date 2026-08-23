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

# 2. Barra lateral (Configurações e envio de arquivo)
with st.sidebar:
    st.header("⚙️ Configurações")
    falar_resposta = st.toggle("🔊 Ouvir respostas da LUMI", value=True)
    
    st.write("---")
    st.header("📁 Anexar Arquivo")
    uploaded_file = st.file_uploader(
        "Envie um PDF, Imagem ou Texto:", 
        type=["pdf", "png", "jpg", "jpeg", "txt", "csv"]
    )
    
    if st.button("🗑️ Limpar Conversa"):
        st.session_state.messages = []
        st.session_state.audio_counter += 1
        st.rerun()

# 3. Inicializar cliente e sessão
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

# 4. Exibir histórico de mensagens
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if "audio" in message and message["audio"] is not None:
            st.audio(message["audio"], format="audio/mp3", autoplay=False)

# 5. Entradas do Usuário
st.write("---")
audio_input = st.audio_input(
    "🎤 Fale com a LUMI clicando no microfone:", 
    key=f"audio_input_{st.session_state.audio_counter}"
)
text_input = st.chat_input("Digite sua mensagem aqui...")

# Identifica o tipo de conteúdo enviado
prompt_envio = None
audio_bytes_envio = None
conteudos_para_envio = []

if uploaded_file is not None:
    # Prepara o arquivo enviado na barra lateral
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

# 6. Processamento e Resposta da LUMI
if conteudos_para_envio:
    # Registra no histórico do chat o envio do arquivo se houver
    mensagem_usuario = ""
    if uploaded_file is not None:
        mensagem_usuario += f"📎 *[Arquivo enviado: {uploaded_file.name}]*\n"
    
    if audio_bytes_envio:
        mensagem_usuario += "🎙️ *[Mensagem de áudio enviada]*"
    elif text_input:
        mensagem_usuario += text_input

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
            # Envia a lista de partes (Texto/Áudio/Arquivo) para a API
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
            
            # Se usou áudio, limpa o gravador
            if audio_bytes_envio:
                st.session_state.audio_counter += 1
                st.rerun()

        except Exception as e:
            st.error(f"Erro ao processar mensagem ou arquivo: {e}")
