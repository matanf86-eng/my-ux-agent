import streamlit as st
import os
from crewai import Agent, Task, Crew, Process
from langchain_anthropic import ChatAnthropic
from crewai_tools import SerperDevTool

# ====================================================
# הגדרת עיצוב הדף
# ====================================================
st.set_page_config(page_title="UX/AI News Generator", page_icon="🎨", layout="centered")
st.title("🎨 מחולל פוסטים + פרומפטים")
st.markdown("המערכת יוצרת פוסט ללינקדאין וגם מכינה לך פרומפט לתמונה (השתמש במפתחות מהכספת או הזן ידנית)")

# ====================================================
# פונקציה חכמה לטעינת מפתחות
# ====================================================
def load_api_key(key_name, user_input):
    if user_input and len(user_input) > 10:
        return user_input
    elif key_name in st.secrets:
        return st.secrets[key_name]
    return None

# ====================================================
# סרגל צד
# ====================================================
with st.sidebar:
    st.header("הגדרות")
    user_anthropic = st.text_input("Anthropic API Key", type="password", help="השאר ריק כדי להשתמש במפתח השמור במערכת")
    user_serper = st.text_input("Serper API Key", type="password", help="השאר ריק כדי להשתמש במפתח השמור במערכת")
    
    st.markdown("---")
    topic = st.text_input("נושא למחקר", "AI Agents in UX Design")
    language = st.selectbox("שפת הפוסט", ["Hebrew", "English"])

# ====================================================
# המנוע
# ====================================================
def run_crew(anthropic_key, serper_key):
    os.environ["ANTHROPIC_API_KEY"] = anthropic_key
    os.environ["SERPER_API_KEY"] = serper_key

    llm = ChatAnthropic(model="claude-3-haiku-20240307", temperature=0.7)
    search_tool = SerperDevTool()

    # סוכנים
    researcher = Agent(
        role='Senior UX/AI Researcher',
        goal=f'Find the latest news about {topic}',
        backstory="You are a trend hunter. You find the most impactful tech news.",
        tools=[search_tool],
        llm=llm,
        verbose=True
    )

    writer = Agent(
        role='Content Creator',
        goal=f'Write engaging LinkedIn posts in {language}',
        backstory=f"You are a top tech influencer. You write in natural {language}.",
        llm=llm,
        verbose=True
    )

    art_director = Agent(
        role='Creative Art Director',
        goal='Create detailed image prompts',
        backstory="You are an expert in Prompt Engineering.",
        llm=llm,
        verbose=True
    )

    # משימות
    task_research = Task(
        description=f"Find 1 interesting news item from the last 7 days regarding '{topic}'.",
        expected_output="A summary of the news item with source link.",
        agent=researcher
    )

    task_write = Task(
        description=f"Write a LinkedIn post in {language} based on the research. Keep it under 200 words.",
        expected_output=f"A full LinkedIn post in {language}.",
        agent=writer,
        context=[task_research]
    )

    task_prompt = Task(
        description="""
        1. Read the post created by the writer task (task_write).
        2. YOUR OUTPUT MUST START with the content of that post (in Hebrew/English as written).
        3. Then add a separator line (---).
        4. Then write the Image Prompt in English.
        """,
        expected_output="The original LinkedIn Post followed by the Image Prompt.",
        agent=art_director,
        context=
