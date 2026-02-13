import streamlit as st
from openai import OpenAI
from supabase import create_client
import uuid
import time

# --- 1. CONFIGURAÇÃO (MATA O CLIQUE DUPLO) ---
st.set_page_config(page_title="Dark Infor", layout="wide")

if "auth_ok" not in st.session_state:
    st.session_state.auth_ok = False
if "u_id" not in st.session_state:
    st.session_state.u_id = None

# Clientes
s_url = st.secrets["SUPABASE_URL"]
s_key = st.secrets["SUPABASE_KEY"]
supabase = create_client(s_url, s_key)
openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- 2. TELA DE LOGIN ---
if not st.session_state.auth_ok:
    st.title("🛡️ Acesso Dark Infor")
    
    with st.container():
        e = st.text_input("E-mail", key="em")
        s = st.text_input("Senha", type="password", key="pw")
        
        if st.button("ENTRAR", use_container_width=True):
            try:
                res = supabase.auth.sign_in_with_password({"email": e, "password": s})
                if res.user:
                    st.session_state.auth_ok = True
                    st.session_state.u_id = res.user.id
                    st.success("Logado!")
                    time.sleep(0.4)
                    st.rerun()
            except:
                st.error("Dados incorretos.")

# --- 3. TELA DO GERADOR (À PROVA DE ERROS) ---
else:
    st.sidebar.button("Sair", on_click=lambda: st.session_state.update({"auth_ok": False}))
    
    st.title("🎙️ Gerador de Voz Profissional")
    txt = st.text_area("Roteiro:", height=200)
    voz = st.selectbox("Escolha a Voz:", ["onyx", "alloy", "echo", "fable", "nova", "shimmer"])
    
    if st.button("🔥 GERAR ÁUDIO AGORA"):
        if txt:
            with st.spinner("Gerando..."):
                try:
                    # GERA O ÁUDIO PRIMEIRO (ISSO NÃO PODE FALHAR)
                    resp = openai_client.audio.speech.create(model="tts-1", voice=voz, input=txt[:4000])
                    audio_bytes = resp.content
                    
                    # MOSTRA O PLAYER NA HORA
                    st.audio(audio_bytes)
                    st.success("Áudio pronto!")

                    # TENTA SALVAR NO FUNDO (SE DER ERRO, O USUÁRIO NEM VÊ)
                    try:
                        f_name = f"{st.session_state.u_id}/{uuid.uuid4()}.mp3"
                        supabase.storage.from_("darkinfor").upload(path=f_name, file=audio_bytes)
                        
                        url = supabase.storage.from_("darkinfor").get_public_url(f_name)
                        supabase.table("historico_audios").insert({
                            "user_id": st.session_state.u_id,
                            "texto": txt[:50],
                            "url_audio": url
                        }).execute()
                    except:
                        # Se o banco falhar, apenas ignora para não mostrar erro vermelho
                        st.info("Aviso: Áudio gerado, mas histórico indisponível no momento.")
                        
                except Exception as ex:
                    st.error(f"Erro na geração da voz: {ex}")

    # --- HISTÓRICO ---
    st.divider()
    try:
        h = supabase.table("historico_audios").select("*").eq("user_id", st.session_state.u_id).execute()
        if h.data:
            for i in h.data:
                with st.expander(f"Áudio: {i['texto']}"):
                    st.audio(i['url_audio'])
    except:
        pass
