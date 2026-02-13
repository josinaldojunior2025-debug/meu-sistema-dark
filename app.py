import streamlit as st
from openai import OpenAI
from supabase import create_client
import uuid
import time

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Dark Infor - Locução IA", layout="wide")

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "usuario_id" not in st.session_state:
    st.session_state.usuario_id = None

# --- 2. CONEXÕES ---
try:
    # Busca exatamente os nomes definidos nos seus Secrets
    s_url = st.secrets["SUPABASE_URL"]
    s_key = st.secrets["SUPABASE_KEY"]
    o_key = st.secrets["OPENAI_API_KEY"]
    
    supabase = create_client(s_url, s_key)
    openai_client = OpenAI(api_key=o_key)
except Exception as e:
    st.error("Erro de configuração nos Secrets. Verifique os nomes das chaves.")
    st.stop()

# --- 3. LÓGICA DE LOGIN ---
if not st.session_state.autenticado:
    st.title("🛡️ Acesso Dark Infor")
    with st.form("form_login"):
        email_input = st.text_input("E-mail")
        senha_input = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar no Sistema"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email_input, "password": senha_input})
                if res.user:
                    st.session_state.autenticado = True
                    st.session_state.usuario_id = res.user.id
                    st.success("Login confirmado!")
                    time.sleep(0.5)
                    st.rerun()
            except:
                st.error("Dados de acesso incorretos.")

# --- 4. TELA DO GERADOR ---
else:
    st.sidebar.title("Painel")
    if st.sidebar.button("Sair"):
        st.session_state.autenticado = False
        st.rerun()

    st.title("🎙️ Gerador de Voz Profissional")
    
    texto_input = st.text_area("Roteiro:", height=200, placeholder="Digite o texto aqui...")
    
    col1, col2 = st.columns(2)
    with col1:
        voz = st.selectbox("Voz:", ["onyx", "alloy", "echo", "fable", "nova", "shimmer"])
    with col2:
        modelo = st.radio("Qualidade:", ["tts-1", "tts-1-hd"], horizontal=True)

    if st.button("🔥 GERAR ÁUDIO", use_container_width=True):
        if not texto_input:
            st.warning("Escreva algo antes de gerar.")
        else:
            with st.spinner("IA Processando..."):
                try:
                    # Geração na OpenAI
                    audio_res = openai_client.audio.speech.create(
                        model=modelo,
                        voice=voz,
                        input=texto_input[:4000]
                    )
                    audio_bytes = audio_res.content
                    
                    # Player na tela
                    st.audio(audio_bytes)
                    st.success("Audio gerado com sucesso!")
                    
                    # Salva no Banco/Storage
                    try:
                        file_path = f"{st.session_state.usuario_id}/{uuid.uuid4()}.mp3"
                        supabase.storage.from_("darkinfor").upload(path=file_path, file=audio_bytes)
                        
                        public_url = supabase.storage.from_("darkinfor").get_public_url(file_path)
                        supabase.table("historico_audios").insert({
                            "user_id": st.session_state.usuario_id,
                            "texto": texto_input[:50],
                            "url_audio": public_url
                        }).execute()
                        st.info("Salvo no historico!")
                    except:
                        st.warning("Audio gerado, mas erro ao salvar no historico.")
                        
                except Exception as e_api:
                    st.error(f"Erro OpenAI: {e_api}")

    # --- HISTÓRICO ---
    st.divider()
    st.subheader("📜 Ultimos Audios")
    try:
        h = supabase.table("historico_audios").select("*").eq("user_id", st.session_state.usuario_id).order("id", desc=True).limit(5).execute()
        if h.data:
            for item in h.data:
                with st.expander(f"Texto: {item['texto']}..."):
                    st.audio(item['url_audio'])
    except:
        pass
