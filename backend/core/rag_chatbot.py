from google import genai
from typing import Optional
import os
from core.document_processor import DocumentProcessor

class DocumentQnAChatbot:
    """
    Chatbot conversacional de Q&A baseado diretamente em documentos processados.
    """

    def __init__(
        self,
        api_key: str,
        document_processor: DocumentProcessor,
        model_name: str = "gemini-2.5-flash",
        max_document_chars: int = 12000,
        max_history_turns: int = 10,
    ):
        """
        Args:
            api_key: Gemini API key
            document_processor: Instância do DocumentProcessor
            model_name: Modelo Gemini
            max_document_chars: Limite de texto do documento no prompt
            max_history_turns: Quantos turnos anteriores incluir
        """
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.document_processor = document_processor

        self.max_document_chars = max_document_chars
        self.max_history_turns = max_history_turns

        # Estado por sessão
        self.sessions: dict[str, dict] = {}


    def ingest_document(
        self,
        session_id: str,
        file_bytes: bytes,
        filename: str,
        mime_type: Optional[str] = None,
    ):
        """
        Processa um documento e associa à sessão de chat.
        """

        processed = self.document_processor.process_document(
            file_bytes=file_bytes,
            filename=filename,
            mime_type=mime_type,
        )

        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "documents": [],
                "messages": [],
            }

        self.sessions[session_id]["documents"].append(processed)
    
    def _build_document_context(self, session_id: str) -> str:
        docs = self.sessions[session_id]["documents"]

        combined = []
        total_chars = 0

        for doc in docs:
            header = f"\n--- Documento: {doc.metadata.filename} ---\n"
            body = doc.content

            remaining = self.max_document_chars - total_chars
            if remaining <= 0:
                break

            combined_text = header + body[:remaining]
            combined.append(combined_text)
            total_chars += len(combined_text)

        return "\n".join(combined)
    
    def _build_prompt(
            self,
            document_context: str,
            chat_history: str,
            user_question: str,
        ) -> str:
            return f"""
        You are a helpful assistant.
        Answer the question using ONLY the document content below.
        If the answer is not present, say "I don't know based on the document."

        Conversation history:
        {chat_history}

        Document content:
        {document_context}

        User question:
        {user_question}

        Answer:
        """.strip()

    def chat(self, session_id: str, user_message: str) -> str:
        if session_id not in self.sessions:
            raise ValueError("Sessão não encontrada. Ingesta um documento primeiro.")

        session = self.sessions[session_id]

        # Build history (sliding window)
        history_msgs = session["messages"][-self.max_history_turns * 2 :]
        chat_history = "\n".join(
            f"{m['role']}: {m['content']}" for m in history_msgs
        )

        document_context = self._build_document_context(session_id)

        prompt = self._build_prompt(
            document_context=document_context,
            chat_history=chat_history,
            user_question=user_message,
        )

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
        )

        answer = response.text.strip()

        # Update memory
        session["messages"].append({"role": "user", "content": user_message})
        session["messages"].append({"role": "assistant", "content": answer})

        return answer



# 1️⃣ Initialize processor
document_processor = DocumentProcessor(
    gemini_api_key=os.getenv("GOOGLE_API_KEY")
)

# 2️⃣ Read file bytes
file_path = r"C:\Users\rafae\Documents\GitHub\ai-app-team-grind\docs\spaced_repetition_timeline.md"
with open(file_path, "rb") as f:
    file_bytes = f.read()

# 3️⃣ Initialize chatbot
chatbot = DocumentQnAChatbot(
    api_key=os.getenv("GOOGLE_API_KEY"),
    document_processor=document_processor
)

# 4️⃣ Ingest document
chatbot.ingest_document(
    session_id="chat_1",
    file_bytes=file_bytes,
    filename="spaced_repetition_timeline.md"
)

# 5️⃣ Ask question
answer = chatbot.chat(
    session_id="chat_1",
    user_message="What is the main point of this document?"
)
print(answer)
