import streamlit as st
from openai import OpenAI
from supabase import create_client
import uuid

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Dark Infor v3", layout="wide")

# Inicializa o estado da sessão para evitar cliques duplos
if "logado" not in st.session_state:
    st.session_state.logado = False

# --- CONEXÕES (Lendo dos Secrets que você acabou de arrumar) ---
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error("Erro nas chaves! Verifique os Secrets no Streamlit.")
    st.stop()

# --- INTERFACE DE LOGIN ---
if not st.session_state.logado:
    st.title("🛡️ Acesso Dark Infor")
    with st.form("form_login"):
        u_email = st.text_input("E-mail")
        u_senha = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar no Sistema"):
            try:
                res = supabase.auth.sign_in_with_password({"email": u_email, "password": u_senha})
                if res.user:
                    st.session_state.logado = True
                    st.session_state.user_id = res.user.id
                    st.rerun()
            except:
                st.error("E-mail ou senha inválidos.")

# --- INTERFACE DO GERADOR ---
else:
    st.sidebar.button("Sair", on_click=lambda: st.session_state.update({"logado": False}))
    st.title("🎙️ Gerador de Voz Profissional")
    
    texto = st.text_area("Roteiro (até 4000 caracteres):", height=200)
    voz = st.selectbox("Escolha a Voz:", ["onyx", "alloy", "echo", "fable", "nova", "shimmer"])
    
    if st.button("🔥 Gerar e Salvar"):
        if not texto:
            st.warning("Digite um texto primeiro!")
        else:
            with st.spinner("Gerando áudio..."):
                try:
                    # 1. Gera o áudio na OpenAI
                    response = openai_client.audio.speech.create(
                        model="tts-1",
                        voice=voz,
                        input=texto
                    )
                    audio_data = response.content
                    
                    # 2. Exibe o Player imediatamente
                    st.audio(audio_data)
                    st.success("Áudio gerado com sucesso!")
                    
                    # 3. Tenta salvar no Supabase (Storage e Banco)
                    try:
                        file_name = f"{st.session_state.user_id}/{uuid.uuid4()}.mp3"
                        # Faz o upload para o bucket 'darkinfor'
                        supabase.storage.from_("darkinfor").upload(file_name, audio_data)
                        
                        # Pega a URL pública e salva no histórico
                        url_publica = supabase.storage.from_("darkinfor").get_public_url(file_name)
                        supabase.table("historico_audios").insert({
                            "user_id": st.session_state.user_id,
                            "texto": texto[:50],
                            "url_audio": url_publica
                        }).execute()
                        st.info("Salvo no seu histórico!")
                    except Exception as e_db:
                        # Se o salvamento falhar, o áudio já está na tela, então apenas avisamos
                        st.warning(f"Áudio pronto, mas não salvo: {e_db}")
                        
                except Exception as e_ai:
                    st.error(f"Erro na geração (OpenAI): {e_ai}")

    # --- SEÇÃO DE HISTÓRICO ---
    st.divider()
    st.subheader("📜 Meus Áudios Recentes")
    try:
        historico = supabase.table("historico_audios").select("*").eq("user_id", st.session_state.user_id).order("id", desc=True).limit(5).execute()
        if historico.data:
            for item in historico.data:
                with st.expander(f"Texto: {item['texto']}..."):
                    st.audio(item['url_audio'])
        else:
            st.write("Nenhum áudio salvo ainda.")
    except:
        st.write("Histórico temporariamente indisponível.")
