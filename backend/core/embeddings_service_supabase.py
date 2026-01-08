"""
Embeddings service using Gemini (no OpenAI required)
"""
import os
from typing import List, Dict, Any
import hashlib


class SupabaseEmbeddingsService:
    """Generate embeddings using Gemini"""

    def __init__(self):
        self.chunk_size = 512
        self.chunk_overlap = 50

    def generate_embedding_gemini(self, text: str) -> List[float]:
        """Generate embedding using Gemini"""
        try:
            from google import genai

            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                return self.generate_embedding_fallback(text)

            client = genai.Client(api_key=api_key)

            # Use Gemini's embedding model with new API
            result = client.models.embed_content(
                model="models/text-embedding-004",
                content=text
            )

            embedding = result.embeddings[0].values

            # Pad to 1536 dimensions to match schema
            if len(embedding) < 1536:
                embedding = list(embedding) + [0.0] * (1536 - len(embedding))

            return embedding[:1536]

        except Exception as e:
            print(f"⚠️  Gemini embedding failed ({e}), using fallback")
            return self.generate_embedding_fallback(text)

    def generate_embedding_fallback(self, text: str) -> List[float]:
        """Fallback: deterministic hash-based embedding"""
        if not text or not text.strip():
            raise ValueError("Cannot generate embedding for empty text")

        # Create deterministic vector from text hash
        text_bytes = text.encode('utf-8')
        hash_obj = hashlib.sha256(text_bytes)
        hash_bytes = hash_obj.digest()

        # Create 1536-dimensional vector
        vector = []
        for i in range(1536):
            byte_index = i % len(hash_bytes)
            value = (hash_bytes[byte_index] / 255.0) * 2 - 1  # Normalize to [-1, 1]
            vector.append(value)

        return vector

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding (tries Gemini first, falls back if needed)"""
        return self.generate_embedding_gemini(text)

    def chunk_text(self, text: str) -> List[Dict[str, Any]]:
        """Split text into chunks"""
        if not text or not text.strip():
            return []

        chunks = []
        start = 0
        chunk_index = 0

        while start < len(text):
            end = start + self.chunk_size

            # Try to break at sentence boundary
            if end < len(text):
                sentence_end = text.rfind('.', start, end)
                if sentence_end == -1:
                    sentence_end = text.rfind('\n', start, end)
                if sentence_end == -1:
                    sentence_end = text.rfind(' ', start, end)

                if sentence_end != -1 and sentence_end > start:
                    end = sentence_end + 1

            chunk_content = text[start:end].strip()

            if chunk_content:
                chunks.append({
                    "content": chunk_content,
                    "chunk_index": chunk_index
                })
                chunk_index += 1

            start = end - self.chunk_overlap if end < len(text) else end

        return chunks

    def generate_embeddings_for_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate embeddings for chunks"""
        if not chunks:
            return []

        for chunk in chunks:
            chunk["embedding"] = self.generate_embedding(chunk["content"])

        return chunks

    def embed_document(self, text: str) -> List[Dict[str, Any]]:
        """Full pipeline: chunk + embed"""
        chunks = self.chunk_text(text)
        return self.generate_embeddings_for_chunks(chunks)


# Global instance
embeddings_service = SupabaseEmbeddingsService()
