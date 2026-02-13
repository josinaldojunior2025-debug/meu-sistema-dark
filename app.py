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
    st.error(f"Erro na conexão com as chaves: {e}")

# Gerenciamento de Estado da Sessão
if "user" not in st.session_state:
    st.session_state.user = None

# --- BLOCO DE LOGIN (MANTIDO CONFORME SOLICITADO) ---
if st.session_state.user is None:
    st.title("🛡️ Login Dark Infor")
    tab1, tab2 = st.tabs(["Entrar", "Cadastrar"])
    
    with tab1:
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
                else:
                    st.error("Erro inesperado no login.")
            except Exception:
                st.error("E-mail ou senha incorretos.")
    
    with tab2:
        ne = st.text_input("Novo E-mail")
        ns = st.text_input("Nova Senha", type="password")
        if st.button("Criar Conta"):
            try:
                supabase.auth.sign_up({"email": ne, "password": ns})
                st.success("Criado!")
            except:
                st.error("Erro no cadastro.")

# --- INTERFACE DO GERADOR (ÁREA DE CORREÇÃO) ---
else:
    st.sidebar.write(f"Logado: {st.session_state.user.email}")
    if st.sidebar.button("Sair"):
        st.session_state.user = None
        st.rerun()

    st.title("🎙️ Gerador de Voz Profissional")
    
    texto = st.text_area("Roteiro:", height=250)
    
    voz = st.selectbox("Escolha a Voz:", ["onyx", "alloy", "echo", "fable", "nova", "shimmer"])
    
    if st.button("🔥 Gerar e Salvar"):
        if not texto:
            st.warning("Insira um texto primeiro.")
        else:
            with st.spinner("Processando áudio..."):
                try:
                    # 1. Geração na OpenAI
                    response = openai_client.audio.speech.create(
                        model="tts-1", voice=voz, input=texto[:4096]
                    )
                    audio_bytes = response.content
                    
                    # 2. Upload para o Storage (Bucket: darkinfor)
                    # Importante: o nome do bucket deve ser exatamente 'darkinfor' (minúsculas)
                    id_arquivo = f"{st.session_state.user.id}/{uuid.uuid4()}.mp3"
                    bucket_id = "darkinfor"

                    supabase.storage.from_(bucket_id).upload(
                        path=id_arquivo,
                        file=audio_bytes,
                        file_options={"content-type": "audio/mpeg"}
                    )

                    # 3. Salvar no Banco de Dados (Historico)
                    url_publica = supabase.storage.from_(bucket_id).get_public_url(id_arquivo)
                    
                    supabase.table("historico_audios").insert({
                        "user_id": st.session_state.user.id,
                        "texto": texto[:50] + "...",
                        "url_audio": url_publica
                    }).execute()

                    st.audio(audio_bytes)
                    st.success("Áudio gerado e salvo com sucesso!")
                
                except Exception as e:
                    # Mostra o erro técnico exato para sabermos se o RLS ainda bloqueia
                    st.error(f"Erro no processamento: {e}")

    # --- SEÇÃO DE HISTÓRICO ---
    st.divider()
    st.subheader("📜 Meus Áudios")
    try:
        # Puxa o histórico filtrando pelo ID do usuário logado
        historico = supabase.table("historico_audios").select("*").eq("user_id", st.session_state.user.id).execute()
        
        if historico.data:
            for item in historico.data:
                with st.expander(f"Áudio de: {item['texto']}"):
                    st.audio(item['url_audio'])
        else:
            st.info("Você ainda não tem áudios salvos.")
    except Exception:
        st.write("O histórico aparecerá aqui após a primeira geração.")
