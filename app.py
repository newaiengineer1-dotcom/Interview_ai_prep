import io
import json
import os
import re
import tempfile
from datetime import datetime

import streamlit as st
from groq import Groq
from pypdf import PdfReader
from docx import Document
from fpdf import FPDF


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="InterviewForge AI",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(
                circle at 10% 10%,
                rgba(80, 70, 180, 0.18),
                transparent 30%
            ),
            radial-gradient(
                circle at 90% 20%,
                rgba(0, 180, 200, 0.12),
                transparent 30%
            ),
            #080b14;
    }

    .hero {
        padding: 30px;
        border-radius: 22px;
        background: linear-gradient(
            135deg,
            rgba(32, 38, 70, 0.96),
            rgba(13, 18, 34, 0.96)
        );
        border: 1px solid rgba(255, 255, 255, 0.10);
        margin-bottom: 20px;
    }

    .card {
        padding: 18px;
        border-radius: 16px;
        background: rgba(20, 25, 42, 0.82);
        border: 1px solid rgba(255, 255, 255, 0.09);
        margin: 10px 0;
    }

    .muted {
        color: #aab4c5;
    }

    .score {
        font-size: 42px;
        font-weight: 800;
    }

    div[data-testid="stMetric"] {
        background: rgba(20, 25, 42, 0.8);
        padding: 12px;
        border-radius: 14px;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="hero">
        <h1>🎯 InterviewForge AI</h1>
        <p class="muted">
            AI-powered interview preparation grounded in your CV,
            job description and target role.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# CONSTANTS
# ============================================================

DEFAULT_MODEL = "openai/gpt-oss-120b"
FALLBACK_MODEL = "openai/gpt-oss-20b"
STT_MODEL = "whisper-large-v3-turbo"

INTERVIEW_KEYWORDS = [
    "experience",
    "employment",
    "work history",
    "professional experience",
    "skills",
    "technical skills",
    "core skills",
    "competencies",
    "project",
    "projects",
    "achievement",
    "achievements",
    "education",
    "degree",
    "certification",
    "certifications",
    "responsibilities",
    "requirements",
    "qualifications",
    "preferred",
    "required",
    "duties",
    "technology",
    "technologies",
    "tools",
    "software",
    "leadership",
    "management",
    "role",
    "summary",
    "profile",
    "objective",
    "industry",
]


# ============================================================
# FILE EXTRACTION
# ============================================================

def extract_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF."""

    reader = PdfReader(io.BytesIO(file_bytes))

    pages = []

    for page in reader.pages:
        text = page.extract_text()

        if text:
            pages.append(text)

    return "\n".join(pages).strip()


def extract_docx(file_bytes: bytes) -> str:
    """Extract text from a DOCX file."""

    document = Document(io.BytesIO(file_bytes))

    paragraphs = []

    for paragraph in document.paragraphs:
        if paragraph.text.strip():
            paragraphs.append(paragraph.text)

    return "\n".join(paragraphs).strip()


def extract_uploaded_file(uploaded_file) -> str:
    """Extract text from supported uploaded documents."""

    if uploaded_file is None:
        return ""

    file_bytes = uploaded_file.getvalue()
    filename = uploaded_file.name.lower()

    if filename.endswith(".pdf"):
        return extract_pdf(file_bytes)

    if filename.endswith(".docx"):
        return extract_docx(file_bytes)

    if filename.endswith(".txt"):
        return file_bytes.decode(
            "utf-8",
            errors="ignore",
        ).strip()

    raise ValueError(
        "Unsupported file type. Please upload PDF, DOCX or TXT."
    )


# ============================================================
# TEXT CLEANING
# ============================================================

def normalize_text(text: str) -> str:
    """Normalize document text."""

    if not text:
        return ""

    text = text.replace("\x00", " ")

    text = re.sub(
        r"[ \t]+",
        " ",
        text,
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    return text.strip()


def compact_document(
    text: str,
    max_chars: int = 6000,
) -> str:
    """
    Reduce document size before sending it to Groq.

    This protects the application from large-token requests.
    """

    text = normalize_text(text)

    if not text:
        return ""

    if len(text) <= max_chars:
        return text

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    if not lines:
        return text[:max_chars]

    head_size = int(max_chars * 0.45)
    tail_size = int(max_chars * 0.12)

    head = text[:head_size]
    tail = text[-tail_size:]

    remaining = max_chars - len(head) - len(tail) - 100

    scored_lines = []

    for index, line in enumerate(lines):

        lower = line.lower()

        score = 0

        for keyword in INTERVIEW_KEYWORDS:

            if keyword in lower:
                score += 2

        if index < 25:
            score += 2

        if len(line) < 120:
            score += 1

        scored_lines.append(
            (
                score,
                index,
                line,
            )
        )

    scored_lines.sort(
        key=lambda item: (
            -item[0],
            item[1],
        )
    )

    selected = []

    for _, _, line in scored_lines:

        if remaining <= 0:
            break

        addition = line + "\n"

        if len(addition) <= remaining:

            selected.append(addition)

            remaining -= len(addition)

    result = (
        head
        + "\n\n[Relevant Evidence]\n"
        + "".join(selected)
        + "\n[End Relevant Evidence]\n\n"
        + tail
    )

    return result[:max_chars]


# ============================================================
# GROQ ERROR HANDLING
# ============================================================

def is_large_request_error(error: Exception) -> bool:
    """Detect Groq 413 / TPM errors."""

    message = str(error).lower()

    return (
        "413" in message
        or "request too large" in message
        or "tpm limit" in message
        or "tokens per minute" in message
        or "request too large for model" in message
    )


def groq_json_call(
    client: Groq,
    model: str,
    system_prompt: str,
    user_prompt: str,
):
    """
    Send JSON request to Groq.

    Automatically falls back to GPT-OSS 20B if
    the primary model rejects the request because
    of request size.
    """

    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": user_prompt,
        },
    ]

    try:

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.15,
            response_format={
                "type": "json_object"
            },
        )

        content = response.choices[0].message.content

        return json.loads(content)

    except Exception as first_error:

        if not is_large_request_error(first_error):
            raise

        if model == FALLBACK_MODEL:
            raise

        fallback_messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": compact_document(
                    user_prompt,
                    8000,
                ),
            },
        ]

        response = client.chat.completions.create(
            model=FALLBACK_MODEL,
            messages=fallback_messages,
            temperature=0.15,
            response_format={
                "type": "json_object"
            },
        )

        content = response.choices[0].message.content

        return json.loads(content)


# ============================================================
# AI SYSTEM PROMPT
# ============================================================

GROUNDING_SYSTEM = """
You are a strict professional AI interview coach.

Use ONLY information explicitly supported by:
1. Candidate CV
2. Job description
3. Target role
4. Interview conversation

Never invent:

- employers
- job titles
- projects
- project values
- project capacities
- responsibilities
- achievements
- certifications
- technologies
- dates
- metrics
- qualifications

If information is unavailable, write UNKNOWN or NOT PROVIDED.

Never transform assumptions into facts.

Interview questions must be:

- realistic
- concise
- human
- practical
- relevant to the target role
- grounded in the provided evidence

Return valid JSON only.
"""


# ============================================================
# PROFILE GENERATION
# ============================================================

def generate_profile(
    client: Groq,
    model: str,
    role: str,
    cv: str,
    jd: str,
):
    """
    Generate a compact verified candidate profile.

    Only compact CV/JD context is sent to Groq.
    """

    cv_context = compact_document(
        cv,
        6000,
    )

    jd_context = compact_document(
        jd,
        6000,
    )

    prompt = f"""
TARGET ROLE:
{role}

CANDIDATE CV:
{cv_context}

JOB DESCRIPTION:
{jd_context}

Create a compact evidence-grounded interview profile.

Return exactly this JSON structure:

{{
    "candidate_summary": "...",
    "verified_skills": [],
    "verified_experience": [],
    "verified_projects": [],
    "education_certifications": [],
    "jd_requirements": [],
    "matching_areas": [],
    "gaps_or_unknowns": []
}}
"""

    return groq_json_call(
        client,
        model,
        GROUNDING_SYSTEM,
        prompt,
    )


# ============================================================
# QUESTION GENERATION
# ============================================================

def generate_question(
    client: Groq,
    model: str,
    role: str,
    profile: dict,
    cv: str,
    jd: str,
    history: list,
):
    """Generate the next interview question."""

    cv_context = compact_document(
        cv,
        2500,
    )

    jd_context = compact_document(
        jd,
        2500,
    )

    recent_history = history[-4:]

    history_json = json.dumps(
        recent_history,
        ensure_ascii=False,
    )

    profile_json = json.dumps(
        profile,
        ensure_ascii=False,
    )

    prompt = f"""
TARGET ROLE:
{role}

VERIFIED CANDIDATE PROFILE:
{profile_json}

CV EVIDENCE:
{cv_context}

JOB DESCRIPTION EVIDENCE:
{jd_context}

RECENT INTERVIEW HISTORY:
{history_json}

Generate the next interview question.

Rules:

- Ask exactly one main question.
- Keep it concise.
- Make it sound like a real human interviewer.
- Prioritize the job description.
- Use verified CV information.
- Adapt to previous answers.
- Do not invent candidate facts.
- Avoid repeating previous questions.

Return:

{{
    "question": "...",
    "category": "Technical|Behavioral|Experience|Role Fit|Situational",
    "why": "brief reason"
}}
"""

    return groq_json_call(
        client,
        model,
        GROUNDING_SYSTEM,
        prompt,
    )


# ============================================================
# ANSWER ANALYSIS
# ============================================================

def analyze_answer(
    client: Groq,
    model: str,
    role: str,
    profile: dict,
    cv: str,
    jd: str,
    question: str,
    answer: str,
):
    """Evaluate candidate answer."""

    cv_context = compact_document(
        cv,
        2500,
    )

    jd_context = compact_document(
        jd,
        2500,
    )

    profile_json = json.dumps(
        profile,
        ensure_ascii=False,
    )

    prompt = f"""
TARGET ROLE:
{role}

VERIFIED PROFILE:
{profile_json}

CV EVIDENCE:
{cv_context}

JOB DESCRIPTION:
{jd_context}

INTERVIEW QUESTION:
{question}

CANDIDATE ANSWER:
{answer}

Evaluate the candidate answer strictly against
the available evidence.

Return:

{{
    "overall_score": 0,
    "relevance": 0,
    "completeness": 0,
    "communication": 0,
    "evidence_grounding": 0,
    "strengths": [],
    "missing_points": [],
    "unsupported_claims": [],
    "improved_answer": "...",
    "verdict": "Strong|Good|Needs Improvement|Weak",
    "follow_up_focus": "..."
}}

All scores must be integers between 0 and 100.

The improved answer MUST NOT introduce facts
that are absent from the CV, JD or answer.
"""

    return groq_json_call(
        client,
        model,
        GROUNDING_SYSTEM,
        prompt,
    )


# ============================================================
# PDF REPORT
# ============================================================

def pdf_safe(value) -> str:
    """Make text safe for the default FPDF font."""

    return (
        str(value)
        .encode(
            "latin-1",
            errors="replace",
        )
        .decode("latin-1")
    )


def create_pdf_report(
    role: str,
    profile: dict,
    history: list,
) -> bytes:

    pdf = FPDF()

    pdf.set_auto_page_break(
        auto=True,
        margin=15,
    )

    pdf.add_page()

    pdf.set_font(
        "Helvetica",
        "B",
        18,
    )

    pdf.cell(
        0,
        10,
        pdf_safe(
            "InterviewForge AI - Interview Report"
        ),
        ln=True,
    )

    pdf.set_font(
        "Helvetica",
        size=10,
    )

    pdf.cell(
        0,
        7,
        pdf_safe(
            f"Target Role: {role}"
        ),
        ln=True,
    )

    pdf.cell(
        0,
        7,
        pdf_safe(
            f"Generated: {datetime.now():%Y-%m-%d %H:%M}"
        ),
        ln=True,
    )

    pdf.ln(5)

    pdf.set_font(
        "Helvetica",
        "B",
        13,
    )

    pdf.cell(
        0,
        8,
        "Candidate Profile",
        ln=True,
    )

    pdf.set_font(
        "Helvetica",
        size=10,
    )

    pdf.multi_cell(
        0,
        6,
        pdf_safe(
            profile.get(
                "candidate_summary",
                "Not provided",
            )
        ),
    )

    sections = [
        (
            "Verified Skills",
            "verified_skills",
        ),
        (
            "Verified Experience",
            "verified_experience",
        ),
        (
            "Verified Projects",
            "verified_projects",
        ),
        (
            "Education / Certifications",
            "education_certifications",
        ),
        (
            "JD Requirements",
            "jd_requirements",
        ),
        (
            "Matching Areas",
            "matching_areas",
        ),
        (
            "Gaps / Unknowns",
            "gaps_or_unknowns",
        ),
    ]

    for title, key in sections:

        pdf.ln(2)

        pdf.set_font(
            "Helvetica",
            "B",
            11,
        )

        pdf.cell(
            0,
            7,
            pdf_safe(title),
            ln=True,
        )

        pdf.set_font(
            "Helvetica",
            size=10,
        )

        values = profile.get(
            key,
            [],
        )

        if not values:
            values = [
                "Not provided"
            ]

        for value in values:

            pdf.multi_cell(
                0,
                6,
                pdf_safe(
                    f"- {value}"
                ),
            )

    if history:

        pdf.add_page()

        pdf.set_font(
            "Helvetica",
            "B",
            14,
        )

        pdf.cell(
            0,
            8,
            "Interview Performance",
            ln=True,
        )

        for index, item in enumerate(
            history,
            start=1,
        ):

            question = item.get(
                "question",
                "",
            )

            answer = item.get(
                "answer",
                "",
            )

            analysis = item.get(
                "analysis",
                {},
            )

            pdf.ln(4)

            pdf.set_font(
                "Helvetica",
                "B",
                11,
            )

            pdf.multi_cell(
                0,
                6,
                pdf_safe(
                    f"{index}. {question}"
                ),
            )

            pdf.set_font(
                "Helvetica",
                size=10,
            )

            pdf.multi_cell(
                0,
                6,
                pdf_safe(
                    f"Answer: {answer}"
                ),
            )

            pdf.multi_cell(
                0,
                6,
                pdf_safe(
                    "Score: "
                    + str(
                        analysis.get(
                            "overall_score",
                            "N/A",
                        )
                    )
                    + " | Verdict: "
                    + str(
                        analysis.get(
                            "verdict",
                            "N/A",
                        )
                    )
                ),
            )

            strengths = analysis.get(
                "strengths",
                [],
            )

            if strengths:

                pdf.multi_cell(
                    0,
                    6,
                    pdf_safe(
                        "Strengths: "
                        + "; ".join(
                            map(str, strengths)
                        )
                    ),
                )

            missing = analysis.get(
                "missing_points",
                [],
            )

            if missing:

                pdf.multi_cell(
                    0,
                    6,
                    pdf_safe(
                        "Missing: "
                        + "; ".join(
                            map(str, missing)
                        )
                    ),
                )

    return bytes(
        pdf.output()
    )


# ============================================================
# SESSION STATE
# ============================================================

DEFAULT_STATE = {
    "profile": None,
    "history": [],
    "current_question": None,
    "pending_answer": "",
    "cv_text": "",
    "jd_text": "",
    "role": "",
    "company": "",
    "model": DEFAULT_MODEL,
    "difficulty": "Intermediate",
    "interview_mode": "Mixed",
}


for key, value in DEFAULT_STATE.items():

    if key not in st.session_state:

        st.session_state[key] = value


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("⚙️ Interview Setup")

    api_key = st.text_input(
        "Groq API Key",
        type="password",
        help="Your API key is used for the current application session.",
    )

    model = st.selectbox(
        "AI Model",
        [
            DEFAULT_MODEL,
            FALLBACK_MODEL,
        ],
    )

    role = st.text_input(
        "Target Role",
        placeholder="Example: Solar + BESS Project Engineer",
    )

    company = st.text_input(
        "Company",
        placeholder="Optional",
    )

    difficulty = st.selectbox(
        "Difficulty",
        [
            "Beginner",
            "Intermediate",
            "Expert",
        ],
        index=1,
    )

    interview_mode = st.selectbox(
        "Interview Mode",
        [
            "Mixed",
            "Technical",
            "Behavioral",
            "Role Fit",
        ],
    )

    cv_file = st.file_uploader(
        "CV / Resume",
        type=[
            "pdf",
            "docx",
            "txt",
        ],
    )

    jd_file = st.file_uploader(
        "Job Description",
        type=[
            "pdf",
            "docx",
            "txt",
        ],
    )

    start_button = st.button(
        "🚀 Start Interview",
        use_container_width=True,
    )


# ============================================================
# START INTERVIEW
# ============================================================

if start_button:

    if not api_key.strip():

        st.error(
            "Please enter your Groq API key."
        )

        st.stop()

    if not role.strip():

        st.error(
            "Please enter the target role."
        )

        st.stop()

    if cv_file is None:

        st.error(
            "Please upload your CV / Resume."
        )

        st.stop()

    if jd_file is None:

        st.error(
            "Please upload the Job Description."
        )

        st.stop()

    try:

        with st.spinner(
            "Reading documents and creating verified profile..."
        ):

            cv_text = extract_uploaded_file(
                cv_file
            )

            jd_text = extract_uploaded_file(
                jd_file
            )

            if not cv_text:

                raise ValueError(
                    "The CV contains no extractable text."
                )

            if not jd_text:

                raise ValueError(
                    "The Job Description contains no extractable text."
                )

            client = Groq(
                api_key=api_key.strip()
            )

            profile = generate_profile(
                client=client,
                model=model,
                role=role.strip(),
                cv=cv_text,
                jd=jd_text,
            )

            st.session_state.profile = profile
            st.session_state.history = []
            st.session_state.current_question = None
            st.session_state.pending_answer = ""

            st.session_state.cv_text = cv_text
            st.session_state.jd_text = jd_text
            st.session_state.role = role.strip()
            st.session_state.company = company.strip()
            st.session_state.model = model
            st.session_state.difficulty = difficulty
            st.session_state.interview_mode = interview_mode

        st.success(
            "Interview initialized successfully."
        )

    except Exception as error:

        if is_large_request_error(error):

            st.error(
                "Groq rejected the request because it was too large. "
                "The application uses compact CV/JD context and a fallback model. "
                "Please retry."
            )

        else:

            st.error(
                f"Could not initialize interview: {error}"
            )


# ============================================================
# INTERVIEW DASHBOARD
# ============================================================

if st.session_state.profile:

    profile = st.session_state.profile

    role = st.session_state.role

    model = st.session_state.model

    client = None

    if api_key.strip():

        client = Groq(
            api_key=api_key.strip()
        )

    st.subheader(
        "📋 Verified Candidate Profile"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Target Role",
            role,
        )

    with col2:

        st.metric(
            "AI Model",
            model,
        )

    with col3:

        st.metric(
            "Questions Completed",
            len(
                st.session_state.history
            ),
        )

    with st.expander(
        "View grounding profile"
    ):

        st.json(
            profile
        )

    st.divider()

    # --------------------------------------------------------
    # Generate Question
    # --------------------------------------------------------

    if st.button(
        "🧠 Generate Interview Question",
        use_container_width=True,
    ):

        if client is None:

            st.warning(
                "Please enter your Groq API key."
            )

        else:

            try:

                with st.spinner(
                    "Generating interview question..."
                ):

                    question_data = generate_question(
                        client=client,
                        model=model,
                        role=role,
                        profile=profile,
                        cv=st.session_state.cv_text,
                        jd=st.session_state.jd_text,
                        history=st.session_state.history,
                    )

                    st.session_state.current_question = (
                        question_data
                    )

                    st.session_state.pending_answer = ""

            except Exception as error:

                st.error(
                    f"Could not generate question: {error}"
                )

    # --------------------------------------------------------
    # Current Question
    # --------------------------------------------------------

    if st.session_state.current_question:

        question_data = (
            st.session_state.current_question
        )

        question_text = question_data.get(
            "question",
            "",
        )

        category = question_data.get(
            "category",
            "Interview",
        )

        st.markdown(
            "### 🎤 Interviewer"
        )

        st.markdown(
            f"""
            <div class="card">
                <h3>{question_text}</h3>
                <p class="muted">
                    Category: {category}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ----------------------------------------------------
        # Text Answer
        # ----------------------------------------------------

        text_answer = st.text_area(
            "Type your answer",
            value=st.session_state.pending_answer,
            height=180,
            placeholder=(
                "Write your interview answer here..."
            ),
        )

        # ----------------------------------------------------
        # Voice Answer
        # ----------------------------------------------------

        st.markdown(
            "### 🎙️ Voice Answer"
        )

        audio_input = st.audio_input(
            "Record your answer"
        )

        if audio_input is not None:

            if st.button(
                "Convert Voice to Text"
            ):

                if client is None:

                    st.warning(
                        "Please enter your Groq API key."
                    )

                else:

                    temporary_path = None

                    try:

                        with tempfile.NamedTemporaryFile(
                            delete=False,
                            suffix=".wav",
                        ) as temporary_file:

                            temporary_file.write(
                                audio_input.getvalue()
                            )

                            temporary_path = (
                                temporary_file.name
                            )

                        with st.spinner(
                            "Transcribing your answer..."
                        ):

                            with open(
                                temporary_path,
                                "rb",
                            ) as audio_file:

                                transcription = (
                                    client.audio.transcriptions.create(
                                        file=(
                                            os.path.basename(
                                                temporary_path
                                            ),
                                            audio_file.read(),
                                        ),
                                        model=STT_MODEL,
                                    )
                                )

                        st.session_state.pending_answer = (
                            transcription.text
                        )

                        st.rerun()

                    except Exception as error:

                        st.error(
                            f"Voice transcription failed: {error}"
                        )

                    finally:

                        if (
                            temporary_path
                            and os.path.exists(
                                temporary_path
                            )
                        ):

                            os.remove(
                                temporary_path
                            )

        # ----------------------------------------------------
        # Analyze Answer
        # ----------------------------------------------------

        final_answer = (
            text_answer.strip()
            or
            st.session_state.pending_answer.strip()
        )

        if st.button(
            "📊 Analyze Answer",
            use_container_width=True,
        ):

            if not final_answer:

                st.warning(
                    "Please provide an answer first."
                )

            elif client is None:

                st.warning(
                    "Please enter your Groq API key."
                )

            else:

                try:

                    with st.spinner(
                        "Analyzing your answer..."
                    ):

                        analysis = analyze_answer(
                            client=client,
                            model=model,
                            role=role,
                            profile=profile,
                            cv=st.session_state.cv_text,
                            jd=st.session_state.jd_text,
                            question=question_text,
                            answer=final_answer,
                        )

                    st.session_state.history.append(
                        {
                            "question": question_text,
                            "answer": final_answer,
                            "analysis": analysis,
                        }
                    )

                    st.session_state.pending_answer = ""

                    st.markdown(
                        "### 📊 Answer Evaluation"
                    )

                    score = int(
                        analysis.get(
                            "overall_score",
                            0,
                        )
                    )

                    col1, col2, col3, col4 = st.columns(4)

                    with col1:

                        st.metric(
                            "Overall",
                            score,
                        )

                    with col2:

                        st.metric(
                            "Relevance",
                            analysis.get(
                                "relevance",
                                0,
                            ),
                        )

                    with col3:

                        st.metric(
                            "Completeness",
                            analysis.get(
                                "completeness",
                                0,
                            ),
                        )

                    with col4:

                        st.metric(
                            "Grounding",
                            analysis.get(
                                "evidence_grounding",
                                0,
                            ),
                        )

                    verdict = analysis.get(
                        "verdict",
                        "Reviewed",
                    )

                    if verdict == "Strong":

                        st.success(
                            f"Verdict: {verdict}"
                        )

                    elif verdict == "Good":

                        st.info(
                            f"Verdict: {verdict}"
                        )

                    elif verdict == "Needs Improvement":

                        st.warning(
                            f"Verdict: {verdict}"
                        )

                    else:

                        st.error(
                            f"Verdict: {verdict}"
                        )

                    left, right = st.columns(2)

                    with left:

                        st.markdown(
                            "#### Strengths"
                        )

                        strengths = analysis.get(
                            "strengths",
                            [],
                        )

                        if strengths:

                            for item in strengths:

                                st.write(
                                    f"• {item}"
                                )

                        else:

                            st.write(
                                "No specific strengths identified."
                            )

                        st.markdown(
                            "#### Missing Points"
                        )

                        missing = analysis.get(
                            "missing_points",
                            [],
                        )

                        if missing:

                            for item in missing:

                                st.write(
                                    f"• {item}"
                                )

                        else:

                            st.write(
                                "No major missing points identified."
                            )

                    with right:

                        st.markdown(
                            "#### Unsupported Claims"
                        )

                        unsupported = (
                            analysis.get(
                                "unsupported_claims",
                                [],
                            )
                        )

                        if unsupported:

                            for item in unsupported:

                                st.write(
                                    f"• {item}"
                                )

                        else:

                            st.write(
                                "None identified."
                            )

                        st.markdown(
                            "#### Improved Answer"
                        )

                        st.info(
                            analysis.get(
                                "improved_answer",
                                "",
                            )
                        )

                        st.markdown(
                            "#### Follow-up Focus"
                        )

                        st.write(
                            analysis.get(
                                "follow_up_focus",
                                "",
                            )
                        )

                except Exception as error:

                    if is_large_request_error(error):

                        st.error(
                            "Groq rejected the analysis request "
                            "as too large. The application has "
                            "already minimized the context. "
                            "Please retry."
                        )

                    else:

                        st.error(
                            f"Could not analyze answer: {error}"
                        )


# ============================================================
# INTERVIEW HISTORY
# ============================================================

if st.session_state.history:

    st.divider()

    st.subheader(
        "📝 Interview History"
    )

    for index, item in enumerate(
        st.session_state.history,
        start=1,
    ):

        question = item.get(
            "question",
            "",
        )

        answer = item.get(
            "answer",
            "",
        )

        analysis = item.get(
            "analysis",
            {},
        )

        score = analysis.get(
            "overall_score",
            "N/A",
        )

        with st.expander(
            f"Question {index}: {question[:100]}"
        ):

            st.markdown(
                "**Question**"
            )

            st.write(
                question
            )

            st.markdown(
                "**Answer**"
            )

            st.write(
                answer
            )

            st.markdown(
                f"**Score:** {score}"
            )

            st.markdown(
                f"**Verdict:** "
                f"{analysis.get('verdict', 'N/A')}"
            )

    # --------------------------------------------------------
    # PDF Report
    # --------------------------------------------------------

    try:

        pdf_report = create_pdf_report(
            role=st.session_state.role,
            profile=st.session_state.profile,
            history=st.session_state.history,
        )

        st.download_button(
            label="📥 Download Interview Report PDF",
            data=pdf_report,
            file_name="InterviewForge_AI_Report.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    except Exception as error:

        st.error(
            f"Could not create PDF report: {error}"
        )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="muted" style="text-align:center; margin-top:35px;">
        InterviewForge AI • Evidence-grounded interview coaching
    </div>
    """,
    unsafe_allow_html=True,
)
