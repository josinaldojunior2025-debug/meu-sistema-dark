import streamlit as st
from openai import OpenAI
from supabase import create_client
import uuid

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Dark Infor", layout="wide")

# Inicialização segura dos segredos
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
        email = st.text_input("E-mail", key="login_email_input")
        senha = st.text_input("Senha", type="password", key="login_pass_input")
        if st.button("Fazer Login"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
                if res.user:
                    st.session_state.user = res.user
                    st.rerun() # Entra de primeira sem erro
            except:
                st.error("E-mail ou senha incorretos.")
                
    with tab2:
        n_email = st.text_input("Novo E-mail", key="cad_email_input")
        n_senha = st.text_input("Nova Senha", type="password", key="cad_pass_input")
        if st.button("Criar Conta"):
            try:
                supabase.auth.sign_up({"email": n_email, "password": n_senha})
                st.success("Conta criada! Tente logar.")
            except:
                st.error("Erro ao cadastrar.")

# --- INTERFACE PRINCIPAL ---
else:
    st.sidebar.write(f"Conectado: {st.session_state.user.email}")
    if st.sidebar.button("Sair"):
        st.session_state.user = None
        st.rerun()

    st.title("🎙️ Gerador de Voz Profissional")
    texto = st.text_area("Roteiro (Até 100k caracteres):", height=250, max_chars=100000)
    
    # Linha 67 corrigida (parêntese fechado)
    col1, col2 = st.columns(2)
    
    with col1:
        voz = st.selectbox("Escolha a Voz:", ["alloy", "echo", "fable", "onyx", "nova", "shimmer"])
    
    if st.button("🔥 Gerar e Salvar"):
        if texto:
            with st.spinner("Sintetizando áudio..."):
                try:
                    # Geração na OpenAI
                    response = openai_client.audio.speech.create(
                        model="tts-1", 
                        voice=voz, 
                        input=texto[:4096]
                    )
                    audio_data = response.content
                    
                    # Nome único do arquivo
                    caminho_arquivo = f"{st.session_state.user.id}/{uuid.uuid4()}.mp3"

                    # 1. Faz o Upload para o Bucket DARKINFOR
                    supabase.storage.from_("DARKINFOR").upload(
                        path=caminho_arquivo,
                        file=audio_data,
                        file_options={"content-type": "audio/mpeg"}
                    )

                    # 2. Gera URL e salva no Banco
                    url_p = supabase.storage.from_("DARKINFOR").get_public_url(caminho_arquivo)
                    supabase.table("historico_audios").insert({
                        "user_id": st.session_state.user.id,
                        "texto": texto[:50] + "...",
                        "url_audio": url_p
                    }).execute()

                    st.audio(audio_data)
                    st.success("Áudio salvo no seu histórico!")
                except Exception as e:
                    # Este é o bloco 'except' que faltava na linha 98
                    st.error(f"Erro no processamento: {e}")

    # --- HISTÓRICO ---
    st.divider()
    st.subheader("📜 Meus Áudios")
    try:
        # Puxa o histórico do banco de dados
        hist = supabase.table("historico_audios").select("*").eq("user_id", st.session_state.user.id).execute()
        if hist.data:
            for item in hist.data:
                with st.expander(f"Áudio: {item['texto']}"):
                    st.audio(item['url_audio'])
        else:
            st.info("Nenhum áudio encontrado.")
    except:
        st.warning("Crie a tabela 'historico_audios' no SQL Editor para ativar esta função.")
