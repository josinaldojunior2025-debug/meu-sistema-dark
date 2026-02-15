import streamlit as st
from openai import OpenAI
from supabase import create_client

# Configuração da página
st.set_page_config(page_title="Dark Infor", layout="wide")

if "logado" not in st.session_state:
    st.session_state.logado = False

# Conexão protegida
try:
    s_url = st.secrets["SUPABASE_URL"]
    s_key = st.secrets["SUPABASE_KEY"]
    o_key = st.secrets["OPENAI_API_KEY"]
    supabase = create_client(s_url, s_key)
    openai_client = OpenAI(api_key=o_key)
except Exception as e:
    st.error("Erro crítico nos Secrets. Verifique se as chaves estão em uma linha só.")
    st.stop()

# --- TELA DE LOGIN ---
if not st.session_state.logado:
    st.title("🛡️ Acesso Dark Infor")
    
    with st.form("login_form"):
        email = st.text_input("E-mail").strip()
        senha = st.text_input("Senha", type="password").strip()
        entrar = st.form_submit_button("ENTRAR NO SISTEMA")
        
        if entrar:
            if not email or not senha:
                st.warning("Preencha todos os campos.")
            else:
                try:
                    # Tenta autenticar
                    res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
                    if res.user:
                        st.session_state.logado = True
                        st.rerun()
                except Exception as e:
                    # Se der erro aqui, é porque a chave ou o usuário estão errados
                    if "Invalid API key" in str(e):
                        st.error("Erro técnico: Chave do Supabase inválida nos Secrets.")
                    else:
                        st.error("Acesso negado. Verifique o usuário e senha no Supabase.")

# --- TELA DO GERADOR ---
else:
    st.sidebar.button("Sair", on_click=lambda: st.session_state.update({"logado": False}))
    st.title("🎙️ Gerador de Voz Profissional")
    texto = st.text_area("Roteiro:", height=200)
    if st.button("🔥 GERAR ÁUDIO"):
        if texto:
            with st.spinner("IA Gerando..."):
                try:
                    resp = openai_client.audio.speech.create(model="tts-1", voice="onyx", input=texto[:4000])
                    st.audio(resp.content)
                except Exception as e:
                    st.error(f"Erro na OpenAI: {e}")
