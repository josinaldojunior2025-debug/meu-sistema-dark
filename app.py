import streamlit as st
from openai import OpenAI

# Configuração visual do site
st.set_page_config(page_title="Sistema de Voz Dark", page_icon="🎙️")
st.title("🎙️ Gerador de Voz Realista")
st.write("Cole seu roteiro abaixo e transforme em áudio profissional.")

# Configuração da API (Aqui você colocará sua chave depois)
api_key = st.sidebar.text_input("Insira sua OpenAI API Key", type="password")

if api_key:
    client = OpenAI(api_key=api_key)
    
    # Área de texto
    texto = st.text_area("Roteiro do Vídeo:", placeholder="Era uma vez um canal dark...", height=200)
    
    # Seleção de vozes
    voz = st.selectbox("Escolha a Voz:", ["alloy", "echo", "fable", "onyx", "nova", "shimmer"])

    if st.button("Gerar Áudio"):
        if texto:
            with st.spinner("A IA está narrando seu texto..."):
                # Chamada para a API
                response = client.audio.speech.create(
                    model="tts-1",
                    voice=voz,
                    input=texto
                )
                
                # Salva e exibe o áudio
                response.stream_to_file("output.mp3")
                st.audio("output.mp3")
                st.success("Áudio gerado com sucesso!")
        else:
            st.warning("Por favor, digite um texto.")
else:
    st.info("Insira sua chave da API na lateral para começar.")
