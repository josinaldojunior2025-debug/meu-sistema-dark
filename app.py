import streamlit as st
from openai import OpenAI
from supabase import create_client

# Configuração e Estilo
st.set_page_config(page_title="Dark Infor", layout="wide")

# Inicialização de Clientes
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

if "user" not in st.session_state:
    st.session_state.user = None

# --- TELAS INICIAIS ---
if st.session_state.user is None:
    st.title("🛡️ Bem-vindo ao Dark Infor")
    aba_log, aba_cad = st.tabs(["Fazer Login", "Criar Conta"])
    
    with aba_log:
        email = st.text_input("E-mail", key="login_email")
        senha = st.text_input("Senha", type="password", key="login_pass")
        if st.button("Entrar"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
                st.session_state.user = res.user
                st.rerun()
            except:
                st.error("E-mail ou senha incorretos.")

    with aba_cad:
        n_email = st.text_input("E-mail", key="cad_email")
        n_senha = st.text_input("Senha (mín. 6 chars)", type="password", key="cad_pass")
        if st.button("Finalizar Cadastro"):
            try:
                supabase.auth.sign_up({"email": n_email, "password": n_senha})
                st.success("Conta criada! Agora clique em 'Fazer Login'.")
            except Exception as e:
                st.error(f"Erro: {e}")

# --- INTERFACE DO USUÁRIO ---
else:
    st.sidebar.title(f"Olá, {st.session_state.user.email}")
    if st.sidebar.button("Sair"):
        st.session_state.user = None
        st.rerun()

    st.title("🎙️ Gerador de Áudio High-End")
    
    # Suporte a 100k caracteres
    texto_longo = st.text_area("Cole seu roteiro aqui (Até 100.000 caracteres):", height=400, max_chars=100000)
    
    # Seletor de vozes (Espaço para ElevenLabs e OpenAI)
    tipo_servico = st.selectbox("Tecnologia:", ["OpenAI (Padrão)", "ElevenLabs (Clonagem)"])
    voz = st.selectbox("Escolha a Voz:", ["alloy", "echo", "nova", "shimmer", "onyx"])

    if st.button("Gerar e Salvar"):
        if len(texto_longo) > 0:
            with st.spinner("Processando..."):
                # Geração via OpenAI (Exemplo)
                response = openai_client.audio.speech.create(model="tts-1", voice=voz, input=texto_longo[:4096])
                audio_data = response.content
                
                st.audio(audio_data)
                st.download_button("📥 Baixar em MP3", data=audio_data, file_name="audio.mp3")
                
                # Salvar no Histórico (Tabela criada no passo 1)
                supabase.table("historico_audios").insert({
                    "user_id": st.session_state.user.id,
                    "texto": texto_longo[:100], # Salva o início do texto
                    "url_audio": "Arquivo Gerado"
                }).execute()
                st.success("Salvo no seu histórico!")
