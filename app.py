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
# פונקציה חכמה לטעינת מפתחות (מהכספת או מהמשתמש)
# ====================================================
def load_api_key(key_name, user_input):
    # 1. אם המשתמש הזין ידנית - קח את זה
    if user_input and len(user_input) > 10:
        return user_input
    # 2. אחרת, נסה למשוך מהכספת הסודית
    elif key_name in st.secrets:
        return st.secrets[key_name]
    # 3. אם אין כלום - תחזיר כלום
    return None

# ====================================================
# סרגל צד
# ====================================================
with st.sidebar:
    st.header("הגדרות")
    
    # שדות קלט (משאירים ריק כדי להשתמש בכספת)
    user_anthropic = st.text_input("Anthropic API Key", type="password", help="השאר ריק כדי להשתמש במפתח השמור במערכת")
    user_serper = st.text_input("Serper API Key", type="password", help="השאר ריק כדי להשתמש במפתח השמור במערכת")
    
    st.markdown("---")
    topic = st.text_input("נושא למחקר", "AI Agents in UX Design")
    language = st.selectbox("שפת הפוסט", ["Hebrew", "English"])

# ====================================================
# המנוע
# ====================================================
def run_crew(anthropic_key, serper_key):
    # הזנת המפתחות למערכת ההפעלה
    os.environ["ANTHROPIC_API_KEY"] = anthropic_key
    os.environ["SERPER_API_KEY"] = serper_key

    # הגדרת המודל
    llm = ChatAnthropic(model="claude-3-haiku-20240307", temperature=0.7)
    
    # כלים
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
        1. קרא את הפוסט שהכין הכותב (task_write).
        2. העתק את הפוסט המקורי (בעברית) כמו שהוא להודעה הסופית.
        3. רד שורה והוסף קו מפריד (---).
        4. כתוב מתחתיו את ה-Image Prompt באנגלית.
        """,
        expected_output="הפוסט המלא בעברית, ואחריו ה-Image Prompt באנגלית.",
        agent=art_director,
        context=[task_write]
    )
    )

    crew = Crew(
        agents=[researcher, writer, art_director],
        tasks=[task_research, task_write, task_prompt],
        process=Process.sequential
    )
    
    return crew.kickoff()

# ====================================================
# כפתור ההפעלה
# ====================================================
if st.button("🚀 צור פוסט + פרומפט"):
    # 1. ניסיון לטעון מפתחות
    final_anthropic = load_api_key("ANTHROPIC_API_KEY", user_anthropic)
    final_serper = load_api_key("SERPER_API_KEY", user_serper)

    # 2. בדיקה שיש לנו הכל
    if not final_anthropic or not final_serper:
        st.error("⚠️ לא נמצאו מפתחות! נא להזין בסרגל הצד או להגדיר ב-Secrets.")
    else:
        with st.spinner('הצוות עובד... (זה לוקח דקה)'):
            try:
                result = run_crew(final_anthropic, final_serper)
                st.success("התהליך הסתיים!")
                st.markdown("### 📝 תוצאה:")
                st.markdown(result)
            except Exception as e:
                st.error(f"שגיאה: {e}")
