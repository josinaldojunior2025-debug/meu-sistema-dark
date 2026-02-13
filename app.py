import streamlit as st
from openai import OpenAI
from supabase import create_client
import uuid
import time

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Dark Infor", layout="wide")

# Inicializa as variáveis para o login não cair e não precisar de 2 cliques
if "logado" not in st.session_state:
    st.session_state.logado = False
if "usuario_id" not in st.session_state:
    st.session_state.usuario_id = None

# Conexão (Centralizada para evitar erros)
@st.cache_resource
def iniciar_conexoes():
    s = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    o = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    return s, o

supabase, openai_client = iniciar_conexoes()

# --- TELA DE LOGIN (SOLUÇÃO PARA O CLIQUE DUPLO) ---
if not st.session_state.logado:
    st.title("🛡️ Sistema Dark Infor")
    
    # Organiza o login em uma caixa limpa
    with st.container():
        email_log = st.text_input("E-mail", key="em_final")
        senha_log = st.text_input("Senha", type="password", key="pw_final")
        
        if st.button("ACESSAR SISTEMA", use_container_width=True):
            try:
                # Tenta autenticar
                res = supabase.auth.sign_in_with_password({"email": email_log, "password": senha_log})
                if res.user:
                    # SALVA O ESTADO ANTES DE RECARREGAR
                    st.session_state.logado = True
                    st.session_state.usuario_id = res.user.id
                    st.success("Acesso autorizado!")
                    time.sleep(0.4)
                    st.rerun() # Entra de primeira
            except:
                st.error("E-mail ou senha incorretos.")

# --- TELA DO GERADOR (SÓ ACESSA QUEM ESTÁ LOGADO) ---
else:
    st.sidebar.button("Encerrar Sessão", on_click=lambda: st.session_state.update({"logado": False}))
    st.sidebar.write(f"Usuário: {st.session_state.usuario_id[:8]}...")

    st.title("🎙️ Gerador de Áudio Profissional")
    
    roteiro = st.text_area("Roteiro para a voz:", height=200)
    voz_escolhida = st.selectbox("Escolha a Voz:", ["onyx", "alloy", "echo", "fable", "nova", "shimmer"])
    
    if st.button("🔥 GERAR E SALVAR AGORA"):
        if not roteiro:
            st.warning("O campo de roteiro está vazio.")
        else:
            with st.spinner("Gerando voz e salvando..."):
                try:
                    # 1. Gera o áudio na OpenAI
                    resp = openai_client.audio.speech.create(
                        model="tts-1", voice=voz_escolhida, input=roteiro[:4000]
                    )
                    conteudo_audio = resp.content
                    
                    # 2. Mostra o áudio na tela imediatamente
                    st.audio(conteudo_audio)
                    
                    # 3. Salva no Storage e no Banco (Com tratamento de erro silencioso)
                    try:
                        nome_arq = f"{st.session_state.usuario_id}/{uuid.uuid4()}.mp3"
                        # Tenta fazer o upload
                        supabase.storage.from_("darkinfor").upload(path=nome_arq, file=conteudo_audio)
                        
                        # Pega a URL e salva no histórico
                        url_publica = supabase.storage.from_("darkinfor").get_public_url(nome_arq)
                        supabase.table("historico_audios").insert({
                            "user_id": st.session_state.usuario_id,
                            "texto": roteiro[:50] + "...",
                            "url_audio": url_publica
                        }).execute()
                        st.success("Salvo no histórico com sucesso!")
                    except Exception as e_bd:
                        # Se der erro no banco, ele não trava a tela, apenas avisa
                        st.info(f"Nota: Áudio gerado, mas houve um erro no salvamento automático.")
                        
                except Exception as ex:
                    st.error(f"Erro técnico na OpenAI: {ex}")

    # --- EXIBIÇÃO DO HISTÓRICO ---
    st.divider()
    st.subheader("📜 Seu Histórico de Áudios")
    try:
        dados = supabase.table("historico_audios").select("*").eq("user_id", st.session_state.usuario_id).execute()
        if dados.data:
            for item in dados.data:
                with st.expander(f"Texto: {item['texto']}"):
                    st.audio(item['url_audio'])
        else:
            st.write("Nenhum áudio salvo ainda.")
    except:
        pass
