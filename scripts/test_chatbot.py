import streamlit as st
from google import genai
import os
from dotenv import load_dotenv
from pathlib import Path
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from document_processor import DocumentProcessor  # your custom processor

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(page_title="Gemini Chat RAG", page_icon="🤖", layout="centered")
st.title("🤖 Notiq ChatBot with RAG")

# Initialize Gemini client
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
MODEL = "gemini-2.5-flash-lite"

# --- SIDEBAR SETTINGS ---
with st.sidebar:
    st.header("⚙️ Settings")
    temperature = st.slider("Temperature", 0.0, 2.0, 0.7)
    system_instruction = st.text_area(
        "System Instruction",
        value="You are a helpful assistant. Be concise and friendly.",
        height=100
    )
    st.divider()
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.chat = None
        st.rerun()

# --- SESSION STATE INIT ---
if "chat" not in st.session_state or st.session_state.chat is None:
    st.session_state.chat = client.chats.create(
        model=MODEL,
        config={'system_instruction': system_instruction, 'temperature': temperature}
    )

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- BUILD / LOAD KNOWLEDGE BASE ---
if "knowledge_base" not in st.session_state:
    processor = DocumentProcessor()
    kb = []

    # Folder with docs to process (TXT, PDF, images)
    doc_folder = Path("knowledge_docs")
    doc_folder.mkdir(exist_ok=True)

    for file_path in list(doc_folder.glob("*")):
        with open(file_path, "rb") as f:
            try:
                result = processor.process_document(file_bytes=f.read(), filename=file_path.name)
                kb.append({"content": result.content, "metadata": result.metadata})
                print(f"Processed {file_path.name}")
            except Exception as e:
                print(f"Failed to process {file_path.name}: {e}")

    st.session_state.knowledge_base = kb

# --- EMBEDDINGS ---
if "kb_embeddings" not in st.session_state:
    from openai import OpenAI
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    embeddings = []
    for doc in st.session_state.knowledge_base:
        emb = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=doc["content"]
        ).data[0].embedding
        embeddings.append(np.array(emb))
    st.session_state.kb_embeddings = embeddings

# --- DISPLAY CHAT HISTORY ---
for msg in st.session_state.messages:
    avatar = "👤" if msg["role"] == "user" else "🤖"
    with st.chat_message(msg["role"], avatar=avatar):
        st.write(msg["content"])

# --- CHAT INPUT ---
if user_query := st.chat_input("Insert your doubt...", key="chat_input"):

    with st.chat_message("user", avatar="👤"):
        st.write(user_query)

    st.session_state.messages.append({"role": "user", "content": user_query})

    # --- RAG RETRIEVAL ---
    query_emb = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=user_query
    ).data[0].embedding
    query_emb = np.array(query_emb)

    similarities = cosine_similarity([query_emb], st.session_state.kb_embeddings)[0]
    top_idx = similarities.argsort()[-3:][::-1]  # top 3 documents
    context = "\n".join([st.session_state.knowledge_base[i]["content"] for i in top_idx])

    full_prompt = f"Context:\n{context}\n\nUser Question:\n{user_query}"

    # --- GET GEMINI RESPONSE ---
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Thinking..."):
            try:
                response = st.session_state.chat.send_message(full_prompt)
                st.write(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Error: {e}")

# --- WELCOME MESSAGE ---
if len(st.session_state.messages) == 0:
    st.info(
        "👋 Welcome! Drop TXT/PDF/image files in `knowledge_docs/` folder, "
        "ask questions, and I will answer using the knowledge base!"
    )
