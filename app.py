import streamlit as st
from openai import OpenAI
from supabase import create_client

st.set_page_config(page_title="Dark Infor", layout="wide")

if "logado" not in st.session_state:
    st.session_state.logado = False

# Só tenta conectar se as chaves existirem para evitar erro imediato
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error("Erro na leitura das chaves. Verifique se colou o bloco TOML corretamente.")
    st.stop()

if not st.session_state.logado:
    st.title("🛡️ Acesso Dark Infor")
    
    with st.form("login_form"):
        email = st.text_input("E-mail").strip()
        senha = st.text_input("Senha", type="password").strip()
        entrar = st.form_submit_button("ENTRAR")
        
        # O sistema só valida quando você clica no botão
        if entrar:
            if email and senha:
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
                    if res.user:
                        st.session_state.logado = True
                        st.rerun()
                except Exception:
                    st.error("Falha no login. Verifique e-mail e senha no Supabase.")
            else:
                st.warning("Por favor, preencha os campos.")
else:
    st.title("🎙️ Gerador de Voz")
    texto = st.text_area("Roteiro:")
    if st.button("GERAR"):
        with st.spinner("Gerando..."):
            try:
                resp = openai_client.audio.speech.create(model="tts-1", voice="onyx", input=texto)
                st.audio(resp.content)
            except Exception as e:
                st.error(f"Erro: {e}")
