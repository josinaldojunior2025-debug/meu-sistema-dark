import streamlit as st
from openai import OpenAI
from supabase import create_client
import uuid
import time

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Dark Infor - Voz Profissional", layout="wide")

# Inicialização de Clientes com tratamento de erro
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error(f"Erro na conexão com as chaves: {e}")

# Gerenciamento de Estado da Sessão
if "user" not in st.session_state:
    st.session_state.user = None

# --- TELA DE LOGIN (ENTRADA DE PRIMEIRA) ---
if st.session_state.user is None:
    st.title("🛡️ Login Dark Infor")
    tab_log, tab_cad = st.tabs(["Entrar", "Cadastrar"])
    
    with tab_log:
        email = st.text_input("E-mail", key="email_field")
        senha = st.text_input("Senha", type="password", key="pass_field")
        
        if st.button("Fazer Login"):
            try:
                # Autenticação direta no Supabase
                auth_res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
                
                if auth_res.user:
                    st.session_state.user = auth_res.user
                    st.success("Login realizado! Redirecionando...")
                    time.sleep(1)  # Pausa essencial para o Streamlit processar a sessão
                    st.rerun() # Recarrega para a interface do gerador
            except Exception:
                st.error("E-mail ou senha incorretos.")

    with tab_cad:
        n_email = st.text_input("Novo E-mail")
        n_senha = st.text_input("Nova Senha", type="password")
        if st.button("Criar Conta"):
            try:
                supabase.auth.sign_up({"email": n_email, "password": n_senha})
                st.success("Conta criada com sucesso!")
            except Exception as e:
                st.error(f"Erro no cadastro: {e}")

# --- INTERFACE DO GERADOR (CORREÇÃO DO BUCKET) ---
else:
    st.sidebar.write(f"Conectado como: {st.session_state.user.email}")
    if st.sidebar.button("Sair"):
        st.session_state.user = None
        st.rerun()

    st.title("🎙️ Gerador de Voz Profissional")
    
    texto = st.text_area("Roteiro (Suporta até 100k caracteres):", height=250, max_chars=100000)
    
    col1, col2 = st.columns(2)
    with col1:
        voz = st.selectbox("Escolha a Voz:", ["onyx", "alloy", "echo", "fable", "nova", "shimmer"])
    
    if st.button("🔥 Gerar e Salvar"):
        if not texto:
            st.warning("Insira um texto primeiro.")
        else:
            with st.spinner("Sintetizando áudio..."):
                try:
                    # Geração na OpenAI
                    response = openai_client.audio.speech.create(
                        model="tts-1", voice=voz, input=texto[:4096]
                    )
                    audio_bytes = response.content
                    
                    # Nome de arquivo único
                    id_arq = f"{st.session_state.user.id}/{uuid.uuid4()}.mp3"

                    # CORREÇÃO CRITICAL: O nome deve ser 'darkinfor' (minúsculas) como na sua policy
                    bucket_id = "darkinfor"

                    # Upload para o Storage
                    supabase.storage.from_(bucket_id).upload(
                        path=id_arq,
                        file=audio_bytes,
                        file_options={"content-type": "audio/mpeg"}
                    )

                    # Obter URL e gravar no histórico
                    audio_url = supabase.storage.from_(bucket_id).get_public_url(id_arq)
                    
                    supabase.table("historico_audios").insert({
                        "user_id": st.session_state.user.id,
                        "texto": texto[:60] + "...",
                        "url_audio": audio_url
                    }).execute()

                    st.audio(audio_bytes)
                    st.success("Áudio gerado e salvo no histórico!")
                except Exception as e:
                    # Exibe o erro real para diagnóstico
                    st.error(f"Erro no processamento: {e}")

    # --- SEÇÃO DE HISTÓRICO ---
    st.divider()
    st.subheader("📜 Meus Áudios")
    try:
        # Puxa os dados da tabela que já confirmamos existir
        historico = supabase.table("historico_audios").select("*").eq("user_id", st.session_state.user.id).execute()
        
        if historico.data:
            for item in historico.data:
                with st.expander(f"Áudio de: {item['texto']}"):
                    st.audio(item['url_audio'])
        else:
            st.info("Você ainda não tem áudios salvos.")
    except Exception:
        st.write("Histórico temporariamente indisponível.")
