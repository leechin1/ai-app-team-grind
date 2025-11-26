"""
Data models for the app.
These schemas will be used throught the applicaton for : 
- Data validation 
- API documentation 
- Scalability 

These estabilish the data format used in the app

"""
from pydantic import BaseModel, Field, validator, model_validator
from typing import List, Optional, Literal
from enum import Enum
from datetime import datetime
import uuid

class DifficultyLevel(str, Enum) : 
    """
    Difficulty level os the quizzes                               

    """

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class DocumentType(str, Enum):
    """
    Type of documents supported
    
    """
    PDF = "pdf"
    IMAGE = "image"
    TEXT = "text"
    DOCX = "docx"

# -------------- flashcards ---------------------

class FlashCard(BaseModel): 
    """
    Represents an individual flash card
    
    """
    # flash card ID 
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    #Front side of the card 
    front: str = Field(..., 
                     min_length= 1 , 
                     max_length= 500,
                     description= "front of de card with the concept")
    
    #back side of the card
    back: str = Field(..., 
                    min_length= 1,
                    max_length= 2000,
                    description= "back of the card with the explanation"
                    )
    #base difficulty level 
    difficulty : DifficultyLevel = DifficultyLevel.MEDIUM 

    #tags for organization
    tags : List[str] = Field(default_factory= list)

    # source
    source_text : Optional[str] = None

    # date where the flashcard was generated
    created_at: datetime = Field(default_factory= datetime.now)

    # spaced repetion scheduled (to be developed)


    # next revision 
    next_review_date : Optional[datetime] = None

    #results
    review_count : int = 0

    ease_factor : float = 2.5

class FlashcardGenerationRequest(BaseModel) : 
    """ 
    Data used to generate flash cards\
    
    exemple : 

        {
    "content": "A mitocôndria é...",
    "num_cards": 10,
    "difficulty_filter": "medium",
    "topics": ["biologia", "célula"]
        }
    
    """
    # content to generate the flashcards
    content : str = Field(..., min_length= 50)

    # number of generated cards
    num_cards : int = Field(default = 10 , ge = 1, le = 50)

    # difficulty filter 
    difficulty_filter: Optional[DifficultyLevel] = None

class FlashcardGenerationResponse(BaseModel): 
    """
    Response with the generated flashcards.

    contains the flashcards and useful metadata
    
    """

    #list with the generated flashcards
    flashcards : List[FlashCard]

    # how many flashcards where generates
    total_generated : int

    # length on the generated content
    content_length : int

    # time taken to generate
    generation_time_seconds : float 

    # warnings (to be developed)

# -------------- quizzes ----------------------------------------

class QuizQuestion(BaseModel): 
    """
    one multiple choide quizz question
    
    """
    id : str = Field(default_factory= lambda : str(uuid.uuid4()))

    # the question 
    question : str = Field(..., min_length= 10)

    # option for the answer 
    options: List[str] = Field(min_length=4, max_length=4)
    
    #correct answer 
    correct_answer_index: int = Field(..., ge=0, le=3)  # 0 a 3

    #answer explanation 
    explanation: str

    #concept explanation
    concept: str 

    # orignal source text
    source_text : Optional[str] = None

    # validator
    @validator('correct_answer_index')
    def validate_correct_index(cls, v, values):
        """
        Garantees that correct_answer_index isn't outside of the range of options.
        
        Exemple:
        - if options = ["A", "B", "C", "D"] (4 itens)
        - correct_answer_index can be 0, 1, 2 or 3
        - if it is 4 or more raises an error!
        """
        if 'options' in values and v >= len(values['options']):
            raise ValueError(
                f'correct_answer_index ({v}) outside of the range. '
                f'Options has {len(values["options"])} items.'
            )
        return v

class QuizAnswer(BaseModel):
    """
    Uma resposta do utilizador a uma questão.
    """
    
    question_id: str
    
    # Que opção o user escolheu (índice)
    user_answer_index: int
    
    # Quanto tempo demorou a responder (IMPORTANTE para ML!)
    # Questão: porque isto é importante para revisão espaçada?
    time_spent_seconds: float
    
    # Quando respondeu
    timestamp: datetime = Field(default_factory=datetime.now)


class QuizResult(BaseModel):
    """
    Result of the quizz
    
    Saves the answers and the attempt.

    """
    
    quiz_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Questsions of the quizz
    questions: List[QuizQuestion]
    
    # answers of the user
    answers: List[QuizAnswer]
    
    # number of correct answers 
    correct_count: int
    
    # total number of questions 
    total_questions: int

    # Score final (0-100)
    score: float = 0.0
    
    # time where the quizz was completed
    completed_at: datetime = Field(default_factory=datetime.now)

    #  validator to auto-set score 
    @model_validator(mode='after')
    def calculate_score(self):
        """Auto-calculate score after all fields are set"""
        if self.total_questions > 0:
            self.score = (self.correct_count / self.total_questions) * 100
        return self

# ---------------------------- Documents ---------------------------------------------------------------------

class DocumentMetadata(BaseModel):
    """
    Metadata of the processed source of information for the flashcards and quizz.

    """
    
    document_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Type of documente used
    document_type: DocumentType
    
    # name of the original file
    filename: str
    
    # size in bytes
    file_size_bytes: int
    
    # extratext text in carachters ? 
    extracted_text_length: int
    
    # how it was extracted.
    extraction_method: str
    
    # time where the processing happened
    processed_at: datetime = Field(default_factory=datetime.now)
    
    # number of pages(for pdf only)
    num_pages: Optional[int] = None


class ProcessedDocument(BaseModel):
    """
    Processed document ready to be used.
    """
    
    metadata: DocumentMetadata
    
    # extracted text
    content: str
    
    # preview (using gemini mistral maybe to save tokens)
    preview: str

# ---------------------------------- Spaced Revison Scheduled ----------------------------------------

class ReviewScheduleItem(BaseModel):
    """
    One item in the revision schedule
    """
    
    flashcard_id: str
    flashcard_front: str  # to show the user
    
    # When to review
    next_review_date: datetime
    
    # probability of remembering the topic (0.0 to 1.0()
    # to be developed:: how to calculate this using an ML model
    retention_probability: float = Field(ge=0.0, le=1.0)
    
    # priority (high if retention_prob low)
    priority: Literal["high", "medium", "low"]
    
    # Days until next revision
    days_until_review: int


class StudySessionStats(BaseModel):
    """
    Statistics of a study section
    used for training the ML model
    """
    
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # number of revewied cards
    total_cards_reviewed: int
    
    # number of correct answers 
    correct_answers: int
    
    # right answers rate
    accuracy: float
    
    # average time spent per
    average_time_per_card: float
    
    # Timestamps
    started_at: datetime
    completed_at: datetime