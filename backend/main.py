import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from backend.parser import parse_transcript
from backend.llm_service import extract_answers_from_transcript, synthesize_transcripts
from backend.models import TranscriptAnalysis, CrossTranscriptSynthesis

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
        # Call Groq via our llm_service
        analysis = extract_answers_from_transcript(dialogue_str, t["expert_name"])
        # Ensure the market field is attached
        analysis.market = t["market"]
        analyses.append(analysis)
        
    return analyses

@app.post("/api/synthesize", response_model=CrossTranscriptSynthesis)
def synthesize_all(analyses: list[TranscriptAnalysis]):
    """Takes the extracted answers and finds cross-document themes and disagreements."""
    analyses_dicts = [a.model_dump() for a in analyses]
    synthesis = synthesize_transcripts(analyses_dicts)
    return synthesis