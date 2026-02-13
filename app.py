import streamlit as st
from openai import OpenAI
from supabase import create_client
import uuid
import time

# --- 1. CONFIGURAÇÃO DE SESSÃO (MATA O CLIQUE DUPLO) ---
st.set_page_config(page_title="Dark Infor", layout="wide")

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "usuario_id" not in st.session_state:
    st.session_state.usuario_id = None

# Conexão com Supabase e OpenAI
@st.cache_resource
def iniciar_conexoes():
    s = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    o = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    return s, o

supabase, openai_client = iniciar_conexoes()

# --- 2. TELA DE LOGIN (CORREÇÃO DEFINITIVA) ---
if not st.session_state.autenticado:
    st.title("🛡️ Acesso Dark Infor")
    
    email = st.text_input("E-mail", key="login_email")
    senha = st.text_input("Senha", type="password", key="login_pass")
    
    if st.button("ENTRAR NO SISTEMA", use_container_width=True):
        try:
            res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
            if res.user:
                st.session_state.autenticado = True
                st.session_state.usuario_id = res.user.id
                st.success("Logado com sucesso!")
                time.sleep(0.4)
                st.rerun() # Entra de primeira sem clique duplo
        except:
            st.error("E-mail ou senha incorretos.")

# --- 3. TELA DO GERADOR (SÓ ACESSA LOGADO) ---
else:
    st.sidebar.button("Sair", on_click=lambda: st.session_state.update({"autenticado": False}))
    st.title("🎙️ Gerador de Voz Profissional")
    
    texto = st.text_area("Roteiro:", height=200, placeholder="Digite o texto aqui...")
    voz = st.selectbox("Escolha a Voz:", ["onyx", "alloy", "echo", "fable", "nova", "shimmer"])
    
    if st.button("🔥 GERAR ÁUDIO"):
        if not texto:
            st.warning("Por favor, digite um texto.")
        else:
            with st.spinner("Gerando voz..."):
                try:
                    # 1. OpenAI gera o áudio (Prioridade Total)
                    resp = openai_client.audio.speech.create(model="tts-1", voice=voz, input=texto[:4000])
                    audio_bytes = resp.content
                    
                    # 2. MOSTRA O ÁUDIO NA TELA IMEDIATAMENTE
                    st.audio(audio_bytes)
                    st.success("Áudio gerado com sucesso!")

                    # 3. Tenta salvar no fundo sem travar a tela
                    try:
                        nome_f = f"{st.session_state.usuario_id}/{uuid.uuid4()}.mp3"
                        supabase.storage.from_("darkinfor").upload(path=nome_f, file=audio_bytes)
                        
                        link = supabase.storage.from_("darkinfor").get_public_url(nome_f)
                        supabase.table("historico_audios").insert({
                            "user_id": st.session_state.usuario_id,
                            "texto": texto[:50],
                            "url_audio": link
                        }).execute()
                    except Exception as e_save:
                        # Se falhar o histórico, o áudio continua na tela
                        st.info(f"Nota: Áudio gerado, mas houve um erro ao salvar no histórico.")
                        
                except Exception as ex:
                    st.error(f"Erro na geração: {ex}")

    # --- 4. EXIBIÇÃO DO HISTÓRICO ---
    st.divider()
    st.subheader("📜 Meus Áudios")
    try:
        h = supabase.table("historico_audios").select("*").eq("user_id", st.session_state.usuario_id).execute()
        if h.data:
            for item in h.data:
                with st.expander(f"Áudio: {item['texto']}"):
                    st.audio(item['url_audio'])
    except:
        pass
