import streamlit as st
from google import genai

# Configuração da página
st.set_page_config(page_title="LUMI - Chatbot IA", page_icon="LUMI")
st.title("LUMI - Meu Chatbot Pessoal")
st.write("Converse com a LUMI, IA criada por Marcelo e Isabelle, para um trabalho da faculdade FATEC!")

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
    st.session_state.chat = st.session_state.client.chats.create(model="gemini-3.6-flash")

if "messages" not in st.session_state:
    st.session_state.messages = []

# 3. Exibir histórico de mensagens anteriores
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. Campo de mensagem e envio para a IA
if prompt := st.chat_input("Digite sua mensagem aqui..."):
    # Exibe a mensagem do usuário na tela
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Gera a resposta da LUMI
    with st.chat_message("assistant"):
        try:
            response = st.session_state.chat.send_message(prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"Erro ao responder: {e}")
