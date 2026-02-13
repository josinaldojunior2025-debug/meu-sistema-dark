import streamlit as st
from openai import OpenAI
from supabase import create_client
import uuid
import time

# --- 1. CONFIGURAÇÃO DA PÁGINA E SESSÃO ---
st.set_page_config(page_title="Dark Infor - Gerador Profissional", layout="wide")

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "usuario_id" not in st.session_state:
    st.session_state.usuario_id = None

# --- 2. CONEXÃO COM AS CHAVES DOS SECRETS ---
try:
    # O código busca exatamente os nomes que você salvou nos Secrets
    s_url = st.secrets["SUPABASE_URL"]
    s_key = st.secrets["SUPABASE_KEY"]
    o_key = st.secrets["OPENAI_API_KEY"]
    
    supabase = create_client(s_url, s_key)
    openai_client = OpenAI(api_key=o_key)
except Exception as e:
    st.error(f"⚠️ Erro de Configuração: Verifique se os nomes nos Secrets estão corretos. (Detalhe: {e})")
    st.stop()

# --- 3. LÓGICA DE NAVEGAÇÃO (LOGIN OU GERADOR) ---

# TELA DE LOGIN
if not st.session_state.autenticado:
    st.title("🛡️ Acesso Dark Infor")
    
    with st.container():
        email_input = st.text_input("E-mail")
        senha_input = st.text_input("Senha", type="password")
        
        if st.button("ENTRAR NO SISTEMA", use_container_width=True):
            try:
                # Autenticação no Supabase
                res = supabase.auth.sign_in_with_password({"email": email_input, "password": senha_input})
                if res.user:
                    st.session_state.autenticado = True
                    st.session_state.usuario_id = res.user.id
                    st.success("Login realizado! Entrando...")
                    time.sleep(0.5)
                    st.rerun() # Limpa a tela e vai para o gerador
            except Exception:
                st.error("E-mail ou senha inválidos.")

# TELA DO GERADOR (SÓ APARECE SE ESTIVER LOGADO)
else:
    # Menu Lateral
    st.sidebar.title("Menu")
    st.sidebar.write(f"Logado como: {st.session_state.usuario_id[:8]}...")
    if st.sidebar.button("Encerrar Sessão"):
        st.session_state.autenticado = False
        st.session_state.usuario_id = None
        st.rerun()

    st.title("🎙️ Gerador de Voz Profissional")
    
    # Área de entrada
    texto_roteiro = st.text_area("Digite ou cole seu roteiro aqui:", height=250, placeholder="Olá, este é um exemplo de locução...")
    
    col1, col2 = st.columns(2)
    with col1:
        voz_selecionada = st.selectbox("Escolha a Voz:", ["onyx", "alloy", "echo", "fable", "nova", "shimmer"])
    with col2:
        modelo_ia = st.radio("Modelo:", ["tts-1", "tts-1-hd"], horizontal=True)

    if st.button("🔥 GERAR ÁUDIO AGORA", use_container_width=True):
        if not texto_roteiro:
            st.warning("Por favor, escreva um texto antes de gerar.")
        else:
            with st.spinner("A IA está processando sua voz..."):
                try:
                    # 1. Solicitação para a OpenAI (Isso gera o som)
                    audio_response = openai_client.audio.speech.create(
                        model=modelo_ia,
                        voice=voz_selecionada,
                        input=texto_roteiro[:4000] # Limite de caracteres
                    )
                    audio_bytes = audio_response.content
                    
                    # 2. Exibição do Player (Aparece na hora para o usuário)
                    st.audio(audio_bytes)
                    st.success("Á
