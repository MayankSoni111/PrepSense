import time
import streamlit as st

from pipeline import prepare_interview, evaluate_candidate_answer


# ==================================================
# 1. PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="PrepSense | Interview Workspace",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ==================================================
# 2. SESSION STATE
# ==================================================

if "interview_result" not in st.session_state:
    st.session_state.interview_result = None

if "evaluations" not in st.session_state:
    st.session_state.evaluations = {}


# ==================================================
# 3. CUSTOM CSS
# ==================================================

st.markdown("""
<style>

:root {
    --bg: #FFF8F0;
    --card: #FFFFFF;
    --card-deep: #FFFDF9;
    --border: #F0DFCB;
    --orange: #FF5A36;
    --orange-soft: #FF8A5B;
    --navy: #1F2A44;
    --navy-soft: #2C3A5E;
    --text: #1F2A44;
    --text-muted: #55607A;
    --text-dim: #7C8599;
    --cream: #FFF8F0;
}

/* Main background */

.stApp {
    background:
        radial-gradient(
            circle at 10% 0%,
            rgba(255, 138, 91, 0.20),
            transparent 32%
        ),
        radial-gradient(
            circle at 95% 90%,
            rgba(31, 42, 68, 0.06),
            transparent 35%
        ),
        var(--bg);
    color: var(--text);
}

/* Page width */

.block-container {
    max-width: 1180px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}

/* Header */

[data-testid="stHeader"] {
    background: transparent;
}

/* Typography */

h1, h2, h3 {
    color: var(--text) !important;
    letter-spacing: -0.7px;
}

p {
    color: var(--text-muted);
}

/* Brand */

.brand {
    display: flex;
    align-items: center;
    gap: 11px;
    margin-bottom: 30px;
}

.brand-logo {
    width: 40px;
    height: 40px;
    border-radius: 12px;
    background: linear-gradient(
        135deg,
        var(--orange),
        var(--orange-soft)
    );
    color: #FFFFFF;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 19px;
    font-weight: 900;
    box-shadow: 0 6px 18px rgba(255, 90, 54, 0.30);
}

.brand-name {
    color: var(--navy);
    font-weight: 800;
    font-size: 21px;
    letter-spacing: 1px;
}

.brand-tag {
    margin-left: auto;
    color: var(--orange);
    background: rgba(255, 90, 54, 0.07);
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1.2px;
    border: 1px solid rgba(255, 90, 54, 0.35);
    padding: 7px 12px;
    border-radius: 20px;
}

/* Hero */

.hero {
    background: linear-gradient(
        120deg,
        var(--navy),
        var(--navy-soft)
    );
    border-radius: 22px;
    border-bottom: 4px solid var(--orange);
    padding: 36px 38px;
    margin-bottom: 30px;
    box-shadow: 0 14px 34px rgba(31, 42, 68, 0.18);
}

.hero-label {
    color: var(--orange-soft);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2px;
    margin-bottom: 15px;
}

.hero h1 {
    color: var(--cream) !important;
    font-size: 39px;
    line-height: 1.2;
    margin: 0;
}

.hero h1 span {
    background: linear-gradient(
        90deg,
        var(--orange),
        var(--orange-soft)
    );
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-description {
    color: #C9D1E6;
    font-size: 15px;
    line-height: 1.8;
    max-width: 620px;
    margin-top: 13px;
}

/* Form */

[data-testid="stForm"] {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 24px;
    box-shadow: 0 8px 24px rgba(31, 42, 68, 0.06);
}

/* Section headings */

.section-label {
    color: var(--orange);
    font-size: 11px;
    letter-spacing: 1.7px;
    font-weight: 700;
    margin-bottom: 7px;
}

.section-heading {
    color: var(--text);
    font-size: 22px;
    font-weight: 700;
    margin-bottom: 20px;
}

/* Inputs */

.stTextInput input,
.stTextArea textarea {
    background: var(--card-deep) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
}

.stTextInput input::placeholder,
.stTextArea textarea::placeholder {
    color: #A3A9B8 !important;
}

.stTextInput input:focus,
.stTextArea textarea:focus {
    border-color: var(--orange) !important;
    box-shadow: 0 0 0 1px var(--orange) !important;
}

.stTextInput label,
.stTextArea label,
.stFileUploader label {
    color: var(--text) !important;
    font-weight: 600 !important;
}

/* PDF uploader */

[data-testid="stFileUploaderDropzone"] {
    background: var(--card-deep);
    border: 1px dashed #E2C7A8;
    border-radius: 12px;
}

[data-testid="stFileUploaderDropzone"]:hover {
    border-color: var(--orange);
}

[data-testid="stFileUploaderDropzoneInstructions"] {
    color: var(--text-muted) !important;
}

[data-testid="stFileUploaderDropzone"] button {
    background: var(--navy) !important;
    color: var(--cream) !important;
    border: none !important;
    border-radius: 8px !important;
}

/* Primary button */

.stFormSubmitButton button {
    background: linear-gradient(
        100deg,
        var(--orange),
        var(--orange-soft)
    ) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 800 !important;
    min-height: 48px;
    transition: 0.2s ease;
    box-shadow: 0 8px 20px rgba(255, 90, 54, 0.30);
}

.stFormSubmitButton button:hover {
    filter: brightness(1.05);
    transform: translateY(-1px);
    box-shadow: 0 10px 26px rgba(255, 90, 54, 0.42);
}

/* Information cards */

.info-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 22px;
    margin-bottom: 16px;
    box-shadow: 0 8px 24px rgba(31, 42, 68, 0.06);
}

.info-card h3 {
    font-size: 17px;
    margin-top: 0;
    color: var(--text);
}

.info-card p {
    color: var(--text-muted);
    font-size: 13px;
    line-height: 1.65;
}

/* Information steps */

.step {
    display: flex;
    gap: 13px;
    align-items: flex-start;
    margin-top: 19px;
}

.step-number {
    min-width: 27px;
    height: 27px;
    border-radius: 8px;
    background: rgba(255, 90, 54, 0.10);
    border: 1px solid rgba(255, 90, 54, 0.28);
    color: var(--orange);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 12px;
}

.step-title {
    color: var(--text);
    font-size: 14px;
    font-weight: 600;
}

.step-description {
    color: var(--text-dim);
    font-size: 12px;
    line-height: 1.5;
    margin-top: 4px;
}

/* Statistics */

.stat-box {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 18px;
    text-align: center;
    box-shadow: 0 8px 24px rgba(31, 42, 68, 0.06);
}

.stat-number {
    color: var(--orange);
    font-size: 29px;
    font-weight: 800;
}

.stat-caption {
    color: var(--text-dim);
    font-size: 12px;
}

/* Alerts */

[data-testid="stAlert"] {
    border-radius: 12px;
}

/* Expanders */

[data-testid="stExpander"] {
    background: #FFFFFF;
    border: 1px solid var(--border);
    border-radius: 12px;
    margin-bottom: 14px;
}

[data-testid="stExpander"] summary {
    color: var(--navy);
    font-weight: 600;
}

/* Footer */

.footer {
    text-align: center;
    color: var(--text-dim);
    font-size: 12px;
    margin-top: 38px;
    padding-top: 20px;
    border-top: 1px solid var(--border);
}

.footer b {
    color: var(--orange);
    font-weight: 600;
}

</style>
""", unsafe_allow_html=True)


# ==================================================
# 4. BRANDING
# ==================================================

st.html("""
<div class="brand">
    <div class="brand-logo">P</div>
    <div class="brand-name">PREPSENSE</div>
    <div class="brand-tag">AI INTERVIEW WORKSPACE</div>
</div>
""")


# ==================================================
# 5. HERO SECTION
# ==================================================

st.html("""
<div class="hero">

    <div class="hero-label">
        YOUR NEXT INTERVIEW STARTS HERE
    </div>

    <h1>
        Prepare smarter.<br>
        <span>Interview stronger.</span>
    </h1>

    <div class="hero-description">
        Go beyond generic questions. PrepSense combines
        company research, job requirements and your own
        experience to create a personalized interview session.
    </div>

</div>
""")


# ==================================================
# 6. MAIN PAGE LAYOUT
# ==================================================

left_column, right_column = st.columns(
    [1.65, 1],
    gap="large",
)


# ==================================================
# 7. INTERVIEW INPUT FORM
# ==================================================

with left_column:

    st.html("""
    <div>
        <div class="section-label">
            01 / INTERVIEW SETUP
        </div>

        <div class="section-heading">
            Build your interview brief
        </div>
    </div>
    """)

    with st.form("interview_form"):

        company_name = st.text_input(
            "Target company",
            placeholder="e.g. Microsoft, Google, Amazon, Salesforce",
        )

        job_description = st.text_area(
            "Job description",
            placeholder=(
                "Paste the complete job description here. "
                "Include skills, responsibilities and qualifications..."
            ),
            height=230,
        )

        resume_pdf = st.file_uploader(
            "Your resume",
            type=["pdf"],
            help="Upload your resume in PDF format.",
        )

        st.markdown(
            '<div style="height:12px"></div>',
            unsafe_allow_html=True,
        )

        submitted = st.form_submit_button(
            "Generate my interview session  →",
            use_container_width=True,
            type="primary",
        )


# ==================================================
# 8. RIGHT INFORMATION PANEL
# ==================================================

with right_column:

    st.html("""
    <div class="info-card">

        <h3>Your preparation, personalized.</h3>

        <p>
            Three information sources come together to make
            your interview preparation more relevant.
        </p>

        <div class="step">
            <div class="step-number">01</div>
            <div>
                <div class="step-title">Company intelligence</div>
                <div class="step-description">
                    Research products, services and technology areas.
                </div>
            </div>
        </div>

        <div class="step">
            <div class="step-number">02</div>
            <div>
                <div class="step-title">Role understanding</div>
                <div class="step-description">
                    Extract skills and responsibilities from the job posting.
                </div>
            </div>
        </div>

        <div class="step">
            <div class="step-number">03</div>
            <div>
                <div class="step-title">Resume personalization</div>
                <div class="step-description">
                    Connect your projects, skills and experience to the role.
                </div>
            </div>
        </div>

    </div>
    """)

    st.html("""
    <div class="info-card">

        <div class="section-label">
            PRACTICE & AI FEEDBACK
        </div>

        <h3>Answer & Get Scored</h3>

        <div class="step">
            <div class="step-number">01</div>
            <div>
                <div class="step-title">Practice each question</div>
                <div class="step-description">
                    Type your response directly in the answer box.
                </div>
            </div>
        </div>

        <div class="step">
            <div class="step-number">02</div>
            <div>
                <div class="step-title">Instant AI scoring (0–10)</div>
                <div class="step-description">
                    Get scored on correctness, clarity, and depth.
                </div>
            </div>
        </div>

        <div class="step">
            <div class="step-number">03</div>
            <div>
                <div class="step-title">Coaching feedback</div>
                <div class="step-description">
                    See strengths, missing points, and STAR analysis.
                </div>
            </div>
        </div>

    </div>
    """)


# ==================================================
# 9. PROCESS FORM SUBMISSION
# ==================================================

if submitted:

    # Clear previous results before processing a new request
    st.session_state.interview_result = None
    st.session_state.evaluations = {}

    if not company_name.strip():

        st.error("Please enter the target company.")

    elif not job_description.strip():

        st.error("Please provide the job description.")

    elif resume_pdf is None:

        st.error("Please upload your resume PDF.")

    else:

        try:

            with st.status(
                "Preparing your interview session...",
                expanded=True,
            ) as status:

                start = time.perf_counter()
                print("\n[STREAMLIT] Starting interview preparation...")

                def _on_progress(step: str):
                    st.write(step)

                result = prepare_interview(
                    company_name=company_name.strip(),
                    job_description=job_description.strip(),
                    resume_pdf=resume_pdf,
                    progress_callback=_on_progress,
                )

                elapsed = time.perf_counter() - start
                print(
                    f"\n[STREAMLIT] Total pipeline execution: "
                    f"{elapsed:.2f} seconds"
                )

                status.update(
                    label=f"Interview ready! ({elapsed:.0f}s)",
                    state="complete",
                    expanded=False,
                )

            st.session_state.interview_result = result
            st.session_state.evaluations = {}
            st.success("Your personalized interview session is ready! Scroll down to practice answering questions.")

        except Exception as error:

            st.error(
                "We couldn't prepare your interview. "
                "Please check your inputs and try again."
            )

            with st.expander("Technical error details"):
                st.exception(error)


# ==================================================
# 10. DISPLAY GENERATED INTERVIEW & PRACTICE WORKSPACE
# ==================================================

result = st.session_state.interview_result

if result is not None:

    st.divider()

    st.html("""
    <div class="section-label">
        02 / YOUR PRACTICE WORKSPACE
    </div>
    """)

    st.header(f"Interview Questions · {result['company_name']}")

    questions = result["questions"]

    technical_count = sum(
        question["type"] == "technical"
        for question in questions
    )

    behavioral_count = sum(
        question["type"] == "behavioral"
        for question in questions
    )

    # Display session statistics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.html(f"""
        <div class="stat-box">
            <div class="stat-number">{len(questions)}</div>
            <div class="stat-caption">Total questions</div>
        </div>
        """)

    with col2:
        st.html(f"""
        <div class="stat-box">
            <div class="stat-number">{technical_count}</div>
            <div class="stat-caption">Technical questions</div>
        </div>
        """)

    with col3:
        st.html(f"""
        <div class="stat-box">
            <div class="stat-number">{behavioral_count}</div>
            <div class="stat-caption">Behavioral questions</div>
        </div>
        """)

    st.write("")
    st.markdown("💡 **Tip:** Type your answer for each question below and click **Evaluate My Answer** to receive a score and coaching feedback.")

    # Display interactive practice cards for each question
    for index, question in enumerate(questions, start=1):

        question_type = question["type"].title()
        is_evaluated = index in st.session_state.evaluations

        expander_title = f"Question {index:02d}  |  {question_type}"
        if is_evaluated:
            score_val = st.session_state.evaluations[index].get("score", 0)
            expander_title += f"  —  Score: {score_val}/10 ⭐"

        with st.expander(expander_title, expanded=(index == 1 or is_evaluated)):

            st.markdown(f"#### {question['question']}")

            st.caption(f"🎯 **Why this is asked:** {question['reason']}")

            st.markdown("---")

            # Candidate answer input
            answer_key = f"user_answer_{index}"
            candidate_ans = st.text_area(
                "Your Answer:",
                placeholder="Type your response here. For behavioral questions, explain the Situation, Task, Action, and Result. For technical questions, explain your reasoning and trade-offs...",
                key=answer_key,
                height=130,
            )

            col_btn, _ = st.columns([1.5, 2])
            with col_btn:
                btn_evaluate = st.button(
                    f"Evaluate Answer {index} ✨",
                    key=f"eval_btn_{index}",
                    type="primary",
                )

            if btn_evaluate:
                if not candidate_ans.strip():
                    st.warning("Please type your answer in the text box above before submitting for evaluation.")
                else:
                    with st.spinner(f"Evaluating Question {index} answer with AI coach..."):
                        start_eval = time.perf_counter()
                        feedback = evaluate_candidate_answer(
                            question=question,
                            candidate_answer=candidate_ans.strip(),
                            job_info=result["job_info"],
                        )
                        eval_time = time.perf_counter() - start_eval
                        print(f"[STREAMLIT] Question {index} evaluation took {eval_time:.2f}s")
                        st.session_state.evaluations[index] = feedback
                        st.rerun()

            # Display coaching feedback if evaluated
            if is_evaluated:
                fb = st.session_state.evaluations[index]
                score = fb.get("score", 7)

                score_color = "#10B981" if score >= 8 else ("#F59E0B" if score >= 6 else "#EF4444")

                st.markdown(f"""
                <div style="background: rgba(31, 42, 68, 0.04); border-left: 5px solid {score_color}; border-radius: 8px; padding: 14px 20px; margin: 18px 0;">
                    <div style="font-size: 12px; font-weight: 700; color: #55607A; text-transform: uppercase; letter-spacing: 1px;">Interview Coach Assessment</div>
                    <div style="font-size: 28px; font-weight: 900; color: {score_color}; margin-top: 4px;">Score: {score} / 10</div>
                </div>
                """, unsafe_allow_html=True)

                col_str, col_miss = st.columns(2)

                with col_str:
                    st.markdown("##### ✅ Strengths")
                    for s in fb.get("strengths", []):
                        st.markdown(f"- {s}")

                with col_miss:
                    st.markdown("##### ⚠️ What was Missing")
                    for m in fb.get("missing_points", []):
                        st.markdown(f"- {m}")

                st.markdown("##### 💡 Suggestions to Improve")
                for sug in fb.get("suggestions", []):
                    st.markdown(f"- {sug}")

                star = fb.get("star_feedback", "")
                if star and star.lower() != "not applicable":
                    st.markdown("##### ⭐ STAR Analysis")
                    st.info(star)

    # Additional preparation information
    st.divider()

    with st.expander("🏢 Company Research Summary"):
        st.markdown(result["company_research"])

    with st.expander("📋 Extracted Job Information"):
        st.json(result["job_info"])

    with st.expander("📄 Resume Processing Summary"):
        st.success("Resume text extracted successfully.")
        st.write(
            "Extracted characters:",
            len(result["resume_text"]),
        )


# ==================================================
# 11. FOOTER
# ==================================================

st.html("""
<div class="footer">
    PREPSENSE · COMPANY-AWARE INTERVIEW PREPARATION
    <br><br>
    Built with Python, Streamlit and <b>Qwen3</b>
</div>
""")
