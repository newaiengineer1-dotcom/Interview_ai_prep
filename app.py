from pathlib import Path
import zipfile
import textwrap

out = Path("/mnt/data/InterviewForge_AI_Dashboard_UI")
out.mkdir(parents=True, exist_ok=True)

app_py = r'''
import streamlit as st

st.set_page_config(
    page_title="InterviewForge AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -----------------------------
# Styling
# -----------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --bg: #020b20;
    --panel: rgba(8, 28, 59, 0.78);
    --panel2: rgba(7, 23, 50, 0.92);
    --border: rgba(62, 137, 222, 0.34);
    --blue: #169cff;
    --cyan: #18d8ff;
    --text: #f4f8ff;
    --muted: #9fb2d1;
    --green: #2ce79a;
    --yellow: #ffd12e;
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 50% -10%, rgba(18, 103, 255, 0.25), transparent 35%),
        radial-gradient(circle at 90% 40%, rgba(0, 190, 255, 0.08), transparent 30%),
        linear-gradient(180deg, #020a1d 0%, #03112c 52%, #020a1d 100%);
    color: var(--text);
}

.block-container {
    max-width: 1500px;
    padding: 28px 34px 34px;
}

#MainMenu, footer, header { visibility: hidden; }

.hero {
    text-align: center;
    padding: 0 0 24px;
}

.hero h1 {
    font-size: clamp(38px, 4vw, 62px);
    line-height: 1.05;
    margin: 0;
    font-weight: 800;
    letter-spacing: -2px;
    color: #f7f9ff;
}

.hero h1 span {
    background: linear-gradient(90deg, #ffffff 0%, #55aaff 55%, #27d7ff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero p {
    color: #a9bad5;
    font-size: 19px;
    margin: 10px 0 24px;
}

.steps {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 0;
    max-width: 1100px;
    margin: 0 auto;
}

.step {
    display: flex;
    align-items: center;
    min-width: 210px;
}

.step-icon {
    width: 62px;
    height: 62px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28px;
    border: 1px solid rgba(16, 163, 255, .85);
    background: radial-gradient(circle, rgba(13, 111, 255, .22), rgba(3, 26, 59, .5));
    box-shadow: 0 0 24px rgba(0, 150, 255, .18), inset 0 0 18px rgba(0, 153, 255, .12);
}

.step-text {
    margin-left: 14px;
    text-align: left;
}

.step-num {
    color: #ffffff;
    font-size: 14px;
    font-weight: 700;
}

.step-label {
    color: #f7faff;
    font-size: 16px;
    margin-top: 4px;
}

.arrow {
    flex: 1;
    height: 1px;
    margin: 0 18px;
    background: linear-gradient(90deg, rgba(0, 121, 255, .2), rgba(0, 148, 255, .9), rgba(0, 121, 255, .2));
    position: relative;
}

.arrow:after {
    content: "›";
    position: absolute;
    right: -2px;
    top: -12px;
    color: #0ca4ff;
    font-size: 24px;
}

.card {
    background: linear-gradient(145deg, rgba(9, 31, 66, .92), rgba(3, 17, 40, .96));
    border: 1px solid var(--border);
    border-radius: 17px;
    min-height: 530px;
    padding: 23px;
    box-shadow: 0 16px 45px rgba(0, 0, 0, .24), inset 0 0 30px rgba(11, 91, 175, .04);
}

.card-title {
    font-size: 21px;
    font-weight: 700;
    margin-bottom: 7px;
}

.card-subtitle {
    color: #a9bad5;
    line-height: 1.5;
    font-size: 14px;
    min-height: 43px;
}

.searchbox {
    margin: 19px 0 13px;
    height: 45px;
    border: 1px solid rgba(95, 142, 202, .35);
    background: rgba(2, 15, 36, .55);
    border-radius: 9px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 14px;
    color: #7890b4;
    font-size: 13px;
}

.role {
    height: 50px;
    border: 1px solid rgba(83, 127, 184, .28);
    border-radius: 9px;
    display: flex;
    align-items: center;
    padding: 0 14px;
    margin: 8px 0;
    color: #eef5ff;
    background: rgba(9, 28, 56, .55);
    font-size: 14px;
}

.role.active {
    border-color: #1aaaff;
    box-shadow: 0 0 17px rgba(15, 163, 255, .17);
    background: linear-gradient(90deg, rgba(11, 101, 190, .26), rgba(9, 42, 81, .62));
}

.role-icon {
    width: 29px;
    margin-right: 11px;
    text-align: center;
    color: #39b6ff;
}

.check {
    margin-left: auto;
    color: #35c8ff;
    font-size: 19px;
}

.status {
    float: right;
    padding: 6px 11px;
    border-radius: 20px;
    color: #53efa7;
    background: rgba(25, 215, 143, .09);
    border: 1px solid rgba(25, 215, 143, .17);
    font-size: 12px;
    font-weight: 600;
}

.question {
    margin-top: 22px;
    display: flex;
    align-items: flex-start;
    gap: 12px;
}

.bot {
    width: 48px;
    height: 48px;
    min-width: 48px;
    border-radius: 50%;
    border: 2px solid #16b8ff;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(0, 153, 255, .11);
    box-shadow: 0 0 22px rgba(0, 155, 255, .25);
    font-size: 24px;
}

.bubble {
    background: linear-gradient(135deg, rgba(35, 68, 111, .9), rgba(19, 44, 78, .9));
    border: 1px solid rgba(105, 148, 204, .23);
    border-radius: 11px 15px 15px 15px;
    padding: 15px 17px;
    color: #eef5ff;
    line-height: 1.5;
    font-size: 14px;
}

.answer {
    margin-top: 26px;
    border: 1px solid rgba(82, 128, 184, .23);
    border-radius: 13px;
    padding: 17px;
    background: rgba(4, 20, 43, .55);
}

.answer-head {
    display: flex;
    justify-content: space-between;
    color: #eaf3ff;
    font-size: 14px;
    font-weight: 600;
}

.timer {
    color: #ff5c68;
}

.wave {
    height: 105px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
    overflow: hidden;
    margin: 5px 0;
}

.wave i {
    display: block;
    width: 3px;
    border-radius: 3px;
    background: linear-gradient(180deg, #1be0ff, #168cff);
    box-shadow: 0 0 8px rgba(18, 173, 255, .35);
}

.mic-wrap {
    text-align: center;
    margin-top: 4px;
}

.mic {
    width: 82px;
    height: 82px;
    border-radius: 50%;
    border: 2px solid #129fff;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 35px;
    background: radial-gradient(circle, rgba(18, 145, 255, .25), rgba(3, 25, 56, .7));
    box-shadow: 0 0 0 9px rgba(10, 122, 255, .08), 0 0 35px rgba(0, 145, 255, .25);
}

.tap {
    color: #9fb2d1;
    font-size: 12px;
    margin-top: 7px;
}

.analysis-orb {
    height: 250px;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
}

.orb {
    width: 155px;
    height: 155px;
    border-radius: 50%;
    border: 1px solid rgba(31, 181, 255, .75);
    box-shadow: 0 0 40px rgba(0, 150, 255, .2), inset 0 0 35px rgba(0, 150, 255, .08);
    position: relative;
}

.orb:before, .orb:after {
    content: "";
    position: absolute;
    inset: 19px;
    border-radius: 50%;
    border: 1px solid rgba(21, 165, 255, .42);
}

.orb:after {
    inset: -18px;
    border-color: rgba(21, 165, 255, .18);
}

.signal {
    position: absolute;
    width: 250px;
    height: 70px;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
}

.signal svg {
    width: 100%;
    height: 100%;
}

.analysis-title {
    color: #b1c1d9;
    margin-top: 3px;
    font-size: 14px;
}

.metric-row {
    display: grid;
    grid-template-columns: 28px 1fr 66px;
    gap: 8px;
    align-items: center;
    margin: 16px 0;
    font-size: 13px;
}

.bar {
    height: 8px;
    border-radius: 10px;
    background: #173152;
    overflow: hidden;
}

.fill-blue { height: 100%; width: 85%; background: #149eff; border-radius: 10px; }
.fill-green { height: 100%; width: 78%; background: #2ddd9b; border-radius: 10px; }
.fill-yellow { height: 100%; width: 60%; background: #ffd21c; border-radius: 10px; }

.score-area {
    display: flex;
    align-items: center;
    gap: 17px;
    margin-top: 25px;
}

.score-ring {
    width: 122px;
    height: 122px;
    min-width: 122px;
    border-radius: 50%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background:
        radial-gradient(circle at center, #071b3c 58%, transparent 59%),
        conic-gradient(#159cff 0 82%, #10365f 82% 100%);
    box-shadow: 0 0 28px rgba(0, 151, 255, .13);
}

.score {
    font-size: 31px;
    font-weight: 700;
}

.score small {
    font-size: 12px;
    color: #9fb2d1;
    font-weight: 500;
}

.feedback-text {
    color: #c8d5e8;
    line-height: 1.5;
    font-size: 13px;
}

.feedback-box {
    border-radius: 11px;
    padding: 14px;
    margin-top: 15px;
    border: 1px solid rgba(61, 211, 162, .25);
    background: rgba(31, 174, 133, .07);
}

.feedback-box.suggest {
    border-color: rgba(245, 208, 42, .28);
    background: rgba(209, 176, 25, .06);
}

.feedback-head {
    color: #49edaa;
    font-weight: 700;
    font-size: 13px;
    margin-bottom: 9px;
}

.suggest .feedback-head {
    color: #ffd62d;
}

.feedback-line {
    color: #d5e2f3;
    font-size: 12px;
    margin: 8px 0;
}

.feedback-line span {
    margin-right: 7px;
}

.cta {
    margin-top: 17px;
    background: linear-gradient(90deg, #087cf7, #128fff);
    border-radius: 9px;
    text-align: center;
    padding: 13px;
    color: white;
    font-weight: 600;
    box-shadow: 0 7px 22px rgba(0, 116, 255, .23);
}

.bottom-stats {
    margin-top: 19px;
    padding: 22px 25px;
    border-radius: 17px;
    border: 1px solid rgba(57, 114, 179, .31);
    background: linear-gradient(145deg, rgba(7, 26, 55, .9), rgba(3, 17, 39, .92));
    display: grid;
    grid-template-columns: repeat(4, 1fr);
}

.stat {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 0 28px;
    border-right: 1px solid rgba(64, 128, 194, .35);
}

.stat:last-child { border-right: none; }

.stat-icon {
    width: 57px;
    height: 57px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 25px;
    background: rgba(18, 100, 202, .08);
    border: 1px solid rgba(31, 137, 255, .13);
}

.stat-label { color: #9fb2d1; font-size: 12px; }
.stat-value { color: white; font-size: 22px; font-weight: 700; margin-top: 4px; }
.stat-value small { font-size: 12px; color: #a9bad5; font-weight: 500; }
.stat-green { color: #2ee39b; font-size: 11px; margin-top: 3px; }

.streamlit-btn button {
    width: 100%;
    border-radius: 9px;
}

@media (max-width: 1050px) {
    .steps { display: none; }
    .bottom-stats { grid-template-columns: repeat(2, 1fr); gap: 20px; }
    .stat { border-right: none; }
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Header
# -----------------------------
st.markdown("""
<div class="hero">
    <h1>AI Interview, <span>Smarter You</span></h1>
    <p>Practice. Analyze. Improve. Get interview-ready with AI.</p>
    <div class="steps">
        <div class="step">
            <div class="step-icon">💼</div>
            <div class="step-text"><div class="step-num">1</div><div class="step-label">Select Position</div></div>
        </div>
        <div class="arrow"></div>
        <div class="step">
            <div class="step-icon">💬</div>
            <div class="step-text"><div class="step-num">2</div><div class="step-label">AI Interview</div></div>
        </div>
        <div class="arrow"></div>
        <div class="step">
            <div class="step-icon">〽️</div>
            <div class="step-text"><div class="step-num">3</div><div class="step-label">Voice Analysis</div></div>
        </div>
        <div class="arrow"></div>
        <div class="step">
            <div class="step-icon">✨</div>
            <div class="step-text"><div class="step-num">4</div><div class="step-label">AI Feedback</div></div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------
# Main cards
# -----------------------------
c1, c2, c3, c4 = st.columns(4, gap="small")

with c1:
    st.markdown("""
    <div class="card">
      <div class="card-title">Select Job Position</div>
      <div class="card-subtitle">Choose the role you want<br>to practice for.</div>
      <div class="searchbox"><span>Search job role...</span><span>⌕</span></div>
      <div class="role active"><span class="role-icon">▣</span>Product Manager <span class="check">✓</span></div>
      <div class="role"><span class="role-icon">&lt;/&gt;</span>Software Engineer</div>
      <div class="role"><span class="role-icon">▥</span>Data Analyst</div>
      <div class="role"><span class="role-icon">♢</span>UX Designer</div>
      <div class="role"><span class="role-icon">⚑</span>Marketing Manager</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Start Interview  →", key="start", use_container_width=True):
        st.session_state["started"] = True
        st.toast("Interview started!")

with c2:
    st.markdown("""
    <div class="card">
      <div class="card-title">AI Interview <span class="status">● In Progress</span></div>
      <div class="question">
        <div class="bot">🤖</div>
        <div class="bubble">Can you describe a challenging situation you faced in a previous role and how you handled it?</div>
      </div>
      <div class="answer">
        <div class="answer-head"><span>Your Answer</span><span class="timer">● 00:28</span></div>
        <div class="wave">
    """, unsafe_allow_html=True)

    heights = [20,32,54,38,69,42,25,58,76,47,32,64,83,48,25,40,67,35,74,58,36,63,80,52,29,44,69,55,34,48,75,65,38,57,73,44,30,62,82,51,36,71,59,45,67,78,50,31,43,64,82,57,34,47,70,55,37,61,78,44,30,53,68,39,58,74,51,35,65,80,45,31]
    bars = "".join(f'<i style="height:{h}px"></i>' for h in heights)
    st.markdown(bars + """
        </div>
        <div class="mic-wrap"><div class="mic">🎙</div><div class="tap">Tap to stop</div></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown("""
    <div class="card">
      <div class="card-title">Voice Analysis</div>
      <div class="analysis-title">Analyzing your response...</div>
      <div class="analysis-orb">
        <div class="orb"></div>
        <div class="signal">
          <svg viewBox="0 0 250 70" preserveAspectRatio="none">
            <path d="M0 35 C20 5, 30 65, 50 35 S80 5, 100 35 S130 62, 150 35 S180 10, 200 35 S230 60, 250 35"
                  fill="none" stroke="#11b9ff" stroke-width="2"/>
          </svg>
        </div>
      </div>
      <div class="metric-row"><span>💡</span><span>Clarity</span><span>85/100</span></div>
      <div class="bar"><div class="fill-blue"></div></div>
      <div class="metric-row"><span>♢</span><span>Confidence</span><span>78/100</span></div>
      <div class="bar"><div class="fill-green"></div></div>
      <div class="metric-row"><span>◷</span><span>Pace</span><span>72/100</span></div>
      <div class="bar"><div class="fill-blue" style="width:72%"></div></div>
      <div class="metric-row"><span>≋</span><span>Filler Words</span><span>60/100</span></div>
      <div class="bar"><div class="fill-yellow"></div></div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown("""
    <div class="card">
      <div class="card-title">AI Feedback</div>
      <div class="score-area">
        <div class="score-ring"><div class="score">82</div><div><small>/100</small></div></div>
        <div class="feedback-text">Great job! Your answer was clear and well-structured. Here are some suggestions to make it even better.</div>
      </div>

      <div class="feedback-box">
        <div class="feedback-head">☆ Strengths</div>
        <div class="feedback-line"><span>✓</span>Clear and structured response</div>
        <div class="feedback-line"><span>✓</span>Good use of specific examples</div>
        <div class="feedback-line"><span>✓</span>Confident tone of voice</div>
      </div>

      <div class="feedback-box suggest">
        <div class="feedback-head">💡 Suggestions</div>
        <div class="feedback-line"><span>⌄</span>Try to reduce filler words</div>
        <div class="feedback-line"><span>⌄</span>Add more impact to your opening</div>
        <div class="feedback-line"><span>⌄</span>Elaborate more on results</div>
      </div>

      <div class="cta">View Detailed Feedback  →</div>
    </div>
    """, unsafe_allow_html=True)

# -----------------------------
# Bottom metrics
# -----------------------------
st.markdown("""
<div class="bottom-stats">
  <div class="stat">
    <div class="stat-icon">⌁</div>
    <div><div class="stat-label">Interviews Taken</div><div class="stat-value">12 <small>+3 this week</small></div><div class="stat-green">↗ Weekly progress</div></div>
  </div>
  <div class="stat">
    <div class="stat-icon">◎</div>
    <div><div class="stat-label">Average Score</div><div class="stat-value">78<small>/100</small></div><div class="stat-green">+5 improvement</div></div>
  </div>
  <div class="stat">
    <div class="stat-icon">🏆</div>
    <div><div class="stat-label">Best Score</div><div class="stat-value">92<small>/100</small></div><div class="stat-label">Product Manager</div></div>
  </div>
  <div class="stat">
    <div class="stat-icon">🔥</div>
    <div><div class="stat-label">Current Streak</div><div class="stat-value">7</div><div class="stat-label">days</div></div>
  </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------
# Functional controls below the visual mockup
# -----------------------------
st.markdown("<br>", unsafe_allow_html=True)
with st.expander("⚙️ Prototype controls — connect these to your RAG/voice backend"):
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        role = st.selectbox("Target role", ["Product Manager", "Software Engineer", "Data Analyst", "UX Designer", "Marketing Manager"])
    with col_b:
        mode = st.selectbox("Answer mode", ["Voice", "Text"])
    with col_c:
        difficulty = st.selectbox("Difficulty", ["Beginner", "Intermediate", "Expert"])

    st.info(
        "This file is the dashboard/UI layer. Connect your existing CV/JD RAG engine, "
        "Groq GPT-OSS-120B interviewer/coach, and Whisper speech-to-text backend to these controls."
    )
'''

requirements = """streamlit>=1.45,<2.0
"""
This package recreates the supplied InterviewForge-style dashboard in Streamlit.

## Included

- `app.py` — complete dashboard UI
- `requirements.txt` — minimal dependency

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
