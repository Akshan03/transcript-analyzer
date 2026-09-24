import streamlit as st
import requests

# Set page layout to wide to fit the 3-column matrix
st.set_page_config(page_title="Transcript Analyzer", layout="wide")

API_BASE = "http://127.0.0.1:8000/api"

# --- Data Fetching (Cached for speed during demo) ---

@st.cache_data
def fetch_analysis():
    with st.spinner("Analyzing transcripts via Groq..."):
        try:
            response = requests.post(f"{API_BASE}/analyze", timeout=60)
            if response.status_code == 200:
                return response.json()
            else:
                # This will show you the exact error (e.g., 404, 429 rate limit, or 400)
                st.error(f"API Error {response.status_code}: {response.text}")
                return []
        except Exception as e:
            st.error(f"Connection failed: {e}")
            return []

@st.cache_data
def fetch_synthesis(analyses):
    with st.spinner("Synthesizing cross-document themes..."):
        response = requests.post(f"{API_BASE}/synthesize", json=analyses)
        if response.status_code == 200:
            return response.json()
        st.error("Failed to fetch synthesis.")
        return None

# --- Main UI ---

st.title("Hasamex: Robotic Surgery Market Analysis")

# Fetch data once
analyses = fetch_analysis()
synthesis = None
if analyses:
    synthesis = fetch_synthesis(analyses)

# Create the 3 Tabs
tab1, tab2, tab3 = st.tabs(["📊 The Matrix", "🧠 Synthesis", "💬 Ask the Transcripts"])

# ==========================================
# TAB 1: THE MATRIX (Per-Transcript Answers)
# ==========================================
with tab1:
    st.markdown("### Interview Guide Answers by Expert")
    
    if analyses:
        questions = [
            "1. How would you describe current adoption of robotic surgery in your market? ",
            "2. What are the main barriers to adoption?",
            "3. How important are hospital budgets and ROI in purchasin decisions?",
            "4. How important are surgeon training and clinical outcomes?",
            "5. What adoption trend do you expect over the next 3-5 years?",
            "6. What is the typical hospital decision-making timeline for purchasing a new robotic system?"
        ]
        # We know there are 6 questions
        for q_id in range(1, 7):
            st.markdown(f"**{questions[q_id-1]}**") # Prints the actual question text
            cols = st.columns(3)
            
            for i, expert_data in enumerate(analyses):
                expert_name = expert_data["expert_name"]
                market = expert_data["market"]
                # Find the answer for the current question
                answer = next((a for a in expert_data["answers"] if a["question_id"] == q_id), None)
                
                with cols[i]:
                    st.markdown(f"*{expert_name} ({market})*")
                    if answer:
                        st.info(answer["summary_answer"])
                        
                        # Only show the expander if a quote exists (Handling "Not Discussed")
                        if answer["exact_quote"] and answer["timestamp"]:
                            with st.expander(f"⏱️ {answer['timestamp']} - View Quote"):
                                st.write(f"\"{answer['exact_quote']}\"")
                                if answer.get("is_verified", False):
                                    st.caption("✅ Verified verbatim match from transcript")
                                else:
                                    st.caption("⚠️ Paraphrase / Unverified quote")
            st.divider()

# ==========================================
# TAB 2: SYNTHESIS (Themes & Disagreements)
# ==========================================
with tab2:
    if synthesis:
        st.markdown("### Cross-Transcript Synthesis")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🟢 Common Themes")
            for theme in synthesis["common_themes"]:
                st.markdown(f"**{theme['theme_title']}**")
                st.write(theme["description"])
                st.caption(f"Supported by: {', '.join(theme['supported_by'])}")
                st.markdown("---")
                
        with col2:
            st.subheader("🔴 Key Disagreements & Variances")
            for disagreement in synthesis["key_disagreements"]:
                st.markdown(f"**{disagreement['topic']}**")
                st.write(disagreement["description"])
                st.caption(f"Differing views: {', '.join(disagreement['differing_viewpoints'])}")
                st.markdown("---")

# ==========================================
# TAB 3: GLOBAL CHAT (Ask the Transcripts)
# ==========================================
with tab3:
    st.markdown("### Ask Questions Across All Transcripts")
    
    # Initialize chat history in Streamlit session state
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # React to user input
    if prompt := st.chat_input("E.g., Which market focuses least on pure ROI?"):
        # Display user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        # Call the backend chat endpoint
        with st.spinner("Searching transcripts..."):
            res = requests.post(f"{API_BASE}/chat", json={"query": prompt})
            if res.status_code == 200:
                answer_text = res.json().get("response", "Error getting response.")
            else:
                answer_text = "API Error. Is the backend running?"
                
        # Display assistant response
        st.session_state.messages.append({"role": "assistant", "content": answer_text})
        with st.chat_message("assistant"):
            st.write(answer_text)