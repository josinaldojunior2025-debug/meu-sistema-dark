import streamlit as st
from openai import OpenAI
from supabase import create_client
import uuid
import time

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Dark Infor - Voz Profissional", layout="wide")

# Inicialização de Clientes
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error(f"Erro nos Segredos: {e}")

if "user" not in st.session_state:
    st.session_state.user = None

# --- TELA DE ACESSO (CORRIGIDA PARA ENTRAR DE PRIMEIRA) ---
if st.session_state.user is None:
    st.title("🛡️ Login Dark Infor")
    tab1, tab2 = st.tabs(["Entrar", "Cadastrar"])
    
    with tab1:
        email = st.text_input("E-mail", key="log_email_final")
        senha = st.text_input("Senha", type="password", key="log_pass_final")
        if st.button("Fazer Login"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
                if res.user:
                    st.session_state.user = res.user
                    st.success("Autenticando...")
                    time.sleep(0.5) # Pausa técnica para o Supabase estabilizar a sessão
                    st.rerun() 
            except:
                st.error("E-mail ou senha incorretos.")
                
    with tab2:
        n_email = st.text_input("Novo E-mail", key="cad_email_final")
        n_senha = st.text_input("Nova Senha", type="password", key="cad_pass_final")
        if st.button("Criar Conta"):
            try:
                supabase.auth.sign_up({"email": n_email, "password": n_senha})
                st.success("Cadastro realizado! Tente logar.")
            except:
                st.error("Erro no cadastro.")

# --- INTERFACE DO GERADOR (CORRIGIDA PARA BUCKET MINÚSCULO) ---
else:
    st.sidebar.write(f"Conectado: {st.session_state.user.email}")
    if st.sidebar.button("Sair"):
        st.session_state.user = None
        st.rerun()

    st.title("🎙️ Gerador de Voz Profissional")
    texto = st.text_area("Roteiro (Até 100k caracteres):", height=250, max_chars=100000)
    
    col1, col2 = st.columns(2)
    with col1:
        voz = st.selectbox("Escolha a Voz:", ["onyx", "alloy", "echo", "fable", "nova", "shimmer"])
    
    if st.button("🔥 Gerar e Salvar"):
        if texto:
            with st.spinner("Sintetizando áudio..."):
                try:
                    response = openai_client.audio.speech.create(
                        model="tts-1", voice=voz, input=texto[:4096]
                    )
                    audio_data = response.content
                    
                    nome_arq = f"{st.session_state.user.id}/{uuid.uuid4()}.mp3"

                    # CORREÇÃO DO NOME DO BUCKET PARA MINÚSCULAS
                    bucket_nome = "darkinfor" 

                    # Upload
                    supabase.storage.from_(bucket_nome).upload(
                        path=nome_arq,
                        file=audio_data,
                        file_options={"content-type": "audio/mpeg"}
                    )

                    # URL e Banco de Dados
                    url_p = supabase.storage.from_(bucket_nome).get_public_url(nome_arq)
                    supabase.table("historico_audios").insert({
                        "user_id": st.session_state.user.id,
                        "texto": texto[:50] + "...",
                        "url_audio": url_p
                    }).execute()

                    st.audio(audio_bytes := audio_data)
                    st.success("Salvo no histórico!")
                except Exception as e:
                    st.error(f"Erro no processamento: {e}")

    # --- HISTÓRICO ---
    st.divider()
    st.subheader("📜 Meus Áudios")
    try:
        hist = supabase.table("historico_audios").select("*").eq("user_id", st.session_state.user.id).execute()
        if hist.data:
            for item in hist.data:
                with st.expander(f"Áudio: {item['texto']}"):
                    st.audio(item['url_audio'])
    except:
        st.info("O histórico aparecerá após a criação da tabela no SQL Editor.")
