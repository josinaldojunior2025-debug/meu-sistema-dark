import streamlit as st
from openai import OpenAI
from supabase import create_client
import uuid

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Dark Infor", layout="wide")

# Inicialização do estado de sessão
if "user" not in st.session_state:
    st.session_state.user = None

# Conexão com serviços
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except:
    st.error("Erro nas chaves de conexão.")

# --- 2. TELA DE LOGIN (CORREÇÃO DO CLIQUE DUPLO) ---
if st.session_state.user is None:
    st.title("🛡️ Acesso Dark Infor")
    
    email = st.text_input("E-mail", key="email_input")
    senha = st.text_input("Senha", type="password", key="senha_input")
    
    if st.button("Entrar no Sistema", use_container_width=True):
        try:
            # Tenta autenticar
            res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
            if res.user:
                # Limpa qualquer cache de erro e define o usuário
                st.cache_data.clear()
                st.session_state.user = res.user
                st.success("Acesso concedido!")
                st.rerun() # Recarrega para entrar de primeira
        except:
            # Só mostra o erro se a tentativa falhar completamente
            st.error("E-mail ou senha incorretos.")

# --- 3. TELA DO GERADOR (APÓS LOGIN) ---
else:
    st.sidebar.write(f"Logado: {st.session_state.user.email}")
    if st.sidebar.button("Sair"):
        st.session_state.user = None
        st.cache_data.clear()
        st.rerun()

    st.title("🎙️ Gerador de Voz Profissional")
    txt = st.text_area("Roteiro (até 4000 caracteres):", height=200)
    voz = st.selectbox("Escolha a Voz:", ["onyx", "alloy", "echo", "fable", "nova", "shimmer"])
    
    if st.button("🔥 Gerar e Salvar"):
        if not txt:
            st.warning("Digite um texto.")
        else:
            with st.spinner("Gerando..."):
                try:
                    # 1. Gera áudio na OpenAI
                    resp = openai_client.audio.speech.create(
                        model="tts-1", voice=voz, input=txt[:4000]
                    )
                    audio_bytes = resp.content
                    
                    # 2. Upload para Storage (darkinfor)
                    # Usamos um try/except interno para o salvamento não travar a geração
                    try:
                        path = f"{st.session_state.user.id}/{uuid.uuid4()}.mp3"
                        supabase.storage.from_("darkinfor").upload(path=path, file=audio_bytes)
                        
                        # 3. Salva no Banco
                        url = supabase.storage.from_("darkinfor").get_public_url(path)
                        supabase.table("historico_audios").insert({
                            "user_id": st.session_state.user.id,
                            "texto": txt[:50] + "...",
                            "url_audio": url
                        }).execute()
                        st.success("Salvo no histórico!")
                    except Exception as e_save:
                        st.warning(f"Áudio gerado, mas não salvo no banco: {e_save}")

                    # Mostra o player de áudio independente de ter salvado ou não
                    st.audio(audio_bytes)
                
                except Exception as ex:
                    st.error(f"Erro na geração: {ex}")

    # --- HISTÓRICO ---
    st.divider()
    st.subheader("📜 Meus Áudios")
    try:
        h = supabase.table("historico_audios").select("*").eq("user_id", st.session_state.user.id).execute()
        if h.data:
            for item in h.data:
                with st.expander(f"Áudio: {item['texto']}"):
                    st.audio(item['url_audio'])
    except:
        st.info("O histórico aparecerá aqui.")
