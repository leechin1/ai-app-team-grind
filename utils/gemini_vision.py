"""
Extração de texto de imagens usando Gemini Vision API.
"""

import google.generativeai as genai
from PIL import Image
import io

class GeminiVisionExtractor:
    """
    Extrai texto de imagens usando Gemini Vision.
    
    Vantagens sobre OCR tradicional:
    - Melhor qualidade de reconhecimento
    - Entende contexto (útil para handwriting, diagramas)
    - Suporta múltiplas línguas automaticamente
    """
    
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        # Usa modelo com capacidades de visão
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite')
    
    def extract_text_from_image(self, image_bytes: bytes) -> str:
        """
        Extrai texto de imagem usando Gemini Vision.
        
        Args:
            image_bytes: Conteúdo da imagem em bytes
            
        Returns:
            Texto extraído
            
        Raises:
            ValueError: Se não conseguir extrair texto
            
        Example:
            >>> with open('notes.jpg', 'rb') as f:
            >>>     img_bytes = f.read()
            >>> extractor = GeminiVisionExtractor(api_key="...")
            >>> text = extractor.extract_text_from_image(img_bytes)
        """
        
        try:
            # Converte bytes para Image (Gemini aceita PIL Image)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Prompt otimizado para extração de texto
            prompt = """
            Extrai TODO o texto visível nesta imagem.
            
            Instruções:
            - Transcreve exatamente como está escrito
            - Mantém a estrutura (parágrafos, listas, etc)
            - Se houver texto manuscrito, faz o teu melhor para ler
            - Se houver diagramas com texto, inclui as labels
            - Não adiciones comentários teus, só o texto da imagem
            - Se não houver texto, diz apenas "SEM TEXTO"
            
            Texto extraído:
            """
            
            # Envia imagem + prompt para Gemini
            response = self.model.generate_content([prompt, image])
            
            text = response.text.strip()
            
            # Valida resultado
            if not text or text == "SEM TEXTO" or len(text) < 5:
                raise ValueError(
                    "Gemini não conseguiu extrair texto da imagem. "
                    "Verifica se a imagem contém texto legível."
                )
            
            return text
            
        except Exception as e:
            raise ValueError(f"Erro ao processar imagem com Gemini: {str(e)}")
    
    def extract_and_analyze(self, image_bytes: bytes) -> dict:
        """
        Extrai texto E analisa o conteúdo (útil para gerar flashcards melhores).
        
        Args:
            image_bytes: Conteúdo da imagem
            
        Returns:
            Dict com 'text', 'topics', 'type' (notes/diagram/table/etc)
            
        Example:
            >>> result = extractor.extract_and_analyze(img_bytes)
            >>> print(result['text'])
            >>> print(result['topics'])  # ["biologia", "célula"]
            >>> print(result['type'])    # "handwritten_notes"
        """
        
        try:
            image = Image.open(io.BytesIO(image_bytes))
            
            prompt = """
            Analisa esta imagem e retorna APENAS um JSON com:
            
            {
              "text": "Todo o texto extraído da imagem",
              "type": "handwritten_notes|typed_text|diagram|table|mixed",
              "topics": ["tópico1", "tópico2"],
              "language": "pt|en|es|etc"
            }
            
            Não adiciones ```json nem explicações, só o JSON.
            """
            
            response = self.model.generate_content([prompt, image])
            
            import json
            import re
            
            # Limpa resposta
            text = response.text.strip()
            text = re.sub(r'```json\s*', '', text)
            text = re.sub(r'```\s*', '', text)
            
            result = json.loads(text)
            
            if not result.get('text') or len(result['text']) < 5:
                raise ValueError("Texto extraído muito curto ou vazio")
            
            return result
            
        except json.JSONDecodeError:
            # Fallback: extrai só texto
            return {
                "text": self.extract_text_from_image(image_bytes),
                "type": "unknown",
                "topics": [],
                "language": "unknown"
            }
        except Exception as e:
            raise ValueError(f"Erro na análise: {str(e)}")