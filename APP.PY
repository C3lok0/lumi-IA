import streamlit as st
from google import genai

# Configuração da página
st.set_page_config(page_title="Meu Chatbot IA", page_icon="")
st.title("LUMI Meu Chatbot Pessoal")
st.write("Converse com a LUMI, Ia criada por Marcelo e Isabelle, para um trabalho da faculdade FATEC")

# 1. Pega a chave dos segredos do Streamlit (vamos cadastrar na nuvem depois)
API_KEY = st.secrets["GEMINI_API_KEY"]

# 2. Inicializar o chat
if "chat" not in st.session_state:
    client = genai.Client(api_key=API_KEY)
    st.session_state.chat = client.chats.create(model="gemini-1.5-flash")

if "messages" not in st.session_state:
    st.session_state.messages = []

# 3. Exibir histórico
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. Campo de mensagem
if prompt := st.chat_input("Digite sua mensagem aqui..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = st.session_state.chat.send_message(prompt)
        st.markdown(response.text)
    
    st.session_state.messages.append({"role": "assistant", "content": response.text})