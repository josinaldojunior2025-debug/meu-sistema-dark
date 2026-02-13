import streamlit as st
from openai import OpenAI
from supabase import create_client

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Dark Infor - Gerador", layout="wide")

# Inicializa o estado de login se não existir
if "logado" not in st.session_state:
    st.session_state.logado = False

# --- CONEXÃO COM SERVIÇOS (SECRETS) ---
try:
    # O código busca exatamente os nomes configurados nos seus Secrets
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error("Erro nos Secrets: Verifique se SUPABASE_URL, SUPABASE_KEY e OPENAI_API_KEY estão corretos.")
    st.stop()

# --- INTERFACE DE LOGIN ---
if not st.session_state.logado:
    st.title("🛡️ Acesso Dark Infor")
    
    with st.form("form_login"):
        # O .strip() remove espaços acidentais antes ou depois do texto
        email_input = st.text_input("E-mail").strip()
        senha_input = st.text_input("Senha", type="password").strip()
        
        botao_entrar = st.form_submit_button("ENTRAR NO SISTEMA", use_container_width=True)
        
        if botao_entrar:
            try:
                # Tentativa de login no Supabase
                res = supabase.auth.sign_in_with_password({
                    "email": email_input, 
                    "password": senha_input
                })
                
                if res.user:
                    st.session_state.logado = True
                    st.session_state.u_id = res.user.id
                    st.success("Login realizado com sucesso!")
                    st.rerun() # Recarrega a página para entrar no gerador
            except Exception as error:
                st.error(f"Falha no login: Verifique seu e-mail e senha no painel do Supabase.")

# --- INTERFACE DO GERADOR (APARECE APÓS LOGIN) ---
else:
    # Barra lateral para sair
    if st.sidebar.button("Encerrar Sessão
