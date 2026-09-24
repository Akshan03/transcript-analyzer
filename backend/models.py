from pydantic import BaseModel, Field
from typing import List, Optional

# --- Phase 2: Extraction Schema (Per Transcript) ---

class AnswerExtraction(BaseModel):
    question_id: int = Field(description="The ID of the interview guide question (1-6)")
    summary_answer: str = Field(description="A concise summary of the expert's answer.")
    exact_quote: Optional[str] = Field(description="An exact, verbatim quote from the text that supports the answer. If the answer is not discussed, return null.")
    timestamp: Optional[str] = Field(description="The exact timestamp (e.g., '01:20') associated with the quote. If not discussed, return null.")
    is_verified: bool = Field(default=False, description="Whether the quote was verified against the source text.")

class TranscriptAnalysis(BaseModel):
    expert_name: str
    market: str
    answers: List[AnswerExtraction]

# --- Phase 3: Synthesis Schema (Cross-Transcript) ---

class Theme(BaseModel):
    theme_title: str
    description: str
    supported_by: List[str] = Field(description="List of expert names who support this theme (e.g., ['Dr. Martin', 'Anna Keller'])")

class Disagreement(BaseModel):
    topic: str
    description: str
    differing_viewpoints: List[str] = Field(description="Describe how the experts differ (e.g., 'Dr. Carter emphasizes X, while Anna Keller emphasizes Y')")

class CrossTranscriptSynthesis(BaseModel):
    common_themes: List[Theme]
    key_disagreements: List[Disagreement]