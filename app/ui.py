"""Streamlit chat interface.

Run:  streamlit run app/ui.py
"""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # so `app.` imports work under streamlit
from app.agent import ask  # noqa: E402
from app.bootstrap import ensure_data  # noqa: E402
from app.config import settings  # noqa: E402

st.set_page_config(page_title="Football Analyst Agent", page_icon="⚽")


@st.cache_resource(show_spinner="First start: building the database and the search index (a few minutes)...")
def _prepare_data() -> bool:
    ensure_data()
    return True


_prepare_data()
st.title("⚽ Football Analyst Agent")
st.caption(f"150 years of international football · SQL + RAG agent · LLM: {settings.llm_provider}")

EXAMPLES = [
    "How many matches has Tunisia won, drawn and lost?",
    "Who are the top 5 scorers in FIFA World Cup matches?",
    "What was the Maracanazo?",
    "Who was the first African team to reach a World Cup semi-final, and what was their record in that tournament?",
]

if "history" not in st.session_state:
    st.session_state.history = []

with st.sidebar:
    st.subheader("Try an example")
    for ex in EXAMPLES:
        if st.button(ex, use_container_width=True):
            st.session_state.pending = ex

for turn in st.session_state.history:
    st.chat_message("user").write(turn["question"])
    with st.chat_message("assistant"):
        st.write(turn["answer"])
        with st.expander(f"How I answered · {len(turn['tool_calls'])} tool call(s) · {turn['latency_s']} s"):
            for call in turn["tool_calls"]:
                st.markdown(f"**{call['tool']}**")
                st.code(call["args"].get("sql") or call["args"].get("query", ""), language="sql" if "sql" in call["args"] else None)
                st.text(call["output"][:1500])

question = st.chat_input("Ask about international football...") or st.session_state.pop("pending", None)
if question:
    with st.spinner("Thinking..."):
        try:
            result = ask(question)
        except Exception as exc:  # show a readable error instead of a stack trace
            st.error(f"The agent failed: {exc}")
            st.stop()
    st.session_state.history.append({"question": question, **result})
    st.rerun()
