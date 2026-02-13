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

# Placeholder para limpar mensagens
mensagem_placeholder = st.empty()

# --- TELA DE LOGIN ---
def tela_login():
    st.title("🛡️ Login Dark Infor")
    t1, t2 = st.tabs(["Entrar", "Cadastrar"])
    
    with t1:
        e = st.text_input("E-mail", key="email_final")
        s = st.text_input("Senha", type="password", key="pass_final")
        if st.button("Fazer Login"):
            try:
                # Tenta autenticar
                res = supabase.auth.sign_in_with_password({"email": e, "password": s})
                if res.user:
                    st.session_state.user = res.user
                    mensagem_placeholder.success("Acesso concedido! Entrando...")
                    time.sleep(0.5)
                    st.rerun()
            except:
                # Só mostra erro se o 'if res.user' não acontecer
                mensagem_placeholder.error("Dados de acesso incorretos.")

    with t2:
        ne = st.text_input("Novo E-mail")
        ns = st.text_input("Nova Senha", type="password")
        if st.button("Criar Conta"):
            try:
                supabase.auth.sign_up({"email": ne, "password": ns})
                st.success("Conta criada! Vá em 'Entrar'.")
            except: st.error("Erro ao criar conta.")

# --- INTERFACE DO GERADOR ---
def tela_gerador():
    st.sidebar.write(f"Conectado: {st.session_state.user.email}")
    if st.sidebar.button("Sair"):
        st.session_state.user = None
        st.rerun()

    st.title("🎙️ Gerador de Voz Profissional")
    txt = st.text_area("Roteiro:", height=200)
    vz = st.selectbox("Escolha a Voz:", ["onyx", "alloy", "echo", "fable", "nova", "shimmer"])
    
    if st.button("🔥 Gerar Áudio"):
        if not txt:
            st.warning("Por favor, digite um roteiro.")
        else:
            with st.spinner("Criando áudio..."):
                try:
                    # 1. Gerar na OpenAI
                    resp = openai_client.audio.speech.create(model="tts-1", voice=vz, input=txt[:4000])
                    audio_content = resp.content
                    
                    # 2. Mostrar áudio IMEDIATAMENTE
                    st.audio(audio_content)
                    st.success("Áudio gerado com sucesso!")

                    # 3. Tentar salvar (Silencioso para não dar erro na tela)
                    try:
                        file_path = f"{st.session_state.user.id}/{uuid.uuid4()}.mp3"
                        supabase.storage.from_("darkinfor").upload(path=file_path, file=audio_content, file_options={"content-type": "audio/mpeg"})
                        
                        url_audio = supabase.storage.from_("darkinfor").get_public_url(file_path)
                        supabase.table("historico_audios").insert({
                            "user_id": st.session_state.user.id, "texto": txt[:50] + "...", "url_audio": url_audio
                        }).execute()
                    except:
                        pass # Ignora avisos de banco de dados
                except Exception as ex:
                    st.error(f"Erro técnico: {ex}")

    # --- HISTÓRICO ---
    st.divider()
    st.subheader("📜 Seu Histórico")
    try:
        h = supabase.table("historico_audios").select("*").eq("user_id", st.session_state.user.id).execute()
        if h.data:
            for item in h.data:
                with st.expander(f"Áudio: {item['texto']}"):
                    st.audio(item['url_audio'])
    except:
        pass

# --- CONTROLE DE FLUXO ---
if st.session_state.user is None:
    tela_login()
else:
    tela_gerador()
