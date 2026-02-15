import streamlit as st
from openai import OpenAI
from supabase import create_client
import uuid

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Dark Infor - Locução IA", layout="wide", page_icon="🎙️")

# Estilo CSS para parecer profissional
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #ff4b4b; color: white; }
    .stTextInput>div>div>input { color: white; }
    </style>
    """, unsafe_content_allowed=True)

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

# --- CONEXÕES ---
@st.cache_resource
def iniciar_conexoes():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        openai_key = st.secrets["OPENAI_API_KEY"]
        
        supabase_client = create_client(url, key)
        openai_client = OpenAI(api_key=openai_key)
        return supabase_client, openai_client
    except Exception as e:
        st.error(f"Erro de configuração: {e}")
        return None, None

supabase, openai_client = iniciar_conexoes()

# --- LÓGICA DE ACESSO ---
if not st.session_state.autenticado:
    st.title("🛡️ Sistema Dark Infor")
    st.subheader("Acesse para gerar suas locuções")
    
    with st.container():
        email = st.text_input("E-mail").strip()
        senha = st.text_input("Senha", type="password").strip()
        
        if st.button("ENTRAR NO SISTEMA"):
            if email and senha:
                try:
                    # Tenta autenticar no Supabase
                    auth = supabase.auth.sign_in_with_password({"email": email, "password": senha})
                    if auth.user:
                        st.session_state.autenticado = True
                        st.session_state.user_id = auth.user.id
                        st.success("Acesso liberado!")
                        st.rerun()
                except Exception as e:
                    # Se der "Invalid API key", o erro está nos Secrets do Streamlit
                    if "Invalid API key" in str(e):
                        st.error("Erro técnico: A SUPABASE_KEY nos Secrets está incorreta.")
                    else:
                        st.error("E-mail ou senha não encontrados.")
            else:
                st.warning("Preencha todos os campos.")

# --- PAINEL DO GERADOR ---
else:
    st.sidebar.title("🎙️ Menu")
    if st.sidebar.button("SAIR"):
        st.session_state.autenticado = False
        st.rerun()

    st.title("🎙️ Gerador de Locução Profissional")
    
    texto = st.text_area("Digite o roteiro aqui:", placeholder="Ex: Olá, seja bem-vindo à Dark Infor...", height=200)
    
    col1, col2 = st.columns(2)
    with col1:
        voz = st.selectbox("Escolha a Voz:", ["onyx", "alloy", "echo", "fable", "nova", "shimmer"])
    with col2:
        modelo = st.radio("Qualidade:", ["tts-1", "tts-1-hd"], horizontal=True)

    if st.button("🔥 GERAR ÁUDIO AGORA"):
        if not texto:
            st.error("Por favor, digite um texto.")
        else:
            with st.spinner("IA processando voz..."):
                try:
                    # Gera áudio na OpenAI
                    response = openai_client.audio.speech.create(
                        model=modelo,
                        voice=voz,
                        input=texto[:4000]
                    )
                    
                    audio_content = response.content
                    st.audio(audio_content)
                    st.success("Áudio gerado com sucesso!")
                    
                    # Tenta salvar no banco (opcional)
                    try:
                        nome_arquivo = f"{st.session_state.user_id}/{uuid.uuid4()}.mp3"
                        supabase.storage.from_("darkinfor").upload(nome_arquivo, audio_content)
                    except:
                        pass # Continua mesmo se falhar o upload
                        
                except Exception as e:
                    st.error(f"Erro na OpenAI: {e}")
