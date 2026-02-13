import streamlit as st
from openai import OpenAI
from supabase import create_client
import uuid
import time

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Dark Infor", layout="wide")

try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error(f"Erro nos Segredos: {e}")

if "user" not in st.session_state:
    st.session_state.user = None

# --- TELA DE LOGIN ---
if st.session_state.user is None:
    st.title("🛡️ Login Dark Infor")
    t1, t2 = st.tabs(["Entrar", "Cadastrar"])
    with t1:
        e = st.text_input("E-mail", key="email_final")
        s = st.text_input("Senha", type="password", key="pass_final")
        if st.button("Fazer Login"):
            try:
                res = supabase.auth.sign_in_with_password({"email": e, "password": s})
                if res.user:
                    st.session_state.user = res.user
                    st.success("Acesso concedido!")
                    time.sleep(0.5)
                    st.rerun()
            except:
                st.error("E-mail ou senha incorretos.")
else:
    # --- INTERFACE PRINCIPAL ---
    st.sidebar.write(f"Logado: {st.session_state.user.email}")
    if st.sidebar.button("Sair"):
        st.session_state.user = None
        st.rerun()

    st.title("🎙️ Gerador de Voz Profissional")
    txt = st.text_area("Roteiro:", height=200)
    vz = st.selectbox("Voz:", ["onyx", "alloy", "echo", "fable", "nova", "shimmer"])
    
    if st.button("🔥 Gerar e Salvar"):
        if not txt:
            st.warning("Digite um texto.")
        else:
            with st.spinner("Gerando áudio..."):
                try:
                    # Geração OpenAI
                    resp = openai_client.audio.speech.create(model="tts-1", voice=vz, input=txt[:4096])
                    audio_bytes = resp.content
                    
                    # Nome único
                    path = f"{st.session_state.user.id}/{uuid.uuid4()}.mp3"
                    
                    # 1. Upload para o Storage (darkinfor em minúsculas)
                    supabase.storage.from_("darkinfor").upload(path=path, file=audio_bytes, file_options={"content-type": "audio/mpeg"})
                    
                    # 2. Salvar no Banco (Tabela historico_audios)
                    url = supabase.storage.from_("darkinfor").get_public_url(path)
                    supabase.table("historico_audios").insert({
                        "user_id": st.session_state.user.id,
                        "texto": txt[:50] + "...",
                        "url_audio": url
                    }).execute()

                    st.audio(audio_bytes)
                    st.success("Salvo com sucesso!")
                except Exception as ex:
                    st.error(f"Erro: {ex}")

    # --- HISTÓRICO ---
    st.divider()
    st.subheader("📜 Meus Áudios")
    try:
        h = supabase.table("historico_audios").select("*").eq("user_id", st.session_state.user.id).execute()
        if h.data:
            for item in h.data:
                with st.expander(f"Áudio: {item['texto']}"):
                    st.audio(item['url_audio'])
    except:
        st.write("O histórico aparecerá aqui.")
