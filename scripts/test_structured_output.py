"""
pilot test of the difference bewteen generating flashcards with prompt por directly with a scrutrured outpu
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.models import FlashCard 
from core.ai_generator import AIContentGenerator
from pydantic import TypeAdapter
from google import genai 
from dotenv import load_dotenv 
import json
import os 
import time
from typing import List

load_dotenv()

schema = TypeAdapter(List[FlashCard]).json_schema()

print(json.dumps(schema, indent= 2))


def test_with_structured_output() : 
    try : 
        client = genai.Client(api_key = os.getenv('GEMINI_API_KEY'))
        prompt ="""
                Cria 3 flash card sobre o que é a mitocondria, função, estrutura e importancia.              
                """
        start_time = time.time()
        response = client.models.generate_content(
        model ="gemini-2.5-flash",
        contents =prompt,
        config ={"response_mime_type": "application/json",
                "response_schema": schema
        }
        )
        end_time = time.time()
        print(response.text)
        print(f"Generated in {end_time-start_time} seconds ***************************************************")
    except Exception as e:
        print(f"Ocorreu um erro ao chamar a API: {e}")

def test_with_prompt_engeneering() :
    try : 
        client = genai.Client(api_key = os.getenv('GEMINI_API_KEY'))
        start_time = time.time()
        response =client.models.generate_content(
        model = "gemini-2.5-flash",
        contents = f"""
                Você é um especialista em criar material educacional de alta qualidade.

                TAREFA: Cria 3 flash card sobre o que é a mitocondria, função, estrutura e importancia.

                INSTRUÇÕES IMPORTANTES:
                - Cada flashcard deve testar UM conceito específico
                - Front (pergunta): Clara, concisa, sem ambiguidade (máx 100 caracteres)
                - Back (resposta): Completa mas sucinta, não copiar texto literal (máx 300 caracteres)
                - Tags: Identifica 1-3 tags relevantes (ex: ["biologia", "célula", "organelas"])
                - Difficulty: 
                * easy - definições simples, factos básicos
                * medium - relações entre conceitos, processos
                * hard - análise, aplicação, comparações complexas
                - Varia os tipos de perguntas: "O que é...", "Qual a função...", "Como...", "Diferença entre..."
                - NÃO inventes informação que não está no conteúdo
                - NÃO uses perguntas verdadeiro/falso
                - SÊ específico e preciso

                FORMATO DE SAÍDA (JSON apenas, sem explicações):
                [
                {{
                    "front": "O que é a mitocôndria?",
                    "back": "Organela celular responsável pela produção de energia (ATP) através da respiração celular",
                    "difficulty": "easy",
                    "tags": ["biologia", "célula", "organelas"]
                }},
                {{
                    "front": "Qual o processo que ocorre nas cristas mitocondriais?",
                    "back": "Fosforilação oxidativa, última etapa da respiração celular que produz a maior parte do ATP",
                    "difficulty": "medium",
                    "tags": ["biologia", "respiração celular"]
                }}
                ]

                CRÍTICO: Retorna APENAS o array JSON válido. Sem ```json, sem texto extra, sem explicações.
                """
                    )
        end_time = time.time()
        print(response.text)
        print(f"Generated in {end_time-start_time} seconds ***************************************************")

    except Exception as e:
        print(f"Ocorreu um erro ao chamar a API: {e}")


print("=" * 60)
print("TESTE COM PROMPT ENGINEERING:")
print("=" * 60)
test_with_prompt_engeneering()

print("\n" + "=" * 60)
print("TESTE COM STRUCTURED OUTPUT:")
print("=" * 60)
test_with_structured_output()