import streamlit as st
from openai import OpenAI
from supabase import create_client
import uuid

# --- 1. LIMPEZA DE MEMÓRIA ---
# Se o usuário não está logado, garantimos que não haja lixo de sessão antiga
if "logado" not in st.session_state:
    st.session_state.logado = False
if "u_id" not in st.session_state:
    st.session_state.u_id = None

# --- 2. CONEXÃO DIRETA (SEM CACHE PARA TESTE) ---
# Forçamos a conexão a ser lida do zero
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error(f"Erro crítico nas chaves: {e}")

# --- 3. LOGICA DE TELA ---
if not st.session_state.logado:
    st.title("🛡️ Dark Infor - Acesso Direto")
    
    # Placeholder para mensagens sumirem rápido
    msg = st.empty()
    
    with st.form("login_blindado"):
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        btn = st.form_submit_button("ENTRAR AGORA", use_container_width=True)
        
        if btn:
            try:
                # Tenta logar
                res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
                if res.user:
                    # SUCESSO: Limpa cache e define estado antes do rerun
                    st.session_state.logado = True
                    st.session_state.u_id = res.user.id
                    st.cache_data.clear() # Limpa lixo de erros passados
                    st.rerun()
            except Exception as e_login:
                msg.error("E-mail ou senha inválidos.")

else:
    # TELA DO GERADOR
    st.sidebar.button("SAIR", on_click=lambda: st.session_state.update({"logado": False}))
    st.title("🎙️ Gerador de Voz Profissional")
    
    texto = st.text_area("Roteiro:", height=200)
    voz = st.selectbox("Escolha a Voz:", ["onyx", "alloy", "echo", "fable", "nova", "shimmer"])
    
    if st.button("🔥 GERAR"):
        if texto:
            with st.spinner("Gerando..."):
                try:
                    # 1. OpenAI gera o áudio (Isso aqui SEMPRE tem que aparecer)
                    resp = openai_client.audio.speech.create(model="tts-1", voice=voz, input=texto[:4000])
                    audio_bytes = resp.content
                    
                    # PLAYER IMEDIATO
                    st.audio(audio_bytes)
                    st.success("Áudio gerado!")

                    # 2. SALVAMENTO (Com a Service Role, o bucket 'darkinfor' DEVE funcionar)
                    try:
                        # Nome único
                        f_path = f"{st.session_state.u_id}/{uuid.uuid4()}.mp3"
                        
                        # Upload (Usando bucket em minúsculo conforme SQL)
                        supabase.storage.from_("darkinfor").upload(path=f_path, file=audio_bytes)
                        
                        # Link e Banco
                        link = supabase.storage.from_("darkinfor").get_public_url(f_path)
                        supabase.table("historico_audios").insert({
                            "user_id": st.session_state.u_id,
                            "texto": texto[:50],
                            "url_audio": link
                        }).execute()
                        st.info("Salvo no histórico.")
                    except Exception as e_save:
                        # Se der erro de bucket aqui, é porque o Supabase ainda está processando o SQL que você rodou
                        st.warning(f"Aviso: Áudio pronto, mas o servidor do banco está ocupado (Erro: {e_save})")
                        
                except Exception as ex:
                    st.error(f"Erro na OpenAI: {ex}")

    # HISTÓRICO
    st.divider()
    try:
        h = supabase.table("historico_audios").select("*").eq("user_id", st.session_state.u_id).execute()
        for i in h.data:
            with st.expander(f"Áudio: {i['texto']}"):
                st.audio(i['url_audio'])
    except:
        pass
