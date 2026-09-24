import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from backend.parser import parse_transcript
from backend.llm_service import extract_answers_from_transcript, synthesize_transcripts
from backend.models import TranscriptAnalysis, CrossTranscriptSynthesis
from thefuzz import fuzz    

app = FastAPI(title="Transcript Analyzer API")

# Ensure the data paths exist
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")

# --- Endpoints ---

@app.get("/api/transcripts")
def get_parsed_transcripts():
    """Reads all .txt files in data/raw and returns them as structured JSON."""
    if not os.path.exists(RAW_DIR):
        raise HTTPException(status_code=404, detail="Raw data directory not found.")
        
    files = [f for f in os.listdir(RAW_DIR) if f.endswith('.txt')]
    if not files:
        raise HTTPException(status_code=404, detail="No transcript files found in data/raw.")
        
    parsed_data = []
    for file in files:
        file_path = os.path.join(RAW_DIR, file)
        parsed = parse_transcript(file_path)
        parsed_data.append(parsed)
        
    return {"transcripts": parsed_data}

@app.post("/api/analyze", response_model=list[TranscriptAnalysis])
def analyze_all_transcripts():
    """Passes the parsed JSON through the Groq LLM to extract interview answers."""
    parsed_payload = get_parsed_transcripts()
    transcripts = parsed_payload["transcripts"]
    
    analyses = []
    for t in transcripts:
        # Convert the dialogue list to a JSON string for the LLM prompt
        dialogue_str = json.dumps(t["dialogue"])
        
        # Create a single lowercase string of the full transcript for verification
        full_text = " ".join([d["text"] for d in t["dialogue"]]).lower()
        
        # Call Groq via our llm_service
        analysis = extract_answers_from_transcript(dialogue_str, t["expert_name"])
        
        # Ensure the market field is attached
        analysis.market = t["market"]
        
        # Step 4: Deterministic Quote Verification Layer
        for ans in analysis.answers:
            if ans.exact_quote:
                # Use fuzzy partial matching to ignore minor whitespace/punctuation differences
                # A score > 90 means it's a genuine verbatim match
                match_score = fuzz.partial_ratio(ans.exact_quote.lower(), full_text)
                ans.is_verified = match_score > 90
            else:
                ans.is_verified = False
                
        analyses.append(analysis)
        
    return analyses

@app.post("/api/synthesize", response_model=CrossTranscriptSynthesis)
def synthesize_all(analyses: list[TranscriptAnalysis]):
    """Takes the extracted answers and finds cross-document themes and disagreements."""
    analyses_dicts = [a.model_dump() for a in analyses]
    synthesis = synthesize_transcripts(analyses_dicts)
    return synthesis

from backend.llm_service import chat_with_transcripts

class ChatRequest(BaseModel):
    query: str

@app.post("/api/chat")
def chat_endpoint(request: ChatRequest):
    # Fetch the parsed JSON transcripts to use as context
    parsed_payload = get_parsed_transcripts()
    context_str = json.dumps(parsed_payload["transcripts"])
    
    answer = chat_with_transcripts(request.query, context_str)
    return {"response": answer}

@app.post("/api/analyze", response_model=list[TranscriptAnalysis])
def analyze_all_transcripts():
    parsed_payload = get_parsed_transcripts()
    transcripts = parsed_payload["transcripts"]
    
    analyses = []
    for t in transcripts:
        dialogue_str = json.dumps(t["dialogue"])
        full_text = " ".join([d["text"] for d in t["dialogue"]]).lower()
        
        analysis = extract_answers_from_transcript(dialogue_str, t["expert_name"])
        analysis.market = t["market"]
        
        # Step 4: Deterministic Quote Verification Layer
        for ans in analysis.answers:
            if ans.exact_quote:
                # Clean up punctuation and whitespace for reliable matching
                clean_quote = ans.exact_quote.strip().strip('"').strip("'").lower()
                ans.is_verified = clean_quote in full_text
            else:
                ans.is_verified = False
                
        analyses.append(analysis)
        
    return analyses