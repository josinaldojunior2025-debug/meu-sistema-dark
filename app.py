import streamlit as st
from openai import OpenAI
from supabase import create_client
import uuid
import time

# --- CONFIGURAÇÃO DE ESTADO (MATA O CLIQUE DUPLO E O DESLOGUE) ---
st.set_page_config(page_title="Dark Infor", layout="wide")

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "u_id" not in st.session_state:
    st.session_state.u_id = None

# Conexão Única
@st.cache_resource
def iniciar_conexoes():
    s = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    o = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    return s, o

supabase, openai_client = iniciar_conexoes()

# --- TELA DE LOGIN (CORREÇÃO DEFINITIVA) ---
if not st.session_state.autenticado:
    st.title("🛡️ Login Dark Infor")
    
    with st.container():
        e_input = st.text_input("E-mail", key="email_log")
        s_input = st.text_input("Senha", type="password", key="pass_log")
        
        if st.button("ACESSAR SISTEMA", use_container_width=True):
            try:
                res = supabase.auth.sign_in_with_password({"email": e_input, "password": s_input})
                if res.user:
                    st.session_state.autenticado = True
                    st.session_state.u_id = res.user.id
                    st.success("Entrando...")
                    time.sleep(0.3)
                    st.rerun() # Entra de primeira
            except:
                st.error("E-mail ou senha incorretos.")

# --- TELA DO GERADOR (SÓ APARECE LOGADO) ---
else:
    st.sidebar.button("Sair", on_click=lambda: st.session_state.update({"autenticado": False}))
    st.sidebar.write(f"ID: {st.session_state.u_id[:8]}")

    st.title("🎙️ Gerador de Voz Profissional")
    
    roteiro = st.text_area("Roteiro:", height=200, placeholder="Digite o texto aqui...")
    voz = st.selectbox("Escolha a Voz:", ["onyx", "alloy", "echo", "fable", "nova", "shimmer"])
    
    if st.button("🔥 GERAR ÁUDIO"):
        if not roteiro:
            st.warning("Por favor, digite um texto.")
        else:
            with st.spinner("Gerando voz..."):
                try:
                    # 1. OpenAI gera o áudio primeiro (Prioridade)
                    resp = openai_client.audio.speech.create(model="tts-1", voice=voz, input=roteiro[:4000])
                    audio_content = resp.content
                    
                    # MOSTRA O ÁUDIO IMEDIATAMENTE (Independente do erro de bucket)
                    st.audio(audio_content)
                    st.success("Áudio gerado!")

                    # 2. Tentativa de salvar (Sem travar o usuário)
                    try:
                        nome_f = f"{st.session_state.u_id}/{uuid.uuid4()}.mp3"
                        # Forçamos o bucket 'darkinfor' (deve estar em minúsculo no Supabase)
                        supabase.storage.from_("darkinfor").upload(path=nome_f, file=audio_content)
                        
                        link = supabase.storage.from_("darkinfor").get_public_url(nome_f)
                        supabase.table("historico_audios").insert({
                            "user_id": st.session_state.u_id,
                            "texto": roteiro[:50],
                            "url_audio": link
                        }).execute()
                        st.info("Salvo no histórico.")
                    except Exception as e_save:
                        # Se o bucket der erro, ele apenas avisa, mas não apaga o áudio da tela
                        st.warning(f"Aviso: O áudio não pôde ser salvo no banco (Erro: {e_save})")
                        
                except Exception as ex:
                    st.error(f"Erro na geração: {ex}")

    # --- HISTÓRICO ---
    st.divider()
    st.subheader("📜 Meus Áudios")
    try:
        dados = supabase.table("historico_audios").select("*").eq("user_id", st.session_state.u_id).execute()
        if dados.data:
            for item in dados.data:
                with st.expander(f"Áudio: {item['texto']}"):
                    st.audio(item['url_audio'])
    except:
        pass
