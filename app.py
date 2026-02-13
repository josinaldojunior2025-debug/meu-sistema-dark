import streamlit as st
from openai import OpenAI
from supabase import create_client
import uuid

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Dark Infor", layout="wide")

# Mantém o login vivo na memória
if "logado" not in st.session_state:
    st.session_state.logado = False
if "user" not in st.session_state:
    st.session_state.user = None

# Clientes
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except:
    st.error("Erro nas chaves de conexão.")

# --- TELA 1: LOGIN ---
if not st.session_state.logado:
    st.title("🛡️ Acesso Dark Infor")
    email = st.text_input("E-mail")
    senha = st.text_input("Senha", type="password")
    
    if st.button("Entrar no Sistema", use_container_width=True):
        try:
            res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
            if res.user:
                st.session_state.logado = True
                st.session_state.user = res.user
                st.rerun() # Pula para o gerador imediatamente
        except:
            st.error("E-mail ou senha incorretos.")

# --- TELA 2: GERADOR (SÓ APARECE SE ESTIVER LOGADO) ---
else:
    st.sidebar.write(f"Conectado: {st.session_state.user.email}")
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    st.title("🎙️ Gerador de Voz Profissional")
    txt = st.text_area("Roteiro:", height=200)
    voz = st.selectbox("Voz:", ["onyx", "alloy", "echo", "fable", "nova", "shimmer"])
    
    if st.button("🔥 Gerar e Salvar"):
        if txt:
            with st.spinner("Gerando..."):
                try:
                    resp = openai_client.audio.speech.create(model="tts-1", voice=voz, input=txt[:4000])
                    audio_bytes = resp.content
                    
                    # Salva no Storage e Banco
                    path = f"{st.session_state.user.id}/{uuid.uuid4()}.mp3"
                    supabase.storage.from_("darkinfor").upload(path=path, file=audio_bytes)
                    url = supabase.storage.from_("darkinfor").get_public_url(path)
                    
                    supabase.table("historico_audios").insert({
                        "user_id": st.session_state.user.id,
                        "texto": txt[:50] + "...",
                        "url_audio": url
                    }).execute()
                    
                    st.audio(audio_bytes)
                    st.success("Áudio salvo no histórico!")
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

    # Histórico
    st.divider()
    st.subheader("📜 Meus Áudios")
    try:
        h = supabase.table("historico_audios").select("*").eq("user_id", st.session_state.user.id).execute()
        for item in h.data:
            with st.expander(f"Áudio: {item['texto']}"):
                st.audio(item['url_audio'])
    except:
        st.info("O histórico aparecerá aqui.")
