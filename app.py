import streamlit as st
from openai import OpenAI
from supabase import create_client, Client

st.set_page_config(page_title="Dark Infor", layout="wide")

if "logado" not in st.session_state:
    st.session_state.logado = False

# Conexão
try:
    supabase: Client = create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )
    openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error("Erro nos Secrets. Verifique as chaves.")
    st.stop()

# --- LOGIN ---
if not st.session_state.logado:
    st.title("🛡️ Acesso Dark Infor")

    with st.form("login_form"):
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")

        if st.form_submit_button("ENTRAR", use_container_width=True):

            if not email or not senha:
                st.warning("Preencha e-mail e senha.")
                st.stop()

            try:
                res = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": senha
                })

                if res.user:
                    st.session_state.logado = True
                    st.session_state.u_id = res.user.id
                    st.success("Login realizado!")
                    st.rerun()
                else:
                    st.error("Usuário não retornado.")

            except Exception as e:
                st.error(f"Falha no login: {e}")

# --- APP ---
else:
    st.title("🎙️ Gerador de Voz Profissional")

    texto = st.text_area("Roteiro:", height=200)
    voz = st.selectbox("Voz:", ["onyx", "alloy", "nova", "shimmer"])

    if st.button("GERAR ÁUDIO"):

        if not texto:
            st.warning("Digite um roteiro.")
            st.stop()

        with st.spinner("IA Processando..."):
            try:
                resp = openai_client.audio.speech.create(
                    model="tts-1",
                    voice=voz,
                    input=texto[:4000]
                )

                st.audio(resp.content)
                st.success("Áudio gerado!")

            except Exception as e:
                st.error(f"Erro OpenAI: {e}")

    if st.button("Logout"):
        st.session_state.logado = False
        st.rerun()
