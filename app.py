import streamlit as st
from openai import OpenAI
from supabase import create_client
import uuid

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Dark Infor - Voz Profissional", layout="wide")

# --- INICIALIZAÇÃO DE CLIENTES ---
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error(f"Erro nos Segredos: {e}")

if "user" not in st.session_state:
    st.session_state.user = None

# --- TELAS DE ACESSO ---
def autenticacao():
    st.title("🛡️ Acesso Dark Infor")
    aba_login, aba_cadastro = st.tabs(["Login", "Cadastro"])
    
    with aba_login:
        email = st.text_input("E-mail", key="log_email")
        senha = st.text_input("Senha", type="password", key="log_pass")
        if st.button("Entrar"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
                st.session_state.user = res.user
                st.rerun()
            except:
                st.error("E-mail ou senha incorretos.")

    with aba_cadastro:
        n_email = st.text_input("Novo E-mail", key="cad_email")
        n_senha = st.text_input("Nova Senha", type="password", key="cad_pass")
        if st.button("Criar Conta"):
            try:
                supabase.auth.sign_up({"email": n_email, "password": n_senha})
                st.success("Conta criada! Tente fazer o login.")
            except Exception as e:
                st.error(f"Erro: {e}")

# --- INTERFACE DO GERADOR ---
def interface_gerador():
    st.sidebar.write(f"Logado como: {st.session_state.user.email}")
    if st.sidebar.button("Sair"):
        st.session_state.user = None
        st.rerun()

    st.title("🎙️ Gerador de Voz Profissional")
    
    texto = st.text_area("Roteiro (Até 100k caracteres):", height=300, max_chars=100000)
    
    # LINHA 67 CORRIGIDA AQUI:
    col1, col2 = st.columns(2)
    
    with col1:
        provedor = st.selectbox("Tecnologia:", ["OpenAI", "ElevenLabs"])
    with col2:
        voz = st.selectbox("Voz:", ["alloy", "echo", "fable", "onyx", "nova", "shimmer"])

    if st.button("Gerar Áudio e Salvar"):
        if not texto:
            st.warning("Insira um texto.")
        else:
            with st.spinner("Sintetizando..."):
                try:
                    response = openai_client.audio.speech.create(
                        model="tts-1",
                        voice=voz,
                        input=texto[:4096]
                    )
                    audio_bytes = response.content
                    nome_arquivo = f"{st.session_state.user.id}/{uuid.uuid4()}.mp3"

                    # UPLOAD PARA O BUCKET DARKINFOR
                    supabase.storage.from_("DARKINFOR").upload(
                        path=nome_arquivo,
                        file=audio_bytes,
                        file_options={"content-type": "audio/mpeg"}
                    )

                    url_pub = supabase.storage.from_("DARKINFOR").get_public_url(nome_arquivo)

                    supabase.table("historico_audios").insert({
                        "user_id": st.session_state.user.id,
                        "texto": texto[:100],
                        "url_audio": url_pub
                    }).execute()

                    st.audio(audio_bytes)
                    st.download_button("📥 Baixar MP3", data=audio_bytes, file_name="audio.mp3")
                    st.success("Salvo no histórico!")
                except Exception as e:
                    st.error(f"Erro: {e}")

# --- LÓGICA PRINCIPAL ---
if st.session_state.user is None:
    autenticacao()
else:
    interface_gerador()
