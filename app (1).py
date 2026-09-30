"""AI-Powered Study Buddy
Explain concepts, summarize notes, generate quizzes & flashcards with an LLM.
Run:  streamlit run app.py
"""
import json
import os
import re

import pandas as pd
import streamlit as st
from anthropic import Anthropic
from dotenv import load_dotenv
from pypdf import PdfReader

load_dotenv()

MODEL = os.getenv("MODEL_NAME", "claude-sonnet-5-5")
CHUNK_SIZE = 12000  # characters per chunk for long documents

st.set_page_config(page_title="AI Study Buddy", page_icon="📚", layout="wide")


# ---------- API client ----------
def get_api_key():
    # Streamlit Cloud secret first, then local .env / environment variable
    try:
        if "ANTHROPIC_API_KEY" in st.secrets:
            return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        pass
    return os.getenv("ANTHROPIC_API_KEY")


@st.cache_resource
def get_client(key):
    return Anthropic(api_key=key)


def ask_llm(system, user, max_tokens=1500):
    client = get_client(get_api_key())
    resp = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(b.text for b in resp.content if b.type == "text")


# ---------- Preprocessing ----------
def extract_text(uploaded):
    if uploaded is None:
        return ""
    if uploaded.name.lower().endswith(".pdf"):
        reader = PdfReader(uploaded)
        return "\n".join((p.extract_text() or "") for p in reader.pages)
    return uploaded.read().decode("utf-8", errors="ignore")


def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()


def chunk_text(text, size=CHUNK_SIZE):
    return [text[i:i + size] for i in range(0, len(text), size)]


# ---------- Prompt builders ----------
def explain(topic, level):
    system = (
        "You are a friendly tutor. Explain concepts clearly, with a simple "
        "example and an analogy. Use short paragraphs."
    )
    return ask_llm(system, f"Explain this at {level} level:\n\n{topic}")


def summarize(text):
    system = (
        "You summarize study notes into: Key Points, Definitions, Formulas "
        "(if any) and Quick Revision bullets. Be concise and accurate."
    )
    chunks = chunk_text(text)
    partials = [ask_llm(system, f"Summarize these notes:\n\n{c}") for c in chunks]
    if len(partials) == 1:
        return partials[0]
    combined = "\n\n".join(partials)
    return ask_llm(system, f"Merge these partial summaries into one:\n\n{combined}", 2000)


def parse_json(raw):
    raw = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    return json.loads(raw)


def make_quiz(text, level, n):
    system = "You write exam-quality multiple-choice questions. Reply with JSON only."
    prompt = (
        f"Create {n} {level}-level MCQs from the material below.\n"
        'Return ONLY a JSON list like: [{"question": "...", '
        '"options": ["A","B","C","D"], "answer_index": 0, '
        '"explanation": "..."}]\n\n'
        f"Material:\n{text[:CHUNK_SIZE]}"
    )
    data = parse_json(ask_llm(system, prompt, 3000))
    # validate
    good = []
    for q in data:
        if (
            isinstance(q.get("options"), list)
            and len(q["options"]) >= 2
            and isinstance(q.get("answer_index"), int)
            and 0 <= q["answer_index"] < len(q["options"])
        ):
            good.append(q)
    if not good:
        raise ValueError("Model returned no valid questions")
    return good


def make_flashcards(text, n):
    system = "You create concise study flashcards. Reply with JSON only."
    prompt = (
        f"Create {n} flashcards from the material below.\n"
        'Return ONLY a JSON list like: [{"question": "...", "answer": "..."}]\n\n'
        f"Material:\n{text[:CHUNK_SIZE]}"
    )
    data = parse_json(ask_llm(system, prompt, 2500))
    return [c for c in data if "question" in c and "answer" in c]


# ---------- UI ----------
st.title("📚 AI-Powered Study Buddy")
st.caption("Explain concepts • Summarize notes • Quizzes • Flashcards")

if not get_api_key():
    st.error("No API key found. Add ANTHROPIC_API_KEY to your .env file or Streamlit secrets.")
    st.stop()

with st.sidebar:
    st.header("Settings")
    task = st.radio("Task", ["Explain", "Summarize", "Quiz", "Flashcards"])
    level = st.selectbox("Level", ["Beginner", "Intermediate", "Advanced"])
    n_items = st.slider("Number of questions / cards", 3, 15, 5) if task in ("Quiz", "Flashcards") else 5

col_in, col_out = st.columns(2)

with col_in:
    st.subheader("Input")
    typed = st.text_area("Type a topic/question or paste your notes", height=220)
    uploaded = st.file_uploader("...or upload a PDF / TXT file", type=["pdf", "txt"])
    go = st.button(f"Run: {task}", type="primary")

with col_out:
    st.subheader("Output")

    if go:
        material = clean_text(typed + " " + extract_text(uploaded))
        if not material:
            st.warning("Please type something or upload a file.")
        else:
            try:
                with st.spinner("Thinking..."):
                    if task == "Explain":
                        st.session_state.result = ("text", explain(material[:CHUNK_SIZE], level))
                    elif task == "Summarize":
                        st.session_state.result = ("text", summarize(material))
                    elif task == "Quiz":
                        st.session_state.result = ("quiz", make_quiz(material, level, n_items))
                        st.session_state.submitted = False
                    else:
                        st.session_state.result = ("cards", make_flashcards(material, n_items))
            except Exception as e:
                st.session_state.result = None
                st.error(f"Something went wrong: {e}")

    result = st.session_state.get("result")
    if result:
        kind, data = result

        if kind == "text":
            st.markdown(data)

        elif kind == "quiz":
            answers = {}
            for i, q in enumerate(data):
                answers[i] = st.radio(
                    f"Q{i + 1}. {q['question']}",
                    q["options"],
                    index=None,
                    key=f"q{i}",
                )
            if st.button("Submit answers"):
                st.session_state.submitted = True
            if st.session_state.get("submitted"):
                score = 0
                for i, q in enumerate(data):
                    correct = q["options"][q["answer_index"]]
                    if answers[i] == correct:
                        score += 1
                        st.success(f"Q{i + 1}: Correct")
                    else:
                        st.error(f"Q{i + 1}: Wrong. Correct answer: {correct}")
                    st.caption(q.get("explanation", ""))
                st.subheader(f"Score: {score} / {len(data)}")

        elif kind == "cards":
            for i, c in enumerate(data, 1):
                with st.expander(f"Card {i}: {c['question']}"):
                    st.write(c["answer"])
            csv = pd.DataFrame(data).to_csv(index=False).encode("utf-8")
            st.download_button("Download flashcards (CSV)", csv, "flashcards.csv", "text/csv")
