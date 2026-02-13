import streamlit as st
from openai import OpenAI
from supabase import create_client
import uuid

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Dark Infor - Sistema de Voz Profissional", layout="wide")

# --- ESTILO DARK ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stButton>button { width: 100%; border-radius: 5px; background-color: #ff4b4b; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- INICIALIZAÇÃO DE CLIENTES ---
try:
    # Utiliza as chaves configuradas nos seus Secrets
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error(f"Erro nos Segredos (Secrets): {e}")

# --- GERENCIAMENTO DE SESSÃO ---
if "user" not in st.session_state:
    st.session_state.user = None

# --- TELAS DE ACESSO (LOGIN/CADASTRO) ---
def autenticacao():
    st.title("🛡️ Acesso Dark Infor")
    aba_login, aba_cadastro = st.tabs(["Login", "Cadastro"])
    
    with aba_login:
        email = st.text_input("E-mail", key="log_email")
        senha = st.text_input("Senha", type="password", key="log_pass")
        if st.button("Entrar"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
                st.session_state.user = res.user
                st.rerun()
            except:
                st.error("E-mail ou senha incorretos.")

    with aba_cadastro:
        n_email = st.text_input("Novo E-mail", key="cad_email")
        n_senha = st.text_input("Nova Senha (mín. 6 chars)", type="password", key="cad_pass")
        if st.button("Criar Conta"):
            try:
                supabase.auth.sign_up({"email": n_email, "password": n_senha})
                st.success("Cadastro realizado! Tente fazer o login.")
            except Exception as e:
                st.error(f"Erro: {e}")

# --- INTERFACE DO GERADOR ---
def interface_gerador():
    st.sidebar.write(f"Logado como: {st.session_state.user.email}")
    if st.sidebar.button("Sair"):
        st.session_state.user = None
        st.rerun()

    st.title("🎙️ Gerador de Voz Profissional")
    
    # Campo para 100 mil caracteres
    texto = st.text_area("Roteiro do Vídeo (Até 100.000 caracteres):", height=300, max_chars=100000)
    
    col1, col2 = st.columns(
