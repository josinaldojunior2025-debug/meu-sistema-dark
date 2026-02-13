import streamlit as st
from openai import OpenAI
from supabase import create_client
import uuid
import time

# --- 1. CONFIGURAÇÃO DE PERSISTÊNCIA ---
st.set_page_config(page_title="Dark Infor", layout="wide")

# Inicializa o estado se não existir (Evita deslogar no F5 em alguns casos)
if "user" not in st.session_state:
    st.session_state.user = None

# Conexão Única
@st.cache_resource
def get_clients():
    s = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    o = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    return s, o

supabase, openai_client = get_clients()

# --- 2. TELA DE LOGIN (SOLUÇÃO CLIQUE DUPLO) ---
if st.session_state.user is None:
    st.title("🛡️ Acesso Dark Infor")
    
    # Usamos formulário para processar o clique de uma vez só
    with st.form("form_login"):
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        btn_login = st.form_submit_button("Entrar no Sistema", use_container_width=True)
        
        if btn_login:
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
                if res.user:
                    st.session_state.user = res.user
                    st.success("Autenticado! Entrando...")
                    time.sleep(0.5)
                    st.rerun() # Pula direto para o gerador
            except:
                st.error("E-mail ou senha inválidos.")

# --- 3. TELA DO GERADOR (SÓ APARECE SE LOGADO) ---
else:
    st.sidebar.write(f"Sessão: {st.session_state.user.email}")
    if st.sidebar.button("Sair"):
        st.session_state.user = None
        st.rerun()

    st.title("🎙️ Gerador de Voz Profissional")
    
    texto = st.text_area("Roteiro:", height=200, placeholder="Digite aqui...")
    voz = st.selectbox("Escolha a Voz:", ["onyx", "alloy", "echo", "fable", "nova", "shimmer"])
    
    if st.button("🔥 Gerar e Salvar"):
        if texto:
            with st.spinner("Gerando áudio..."):
                try:
                    # Gera Áudio na OpenAI
                    resp = openai_client.audio.speech.create(model="tts-1", voice=voz, input=texto[:4000])
                    audio_bytes = resp.content
                    
                    # Nome único para o arquivo
                    nome_arquivo = f"{st.session_state.user.id}/{uuid.uuid4()}.mp3"
                    
                    # Tenta salvar (O SQL do Passo 1 resolve o erro que você teve)
                    try:
                        # Upload para o Storage
                        supabase.storage.from_("darkinfor").upload(path=nome_arquivo, file=audio_bytes)
                        
                        # Salva o link no Banco
                        url = supabase.storage.from_("darkinfor").get_public_url(nome_arquivo)
                        supabase.table("historico_audios").insert({
                            "user_id": st.session_state.user.id,
                            "texto": texto[:50] + "...",
                            "url_audio": url
                        }).execute()
                        st.success("Salvo no histórico!")
                    except Exception as e_db:
                        st.warning(f"Áudio gerado, mas o banco de dados recusou o salvamento: {e_db}")
                    
                    # Sempre mostra o áudio para o usuário
                    st.audio(audio_bytes)
                    
                except Exception as e:
                    st.error(f"Erro na OpenAI: {e}")

    # Histórico
    st.divider()
    st.subheader("📜 Meus Áudios")
    try:
        h = supabase.table("historico_audios").select("*").eq("user_id", st.session_state.user.id).execute()
        for item in h.data:
            with st.expander(f"Áudio: {item['texto']}"):
                st.audio(item['url_audio'])
    except:
        st.info("O histórico aparecerá aqui.")
