import streamlit as st
from openai import OpenAI
from supabase import create_client

# Configuração essencial
st.set_page_config(page_title="Dark Infor", layout="wide")

if "logado" not in st.session_state:
    st.session_state.logado = False

# Conexão com serviços
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error("Erro nos Secrets. Verifique se as chaves estão em uma linha só.")
    st.stop()

# --- LOGIN ---
if not st.session_state.logado:
    st.title("🛡️ Acesso Dark Infor")
    with st.form("login"):
        u_email = st.text_input("E-mail").strip()
        u_pass = st.text_input("Senha", type="password").strip()
        if st.form_submit_button("ENTRAR NO SISTEMA"):
            try:
                res = supabase.auth.sign_in_with_password({"email": u_email, "password": u_pass})
                if res.user:
                    st.session_state.logado = True
                    st.rerun()
            except:
                st.error("Acesso negado. Crie o usuário com SENHA MANUAL no Supabase.")

# --- SISTEMA ---
else:
    st.sidebar.button("Sair", on_click=lambda: st.session_state.update({"logado": False}))
    st.title("🎙️ Gerador de Voz Profissional")
    texto = st.text_area("Roteiro:", height=150)
    voz = st.selectbox("Escolha a Voz:", ["onyx", "alloy", "echo", "fable", "nova", "shimmer"])
    
    if st.button("🔥 GERAR ÁUDIO"):
        if texto:
            with st.spinner("IA Processando..."):
                try:
                    resp = openai_client.audio.speech.create(model="tts-1", voice=voz, input=texto[:4000])
                    st.audio(resp.content)
                    st.success("Gerado com sucesso!")
                except Exception as e:
                    st.error(f"Erro OpenAI: {e}")
