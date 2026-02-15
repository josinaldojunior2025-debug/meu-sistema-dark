import streamlit as st
from openai import OpenAI
from supabase import create_client

# Configuração da página
st.set_page_config(page_title="Dark Infor", layout="wide")

# Inicialização do estado de login
if "logado" not in st.session_state:
    st.session_state.logado = False

# Conexão com os serviços usando os Secrets
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error(f"Erro de configuração nos Secrets: {e}")
    st.stop()

# --- TELA DE LOGIN ---
if not st.session_state.logado:
    st.title("🛡️ Acesso Dark Infor")
    
    with st.form("login_form"):
        email = st.text_input("E-mail").strip()
        senha = st.text_input("Senha", type="password").strip()
        entrar = st.form_submit_button("ENTRAR NO SISTEMA")
        
        if entrar:
            try:
                # Autenticação no Supabase
                res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
                if res.user:
                    st.session_state.logado = True
                    st.rerun()
            except Exception as e:
                st.error("Acesso negado. Verifique se o e-mail e senha estão corretos e se o usuário não é OAuth.")

# --- TELA DO GERADOR ---
else:
    st.sidebar.button("Sair", on_click=lambda: st.session_state.update({"logado": False}))
    st.title("🎙️ Gerador de Voz Profissional")
    
    texto = st.text_area("Roteiro:", height=200, placeholder="Digite seu texto aqui...")
    voz = st.selectbox("Escolha a Voz:", ["onyx", "alloy", "echo", "fable", "nova", "shimmer"])
    
    if st.button("🔥 GERAR ÁUDIO"):
        if not texto:
            st.warning("Por favor, digite um texto.")
        else:
            with st.spinner("IA processando áudio..."):
                try:
                    response = openai_client.audio.speech.create(
                        model="tts-1",
                        voice=voz,
                        input=texto[:4000]
                    )
                    st.audio(response.content)
                    st.success("Áudio gerado!")
                except Exception as e:
                    st.error(f"Erro na OpenAI: {e}")
