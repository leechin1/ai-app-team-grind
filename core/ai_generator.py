# core/ai_generator.py

"""
Gerador de conteúdo educacional usando Gemini API.

Este módulo implementa a lógica de:
- Gerar flashcards a partir de texto
- Gerar quizzes de escolha múltipla
- Prompt engineering otimizado
- Validação robusta de outputs
- Retry logic para falhas de API
"""

from google import genai
import json
import re
import time
from typing import List, Optional

from core.models import (
    FlashCard,
    FlashcardGenerationRequest,
    FlashcardGenerationResponse,
    QuizQuestion,
    DifficultyLevel
)


class AIContentGenerator:
    """
    Gera flashcards e quizzes usando Gemini API.
    
    Examples:
        >>> generator = AIContentGenerator(api_key="your_key")
        >>> response = generator.generate_flashcards("A mitocôndria...", num_cards=5)
        >>> print(f"Gerados {len(response.flashcards)} flashcards")
    """
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        """
        Inicializa o gerador.

        Args:
            api_key: Gemini API key
            model_name: Modelo a usar (default: gemini-2.5-flash - rápido e barato)
        """
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
    
    # ========================================================================
    # FLASHCARDS GENERATION
    # ========================================================================
    
    def generate_flashcards(
        self,
        content: str,
        num_cards: int = 10,
        difficulty_filter: Optional[DifficultyLevel] = None,
        focus_topics: Optional[List[str]] = None,
        source_document_id: Optional[str] = None,
        source_document_name: Optional[str] = None
    ) -> FlashcardGenerationResponse:
        """
        Gera flashcards a partir de conteúdo educacional.
        
        Args:
            content: Texto fonte (de PDF, editor, etc)
            num_cards: Quantos flashcards gerar (1-50)
            difficulty_filter: Filtrar por dificuldade específica
            focus_topics: Lista de tópicos para focar
            source_document_id: ID do documento de origem
            source_document_name: Nome do documento de origem
            
        Returns:
            FlashcardGenerationResponse com flashcards validados e metadados
            
        Raises:
            ValueError: Se conteúdo muito curto ou geração falhar
        """
        
        start_time = time.time()
        
        # Validação
        if len(content.strip()) < 50:
            raise ValueError(
                f"Conteúdo muito curto para gerar flashcards. "
                f"Mínimo 50 caracteres, recebido: {len(content)}"
            )
        
        if not 1 <= num_cards <= 50:
            raise ValueError("num_cards deve estar entre 1 e 50")
        
        print(f"Gerando {num_cards} flashcards...")
        
        # Constrói prompt
        prompt = self._build_flashcard_prompt(
            content=content,
            num_cards=num_cards,
            difficulty_filter=difficulty_filter,
            focus_topics=focus_topics
        )
        
        # Chama Gemini
        raw_response = self._call_gemini_with_retry(prompt)
        
        # Parse JSON
        flashcards_data = self._parse_json_response(raw_response)
        
        # Valida e cria Flashcard objects
        flashcards = []
        warnings = []
        
        for i, card_data in enumerate(flashcards_data):
            try:
                # Adiciona metadados de origem
                card_data['source_document_id'] = source_document_id
                card_data['source_document_name'] = source_document_name
                
                # Valida com Pydantic
                flashcard = FlashCard(**card_data)
                flashcards.append(flashcard)
                
            except Exception as e:
                warning = f"Card {i+1} inválido: {str(e)[:80]}"
                warnings.append(warning)
                print(f"   [AVISO] {warning}")
        
        # Verifica que gerou pelo menos alguns
        if len(flashcards) == 0:
            raise ValueError(
                "Nenhum flashcard válido foi gerado. "
                "Tenta com conteúdo diferente ou menos cards."
            )
        
        if len(flashcards) < num_cards // 2:
            warnings.append(
                f"Apenas {len(flashcards)} de {num_cards} cards válidos"
            )
        
        # Calcula metadados
        generation_time = time.time() - start_time
        estimated_reading_time = len(content) / 1000 * 4  # ~250 palavras/min
        
        # Identifica tópicos
        identified_topics = list(set(
            tag 
            for card in flashcards 
            for tag in card.tags
        ))
        
        print(f"[OK] Gerados {len(flashcards)} flashcards em {generation_time:.1f}s")
        
        # Retorna response (using only fields defined in FlashcardGenerationResponse model)
        return FlashcardGenerationResponse(
            flashcards=flashcards,
            total_generated=len(flashcards),
            content_length=len(content),
            generation_time_seconds=round(generation_time, 2)
        )
    
    def _build_flashcard_prompt(
        self,
        content: str,
        num_cards: int,
        difficulty_filter: Optional[DifficultyLevel],
        focus_topics: Optional[List[str]]
    ) -> str:
        """Constrói prompt otimizado para gerar flashcards"""
        
        # Instruções de dificuldade
        if difficulty_filter:
            difficulty_instruction = f"\n- Todos os cards devem ter dificuldade: {difficulty_filter.value}"
        else:
            difficulty_instruction = "\n- Varia a dificuldade (easy/medium/hard) de forma equilibrada"
        
        # Instruções de tópicos
        topics_instruction = ""
        if focus_topics:
            topics_str = ", ".join(focus_topics)
            topics_instruction = f"\n- Foca especialmente nestes tópicos: {topics_str}"
        
        # Trunca se muito longo (limite de tokens)
        max_content_length = 8000
        if len(content) > max_content_length:
            content = content[:max_content_length] + "\n\n[... conteúdo truncado ...]"
        
        # Prompt estruturado
        prompt = f"""
Você é um especialista em criar material educacional de alta qualidade.

TAREFA: Cria {num_cards} flashcards educacionais baseados no conteúdo abaixo.

CONTEÚDO FONTE:
{content}

INSTRUÇÕES IMPORTANTES:
- Cada flashcard deve testar UM conceito específico
- Front (pergunta): Clara, concisa, sem ambiguidade (máx 100 caracteres)
- Back (resposta): Completa mas sucinta, não copiar texto literal (máx 300 caracteres)
- Tags: Identifica 1-3 tags relevantes (ex: ["biologia", "célula", "organelas"])
- Difficulty: 
  * easy - definições simples, factos básicos
  * medium - relações entre conceitos, processos
  * hard - análise, aplicação, comparações complexas{difficulty_instruction}{topics_instruction}
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
        
        return prompt
    
    # ========================================================================
    # QUIZ GENERATION
    # ========================================================================
    
    def generate_quiz(
        self,
        content: str,
        num_questions: int = 5,
        difficulty_filter: Optional[DifficultyLevel] = None,
        focus_topics: Optional[List[str]] = None
    ) -> List[QuizQuestion]:
        """
        Gera quiz de escolha múltipla (sempre 4 opções).
        
        Args:
            content: Texto fonte
            num_questions: Quantas questões (1-20)
            difficulty_filter: Filtro de dificuldade
            focus_topics: Tópicos específicos
            
        Returns:
            Lista de QuizQuestion validados
            
        Raises:
            ValueError: Se conteúdo muito curto ou geração falhar
        """
        
        # Validação
        if len(content.strip()) < 50:
            raise ValueError("Conteúdo muito curto para gerar quiz")
        
        if not 1 <= num_questions <= 20:
            raise ValueError("num_questions deve estar entre 1 e 20")
        
        print(f"Gerando {num_questions} questoes de quiz...")
        
        # Constrói prompt
        prompt = self._build_quiz_prompt(
            content=content,
            num_questions=num_questions,
            difficulty_filter=difficulty_filter,
            focus_topics=focus_topics
        )
        
        # Chama Gemini
        raw_response = self._call_gemini_with_retry(prompt)
        
        # Parse JSON
        questions_data = self._parse_json_response(raw_response)
        
        # Valida e cria QuizQuestion objects
        questions = []
        
        for i, q_data in enumerate(questions_data):
            try:
                # Pydantic vai validar automaticamente:
                # - Exatamente 4 opções
                # - correct_answer_index entre 0-3
                # - Sem duplicatas, etc
                question = QuizQuestion(**q_data)
                questions.append(question)
                
            except Exception as e:
                print(f"   [AVISO] Questao {i+1} invalida: {str(e)[:80]}")
        
        if len(questions) == 0:
            raise ValueError("Nenhuma questão válida foi gerada")
        
        print(f"[OK] Geradas {len(questions)} questoes validas")
        
        return questions
    
    def _build_quiz_prompt(
        self,
        content: str,
        num_questions: int,
        difficulty_filter: Optional[DifficultyLevel],
        focus_topics: Optional[List[str]]
    ) -> str:
        """Constrói prompt para gerar quiz"""
        
        # Instruções de dificuldade
        if difficulty_filter:
            difficulty_instruction = f"\n- Todas as questões: dificuldade {difficulty_filter.value}"
        else:
            difficulty_instruction = "\n- Varia a dificuldade de forma equilibrada"
        
        # Instruções de tópicos
        topics_instruction = ""
        if focus_topics:
            topics_str = ", ".join(focus_topics)
            topics_instruction = f"\n- Foca nestes tópicos: {topics_str}"
        
        # Trunca se necessário
        max_length = 8000
        if len(content) > max_length:
            content = content[:max_length] + "\n\n[... truncado ...]"
        
        prompt = f"""
Você é um especialista em criar avaliações educacionais.

TAREFA: Cria {num_questions} questões de escolha múltipla baseadas no conteúdo.

CONTEÚDO FONTE:
{content}

INSTRUÇÕES CRÍTICAS:
- Cada questão DEVE ter EXATAMENTE 4 opções (nem mais, nem menos)
- Apenas UMA resposta correta por questão
- Opções incorretas (distratores) devem ser:
  * Plausíveis (baseadas em misconceptions comuns)
  * Claramente erradas para quem sabe o conteúdo
  * Não absurdas ou óbvias
- Question: Clara, completa, sem ambiguidade
- Explanation: 2-3 frases explicando porque a resposta está correta
- Concept: Conceito principal testado (ex: "Organelas celulares")
- Difficulty:{difficulty_instruction}{topics_instruction}
- Varia os tipos: definições, aplicação, comparação, causa-efeito
- NÃO uses "todas as anteriores" ou "nenhuma das anteriores"
- NÃO inventes informação que não está no conteúdo
- Opções devem ter tamanho similar (não dar pistas)

FORMATO DE SAÍDA (JSON apenas):
[
  {{
    "question": "Qual a função principal da mitocôndria na célula?",
    "options": [
      "Produzir energia através da respiração celular",
      "Sintetizar proteínas para a célula",
      "Armazenar material genético",
      "Regular a entrada e saída de substâncias"
    ],
    "correct_answer_index": 0,
    "explanation": "A mitocôndria é responsável pela produção de ATP (energia) através da respiração celular. Este processo ocorre nas cristas mitocondriais através da fosforilação oxidativa.",
    "difficulty": "easy",
    "concept": "Função das organelas celulares"
  }}
]

CRÍTICO: 
- Retorna APENAS o array JSON
- Cada questão tem EXATAMENTE 4 opções
- correct_answer_index é 0, 1, 2 ou 3
- Sem ```json, sem texto extra
"""
        
        return prompt
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _call_gemini_with_retry(
        self, 
        prompt: str, 
        max_retries: int = 3
    ) -> str:
        """
        Chama Gemini com retry logic para falhas temporárias.
        
        Implementa exponential backoff:
        - Tentativa 1: imediato
        - Tentativa 2: espera 1s
        - Tentativa 3: espera 2s
        - Tentativa 4: espera 4s
        """
        
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )

                if not response.text:
                    raise ValueError("Gemini retornou resposta vazia")

                return response.text
                
            except Exception as e:
                error_msg = str(e)
                print(f"   [AVISO] Tentativa {attempt + 1}/{max_retries} falhou: {error_msg[:80]}")
                
                if attempt < max_retries - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    print(f"      Aguardando {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    # Última tentativa falhou
                    raise Exception(
                        f"Gemini API falhou após {max_retries} tentativas. "
                        f"Último erro: {error_msg}"
                    )
    
    def _parse_json_response(self, raw_text: str) -> list:
        """
        Limpa e parseia resposta JSON do Gemini.
        
        Lida com:
        - Markdown code blocks (```json)
        - Texto extra antes/depois do JSON
        - Whitespace
        """
        
        # Remove markdown code blocks
        clean_text = re.sub(r'```json\s*', '', raw_text)
        clean_text = re.sub(r'```\s*', '', clean_text)
        
        # Encontra início do JSON ([ ou {)
        json_start = -1
        for i, char in enumerate(clean_text):
            if char in '[{':
                json_start = i
                break
        
        if json_start == -1:
            raise ValueError(
                "Não foi encontrado JSON válido na resposta. "
                f"Resposta: {raw_text[:200]}..."
            )
        
        # Encontra fim do JSON (] ou })
        json_end = -1
        for i in range(len(clean_text) - 1, -1, -1):
            if clean_text[i] in ']}':
                json_end = i + 1
                break
        
        if json_end == -1:
            raise ValueError("JSON incompleto na resposta")
        
        # Extrai só JSON
        json_text = clean_text[json_start:json_end].strip()
        
        # Parse
        try:
            parsed = json.loads(json_text)
            
            if not isinstance(parsed, list):
                raise ValueError(f"Esperava lista, recebeu {type(parsed).__name__}")
            
            if len(parsed) == 0:
                raise ValueError("Lista JSON está vazia")
            
            return parsed
            
        except json.JSONDecodeError as e:
            print(f"❌ Erro ao parsear JSON:")
            print(f"   {str(e)}")
            print(f"   JSON problemático:")
            print(f"   {json_text[:300]}...")
            raise ValueError(f"JSON inválido: {str(e)}")
    
    def _assess_content_difficulty(
        self,
        flashcards: List[FlashCard]
    ) -> Optional[DifficultyLevel]:
        """
        Avalia dificuldade geral do conteúdo baseado nos flashcards.
        
        Lógica:
        - Se >50% são hard → conteúdo é hard
        - Se >50% são easy → conteúdo é easy
        - Caso contrário → medium
        """
        if not flashcards:
            return None
        
        difficulty_counts = {
            DifficultyLevel.EASY: 0,
            DifficultyLevel.MEDIUM: 0,
            DifficultyLevel.HARD: 0
        }
        
        for card in flashcards:
            difficulty_counts[card.difficulty] += 1
        
        total = len(flashcards)
        
        if difficulty_counts[DifficultyLevel.HARD] > total * 0.5:
            return DifficultyLevel.HARD
        elif difficulty_counts[DifficultyLevel.EASY] > total * 0.5:
            return DifficultyLevel.EASY
        else:
            return DifficultyLevel.MEDIUM