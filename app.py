import streamlit as st
from openai import OpenAI
from supabase import create_client
import uuid

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Dark Infor", layout="wide")

# Inicializa as variáveis para não perder o login no clique
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "dados_usuario" not in st.session_state:
    st.session_state.dados_usuario = None

# Conexão com os serviços
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error("Erro de conexão com as chaves secretas.")

# --- FUNÇÃO DE LOGIN ---
def fazer_login(email, senha):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
        if res.user:
            st.session_state.autenticado = True
            st.session_state.dados_usuario = res.user
            st.rerun()
    except:
        st.error("E-mail ou senha incorretos.")

# --- CONTROLE DE TELAS ---
if not st.session_state.autenticado:
    # TELA DE LOGIN
    st.title("🛡️ Acesso Dark Infor")
    
    with st.container():
        email_input = st.text_input("E-mail")
        senha_input = st.text_input("Senha", type="password")
        
        if st.button("Entrar no Sistema", use_container_width=True):
            if email_input and senha_input:
                fazer_login(email_input, senha_input)
            else:
                st.warning("Preencha todos os campos.")
else:
    # TELA DO GERADOR (SÓ APARECE SE ESTIVER LOGADO)
    st.sidebar.write(f"Conectado: {st.session_state.dados_usuario.email}")
    if st.sidebar.button("Sair"):
        st.session_state.autenticado = False
        st.session_state.dados_usuario = None
        st.rerun()

    st.title("🎙️ Gerador de Voz Profissional")
    
    texto = st.text_area("Roteiro:", height=200)
    voz = st.selectbox("Escolha a Voz:", ["onyx", "alloy", "echo", "fable", "nova", "shimmer"])
    
    if st.button("🔥 Gerar e Salvar"):
        if texto:
            with st.spinner("Processando..."):
                try:
                    # 1. OpenAI gera o áudio
                    resp = openai_client.audio.speech.create(
                        model="tts-1", voice=voz, input=texto[:4000]
                    )
                    audio_bytes = resp.content
                    
                    # 2. Upload para o Storage (Bucket darkinfor)
                    caminho = f"{st.session_state.dados_usuario.id}/{uuid.uuid4()}.mp3"
                    supabase.storage.from_("darkinfor").upload(
                        path=caminho, 
                        file=audio_bytes, 
                        file_options={"content-type": "audio/mpeg"}
                    )
                    
                    # 3. Salva no Banco de Histórico
                    url_p = supabase.storage.from_("darkinfor").get_public_url(caminho)
                    supabase.table("historico_audios").insert({
                        "user_id": st.session_state.dados_usuario.id,
                        "texto": texto[:50] + "...",
                        "url_audio": url_p
                    }).execute()
                    
                    st.audio(audio_bytes)
                    st.success("Áudio gerado e salvo com sucesso!")
                except Exception as e:
                    st.error(f"Erro na geração/salvamento: {e}")

    # Exibição do Histórico
    st.divider()
    st.subheader("📜 Meus Áudios")
    try:
        historico = supabase.table("historico_audios").select("*").eq("user_id", st.session_state.dados_usuario.id).execute()
        for item in historico.data:
            with st.expander(f"Áudio: {item['texto']}"):
                st.audio(item['url_audio'])
    except:
        st.info("O histórico aparecerá aqui.")
