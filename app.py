import streamlit as st
from openai import OpenAI
from supabase import create_client
import uuid

# --- 1. CONFIGURAÇÃO DE ESTADO ---
st.set_page_config(page_title="Dark Infor", layout="wide")

# Inicializa as variáveis de sessão para não perder no F5
if "logado" not in st.session_state:
    st.session_state.logado = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None

# Conexão Única
@st.cache_resource
def conexao():
    s = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    o = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    return s, o

supabase, openai_client = conexao()

# --- 2. TELA DE LOGIN ---
def mostrar_login():
    st.title("🛡️ Acesso Dark Infor")
    
    col_login, _ = st.columns([1, 1])
    with col_login:
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        
        if st.button("Entrar Agora", use_container_width=True):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
                if res.user:
                    st.session_state.logado = True
                    st.session_state.user_id = res.user.id
                    st.session_state.user_email = res.user.email
                    st.rerun() # Pula direto para o gerador
            except:
                st.error("E-mail ou senha inválidos.")

# --- 3. TELA DO GERADOR ---
def mostrar_gerador():
    st.sidebar.write(f"Sessão: {st.session_state.user_email}")
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    st.title("🎙️ Gerador de Voz Profissional")
    
    texto = st.text_area("Roteiro:", height=200)
    voz = st.selectbox("Escolha a Voz:", ["onyx", "alloy", "echo", "fable", "nova", "shimmer"])
    
    if st.button("🔥 Gerar e Salvar"):
        if texto:
            with st.spinner("Gerando áudio..."):
                try:
                    # Gera Áudio
                    resp = openai_client.audio.speech.create(model="tts-1", voice=voz, input=texto[:4000])
                    audio_bytes = resp.content
                    
                    # Nome único
                    nome_f = f"{st.session_state.user_id}/{uuid.uuid4()}.mp3"
                    
                    # Salva no Storage
                    supabase.storage.from_("darkinfor").upload(path=nome_f, file=audio_bytes, file_options={"content-type": "audio/mpeg"})
                    
                    # Salva no Banco
                    url = supabase.storage.from_("darkinfor").get_public_url(nome_f)
                    supabase.table("historico_audios").insert({
                        "user_id": st.session_state.user_id,
                        "texto": texto[:50],
                        "url_audio": url
                    }).execute()
                    
                    st.audio(audio_bytes)
                    st.success("Áudio gerado e salvo!")
                except Exception as e:
                    st.error(f"Erro: {e}")

    # Histórico
    st.divider()
    st.subheader("📜 Histórico")
    try:
        h = supabase.table("historico_audios").select("*").eq("user_id", st.session_state.user_id).execute()
        for item in h.data:
            with st.expander(f"Áudio: {item['texto']}"):
                st.audio(item['url_audio'])
    except:
        pass

# --- 4. CONTROLE DE FLUXO ---
if not st.session_state.logado:
    mostrar_login()
else:
    mostrar_gerador()
