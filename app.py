import streamlit as st
from openai import OpenAI
from supabase import create_client
import uuid
import time

# --- 1. CONFIGURAÇÃO E PERSISTÊNCIA ---
st.set_page_config(page_title="Dark Infor", layout="wide")

# Inicializa o estado do usuário se não existir
if "user" not in st.session_state:
    st.session_state.user = None

# Função para conectar ao Supabase e OpenAI
@st.cache_resource
def get_clients():
    s_url = st.secrets["SUPABASE_URL"]
    s_key = st.secrets["SUPABASE_KEY"]
    o_key = st.secrets["OPENAI_API_KEY"]
    return create_client(s_url, s_key), OpenAI(api_key=o_key)

try:
    supabase, openai_client = get_clients()
except Exception as e:
    st.error(f"Erro de conexão: {e}")
    st.stop()

# --- 2. FUNÇÕES DE SUPORTE ---
def deslogar():
    st.session_state.user = None
    st.rerun()

# --- 3. TELA DE LOGIN (CORREÇÃO DO CLIQUE DUPLO) ---
if st.session_state.user is None:
    st.title("🛡️ Login Dark Infor")
    t1, t2 = st.tabs(["Entrar", "Cadastrar"])
    
    with t1:
        with st.form("login_form"):
            e = st.text_input("E-mail")
            s = st.text_input("Senha", type="password")
            submit = st.form_submit_button("Acessar Conta")
            
            if submit:
                try:
                    res = supabase.auth.sign_in_with_password({"email": e, "password": s})
                    if res.user:
                        # Define o usuário e recarrega IMEDIATAMENTE
                        st.session_state.user = res.user
                        st.success("Autenticado! Entrando...")
                        time.sleep(0.5)
                        st.rerun()
                except:
                    st.error("E-mail ou senha incorretos.")

    with t2:
        with st.form("cadastro_form"):
            ne = st.text_input("Novo E-mail")
            ns = st.text_input("Nova Senha", type="password")
            btn_cad = st.form_submit_button("Criar Conta")
            if btn_cad:
                try:
                    supabase.auth.sign_up({"email": ne, "password": ns})
                    st.info("Verifique seu e-mail ou tente logar.")
                except: st.error("Erro ao cadastrar.")

# --- 4. INTERFACE DO GERADOR (APÓS LOGIN) ---
else:
    st.sidebar.write(f"Sessão ativa: {st.session_state.user.email}")
    if st.sidebar.button("Sair / Deslogar"):
        deslogar()

    st.title("🎙️ Gerador de Voz Profissional")
    txt = st.text_area("Roteiro:", height=200, placeholder="Cole seu texto aqui...")
    vz = st.selectbox("Escolha a Voz:", ["onyx", "alloy", "echo", "fable", "nova", "shimmer"])
    
    if st.button("🔥 Gerar e Salvar"):
        if not txt:
            st.warning("O texto está vazio.")
        else:
            with st.spinner("Processando áudio e salvando..."):
                try:
                    # 1. OpenAI
                    resp = openai_client.audio.speech.create(model="tts-1", voice=vz, input=txt[:4000])
                    audio_content = resp.content
                    
                    # 2. Mostrar logo o player
                    st.audio(audio_content)
                    
                    # 3. Tentar salvar (Ignora erros de RLS para não travar o usuário)
                    try:
                        file_id = f"{st.session_state.user.id}/{uuid.uuid4()}.mp3"
                        # Forçando bucket em minúsculo
                        bucket = "darkinfor"
                        
                        # Upload
                        supabase.storage.from_(bucket).upload(
                            path=file_id, 
                            file=audio_content, 
                            file_options={"content-type": "audio/mpeg"}
                        )
                        
                        # Inserção no Banco
                        public_url = supabase.storage.from_(bucket).get_public_url(file_id)
                        supabase.table("historico_audios").insert({
                            "user_id": st.session_state.user.id,
                            "texto": txt[:50] + "...",
                            "url_audio": public_url
                        }).execute()
                        
                        st.success("Salvo no histórico!")
                    except Exception as e_db:
                        st.warning(f"Áudio gerado, mas houve um erro ao salvar no banco: {e_db}")

                except Exception as ex:
                    st.error(f"Erro na geração: {ex}")

    # --- 5. HISTÓRICO ---
    st.divider()
    st.subheader("📜 Meus Áudios")
    try:
        h = supabase.table("historico_audios").select("*").eq("user_id", st.session_state.user.id).execute()
        if h.data:
            for item in h.data:
                with st.expander(f"Texto: {item['texto']}"):
                    st.audio(item['url_audio'])
        else:
            st.info("Nenhum áudio encontrado.")
    except:
        st.write("Histórico carregando...")
