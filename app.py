import streamlit as st
from openai import OpenAI
from supabase import create_client
import uuid

# Configurações Iniciais
st.set_page_config(page_title="Dark Infor", layout="wide")

if "logado" not in st.session_state:
    st.session_state.logado = False

# Conexão com Secrets
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error("Erro nas chaves nos Secrets do Streamlit.")
    st.stop()

# --- TELA DE ACESSO ---
if not st.session_state.logado:
    st.title("🛡️ Acesso Dark Infor")
    
    with st.form("login_form"):
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar no Sistema", use_container_width=True):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
                if res.user:
                    st.session_state.logado = True
                    st.session_state.user_id = res.user.id
                    st.rerun()
            except:
                st.error("Acesso negado. Verifique se o usuario existe e foi confirmado no Supabase.")

# --- TELA DO GERADOR ---
else:
    st.sidebar.button("Sair", on_click=lambda: st.session_state.update({"logado": False}))
    st.title("🎙️ Gerador de Voz")
    
    texto = st.text_area("Roteiro:")
    voz = st.selectbox("Voz:", ["onyx", "alloy", "echo", "fable", "nova", "shimmer"])
    
    if st.button("🔥 GERAR"):
        if texto:
            with st.spinner("Gerando..."):
                try:
                    resp = openai_client.audio.speech.create(model="tts-1", voice=voz, input=texto[:4000])
                    st.audio(resp.content)
                    st.success("Pronto!")
                    
                    # Salva no Banco (Opcional - nao trava se falhar)
                    try:
                        f_name = f"{st.session_state.user_id}/{uuid.uuid4()}.mp3"
                        supabase.storage.from_("darkinfor").upload(path=f_name, file=resp.content)
                    except:
                        pass
                except Exception as e:
                    st.error(f"Erro OpenAI: {e}")
