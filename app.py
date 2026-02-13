import streamlit as st
from openai import OpenAI
from supabase import create_client
import uuid
import time

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Dark Infor", layout="wide")

try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error(f"Erro de conexão: {e}")

if "user" not in st.session_state:
    st.session_state.user = None

# --- LÓGICA DE LOGIN (CORREÇÃO DEFINITIVA DO CLIQUE DUPLO) ---
def tela_login():
    st.title("🛡️ Login Dark Infor")
    t1, t2 = st.tabs(["Entrar", "Cadastrar"])
    
    with t1:
        e = st.text_input("E-mail", key="email_final")
        s = st.text_input("Senha", type="password", key="pass_final")
        if st.button("Fazer Login"):
            try:
                res = supabase.auth.sign_in_with_password({"email": e, "password": s})
                if res.user:
                    st.session_state.user = res.user
                    st.success("Acesso concedido!")
                    time.sleep(0.5)
                    st.rerun()
                    return # Para a execução aqui para não mostrar erro embaixo
            except:
                st.error("Dados de acesso incorretos.")

    with t2:
        ne = st.text_input("Novo E-mail")
        ns = st.text_input("Nova Senha", type="password")
        if st.button("Criar Conta"):
            try:
                supabase.auth.sign_up({"email": ne, "password": ns})
                st.success("Conta criada! Vá em 'Entrar'.")
            except: st.error("Erro ao criar conta.")

# --- INTERFACE PRINCIPAL ---
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
                    # 1. Gerar áudio na OpenAI
                    resp = openai_client.audio.speech.create(model="tts-1", voice=vz, input=txt[:4000])
                    audio_content = resp.content
                    
                    # Mostrar áudio IMEDIATAMENTE (Independente do banco de dados)
                    st.audio(audio_content)
                    st.success("Áudio gerado com sucesso!")

                    # 2. Tentar salvar em segundo plano (Se der erro de aviso, ele não trava a tela)
                    try:
                        file_path = f"{st.session_state.user.id}/{uuid.uuid4()}.mp3"
                        supabase.storage.from_("darkinfor").upload(path=file_path, file=audio_content, file_options={"content-type": "audio/mpeg"})
                        
                        url_audio = supabase.storage.from_("darkinfor").get_public_url(file_path)
                        supabase.table("historico_audios").insert({
                            "user_id": st.session_state.user.id,
                            "texto": txt[:50] + "...",
                            "url_audio": url_audio
                        }).execute()
                    except:
                        # Silencia avisos de permissão para não sujar a tela
                        pass
                
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
        st.write("Histórico não disponível.")

# --- CONTROLE DE FLUXO ---
if st.session_state.user is None:
    tela_login()
else:
    tela_gerador()
