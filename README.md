# JOBLANDER AI — Complete Interview Copilot

A Streamlit interview-practice application that accepts a CV/Resume and Job Description and provides adaptive, evidence-grounded interview questions, voice transcription, typed answers, answer scoring, anti-hallucination checks, and a downloadable PDF report.

## Features

- CV/Resume upload: PDF, DOCX, TXT
- Job Description upload: PDF, DOCX, TXT
- Manual Groq API key input
- Configurable Groq LLM model
- Groq Whisper voice transcription
- Text answer mode
- Evidence-grounded interview profile
- Adaptive one-question-at-a-time interview flow
- Technical, behavioral, hiring-manager, resume-verification and stress modes
- Concise humanized questions
- Concise first-person answer improvements
- Unsupported-claim detection
- JD/CV match score
- Downloadable PDF interview report
- Modern Streamlit dashboard

## Important real-time note

This MVP uses Streamlit's microphone recorder and sends each recorded answer to speech-to-text. It is near-real-time, turn-based interview practice, not a continuous WebRTC live conversation. For a production continuous conversation, use a browser/WebRTC frontend and a streaming speech architecture.

## Run locally

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install:

```bash
pip install -r requirements.txt
```

Run:

```bash
streamlit run app.py
```

Open the local URL shown by Streamlit.

## Groq key

For local testing, paste your Groq key into the sidebar.

For Streamlit deployment, prefer:

```toml
# .streamlit/secrets.toml
GROQ_API_KEY = "your_key_here"
```

Then modify the application to read `st.secrets["GROQ_API_KEY"]` if you want the key hidden from the UI.

Never commit a real API key to GitHub.

## GitHub web UI deployment

1. Create a new GitHub repository.
2. Upload `app.py`, `requirements.txt`, and `README.md`.
3. Commit the files.
4. Open Streamlit Community Cloud.
5. Create a new app.
6. Select the GitHub repository and `app.py`.
7. Deploy.
8. Add `GROQ_API_KEY` under the app's Secrets if using secrets.
9. Restart/redeploy.

## Grounding policy

The application instructs the model not to invent:
- employers
- projects
- responsibilities
- certifications
- technologies
- project capacities
- achievements
- years of experience

Unknown information is treated as unknown. Unsupported claims in candidate answers are flagged.

## Web research

The UI includes a Web Research toggle as an architectural placeholder. The included MVP does not silently scrape the web. Before enabling automated research, add a permitted search provider/API and store source URL/title/date with every external fact. This keeps the evidence chain auditable.

## Recommended production improvements

- Browser WebRTC/streaming voice pipeline
- Persistent interview sessions
- Vector retrieval for very large CV/JD document sets
- Official-company-source research connector
- Source citations per question
- Authentication and encrypted storage
- Evaluation test suite
- Rate limiting
- Redaction of sensitive candidate data
- Separate frontend/backend for scalable real-time audio
