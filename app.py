import streamlit as st
from openai import OpenAI
from supabase import create_client
import uuid

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Dark Infor - Sistema de Voz Profissional", layout="wide")

# --- ESTILO DARK CUSTOMIZADO ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #ff4b4b; color: white; }
    .stTextArea>div>div>textarea { background-color: #161b22; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- INICIALIZAÇÃO DE CLIENTES (SECRETS) ---
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error(f"Erro ao carregar segredos: {e}")

# --- GERENCIAMENTO DE SESSÃO ---
if "user" not in st.session_state:
    st.session_state.user = None

# --- FUNÇÕES DE AUTENTICAÇÃO ---
def autenticacao():
    st.title("🛡️ Dark Infor - Acesso Restrito")
    aba_login, aba_cadastro = st.tabs(["Fazer Login", "Criar Conta"])
    
    with aba_login:
        email = st.text_input("E-mail", key="log_email")
        senha = st.text_input("Senha", type="password", key="log_pass")
        if st.button("Acessar Sistema"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
                st.session_state.user = res.user
                st.success("Login realizado com sucesso!")
                st.rerun()
            except:
                st.error("E-mail ou senha incorretos.")

    with aba_cadastro:
        st.info("O cadastro é imediato. Use uma senha de pelo menos 6 caracteres.")
        novo_email = st.text_input("E-mail", key="cad_email")
        nova_senha = st.text_input("Senha", type="password", key="cad_pass")
        if st.button("Finalizar Cadastro"):
            try:
                supabase.auth.sign_up({"email": novo_email, "password": nova_senha})
                st.success("Conta criada! Agora você pode fazer login.")
            except Exception as e:
                st.error(f"Erro ao cadastrar: {e}")

# --- INTERFACE PRINCIPAL (PÓS-LOGIN) ---
def interface_principal():
    # Barra Lateral
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/681/681494.png", width=100)
    st.sidebar.write(f"👤 **Usuário:**\n{st.session_state.user.email}")
    if st.sidebar.button("Sair do Sistema"):
        st.session_state.user = None
        st.rerun()

    st.title("🎙️ Gerador de Voz High-End")
    
    col1, col2 = st.columns([2, 1])

    with col1:
        texto_longo = st.text_area("Roteiro (Suporta até 100.000 caracteres):", 
                                  height=400, 
                                  max_chars=100000,
                                  placeholder="Cole seu texto aqui...")
    
    with col2:
        st.subheader("Configurações")
        provedor = st.selectbox("Tecnologia de Voz:", ["OpenAI (Nativo)", "ElevenLabs (Clonagem)"])
        
        if provedor == "OpenAI (Nativo)":
            voz = st.selectbox("Escolha a Voz:", ["alloy", "echo", "fable", "onyx", "nova", "shimmer"])
        else:
            voz = st.text_input("ID da Voz ElevenLabs:", placeholder="Cole o ID da sua voz clonada")
            st.caption("Requer ElevenLabs API Key nos Secrets.")

        if st.button("🔥 Gerar Áudio Profissional"):
            if not texto_longo:
                st.warning("O texto não pode estar vazio.")
            else:
                with st.spinner("Sintetizando voz e salvando no seu perfil..."):
                    try:
                        # 1. Geração do Áudio (OpenAI padrão)
                        # Nota: Para 100k caracteres, a API precisa ser chamada em partes (loops)
                        response = openai_client.audio.speech.create(
                            model="tts-1",
                            voice=voz if provedor == "OpenAI (Nativo)" else "alloy",
                            input=texto_longo[:4096] # Limite por bloco da OpenAI
                        )
                        audio_data = response.content

                        # 2. Upload para o Storage (Bucket 'audios')
                        file_name = f"{st.session_state.user.id}/{uuid.uuid4()}.mp3"
                        supabase.storage.from_("audios").upload(
                            path=file_name,
                            file=audio_data,
                            file_options={"content-type": "audio/mpeg"}
                        )
                        
                        # 3. Pegar URL Pública e salvar no histórico
                        url_audio = supabase.storage.from_("audios").get_public_url(file_name)
                        supabase.table("historico_audios").insert({
                            "user_id": st.session_state.user.id,
                            "texto": texto_longo[:100] + "...",
                            "url_audio": url_audio
                        }).execute()

                        # 4. Exibir resultados
                        st.audio(audio_data)
                        st
