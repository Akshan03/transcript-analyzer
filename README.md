# AI Transcript Analyzer 

A proof-of-concept AI application that ingests expert-call transcripts, extracts structured answers, and synthesizes cross-document themes with verified source timestamps.

## Architecture Highlights
- **Deterministic Pre-processing:** Raw transcripts are uploaded and passed through a parser and segmentation layer. This structures the text into JSON dialogues before interacting with the LLM to prevent hallucinated timestamps.
- **Structured Extraction:** The pipeline uses `instructor` and Pydantic models to force the LLM to return strictly typed JSON arrays for the interview guide questions. 
- **Programmatic Verification Layer:** Extracted quotes pass through a dedicated verification layer for quote validation. The system cross-checks quotes against the raw transcript text using fuzzy string matching. Verified quotes receive a green badge; unverified paraphrases are flagged.

## Running Locally
**Prerequisites:** Python 3.9+, Git

1. Clone the repository and navigate into the folder.
2. Create and activate a virtual environment:
   `python -m venv venv`
   `.\venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux)
3. Install dependencies:
   `pip install -r requirements.txt`
4. Configure API Keys:
   Create a `.env` file in the root directory and add `GROQ_API_KEY=your_key_here`.
5. Run the Backend API:
   `uvicorn backend.main:app --reload`
6. Run the Frontend UI (in a new terminal):
   `streamlit run frontend/app.py`

## Scaling Strategy (3 to 30+ Transcripts)
To scale beyond the 3-transcript MVP, the architecture transitions to a two-tier hybrid system:
1. **Map-Reduce Synthesis:** Process extractions asynchronously over individual interviews in parallel utilizing the map-reduce synthesis branch for themes and disagreements.
2. **Context Indexing:** Implement context indexing using a RAG vector database. This allows the chat interface to chunk and retrieve relevant dialogue blocks dynamically across 30+ files while preserving exact speaker attribution.