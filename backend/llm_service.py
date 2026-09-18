import os
import instructor
from groq import Groq
from dotenv import load_dotenv
from .models import TranscriptAnalysis, CrossTranscriptSynthesis

# Load environment variables from .env file
load_dotenv()

# Initialize the Groq client and patch it with Instructor
# Ensure you have GROQ_API_KEY set in your .env file
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
instructor_client = instructor.from_groq(client, mode=instructor.Mode.JSON)

# We recommend llama3-70b-8192 or llama3-8b-8192 for fast, accurate JSON extraction
MODEL_NAME = "llama3-70b-8192"

def extract_answers_from_transcript(transcript_json: str, expert_name: str) -> TranscriptAnalysis:
    """
    Takes a single parsed transcript and extracts the answers to the 6 guide questions.
    """
    
    interview_guide = """
    1. How would you describe current adoption of robotic surgery in your market?
    2. What are the main barriers to adoption?
    3. How important are hospital budgets and ROI in purchasing decisions?
    4. How important are surgeon training and clinical outcomes?
    5. What adoption trend do you expect over the next 3–5 years?
    6. What is the typical hospital decision-making timeline for purchasing a new robotic system?
    """

    prompt = f"""
    You are an expert qualitative researcher analyzing an interview transcript with {expert_name}.
    Your task is to answer the 6 interview guide questions based ONLY on the provided transcript.
    
    CRITICAL INSTRUCTIONS:
    - You must extract an exact, verbatim quote to support your answer.
    - You must include the exact timestamp associated with that quote.
    - If a question is NOT answered or discussed in the transcript, set summary_answer to 'Not discussed' and set exact_quote and timestamp to null. Do not invent an answer.
    
    Interview Guide:
    {interview_guide}
    
    Transcript Data:
    {transcript_json}
    """

    # Instructor automatically handles parsing the LLM response into our Pydantic model
    analysis = instructor_client.chat.completions.create(
        model=MODEL_NAME,
        response_model=TranscriptAnalysis,
        messages=[
            {"role": "system", "content": "You are a precise data extraction assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0 # Keep temperature at 0 for deterministic factual extraction
    )
    
    return analysis

def synthesize_transcripts(all_analyses: list[dict]) -> CrossTranscriptSynthesis:
    """
    Takes the structured answers from all 3 experts and finds common themes and disagreements.
    """
    prompt = f"""
    You are a lead market analyst. Review the extracted answers from 3 experts regarding robotic surgery adoption.
    Identify the common themes they agree on, and the key areas where they disagree or have different market realities.
    
    Extracted Data:
    {all_analyses}
    """

    synthesis = instructor_client.chat.completions.create(
        model=MODEL_NAME,
        response_model=CrossTranscriptSynthesis,
        messages=[
            {"role": "system", "content": "You are an analytical assistant synthesizing cross-document themes."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )
    
    return synthesis