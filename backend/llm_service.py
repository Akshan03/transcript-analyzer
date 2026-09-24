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
MODEL_NAME = "openai/gpt-oss-120b"

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
    
    CRITICAL INSTRUCTIONS (FAILURE IS NOT AN OPTION):
    1. You must extract an exact, verbatim quote to support your answer.
    2. You must include the exact timestamp associated with that quote.
    3. NO HALLUCINATIONS: If the transcript ends before a question is asked, or the topic is genuinely missing, you MUST set summary_answer to 'Not discussed'. 
    4. Do NOT invent timestamps. Do NOT invent answers.
    
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

def chat_with_transcripts(user_query: str, all_transcripts_json: str) -> str:
    """Handles global Q&A across all transcripts."""
    system_prompt = f"""
    You are an expert analyst answering questions based ONLY on the provided interview transcripts.
    Whenever you make a claim, you MUST append a citation in the format [Expert Name - Timestamp].
    If the answer is not in the transcripts, say "I cannot find this in the transcripts."
    
    Transcripts:
    {all_transcripts_json}
    """
    
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ],
        temperature=0.3
    )
    return response.choices[0].message.content