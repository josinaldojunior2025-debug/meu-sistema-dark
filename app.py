import streamlit as st
from openai import OpenAI
from supabase import create_client
import uuid

# 1. FORÇAR ESTADO INICIAL
if "logado" not in st.session_state:
    st.session_state.logado = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None

# 2. CONEXÃO (Use a Service Role Key no segredo para ignorar erros de permissão)
s_url = st.secrets["SUPABASE_URL"]
s_key = st.secrets["SUPABASE_KEY"] # Certifique-se que aqui esteja a SERVICE_ROLE
supabase = create_client(s_url, s_key)
openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- FUNÇÃO DE LOGIN DIRETA ---
def executar_login(e, s):
    try:
        res = supabase.auth.sign_in_with_password({"email": e, "password": s})
        if res.user:
            st.session_state.user_id = res.user.id
            st.session_state.logado = True
            st.rerun()
    except:
        st.error("Falha na autenticação.")

# --- CONTROLE DE TELA (NÍVEL 0) ---
if not st.session_state.logado:
    st.title("🛡️ Sistema Dark Infor")
    
    # Campo de entrada sem formulário para evitar o delay do submit
    email_user = st.text_input("E-mail")
    senha_user = st.text_input("Senha", type="password")
    
    if st.button("ACESSAR AGORA"):
        executar_login(email_user, senha_user)

else:
    # SE CHEGOU AQUI, O LOGIN FOI IGNORADO
    st.sidebar.button("Sair", on_click=lambda: st.session_state.update({"logado": False}))
    
    st.title("🎙️ Gerador de Áudio")
    txt = st.text_area("Roteiro:")
    vz = st.selectbox("Voz:", ["onyx", "alloy", "echo", "fable", "nova", "shimmer"])

    if st.button("🔥 GERAR"):
        if txt:
            with st.spinner("Gerando..."):
                try:
                    # Geração OpenAI
                    resp = openai_client.audio.speech.create(model="tts-1", voice=vz, input=txt[:4000])
                    audio_data = resp.content
                    
                    # Upload Direto (A Service Role garante que não haverá erro de política)
                    path = f"audios/{uuid.uuid4()}.mp3"
                    supabase.storage.from_("darkinfor").upload(path, audio_data)
                    
                    # Link e Histórico
                    url = supabase.storage.from_("darkinfor").get_public_url(path)
                    supabase.table("historico_audios").insert({
                        "user_id": st.session_state.user_id,
                        "texto": txt[:50],
                        "url_audio": url
                    }).execute()
                    
                    st.audio(audio_data)
                    st.success("Sucesso!")
                except Exception as e:
                    st.error(f"Erro: {e}")

    # Exibição do histórico simplificada
    st.divider()
    try:
        h = supabase.table("historico_audios").select("*").eq("user_id", st.session_state.user_id).execute()
        for i in h.data:
            st.audio(i['url_audio'])
    except: pass
