import streamlit as st
from openai import OpenAI
from supabase import create_client
import uuid

# --- 1. CONFIGURAÇÃO DA PÁGINA E ESTILO ---
st.set_page_config(page_title="Dark Infor - Sistema Profissional", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #ff4b4b; color: white; font-weight: bold; }
    .stTextArea>div>div>textarea { background-color: #161b22; color: white; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. INICIALIZAÇÃO DE CONEXÕES (SECRETS) ---
try:
    # Conecta ao Supabase e OpenAI usando seus Secrets
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error(f"Erro ao carregar as chaves de acesso: {e}")

# Gerenciamento de sessão para evitar desconexões
if "user" not in st.session_state:
    st.session_state.user = None

# --- 3. LÓGICA DE AUTENTICAÇÃO (LOGIN/CADASTRO) ---
def tela_autenticacao():
    st.title("🛡️ Sistema Dark Infor")
    tab_login, tab_cadastro = st.tabs(["Acessar Conta", "Criar Nova Conta"])
    
    with tab_login:
        email = st.text_input("E-mail", key="email_login")
        senha = st.text_input("Senha", type="password", key="senha_login")
        
        if st.button("Fazer Login"):
            try:
                # Tenta autenticar no Supabase
                res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
                if res.user:
                    st.session_state.user = res.user
                    st.success("Login realizado! Entrando...")
                    st.rerun() # Atualiza a tela imediatamente para não dar erro
            except:
                st.error("E-mail ou senha incorretos. Verifique suas credenciais.")

    with tab_cadastro:
        st.info("Sua senha deve ter no mínimo 6 caracteres.")
        novo_email = st.text_input("E-mail", key="email_cad")
        nova_senha = st.text_input("Senha", type="password", key="senha_cad")
        
        if st.button("Cadastrar Agora"):
            try:
                supabase.auth.sign_up({"email": novo_email, "password": nova_senha})
                st.success("Cadastro realizado com sucesso! Agora clique na aba 'Acessar Conta'.")
            except Exception as e:
                st.error(f"Erro ao cadastrar: {e}")

# --- 4. INTERFACE DO GERADOR DE VOZ ---
def interface_principal():
    # Barra lateral de controle
    st.sidebar.markdown(f"👤 **Usuário:**\n{st.session_state.user.email}")
    if st.sidebar.button("Encerrar Sessão (Sair)"):
        st.session_state.user = None
        st.rerun()

    st.title("🎙️ Gerador de Voz Profissional")
    
    # Suporte para textos longos (até 100k caracteres)
    texto_roteiro = st.text_area("Insira o seu roteiro aqui:", height=300, max_chars=100000, placeholder="Era uma vez...")

    col1, col2 = st.columns(2)
    with col1:
        tecnologia = st.selectbox("Tecnologia de Voz:", ["OpenAI (Nativo)", "ElevenLabs (Clonagem)"])
    with col2:
        voz_selecionada = st.selectbox("Escolha a Voz:", ["alloy", "echo", "fable", "onyx", "nova", "shimmer"])

    if st.button("🔥 Gerar Áudio e Salvar no Histórico"):
        if not texto_roteiro:
            st.warning("Por favor, digite um texto para gerar o áudio.")
        else:
            with st.spinner("Processando áudio profissional..."):
                try:
                    # Geração do áudio via OpenAI
                    response = openai_client.audio.speech.create(
                        model="tts-1",
                        voice=voz_selecionada,
                        input=texto_roteiro[:4096] # Limite de caracteres por bloco
                    )
                    audio_bytes = response.content

                    # Criar nome de arquivo único para o Storage
                    id_unico = str(uuid.uuid4())
                    caminho_storage = f"{st.session_state.user.id}/{id_unico}.mp3"

                    # 1. Faz o Upload para o Bucket DARKINFOR
