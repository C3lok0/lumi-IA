import io
import streamlit as st
from google import genai
from google.genai import types
from gtts import gtts

# Configuração da página
st.set_page_config(page_title="LUMI", page_icon="🌟")
st.title("LUMI")
st.write("Converse com a LUMI, IA criada por Marcelo e Isabelle, para um trabalho da faculdade FATEC!")

# Função para converter texto da LUMI em áudio
def gerar_audio(texto):
    tts = gtts(text=texto, lang='pt', tld='com.br')
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    return fp

# 1. Obter a chave dos Secrets de forma segura
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error("⚠️ Chave 'GEMINI_API_KEY' não encontrada nos Secrets do Streamlit!")
    st.stop()

# 2. Inicializar o cliente e o chat na sessão do Streamlit
if "client" not in st.session_state:
    st.session_state.client = genai.Client(api_key=API_KEY)

if "chat" not in st.session_state:
    instrucao_sistema = (
        "Você é a LUMI, uma inteligência artificial amigável e prestativa. "
        "Você deve SEMPRE se identificar como LUMI, falar de forma educada e, "
        "caso perguntem quem é você ou quem te criou, mencione o Marcelo e a Isabelle enquanto estavam na FATEC. "
        "Responda de forma direta e se for usar formatações complexas como tabelas, diga que está a exibir uma tabela, pois responderá com áudio."
    )

    st.session_state.chat = st.session_state.client.chats.create(
        model="gemini-3.6-flash",
        config=types.GenerateContentConfig(
            system_instruction=instrucao_sistema
        )
    )

if "messages" not in st.session_state:
    st.session_state.messages = []

# 3. Exibir histórico de mensagens anteriores (com os áudios gravados)
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "audio" in message:
            st.audio(message["audio"], format="audio/mp3")

# 4. Entradas do Usuário (Texto ou Gravação de Áudio)
st.write("---")
audio_input = st.audio_input("🎤 Fale com a LUMI clicando no microfone:")
text_input = st.chat_input("Digite sua mensagem aqui...")

# Lógica para processar áudio ou texto digitado
prompt_envio = None
audio_bytes_envio = None

if audio_input is not None:
    audio_bytes_envio = audio_input.read()
    prompt_envio = types.Part.from_bytes(
        data=audio_bytes_envio,
        mime_type="audio/wav"
    )
elif text_input:
    prompt_envio = text_input

# 5. Envio e Resposta da LUMI
if prompt_envio is not None:
    # Exibe a entrada do usuário (texto ou player de áudio enviado)
    if audio_bytes_envio:
        st.session_state.messages.append({
            "role": "user", 
            "content": "🎙️ *[Mensagem de áudio enviada]*", 
            "audio": audio_bytes_envio
        })
        with st.chat_message("user"):
            st.markdown("🎙️ *[Mensagem de áudio enviada]*")
            st.audio(audio_bytes_envio)
    else:
        st.session_state.messages.append({"role": "user", "content": prompt_envio})
        with st.chat_message("user"):
            st.markdown(prompt_envio)

    # Gera a resposta e o áudio da LUMI
    with st.chat_message("assistant"):
        try:
            response = st.session_state.chat.send_message(prompt_envio)
            st.markdown(response.text)
            
            # Gera e reproduz a voz da LUMI
            audio_bytes = gerar_audio(response.text)
            st.audio(audio_bytes, format="audio/mp3", autoplay=True)

            # Salva no histórico
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response.text,
                "audio": audio_bytes
            })
        except Exception as e:
            st.error(f"Erro ao responder: {e}")
