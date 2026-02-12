import streamlit as st
from openai import OpenAI

# 1. Busca a chave escondida nos Secrets
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except:
    st.error("Erro: A chave API não foi configurada nos Secrets do Streamlit.")

st.set_page_config(page_title="Sistema de Voz Dark", page_icon="🎙️")
st.title("🎙️ Gerador de Voz Realista")

# 2. Senha para proteger seus créditos
SENHA_MESTRA = "suasenha123" 

# Barra lateral configurada para Senha
senha_digitada = st.sidebar.text_input("Senha de Acesso:", type="password")

if senha_digitada == SENHA_MESTRA:
    st.sidebar.success("Acesso Liberado!")
    
    texto = st.text_area("Roteiro do Vídeo:", placeholder="Cole seu roteiro aqui...", height=200)
    voz = st.selectbox("Escolha a Voz:", ["alloy", "echo", "fable", "onyx", "nova", "shimmer"])

    if st.button("Gerar Áudio"):
        if texto:
            with st.spinner("Gerando narração..."):
                try:
                    response = client.audio.speech.create(
                        model="tts-1",
                        voice=voz,
                        input=texto
                    )
                    # Salva e mostra o áudio
                    response.stream_to_file("audio_dark.mp3")
                    st.audio("audio_dark.mp3")
                    st.success("Pronto! Clique nos 3 pontos do áudio para baixar.")
                except Exception as e:
                    st.error(f"Erro na OpenAI: {e}")
        else:
            st.warning("O campo de texto está vazio.")
else:
    if senha_digitada != "":
        st.sidebar.error("Senha Incorreta!")
    st.info("Digite a senha na barra lateral esquerda para liberar o sistema.")
