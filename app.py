import streamlit as st
from openai import OpenAI
from supabase import create_client

st.set_page_config(page_title="Dark Infor", layout="wide")

if "logado" not in st.session_state:
    st.session_state.logado = False

# Conexão segura
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error(f"Erro de configuração: {e}")
    st.stop()

if not st.session_state.logado:
    st.title("🛡️ Acesso Dark Infor")
    with st.form("login_form"):
        u_email = st.text_input("E-mail").strip()
        u_pass = st.text_input("Senha", type="password").strip()
        if st.form_submit_button("ENTRAR NO SISTEMA"):
            try:
                res = supabase.auth.sign_in_with_password({"email": u_email, "password": u_pass})
                if res.user:
                    st.session_state.logado = True
                    st.rerun()
            except Exception:
                st.error("Acesso negado. Verifique os Secrets e se o usuário tem SENHA MANUAL.")
else:
    st.sidebar.button("Sair", on_click=lambda: st.session_state.update({"logado": False}))
    st.title("🎙️ Gerador de Voz")
    texto = st.text_area("Roteiro:")
    if st.button("GERAR ÁUDIO"):
        if texto:
            with st.spinner("IA Gerando..."):
                try:
                    resp = openai_client.audio.speech.create(model="tts-1", voice="onyx", input=texto[:4000])
                    st.audio(resp.content)
                except Exception as e:
                    st.error(f"Erro OpenAI: {e}")
