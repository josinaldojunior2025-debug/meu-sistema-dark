import streamlit as st
from openai import OpenAI
from supabase import create_client
import uuid
import time

# --- SETUP INICIAL ---
st.set_page_config(page_title="Dark Infor", layout="wide")

try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error(f"Erro de configuração: {e}")

if "user" not in st.session_state:
    st.session_state.user = None

# --- FLUXO DE LOGIN (CORREÇÃO DE MENSAGENS DUPLAS) ---
if st.session_state.user is None:
    st.title("🛡️ Login Dark Infor")
    t1, t2 = st.tabs(["Entrar", "Cadastrar"])
    
    with t1:
        e = st.text_input("E-mail", key="email_log")
        s = st.text_input("Senha", type="password", key="pass_log")
        if st.button("Fazer Login"):
            try:
                # Tenta autenticar primeiro
                res = supabase.auth.sign_in_with_password({"email": e, "password": s})
                if res.user:
                    st.session_state.user = res.user
                    st.success("Acesso concedido!")
                    time.sleep(0.6)
                    st.rerun()
                else:
                    st.error("Erro inesperado no login.")
            except Exception:
                # Se cair aqui, é porque a senha/email realmente estão errados
                st.error("E-mail ou senha incorretos.")
else:
    # --- INTERFACE DO GERADOR ---
    st.sidebar.write(f"Logado: {st.session_state.user.email}")
    if st.sidebar.button("Sair"):
        st.session_state.user = None
        st.rerun()

    st.title("🎙️ Gerador de Voz Profissional")
    txt = st.text_area("Roteiro:", height=200)
    vz = st.selectbox("Voz:", ["onyx", "alloy", "echo", "fable", "nova", "shimmer"])
    
    if st.button("🔥 Gerar e Salvar"):
        if not txt:
            st.warning("Por favor, digite um texto.")
        else:
            with st.spinner("Processando áudio..."):
                try:
                    # 1. OpenAI
                    resp = openai_client.audio.speech.create(model="tts-1", voice=vz, input=txt[:4096])
                    audio_data = resp.content
                    
                    # 2. Storage (Bucket: darkinfor)
                    path = f"{st.session_state.user.id}/{uuid.uuid4()}.mp3"
                    supabase.storage.from_("darkinfor").upload(path=path, file=audio_data, file_options={"content-type": "audio/mpeg"})
                    
                    # 3. Banco de Dados (Historico)
                    url = supabase.storage.from_("darkinfor").get_public_url(path)
                    supabase.table("historico_audios").insert({
                        "user_id": st.session_state.user.id,
                        "texto": txt[:50] + "...",
                        "url_audio": url
                    }).execute()

                    st.audio(audio_data)
                    st.success("Áudio gerado e salvo com sucesso!")
                except Exception as ex:
                    st.error(f"Erro técnico: {ex}")

    # --- LISTAGEM DO HISTÓRICO ---
    st.divider()
    st.subheader("📜 Meus Áudios")
    try:
        h = supabase.table("historico_audios").select("*").eq("user_id", st.session_state.user.id).execute()
        if h.data:
            for item in h.data:
                with st.expander(f"Áudio: {item['texto']}"):
                    st.audio(item['url_audio'])
        else:
            st.info("Ainda não há áudios no seu histórico.")
    except:
        st.write("Histórico indisponível no momento.")
