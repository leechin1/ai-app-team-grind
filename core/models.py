"""
Data models for the app.
These schemas will be used throught the applicaton for : 
- Data validation 
- API documentation 
- Scalability 

These estabilish the data format used in the app

"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal
from enum import Enum
from datetime import datetime
import uuid

class DifficultyLevel(str, enum) : 
    """
    Difficulty level os the quizzes

    """

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class DocumentType(str, enum):
    """
    Type of documents supported
    
    """
    PDF = "pdf"
    IMAGE = "image"
    TEXT = "text"
    DOCX = "docx"

class FlashCard(BaseModel): 
    """
    Represents an individual flash card
    
    """
    # flash card ID 
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    front: str Field(..., 
                     min_length= 1 , 
                     max_length= 500
                     description= "front of de card with the concept")
    
    back: str Field(..., 
                    min_length= 1
                    max_length= 2000
                    description= "back of the card with the explanation"
                    )
    
    difficulty : DifficultyLevel = DifficultyLevel.MEDIUM 

    #tags for organization


