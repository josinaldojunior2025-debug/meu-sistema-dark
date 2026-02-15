import streamlit as st
from openai import OpenAI
from supabase import create_client

# Configuração da página
st.set_page_config(page_title="Dark Infor", layout="wide")

# Inicialização do estado
if "logado" not in st.session_state:
    st.session_state.logado = False

# Conexão com os serviços
try:
    s_url = st.secrets["SUPABASE_URL"]
    s_key = st.secrets["SUPABASE_KEY"]
    o_key = st.secrets["OPENAI_API_KEY"]
    
    supabase = create_client(s_url, s_key)
    openai_client = OpenAI(api_key=o_key)
except Exception as e:
    st.error(f"Erro de configuração: {e}")
    st.stop()

# --- TELA DE LOGIN ---
if not st.session_state.logado:
    st.title("🛡️ Acesso Dark Infor")
    
    with st.form("login_form"):
        email = st.text_input("E-mail").strip()
        senha = st.text_input("Senha", type="password").strip()
        entrar = st.form_submit_button("ENTRAR")
        
        if entrar:
            try:
                # Login via e-mail e senha manual
                res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
                if res.user:
                    st.session_state.logado = True
                    st.rerun()
            except Exception as e:
                st.error("Falha no acesso. Verifique e-mail e senha.")

# --- TELA DO GERADOR ---
else:
    st.sidebar.button("Sair", on_click=lambda: st.session_state.update({"logado": False}))
    st.title("🎙️ Gerador de Voz Profissional")
    
    texto = st.text_area("Roteiro:", height=200)
    voz = st.selectbox("Escolha a Voz:", ["onyx", "alloy", "echo", "fable", "nova", "shimmer"])
    
    if st.button("🔥 GERAR ÁUDIO"):
        if texto:
            with st.spinner("Gerando voz..."):
                try:
                    response = openai_client.audio.speech.create(
                        model="tts-1",
                        voice=voz,
                        input=texto[:4000]
                    )
                    st.audio(response.content)
                    st.success("Pronto!")
                except Exception as e:
                    st.error(f"Erro na OpenAI: {e}")
