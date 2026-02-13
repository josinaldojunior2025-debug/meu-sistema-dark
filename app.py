import streamlit as st
from openai import OpenAI
from supabase import create_client
import uuid

# Configuração de Página
st.set_page_config(page_title="Dark Infor v3", layout="wide")

# Inicialização de estado
if "logado" not in st.session_state:
    st.session_state.logado = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None

# Tenta carregar conexões
try:
    s_url = st.secrets["SUPABASE_URL"]
    s_key = st.secrets["SUPABASE_KEY"]
    o_key = st.secrets["OPENAI_API_KEY"]
    
    supabase = create_client(s_url, s_key)
    openai_client = OpenAI(api_key=o_key)
except Exception as e:
    st.error(f"Erro crítico nas chaves: {e}")
    st.stop()

# --- TELA DE ACESSO ---
if not st.session_state.logado:
    st.title("🛡️ Acesso Dark Infor")
    
    with st.form("login_form"):
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        entrar = st.form_submit_button("Entrar no Sistema", use_container_width=True)
        
        if entrar:
            try:
                # Tenta autenticar
                res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
                if res.user:
                    st.session_state.logado = True
                    st.session_state.user_id = res.user.id
                    st.rerun()
            except Exception:
                st.error("E-mail ou senha inválidos. Verifique o cadastro no Supabase.")

# --- TELA DO GERADOR ---
else:
    st.sidebar.button("Sair", on_click=lambda: st.session_state.update({"logado": False}))
    st.title("🎙️ Gerador de Voz Profissional")
    
    texto = st.text_area("Roteiro:", height=200)
    voz = st.selectbox("Escolha a Voz:", ["onyx", "alloy", "echo", "fable", "nova", "shimmer"])
    
    if st.button("🔥 GERAR ÁUDIO"):
        if texto:
            with st.spinner("IA Gerando..."):
                try:
                    # Geração OpenAI
                    response = openai_client.audio.speech.create(model="tts-1", voice=voz, input=texto[:4000])
                    audio_bytes = response.content
                    
                    # Player
                    st.audio(audio_bytes)
                    st.success("Audio pronto!")
                    
                    # Salva no Banco (Sem travar se falhar)
                    try:
                        f_name = f"{st.session_state.user_id}/{uuid.uuid4()}.mp3"
                        supabase.storage.from_("darkinfor").upload(path=f_name, file=audio_bytes)
                        
                        url = supabase.storage.from_("darkinfor").get_public_url(f_name)
                        supabase.table("historico_audios").insert({
                            "user_id": st.session_state.user_id,
                            "texto": texto[:50],
                            "url_audio": url
                        }).execute()
                    except:
                        pass
                except Exception as e:
                    st.error(f"Erro na OpenAI: {e}")
