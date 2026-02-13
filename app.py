import streamlit as st
from openai import OpenAI
from supabase import create_client
import time

# Configuração simples
st.set_page_config(page_title="Dark Infor", layout="wide")

if "logado" not in st.session_state:
    st.session_state.logado = False

# Conexão com chaves
try:
    # O código busca exatamente os nomes nos seus Secrets
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error("Erro nas chaves dos Secrets.")
    st.stop()

# --- LOGIN ---
if not st.session_state.logado:
    st.title("🛡️ Acesso Dark Infor")
    with st.form("login"):
        u_email = st.text_input("E-mail")
        u_pass = st.text_input("Senha", type="password")
        if st.form_submit_button("ENTRAR"):
            try:
                # Agora vai funcionar se você criou o usuário com senha manual
                res = supabase.auth.sign_in_with_password({"email": u_email, "password": u_pass})
                if res.user:
                    st.session_state.logado = True
                    st.session_state.u_id = res.user.id
                    st.rerun()
            except:
                st.error("Erro: Verifique e-mail e senha (devem ser os mesmos criados no Supabase).")

# --- GERADOR ---
else:
    st.title("🎙️ Gerador de Voz Profissional")
    txt = st.text_area("Roteiro:")
    voz = st.selectbox("Voz:", ["onyx", "alloy", "nova", "shimmer"])
    
    if st.button("GERAR"):
        if txt:
            with st.spinner("Gerando..."):
                try:
                    resp = openai_client.audio.speech.create(model="tts-1", voice=voz, input=txt[:4000])
                    st.audio(resp.content)
                    st.success("Áudio gerado!")
                except Exception as e:
                    st.error(f"Erro OpenAI: {e}")
