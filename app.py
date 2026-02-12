import streamlit as st
from openai import OpenAI
from supabase import create_client, Client

# 1. Configuração de conexão com as APIs (Secrets)
try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error("Erro nas chaves de configuração. Verifique os Secrets.")

st.set_page_config(page_title="Dark Infor - Vozes Realistas", page_icon="🎙️")

# --- SISTEMA DE AUTENTICAÇÃO ---
if "user" not in st.session_state:
    st.session_state.user = None

def login():
    st.sidebar.title("Entrar no Dark Infor")
    email = st.sidebar.text_input("E-mail")
    password = st.sidebar.text_input("Senha", type="password")
    if st.sidebar.button("Login"):
        try:
            res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            st.session_state.user = res.user
            st.rerun()
        except:
            st.sidebar.error("E-mail ou senha incorretos.")

def cadastro():
    st.sidebar.title("Criar Nova Conta")
    novo_email = st.sidebar.text_input("Novo E-mail")
    nova_senha = st.sidebar.text_input("Nova Senha", type="password")
    if st.sidebar.button("Cadastrar"):
        try:
            supabase.auth.sign_up({"email": novo_email, "password": nova_senha})
            st.sidebar.success("Conta criada! Agora faça o login.")
        except Exception as e:
            st.sidebar.error(f"Erro ao cadastrar: {e}")

# --- LÓGICA DE TELAS ---
if st.session_state.user is None:
    st.title("🎙️ Bem-vindo ao Dark Infor")
    st.info("Para usar nossas vozes neurais, faça login ou crie sua conta na barra lateral.")
    
    aba = st.sidebar.radio("Escolha uma opção:", ["Login", "Cadastro"])
    if aba == "Login":
        login()
    else:
        cadastro()
else:
    # --- ÁREA LOGADA (O GERADOR) ---
    st.sidebar.success(f"Logado como: {st.session_state.user.email}")
    if st.sidebar.button("Sair"):
        st.session_state.user = None
        st.rerun()

    st.title("🎙️ Gerador de Voz Profissional")
    texto = st.text_area("Roteiro do Vídeo:", placeholder="Cole seu roteiro aqui...", height=200)
    voz = st.selectbox("Escolha a Voz:", ["alloy", "echo", "fable", "onyx", "nova", "shimmer"])

    if st.button("Gerar Áudio"):
        if texto:
            with st.spinner("IA Dark Infor processando..."):
                try:
                    response = client.audio.speech.create(model="tts-1", voice=voz, input=texto)
                    response.stream_to_file("output.mp3")
                    st.audio("output.mp3")
                    st.success("Áudio gerado com sucesso!")
                except Exception as e:
                    st.error(f"Erro na geração: {e}")
        else:
            st.warning("O roteiro está vazio.")
