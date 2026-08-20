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
    # Remove marcações de formatação antes de gerar o áudio para evitar ruídos
    texto_limpo = re.sub(r'[\*\_\#\`]', '', texto)
    tts = gTTS(text=texto_limpo, lang='pt', tld='com.br')
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

# 2. Opção na barra lateral
with st.sidebar:
    st.header("⚙️ Configurações")
    falar_resposta = st.toggle("🔊 Ouvir respostas da LUMI", value=True)
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
        "Responda de forma direta e sem incluir marcações de tempo ou legendas. Se for usar tabelas, avise que exibirá uma tabela."
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

# 4. Exibir histórico de mensagens anteriores
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

# 6. Processamento da Resposta
if prompt_envio is not None:
    if audio_bytes_envio:
        st.session_state.messages.append({
            "role": "user", 
            "content": "🎙️ [Mensagem de áudio enviada]", 
            "audio": audio_bytes_envio
        })
        with st.chat_message("user"):
            st.write("🎙️ [Mensagem de áudio enviada]")
            st.audio(audio_bytes_envio)
    else:
        st.session_state.messages.append({"role": "user", "content": prompt_envio})
        with st.chat_message("user"):
            st.write(prompt_envio)

    with st.chat_message("assistant"):
        try:
            response = st.session_state.chat.send_message(prompt_envio)
            texto_resposta = response.text
            
            # Sanitiza o texto limpando padrões de timestamp remanescentes
            texto_limpo = re.sub(r'\d{2}:\d{2}', '', texto_resposta)
            
            # Exibe em texto puro (st.write evita injeções de atributos do markdown)
            st.write(texto_limpo)
            
            audio_bytes = None
            if falar_resposta:
                audio_bytes = gerar_audio(texto_limpo)
                st.audio(audio_bytes, format="audio/mp3", autoplay=True)

            # Salva o texto sanitizado no histórico
            st.session_state.messages.append({
                "role": "assistant", 
                "content": texto_limpo,
                "audio": audio_bytes
            })
            
            if audio_bytes_envio:
                st.session_state.audio_counter += 1
                st.rerun()

        except Exception as e:
            st.error(f"Erro ao responder: {e}")
