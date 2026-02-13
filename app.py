import streamlit as st
from openai import OpenAI
from supabase import create_client
import uuid
import time

# --- 1. FORÇAR REFRESH DE ESTADO ---
st.set_page_config(page_title="Dark Infor", layout="wide")

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "u_id" not in st.session_state:
    st.session_state.u_id = None

# Conexão
s_url = st.secrets["SUPABASE_URL"]
s_key = st.secrets["SUPABASE_KEY"]
supabase = create_client(s_url, s_key)
openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- 2. LOGIN (MATA O CLIQUE DUPLO) ---
if not st.session_state.autenticado:
    st.title("🛡️ Acesso Dark Infor")
    
    # Placeholder para limpar mensagens antigas
    container_msg = st.empty()
    
    e = st.text_input("E-mail", key="email_box")
    s = st.text_input("Senha", type="password", key="pass_box")
    
    if st.button("ENTRAR AGORA", use_container_width=True):
        try:
            res = supabase.auth.sign_in_with_password({"email": e, "password": s})
            if res.user:
                st.session_state.autenticado = True
                st.session_state.u_id = res.user.id
                container_msg.success("Acesso confirmado! Redirecionando...")
                time.sleep(0.5)
                st.rerun() # FORÇA O STREAMLIT A MUDAR DE PÁGINA
        except:
            container_msg.error("E-mail ou senha incorretos.")

# --- 3. GERADOR (À PROVA DE ERRO DE BUCKET) ---
else:
    st.sidebar.button("Sair", on_click=lambda: st.session_state.update({"autenticado": False}))
    st.title("🎙️ Gerador de Voz")
    
    txt = st.text_area("Roteiro:", height=200)
    voz = st.selectbox("Voz:", ["onyx", "alloy", "echo", "fable", "nova", "shimmer"])
    
    if st.button("🔥 GERAR"):
        if txt:
            with st.spinner("Processando..."):
                try:
                    # GERA O ÁUDIO PRIMEIRO
                    resp = openai_client.audio.speech.create(model="tts-1", voice=voz, input=txt[:4000])
                    audio_bytes = resp.content
                    
                    # MOSTRA O ÁUDIO NA TELA (Isso aqui tem que aparecer!)
                    st.audio(audio_bytes)
                    st.success("Áudio pronto!")

                    # TENTA SALVAR (Se der erro de bucket, ele não mostra erro vermelho)
                    try:
                        f_name = f"{st.session_state.u_id}/{uuid.uuid4()}.mp3"
                        # O segredo: o bucket no Supabase DEVE estar em minúsculo: darkinfor
                        supabase.storage.from_("darkinfor").upload(path=f_name, file=audio_bytes)
                        
                        url = supabase.storage.from_("darkinfor").get_public_url(f_name)
                        supabase.table("historico_audios").insert({
                            "user_id": st.session_state.u_id,
                            "texto": txt[:50],
                            "url_audio": url
                        }).execute()
                    except Exception as e_interno:
                        # Se o bucket der erro, ele avisa mas NÃO trava a tela
                        st.info("Nota: Áudio disponível acima, mas o histórico está em manutenção.")
                except Exception as ex:
                    st.error(f"Erro na geração da voz: {ex}")

    # HISTÓRICO
    st.divider()
    try:
        h = supabase.table("historico_audios").select("*").eq("user_id", st.session_state.u_id).execute()
        for i in h.data:
            with st.expander(f"Texto: {i['texto']}"):
                st.audio(i['url_audio'])
    except:
        pass
