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

# --- TELA DE ACESSO ---
if st.session_state.user is None:
    st.title("🛡️ Login Dark Infor")
    tab1, tab2 = st.tabs(["Entrar", "Cadastrar"])
    with tab1:
        email = st.text_input("E-mail", key="email_v4")
        senha = st.text_input("Senha", type="password", key="pass_v4")
        if st.button("Fazer Login"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
                if res.user:
                    st.session_state.user = res.user
                    st.success("Entrando...")
                    time.sleep(0.5)
                    st.rerun()
            except:
                st.error("Dados incorretos.")
    with tab2:
        n_email = st.text_input("Novo E-mail")
        n_senha = st.text_input("Nova Senha", type="password")
        if st.button("Criar Conta"):
            try:
                supabase.auth.sign_up({"email": n_email, "password": n_senha})
                st.success("Criado!")
            except:
                st.error("Erro.")

# --- INTERFACE PRINCIPAL ---
else:
    st.sidebar.write(f"Logado: {st.session_state.user.email}")
    if st.sidebar.button("Sair"):
        st.session_state.user = None
        st.rerun()

    st.title("🎙️ Gerador de Voz Profissional")
    texto = st.text_area("Roteiro:", height=250, max_chars=100000)
    
    voz = st.selectbox("Escolha a Voz:", ["onyx", "alloy", "echo", "fable", "nova", "shimmer"])
    
    if st.button("🔥 Gerar e Salvar"):
        if texto:
            with st.spinner("Gerando..."):
                try:
                    # Geração OpenAI
                    response = openai_client.audio.speech.create(model="tts-1", voice=voz, input=texto[:4096])
                    audio_data = response.content
                    
                    # Nome do arquivo
                    caminho = f"{st.session_state.user.id}/{uuid.uuid4()}.mp3"
                    
                    # BUCKET: darkinfor (minúsculas conforme sua policy)
                    bucket_id = "darkinfor"

                    # 1. Upload para o Storage
                    supabase.storage.from_(bucket_id).upload(
                        path=caminho, 
                        file=audio_data, 
                        file_options={"content-type": "audio/mpeg"}
                    )

                    # 2. Link Público
                    url_p = supabase.storage.from_(bucket_id).get_public_url(caminho)

                    # 3. Salvar no Banco (Tabela historico_audios)
                    supabase.table("historico_audios").insert({
                        "user_id": st.session_state.user.id,
                        "texto": texto[:50] + "...",
                        "url_audio": url_p
                    }).execute()

                    st.audio(audio_data)
                    st.success("Áudio salvo com sucesso!")
                except Exception as e:
                    st.error(f"Erro no processamento: {e}")

    # --- HISTÓRICO ---
    st.divider()
    st.subheader("📜 Meus Áudios")
    try:
        hist = supabase.table("historico_audios").select("*").eq("user_id", st.session_state.user.id).execute()
        for item in hist.data:
            with st.expander(f"Áudio: {item['texto']}"):
                st.audio(item['url_audio'])
    except:
        st.info("O histórico aparecerá aqui.")
