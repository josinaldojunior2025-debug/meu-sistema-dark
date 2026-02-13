import streamlit as st
from openai import OpenAI
from supabase import create_client
import uuid

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Dark Infor", layout="wide")

try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error(f"Erro nos Secrets: {e}")

if "user" not in st.session_state:
    st.session_state.user = None

# --- AUTENTICAÇÃO ---
if st.session_state.user is None:
    st.title("🛡️ Login Dark Infor")
    aba1, aba2 = st.tabs(["Entrar", "Cadastrar"])
    with aba1:
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        if st.button("Login"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
                st.session_state.user = res.user
                st.rerun()
            except:
                st.error("Erro no login.")
    with aba2:
        n_email = st.text_input("Novo E-mail")
        n_senha = st.text_input("Nova Senha", type="password")
        if st.button("Criar Conta"):
            try:
                supabase.auth.sign_up({"email": n_email, "password": n_senha})
                st.success("Conta criada!")
            except:
                st.error("Erro no cadastro.")

# --- GERADOR ---
else:
    st.sidebar.write(f"Logado: {st.session_state.user.email}")
    if st.sidebar.button("Sair"):
        st.session_state.user = None
        st.rerun()

    st.title("🎙️ Gerador de Voz Profissional")
    texto = st.text_area("Roteiro (Até 100k caracteres):", height=250, max_chars=100000)
    
    # LINHA 67 CORRIGIDA:
    col1, col2 = st.columns(2)
    
    with col1:
        voz = st.selectbox("Escolha a Voz:", ["alloy", "echo", "fable", "onyx", "nova", "shimmer"])
    
    if st.button("Gerar e Salvar no Perfil"):
        if texto:
            with st.spinner("Gerando..."):
                try:
                    # Geração OpenAI
                    response = openai_client.audio.speech.create(model="tts-1", voice=voz, input=texto[:4096])
                    audio_data = response.content
                    
                    # Nome único do arquivo
                    caminho = f"{st.session_state.user.id}/{uuid.uuid4()}.mp3"

                    # UPLOAD PARA O BUCKET CORRETO (DARKINFOR)
                    supabase.storage.from_("DARKINFOR").upload(
                        path=caminho, 
                        file=audio_data, 
                        file_options={"content-type": "audio/mpeg"}
                    )

                    # LINK E HISTÓRICO
                    url_p = supabase.storage.from_("DARKINFOR").get_public_url(caminho)
                    supabase.table("historico_audios").insert({
                        "user_id": st.session_state.user.id,
                        "texto": texto[:50] + "...",
                        "url_audio": url_p
                    }).execute()

                    st.audio(audio_data)
                    st.success("Áudio salvo com sucesso no seu histórico!")
                except Exception as e:
                    st.error(f"Erro: {e}")

    # EXIBIR HISTÓRICO
    st.divider()
    st.subheader("📜 Meus Áudios")
    try:
        hist = supabase.table("historico_audios").select("*").eq("user_id", st.session_state.user.id).execute()
        for item in hist.data:
            with st.expander(f"Áudio: {item['texto']}"):
                st.audio(item['url_audio'])
    except:
        st.write("Crie seu primeiro áudio!")
