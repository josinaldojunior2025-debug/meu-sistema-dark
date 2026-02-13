import streamlit as st
from openai import OpenAI
from supabase import create_client
import uuid

# --- 1. CONFIGURAÇÃO DE ESTADO ---
st.set_page_config(page_title="Dark Infor", layout="wide")

# Inicializa as variáveis de controle (Essencial para F5 e clique único)
if "logado" not in st.session_state:
    st.session_state.logado = False
if "u_id" not in st.session_state:
    st.session_state.u_id = None

# Conexão com Supabase e OpenAI
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- 2. TELA DE LOGIN (SEM CLIQUE DUPLO) ---
if not st.session_state.logado:
    st.title("🛡️ Acesso Dark Infor")
    
    with st.container():
        email = st.text_input("E-mail", key="em")
        senha = st.text_input("Senha", type="password", key="pw")
        
        if st.button("ENTRAR NO SISTEMA", use_container_width=True):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
                if res.user:
                    st.session_state.logado = True
                    st.session_state.u_id = res.user.id
                    st.rerun() # Entra imediatamente
            except:
                st.error("Dados incorretos. Verifique e tente novamente.")

# --- 3. TELA DO GERADOR (SÓ ACESSA SE LOGADO) ---
else:
    st.sidebar.button("Sair", on_click=lambda: st.session_state.update({"logado": False}))
    st.title("🎙️ Gerador de Voz Profissional")
    
    txt = st.text_area("Digite o texto aqui:", height=200)
    voz = st.selectbox("Escolha a Voz:", ["onyx", "alloy", "echo", "fable", "nova", "shimmer"])
    
    if st.button("🔥 GERAR E SALVAR"):
        if not txt:
            st.warning("Escreva algo primeiro.")
        else:
            with st.spinner("Processando..."):
                try:
                    # 1. Gerar áudio
                    resp = openai_client.audio.speech.create(model="tts-1", voice=voz, input=txt[:4000])
                    audio_content = resp.content
                    
                    # 2. Salvar (O SQL acima garante que o bucket 'darkinfor' exista)
                    f_name = f"{st.session_state.u_id}/{uuid.uuid4()}.mp3"
                    
                    # Tentativa de upload
                    try:
                        supabase.storage.from_("darkinfor").upload(path=f_name, file=audio_content)
                        
                        # 3. Registrar no banco
                        f_url = supabase.storage.from_("darkinfor").get_public_url(f_name)
                        supabase.table("historico_audios").insert({
                            "user_id": st.session_state.u_id,
                            "texto": txt[:50] + "...",
                            "url_audio": f_url
                        }).execute()
                        st.success("Áudio salvo no histórico!")
                    except Exception as e_stor:
                        st.error(f"Erro no Storage: {e_stor}. Verifique se o bucket 'darkinfor' existe no Supabase.")

                    # Mostrar o player
                    st.audio(audio_content)
                except Exception as ex:
                    st.error(f"Erro na geração: {ex}")

    # --- 4. EXIBIR HISTÓRICO ---
    st.divider()
    st.subheader("📜 Meus Áudios Antigos")
    try:
        h = supabase.table("historico_audios").select("*").eq("user_id", st.session_state.u_id).execute()
        if h.data:
            for item in h.data:
                with st.expander(f"Áudio: {item['texto']}"):
                    st.audio(item['url_audio'])
    except:
        pass
