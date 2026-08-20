import io
import streamlit as st
from google import genai
from google.genai import types
from gtts import gTTS

# Configuração da página
st.set_page_config(page_title="LUMI", page_icon="🌟")
st.title("LUMI")
st.write("Converse com a LUMI, IA criada por Marcelo e Isabelle, para um trabalho da faculdade FATEC!")

# Função para converter texto em áudio na memória
def gerar_audio(texto):
    tts = gTTS(text=texto, lang='pt', tld='com.br')
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
        "Responda de forma direta e se for usar formatações complexas como tabelas, diga que esta a exibir uma tabela, pois respondara com audio."
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

# 4. Campo de mensagem e envio para a IA
if prompt := st.chat_input("Digite sua mensagem aqui..."):
    # Exibe a mensagem do usuário na tela
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Gera a resposta da LUMI e o áudio
    with st.chat_message("assistant"):
        try:
            response = st.session_state.chat.send_message(prompt)
            st.markdown(response.text)
            
            # Gera a voz da LUMI
            audio_bytes = gerar_audio(response.text)
            st.audio(audio_bytes, format="audio/mp3", autoplay=True)

            # Salva no histórico com o áudio
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response.text,
                "audio": audio_bytes
            })
        except Exception as e:
            st.error(f"Erro ao responder: {e}")
