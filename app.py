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
    st.error(f"Erro de conexão: {e}")

if "user" not in st.session_state:
    st.session_state.user = None

# --- BLOCO DE LOGIN (MANTIDO EXATAMENTE COMO ESTÁ) ---
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
                    st.success("Acesso concedido!")
                    time.sleep(0.6)
                    st.rerun()
            except:
                st.error("E-mail ou senha incorretos.")
    with t2:
        ne = st.text_input("Novo E-mail")
        ns = st.text_input("Nova Senha", type="password")
        if st.button("Criar Conta"):
            try:
                supabase.auth.sign_up({"email": ne, "password": ns})
                st.success("Criado!")
            except: st.error("Erro.")

# --- PARTE DE GERAÇÃO (CORRIGIDA) ---
else:
    st.sidebar.write(f"Logado: {st.session_state.user.email}")
    if st.sidebar.button("Sair"):
        st.session_state.user = None
        st.rerun()

    st.title("🎙️ Gerador de Voz Profissional")
    txt = st.text_area("Roteiro:", height=200)
    vz = st.selectbox("Voz:", ["onyx", "alloy", "echo", "fable", "nova", "shimmer"])
    
    if st.button("🔥 Gerar e Salvar"):
        if txt:
            with st.spinner("Processando..."):
                try:
                    # 1. OpenAI
                    resp = openai_client.audio.speech.create(model="tts-1", voice=vz, input=txt[:4096])
                    audio_data = resp.content
                    
                    # 2. Upload (Bucket: darkinfor)
                    path = f"{st.session_state.user.id}/{uuid.uuid4()}.mp3"
                    supabase.storage.from_("darkinfor").upload(path=path, file=audio_data, file_options={"content-type": "audio/mpeg"})
                    
                    # 3. Salvar no Banco (Aqui o SQL acima resolve o erro 403)
                    url = supabase.storage.from_("darkinfor").get_public_url(path)
                    supabase.table("historico_audios").insert({
                        "user_id": st.session_state.user.id,
                        "texto": txt[:50] + "...",
                        "url_audio": url
                    }).execute()

                    st.audio(audio_data)
                    st.success("Salvo com sucesso!")
                except Exception as ex:
                    st.error(f"Erro técnico: {ex}")

    # --- HISTÓRICO ---
    st.divider()
    st.subheader("📜 Meus Áudios")
    try:
        h = supabase.table("historico_audios").select("*").eq("user_id", st.session_state.user.id).execute()
        for i in h.data:
            with st.expander(f"Áudio: {i['texto']}"):
                st.audio(i['url_audio'])
    except:
        st.write("O histórico aparecerá aqui.")
