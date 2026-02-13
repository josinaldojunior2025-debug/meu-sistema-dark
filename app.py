import streamlit as st
from openai import OpenAI
from supabase import create_client
import uuid
import time

# --- SETUP ---
st.set_page_config(page_title="Dark Infor", layout="wide")

try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error(f"Erro nos Segredos: {e}")

if "user" not in st.session_state:
    st.session_state.user = None

# --- LOGIN (SEM MENSAGENS DUPLAS) ---
if st.session_state.user is None:
    st.title("🛡️ Login Dark Infor")
    t1, t2 = st.tabs(["Entrar", "Cadastrar"])
    with t1:
        e = st.text_input("E-mail", key="email_log")
        s = st.text_input("Senha", type="password", key="pass_log")
        if st.button("Fazer Login"):
            try:
                res = supabase.auth.sign_in_with_password({"email": e, "password": s})
                if res.user:
                    st.session_state.user = res.user
                    st.success("Entrando...") # Única mensagem de sucesso
                    time.sleep(0.5)
                    st.rerun()
            except:
                st.error("Dados incorretos.") # Só aparece se falhar
    with t2:
        ne = st.text_input("Novo E-mail")
        ns = st.text_input("Nova Senha", type="password")
        if st.button("Criar Conta"):
            try:
                supabase.auth.sign_up({"email": ne, "password": ns})
                st.success("Criado!")
            except: st.error("Erro.")

# --- INTERFACE ---
else:
    st.sidebar.write(f"Logado: {st.session_state.user.email}")
    if st.sidebar.button("Sair"):
        st.session_state.user = None
        st.rerun()

    st.title("🎙️ Gerador de Voz")
    txt = st.text_area("Roteiro:", height=200)
    vz = st.selectbox("Voz:", ["onyx", "alloy", "echo", "fable", "nova", "shimmer"])
    
    if st.button("🔥 Gerar e Salvar"):
        if txt:
            with st.spinner("Processando..."):
                try:
                    # 1. Gerar Áudio
                    resp = openai_client.audio.speech.create(model="tts-1", voice=vz, input=txt[:4096])
                    data = resp.content
                    
                    # 2. Upload para Storage (darkinfor minúsculo)
                    path = f"{st.session_state.user.id}/{uuid.uuid4()}.mp3"
                    supabase.storage.from_("darkinfor").upload(path=path, file=data, file_options={"content-type": "audio/mpeg"})
                    
                    # 3. Salvar no Histórico (A tabela que você já criou)
                    url = supabase.storage.from_("darkinfor").get_public_url(path)
                    supabase.table("historico_audios").insert({
                        "user_id": st.session_state.user.id,
                        "texto": txt[:50] + "...",
                        "url_audio": url
                    }).execute()

                    st.audio(data)
                    st.success("Salvo com sucesso!")
                except Exception as ex:
                    st.error(f"Erro: {ex}") # Aqui veremos se o RLS ainda bloqueia

    # --- LISTAGEM ---
    st.divider()
    st.subheader("📜 Meus Áudios")
    try:
        h = supabase.table("historico_audios").select("*").eq("user_id", st.session_state.user.id).execute()
        for i in h.data:
            with st.expander(f"Áudio: {i['texto']}"):
                st.audio(i['url_audio'])
    except:
        st.info("O histórico aparecerá aqui.")
