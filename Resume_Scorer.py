import streamlit as st
import re
import nltk
from collections import Counter
import io
from PyPDF2 import PdfReader
import docx

# Download NLTK data for first run
# Ensure NLTK data is available in all environments
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
try:
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    nltk.download('averaged_perceptron_tagger')

desired_keywords = [
    'python', 'sql', 'data analysis', 'machine learning', 'excel', 'communication', 'leadership',
    'project management', 'cloud', 'aws', 'azure', 'google cloud', 'deep learning', 'statistics',
    'visualization', 'presentation', 'collaboration', 'problem solving', 'agile', 'scrum', 'docker',
    'kubernetes', 'linux', 'git', 'rest api', 'tensorflow', 'pytorch', 'nlp', 'data engineering'
]

action_verbs = [
    'achieved', 'managed', 'developed', 'led', 'designed', 'implemented', 'created', 'improved',
    'increased', 'reduced', 'analyzed', 'built', 'delivered', 'organized', 'launched', 'optimized',
    'streamlined', 'coordinated', 'mentored', 'initiated', 'executed'
]

def extract_text_from_pdf(file):
    try:
        pdf_reader = PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        st.error("Error reading PDF: " + str(e))
        return ""

def extract_text_from_docx(file):
    try:
        doc = docx.Document(file)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
    except Exception as e:
        st.error("Error reading DOCX: " + str(e))
        return ""

def extract_years_of_experience(text):
    patterns = [
        r'(\d+)\s*\+?\s*years',
        r'over\s+(\d+)\s*years',
        r'(\d+)\s*years? of experience',
        r'experience\s*of\s*(\d+)\s*years'
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return 0

def extract_education(text):
    degrees = [
        'bachelor', 'master', 'phd', 'b\.sc', 'm\.sc', 'b\.tech', 'm\.tech',
        'mba', 'bachelor of science', 'master of science', 'doctorate', 'bachelors', 'masters'
    ]
    for degree in degrees:
        if re.search(degree, text, re.IGNORECASE):
            return True
    return False

def extract_certifications(text):
    certs = [
        'certified', 'certificate', 'certification', 'aws certified', 'azure certified',
        'google cloud certified', 'pmp', 'scrum master', 'six sigma', 'cfa', 'cpa'
    ]
    found = []
    for cert in certs:
        if re.search(cert, text, re.IGNORECASE):
            found.append(cert)
    return found

def get_ideal_word_count_range(user_exp):
    """
    Returns (min_words, max_words) based on user experience.
    - 0-2 years: 300-600 words (entry/junior)
    - 3-5 years: 500-900 words (mid-level)
    - 6-10 years: 700-1200 words (senior)
    - 11+ years: 900-1600 words (leadership/executive)
    """
    if user_exp <= 2:
        return (300, 600)
    elif user_exp <= 5:
        return (500, 900)
    elif user_exp <= 10:
        return (700, 1200)
    else:
        return (900, 1600)

def score_resume(text, user_exp):
    score = 0
    feedback = []
    suggestions = []

    # --- Production-level word count logic ---
    min_words, max_words = get_ideal_word_count_range(user_exp)
    word_count = len(text.split())
    if min_words <= word_count <= max_words:
        score += 10
        feedback.append(f"✅ Good word count for your experience level ({user_exp} years).")
    elif word_count < min_words:
        feedback.append(f"⚠️ Word count ({word_count}) is too low for your experience ({user_exp} years).")
        suggestions.append(f"Add more details about your experience, skills, and achievements. For {user_exp} years, aim for {min_words}-{max_words} words.")
    else:
        feedback.append(f"⚠️ Word count ({word_count}) is too high for your experience ({user_exp} years).")
        suggestions.append(f"Try to keep your resume concise and relevant. For {user_exp} years, aim for {min_words}-{max_words} words.")

    # Keyword presence (simulate ML feature extraction)
    text_lower = text.lower()
    matched_keywords = [kw for kw in desired_keywords if kw in text_lower]
    score += min(len(matched_keywords), 10) * 5  # Max 50 points for keywords
    if matched_keywords:
        feedback.append(f"✅ Contains important keywords: {', '.join(matched_keywords[:10])}.")
        if len(matched_keywords) < 5:
            suggestions.append("Include more relevant keywords from the job description.")
    else:
        feedback.append("⚠️ No important keywords detected.")
        suggestions.append("Add more industry-relevant keywords and skills.")

    # 3️⃣ Check for contact info (basic)
    email_pattern = r'[\w\.-]+@[\w\.com]+'
    phone_pattern1 = r'\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}'
    phone_pattern2 = r'\d{10}'

    if re.search(email_pattern, text):
        score += 5
        feedback.append("✅ Email detected.")
    else:
        feedback.append("⚠️ No email found.")
        suggestions.append("Include a professional email address.")

    if re.search(phone_pattern1, text) or re.search(phone_pattern2, text):
        score += 5
        feedback.append("✅ Phone number detected.")
    else:
        feedback.append("⚠️ No phone number found.")
        suggestions.append("Include a phone number with or without country code.")

    # Work experience check
    years_exp = extract_years_of_experience(text)
    if user_exp >= 8:
        score += 15
        feedback.append(f"✅ Strong work experience (user input): {user_exp} years.")
    elif user_exp >= 4:
        score += 10
        feedback.append(f"✅ Moderate work experience (user input): {user_exp} years.")
    elif user_exp > 0:
        score += 5
        feedback.append(f"⚠️ Limited work experience (user input): {user_exp} years.")
        suggestions.append("Highlight more of your work experience and achievements.")
    else:
        feedback.append("⚠️ No work experience entered.")
        suggestions.append("Clearly mention your total years of experience.")

    # Education check
    if extract_education(text):
        score += 5
        feedback.append("✅ Education details detected.")
    else:
        feedback.append("⚠️ No education details found.")
        suggestions.append("Include your highest degree and relevant education.")

    # Certifications check
    certs = extract_certifications(text)
    if certs:
        score += 5
        feedback.append(f"✅ Certifications detected: {', '.join(set(certs))}.")
    else:
        feedback.append("⚠️ No certifications found.")
        suggestions.append("Add relevant certifications to strengthen your profile.")

    # Grammar check (POS balance)
    try:
        tokens = nltk.word_tokenize(text)
        tags = nltk.pos_tag(tokens)
        pos_counts = Counter(tag for word, tag in tags)
        if pos_counts['NN'] + pos_counts['NNS'] > 10:
            score += 5
            feedback.append("✅ Good use of nouns (likely indicating achievements/roles).")
        else:
            feedback.append("⚠️ Low noun usage — consider detailing roles/achievements more.")
            suggestions.append("Describe your roles and achievements using clear, strong nouns.")
    except Exception as e:
        feedback.append("⚠️ Could not analyze grammar due to an error.")
        suggestions.append("Ensure your resume text is clear and well-formatted.")

    # Action verbs check
    found_verbs = [verb for verb in action_verbs if verb in text_lower]
    if len(found_verbs) >= 3:
        score += 5
        feedback.append("✅ Good use of action verbs.")
    else:
        feedback.append("⚠️ Few action verbs detected.")
        suggestions.append("Use more action verbs to describe your achievements (e.g., managed, developed, improved).")

    # Formatting check (basic)
    if re.search(r'(curriculum vitae|resume)', text_lower):
        feedback.append("⚠️ Remove generic headers like 'Resume' or 'Curriculum Vitae'.")
        suggestions.append("Start your resume with your name, not with 'Resume' or 'Curriculum Vitae'.")

    final_score = min(score, 100)
    return final_score, feedback, suggestions

# --- Professional & Elegant UI ---

st.set_page_config(
    page_title="Resume Scorer AI",
    page_icon="📝",
    layout="centered"
)

st.markdown(
    """
    <style>
    html, body, [class*="css"]  {
        font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
        background-color: #f5f7fa;
    }
    .main-title {
        font-size:2.3rem !important;
        font-weight:700;
        color:#2d3a4a;
        letter-spacing: -1px;
        margin-bottom: 0.2em;
    }
    .subtitle {
        font-size:1.1rem !important;
        color:#4F8BF9;
        margin-bottom: 1.5rem;
    }
    .score-badge {
        display:inline-block;
        background:linear-gradient(90deg,#4F8BF9,#38B6FF);
        color:white;
        font-size:2rem;
        font-weight:700;
        border-radius:1.5rem;
        padding:0.5rem 2.5rem;
        margin:1rem 0;
        box-shadow:0 2px 8px rgba(79,139,249,0.10);
    }
    .feedback-section {
        background: #fff;
        border-radius: 1rem;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1.5rem;
        border: 1px solid #e3eafc;
        box-shadow: 0 1px 4px rgba(79,139,249,0.04);
    }
    .suggestion-section {
        background: #f9f6e7;
        border-radius: 1rem;
        padding: 1.2rem 1.5rem;
        border: 1px solid #ffe082;
        box-shadow: 0 1px 4px rgba(255,224,130,0.07);
    }
    .stButton>button {
        background: linear-gradient(90deg,#4F8BF9,#38B6FF);
        color: #fff;
        font-weight: 600;
        border-radius: 0.7rem;
        border: none;
        padding: 0.7rem 2.2rem;
        font-size: 1.1rem;
        margin-top: 0.7rem;
        margin-bottom: 0.7rem;
        transition: background 0.2s;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg,#38B6FF,#4F8BF9);
        color: #fff;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="main-title">📝 Resume Scorer AI</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Professional, AI-powered feedback for your resume</div>', unsafe_allow_html=True)

with st.expander("ℹ️ How does this work?", expanded=False):
    st.markdown(
        """
        - **Upload** your resume as PDF, DOCX, or TXT, or paste the text below.
        - **Enter your years of experience** for a personalized evaluation.
        - Click **Score My Resume** to get a detailed score, feedback, and improvement tips.
        - All processing is done locally—your data is never stored.
        """
    )

st.markdown("#### 1. Enter your details")

col1, col2 = st.columns([1, 2])
with col1:
    user_exp = st.number_input(
        "Years of Experience",
        min_value=0,
        max_value=50,
        step=1,
        help="Please enter your total professional experience in years."
    )
with col2:
    uploaded_file = st.file_uploader(
        "Upload Resume (.pdf, .docx, .txt)",
        type=['pdf', 'docx', 'txt'],
        help="Supported formats: PDF, Word, or plain text."
    )

st.markdown("#### 2. Or paste your resume text")
resume_text = st.text_area(
    "Resume Text",
    height=180,
    placeholder="Paste your resume content here if you don't want to upload a file.",
    label_visibility="collapsed"
)

if uploaded_file is not None:
    file_type = uploaded_file.type
    if file_type == "application/pdf":
        resume_text = extract_text_from_pdf(uploaded_file)
    elif file_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
        resume_text = extract_text_from_docx(uploaded_file)
    elif file_type == "text/plain":
        resume_text = uploaded_file.read().decode('utf-8')
    else:
        st.warning("Unsupported file type. Please upload PDF, DOCX, or TXT.")

score_btn = st.button("Score My Resume")

if score_btn:
    if resume_text.strip() == "":
        st.warning("Please paste text or upload a file!")
    else:
        score, feedback, suggestions = score_resume(resume_text, user_exp)
        st.markdown(
            f'<div class="score-badge">Score: {score} / 100</div>',
            unsafe_allow_html=True
        )
        st.markdown('<div class="feedback-section"><b>Feedback</b><ul>', unsafe_allow_html=True)
        for fb in feedback:
            st.markdown(f"<li>{fb}</li>", unsafe_allow_html=True)
        st.markdown('</ul></div>', unsafe_allow_html=True)
        if suggestions:
            st.markdown('<div class="suggestion-section"><b>Suggestions to Improve Your Score</b><ul>', unsafe_allow_html=True)
            for sug in suggestions:
                st.markdown(f"<li>{sug}</li>", unsafe_allow_html=True)
            st.markdown('</ul></div>', unsafe_allow_html=True)
        else:
            st.success("Your resume looks great! 🎉")

st.markdown(
    """
    <hr style="margin-top:2rem;margin-bottom:1rem;">
    <div style="text-align:center; color:#aaa; font-size:0.95rem;">
        Made with <span style="color:#e25555;">&#10084;</span> using Streamlit & AI
    </div>
    """,
    unsafe_allow_html=True
)
