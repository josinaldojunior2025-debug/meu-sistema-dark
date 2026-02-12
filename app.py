import streamlit as st
from openai import OpenAI
from supabase import create_client
import os

# Configurações de página e Estilo Dark
st.set_page_config(page_title="Dark Infor - Vozes Profissionais", layout="centered")

# Inicializar clientes
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error(f"Erro na conexão com as chaves: {e}")

# Gerenciamento de Sessão (Para não desconectar)
if "user" not in st.session_state:
    st.session_state.user = None

def login():
    st.title("Entrar no Dark Infor")
    email = st.text_input("E-mail")
    senha = st.text_input("Senha", type="password")
    if st.button("Login"):
        try:
            res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
            st.session_state.user = res.user
            st.rerun()
        except:
            st.error("E-mail ou senha incorretos.")

def cadastro():
    st.title("Criar Nova Conta")
    novo_email = st.text_input("Novo E-mail")
    nova_senha = st.text_input("Nova Senha", type="password")
    if st.button("Cadastrar"):
        try:
            supabase.auth.sign_up({"email": novo_email, "password": nova_senha})
            st.success("Cadastro realizado! Tente fazer o login.")
        except Exception as e:
            st.error(f"Erro ao cadastrar: {e}")

# Interface Principal
if st.session_state.user is None:
    tab1, tab2 = st.tabs(["Login", "Cadastro"])
    with tab1: login()
    with tab2: cadastro()
else:
    # Barra Lateral
    st.sidebar.success(f"Logado: {st.session_state.user.email}")
    if st.sidebar.button("Sair"):
        st.session_state.user = None
        st.rerun()

    st.title("🎙️ Gerador de Voz Profissional")
    
    # Suporte a 100 mil caracteres
    roteiro = st.text_area("Roteiro do Vídeo (Até 100k caracteres):", height=300, max_chars=100000)
    
    # Lista de Vozes (Aqui você pode adicionar nomes do ElevenLabs depois)
    voz = st.selectbox("Escolha a Voz:", ["alloy", "echo", "fable", "onyx", "nova", "shimmer"])

    if st.button("Gerar Áudio"):
        if not roteiro:
            st.warning("Por favor, cole um texto.")
        else:
            with st.spinner("Gerando áudio..."):
                try:
                    response = client.audio.speech.create(
                        model="tts-1",
                        voice=voz,
                        input=roteiro
                    )
                    # Gerar arquivo para download
                    audio_bytes = response.content
                    st.audio(audio_bytes, format="audio/mp3")
                    
                    st.download_button(
                        label="📥 Baixar Áudio (MP3)",
                        data=audio_bytes,
                        file_name="audio_dark_infor.mp3",
                        mime="audio/mp3"
                    )
                    st.success("Áudio gerado com sucesso!")
                except Exception as e:
                    st.error(f"Erro: {e}")

    st.info("Nota: Para clonagem de voz e ElevenLabs, é necessário integrar a API Key específica.")
