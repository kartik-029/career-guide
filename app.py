# app.py — AI Career Guide
# Run: streamlit run app.py

import streamlit as st
from utils.gemini_helper import (
    generate_response,
    generate_chat_response,
    stream_response,
    check_gemini_connection,
    MODEL_NAME,
    load_env_file,
)
from utils.resume_parser import extract_text_from_pdf, clean_resume_text, get_resume_stats
from utils.prompts import (
    CAREER_CHAT_SYSTEM,
    ROADMAP_PROMPT,
    SKILL_ANALYZER_PROMPT,
    RESUME_ANALYZER_PROMPT,
)

# Page Configuration
st.set_page_config(
    page_title="AI Career Guide",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS — Dark Theme + Clean UI
st.markdown("""
<style>
/* ── Global ──────────────────────────────────────────── */
[data-testid="stAppViewContainer"] {
    background: #0f1117;
    color: #e0e0e0;
}
[data-testid="stSidebar"] {
    background: #1a1d27;
    border-right: 1px solid #2d3149;
}

/* ── Cards ───────────────────────────────────────────── */
.card {
    background: #1e2130;
    border: 1px solid #2d3149;
    border-radius: 12px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
}
.card-accent {
    background: linear-gradient(135deg, #1e2130 0%, #1a2340 100%);
    border: 1px solid #3d4f8a;
    border-radius: 12px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
}

/* ── Headings ────────────────────────────────────────── */
h1 { color: #7c9ef8 !important; }
h2 { color: #a8c0ff !important; }
h3 { color: #c8d8ff !important; }

/* ── Sidebar nav items ───────────────────────────────── */
.nav-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 14px;
    border-radius: 8px;
    margin-bottom: 4px;
    cursor: pointer;
    transition: background 0.2s;
    color: #b0b8d4;
    font-size: 0.95rem;
}
.nav-item:hover { background: #2d3149; }
.nav-item.active { background: #2d3f80; color: #fff; font-weight: 600; }

/* ── Chat bubbles ────────────────────────────────────── */
.chat-user {
    background: #1e3a5f;
    border-radius: 12px 12px 0 12px;
    padding: 0.7rem 1rem;
    margin: 0.4rem 0;
    text-align: right;
    color: #e0eeff;
}
.chat-ai {
    background: #1e2130;
    border: 1px solid #2d3149;
    border-radius: 12px 12px 12px 0;
    padding: 0.7rem 1rem;
    margin: 0.4rem 0;
    color: #d0d8f0;
}

/* ── Stat chips ──────────────────────────────────────── */
.stat-chip {
    display: inline-block;
    background: #2d3149;
    border-radius: 20px;
    padding: 4px 14px;
    margin: 4px;
    font-size: 0.85rem;
    color: #a8c0ff;
}

/* ── Buttons ─────────────────────────────────────────── */
[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #3d5af1, #2d3f80);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 0.5rem 1.4rem;
    font-weight: 600;
    transition: opacity 0.2s;
}
[data-testid="stButton"] > button:hover { opacity: 0.85; }

/* ── Inputs ──────────────────────────────────────────── */
[data-testid="stTextArea"] textarea,
[data-testid="stTextInput"] input {
    background: #1e2130 !important;
    border: 1px solid #2d3149 !important;
    color: #e0e0e0 !important;
    border-radius: 8px !important;
}

/* ── Selectbox ───────────────────────────────────────── */
[data-testid="stSelectbox"] > div > div {
    background: #1e2130 !important;
    border: 1px solid #2d3149 !important;
    color: #e0e0e0 !important;
}

/* ── Divider ─────────────────────────────────────────── */
hr { border-color: #2d3149; }
</style>
""", unsafe_allow_html=True)

# Session State Initialisation
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []   # list of {"role": "user"|"ai", "content": str}

if "page" not in st.session_state:
    st.session_state.page = "Home"


# Sidebar Navigation
with st.sidebar:
    st.markdown("##  AI Career Guide")
    st.markdown(f"<span class='stat-chip'>Model: {MODEL_NAME}</span>", unsafe_allow_html=True)
    st.markdown("---")

    pages = {
        "Home": "Home",
        "Career Chat": "Career Chat",
        "Roadmap Generator": "Roadmap Generator",
        "Skill Analyzer": "Skill Analyzer",
        "Resume Analyzer": "Resume Analyzer",
    }

    for label, key in pages.items():
        active_cls = "active" if st.session_state.page == key else ""
        if st.button(label, key=f"nav_{key}", use_container_width=True):
            st.session_state.page = key
            st.rerun()

    st.markdown("---")

    # Gemini Configuration
    st.markdown("### ⚙️ Gemini Setup")
    import os
    load_env_file()  # Ensure .env variables are loaded into os.environ
    env_key = os.environ.get("GEMINI_API_KEY", "")

    if env_key:
        st.success("🔑 API Key loaded from environment / .env")
    else:
        user_key = st.text_input(
            "Enter Gemini API Key",
            type="password",
            value=st.session_state.get("gemini_api_key", ""),
            help="Get your free API key from Google AI Studio"
        )
        if user_key:
            st.session_state.gemini_api_key = user_key

    if st.button("Test Connection", key="check_conn"):
        with st.spinner("Testing connection..."):
            ok, msg = check_gemini_connection()
            if ok:
                st.success(msg)
            else:
                st.error(msg)

    st.markdown("""
    <div style='font-size:0.8rem; color:#6a7290; margin-top:1rem;'>
    Need a key? Get a free API key at <a href="https://aistudio.google.com/" target="_blank" style="color: #7c9ef8;">Google AI Studio</a>.
    </div>
    """, unsafe_allow_html=True)

# Page: Home
if st.session_state.page == "Home":
    st.markdown("#  AI Career Guide")
    st.markdown("**Your personal AI-powered career mentor — powered by Gemini API**")
    st.markdown("---")

    cols = st.columns(2)

    features = [
        ( "Career Chat", "Have a free-form conversation with your AI career mentor. Ask anything about tech careers, job switching, or interview prep."),
        ( "Roadmap Generator", "Select a target role and your current level. Get a detailed, phase-by-phase learning roadmap with projects and resources."),
        ( "Skill Analyzer", "Enter your current skills and dream role. The AI will identify gaps and suggest a personalised action plan."),
        ( "Resume Analyzer", "Upload your PDF resume. Get ATS optimisation tips, missing skills, and project recommendations."),
    ]

    for i, (title, desc) in enumerate(features):
        with cols[i % 2]:
            st.markdown(f"""
            <div class="card-accent">
                <h3>{title}</h3>
                <p style='color:#9ba8cc; font-size:0.93rem;'>{desc}</p>
            </div>
            """, unsafe_allow_html=True)

    

# Page: Career Chat
elif st.session_state.page == "Career Chat":
    st.markdown("# " \
    " Career Chat")
    st.markdown("Ask your AI career mentor anything about tech careers, skills, and job hunting.")
    st.markdown("---")

    # Starter suggestions
    starter_questions = [
        "Which career is good for me if I like coding?",
        "How do I become an AI Engineer?",
        "What skills should I learn in 2025?",
        "Give me a 3-month study plan for web dev.",
        "How do I prepare for technical interviews?",
    ]

    st.markdown("**Try asking:**")
    q_cols = st.columns(len(starter_questions))
    for i, q in enumerate(starter_questions):
        with q_cols[i]:
            if st.button(q, key=f"starter_{i}"):
                st.session_state.chat_history.append({"role": "user", "content": q})
                with st.spinner("Thinking..."):
                    reply = generate_chat_response(CAREER_CHAT_SYSTEM, q)
                st.session_state.chat_history.append({"role": "ai", "content": reply})
                st.rerun()

    st.markdown("---")

    # Chat history display
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f"<div class='chat-user'> {msg['content']}</div>", unsafe_allow_html=True)
        else:
            with st.container():
                st.markdown(f"<div class='chat-ai'> <strong>AI Mentor</strong></div>", unsafe_allow_html=True)
                st.markdown(msg["content"])

    # Input
    st.markdown("---")
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_area(
            "Your message",
            placeholder="e.g. How do I transition from web dev to ML?",
            height=90,
            label_visibility="collapsed",
        )
        col1, col2 = st.columns([5, 1])
        with col2:
            submitted = st.form_submit_button("Send ", use_container_width=True)

    if submitted and user_input.strip():
        st.session_state.chat_history.append({"role": "user", "content": user_input.strip()})
        with st.spinner("AI is thinking..."):
            reply = generate_chat_response(CAREER_CHAT_SYSTEM, user_input.strip())
        st.session_state.chat_history.append({"role": "ai", "content": reply})
        st.rerun()

    if st.session_state.chat_history:
        if st.button("Clear Chat", key="clear_chat"):
            st.session_state.chat_history = []
            st.rerun()

# Page: Roadmap Generator
elif st.session_state.page == "Roadmap Generator":
    st.markdown("# Roadmap Generator")
    st.markdown("Select your target role and experience level to get a customised learning roadmap.")
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        role = st.selectbox(
            "Target Role",
            ["AI Engineer", "Backend Developer", "Full Stack Developer", "Data Scientist",
             "DevOps Engineer", "Mobile Developer", "Cybersecurity Engineer"],
            key="roadmap_role",
        )

    with col2:
        level = st.selectbox(
            "Your Current Level",
            ["Complete Beginner", "Beginner", "Intermediate", "Advanced"],
            key="roadmap_level",
        )

    st.markdown("")
    generate_btn = st.button("⚡ Generate Roadmap", key="gen_roadmap", use_container_width=False)

    if generate_btn:
        prompt = ROADMAP_PROMPT.format(role=role, level=level)
        st.markdown("---")
        st.markdown(f"### Roadmap: {role} ({level})")

        with st.spinner(f"Generating roadmap for {role}..."):
            result = generate_response(prompt)

        st.markdown(f"""
        <div class="card">
        """, unsafe_allow_html=True)
        st.markdown(result)
        st.markdown("</div>", unsafe_allow_html=True)

        # Download button
        st.download_button(
            label="Download Roadmap",
            data=result,
            file_name=f"roadmap_{role.lower().replace(' ', '_')}.md",
            mime="text/markdown",
        )

# Page: Skill Analyzer

elif st.session_state.page == "Skill Analyzer":
    st.markdown("# Skill Analyzer")
    st.markdown("Enter your current skills and target role. The AI will identify gaps and suggest next steps.")
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        current_skills = st.text_area(
            "Your Current Skills",
            placeholder="e.g. Python, basic HTML/CSS, a bit of JavaScript, SQL basics...",
            height=160,
            key="skills_input",
        )

    with col2:
        target_role = st.selectbox(
            "Target Role",
            ["AI Engineer", "Backend Developer", "Full Stack Developer", "Data Scientist",
             "DevOps Engineer", "Mobile Developer", "Cybersecurity Engineer"],
            key="skill_role",
        )
        st.markdown("")
        st.markdown("""
        <div class="card" style="padding:1rem;">
            <strong>Tips for best results</strong>
            <ul style='color:#9ba8cc; font-size:0.9rem; margin-top:0.5rem;'>
                <li>List all your skills, even basic ones</li>
                <li>Include years of experience if possible</li>
                <li>Mention any tools or frameworks you know</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    analyze_btn = st.button("Analyze Skills", key="analyze_skills")

    if analyze_btn:
        if not current_skills.strip():
            st.warning("Please enter your current skills before analyzing.")
        else:
            prompt = SKILL_ANALYZER_PROMPT.format(
                target_role=target_role,
                current_skills=current_skills.strip(),
            )
            st.markdown("---")
            st.markdown(f"### Skill Gap Analysis: {target_role}")

            with st.spinner("Analyzing your skills..."):
                result = generate_response(prompt)

            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown(result)
            st.markdown("</div>", unsafe_allow_html=True)

            st.download_button(
                label="Download Analysis",
                data=result,
                file_name=f"skill_analysis_{target_role.lower().replace(' ', '_')}.md",
                mime="text/markdown",
            )

# Page: Resume Analyzer
 
elif st.session_state.page == "Resume Analyzer":
    st.markdown("# Resume Analyzer")
    st.markdown("Upload your resume PDF to get AI-powered ATS tips, skill gap analysis, and project recommendations.")
    st.markdown("---")

    uploaded_file = st.file_uploader(
        "Upload your Resume (PDF)",
        type=["pdf"],
        help="Only PDF files are supported.",
        key="resume_upload",
    )

    if uploaded_file is not None:
        # Show file info
        st.markdown(f"""
        <div class="card">
            <strong>📎 Uploaded:</strong> {uploaded_file.name}
            &nbsp;&nbsp;
            <span class="stat-chip">{round(uploaded_file.size / 1024, 1)} KB</span>
        </div>
        """, unsafe_allow_html=True)

        # Extract text
        with st.spinner("Extracting text from PDF..."):
            raw_text = extract_text_from_pdf(uploaded_file)
            clean_text = clean_resume_text(raw_text)
            stats = get_resume_stats(clean_text)

        if clean_text.startswith("❌") or clean_text.startswith("Error"):
            st.error(clean_text)
        else:
            # Stats row
            c1, c2, c3 = st.columns(3)
            c1.metric("Words", stats["word_count"])
            c2.metric("Lines", stats["line_count"])
            c3.metric("Characters", stats["char_count"])

            with st.expander("View Extracted Text"):
                st.text_area("Raw extracted text", clean_text, height=250, key="raw_text_view")

            st.markdown("")
            analyze_resume_btn = st.button("Analyze Resume with AI", key="analyze_resume")

            if analyze_resume_btn:
                # Truncate to ~4000 chars to stay within context window
                truncated = clean_text[:4000]
                if len(clean_text) > 4000:
                    st.info("ℹResume is long — analyzing the first 4,000 characters.")

                prompt = RESUME_ANALYZER_PROMPT.format(resume_text=truncated)
                st.markdown("---")
                st.markdown("### AI Resume Analysis")

                with st.spinner("AI is analyzing your resume..."):
                    result = generate_response(prompt)

                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown(result)
                st.markdown("</div>", unsafe_allow_html=True)

                st.download_button(
                    label="Download Analysis",
                    data=result,
                    file_name="resume_analysis.md",
                    mime="text/markdown",
                )
    else:
        st.markdown("""
        <div class="card" style="text-align:center; padding:2.5rem;">
            <h2 style='color:#6a7290;'>📎 No file uploaded</h2>
            <p style='color:#6a7290;'>Upload a PDF resume above to get started.</p>
        </div>
        """, unsafe_allow_html=True)
