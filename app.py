import streamlit as st
import os
from crewai import Agent, Task, Crew, Process
from langchain_anthropic import ChatAnthropic
from crewai_tools import SerperDevTool

# ====================================================
# הגדרת הכותרת והעיצוב
# ====================================================
st.set_page_config(page_title="UX/AI News Generator", page_icon="🎨", layout="centered")
st.title("🎨 מחולל פוסטים + פרומפטים")
st.markdown("המערכת יוצרת פוסט ללינקדאין וגם מכינה לך פרומפט לתמונה בחינם")

# ====================================================
# סרגל צד להגדרות
# ====================================================
with st.sidebar:
    st.header("הגדרות")
    # שדות להזנת מפתחות
    anthropic_key = st.text_input("Anthropic API Key", type="password", value="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")
    serper_key = st.text_input("Serper API Key", type="password", value="ה27524dc96669fdd53f6eb3e634267f94c2d759ed")
    
    st.markdown("---")
    topic = st.text_input("נושא למחקר", "AI Agents in UX Design")
    language = st.selectbox("שפת הפוסט", ["Hebrew", "English"])

# ====================================================
# פונקציית המנוע
# ====================================================
def run_crew():
    # 1. הזנת מפתחות
    os.environ["ANTHROPIC_API_KEY"] = anthropic_key
    os.environ["SERPER_API_KEY"] = serper_key

    # 2. הגדרת המודל (Haiku - מהיר וזול)
    # אם שילמת ל-Anthropic, אפשר לשנות ל- sonnet או opus
    llm = ChatAnthropic(model="claude-3-haiku-20240307", temperature=0.7)
    
    # 3. כלים
    search_tool = SerperDevTool()

    # --- סוכן 1: חוקר ---
    researcher = Agent(
        role='Senior UX/AI Researcher',
        goal=f'Find the latest news about {topic}',
        backstory="You are a trend hunter. You find the most impactful tech news.",
        tools=[search_tool],
        llm=llm,
        verbose=True
    )

    # --- סוכן 2: כותב ---
    writer = Agent(
        role='Content Creator',
        goal=f'Write engaging LinkedIn posts in {language}',
        backstory=f"You are a top tech influencer. You write in natural {language}.",
        llm=llm,
        verbose=True
    )

    # --- סוכן 3: ארט דירקטור (ללא כלי ציור, רק מוח) ---
    art_director = Agent(
        role='Creative Art Director',
        goal='Create detailed image prompts for Generative AI',
        backstory="You are an expert in Prompt Engineering. You know how to describe abstract tech concepts for tools like Midjourney, DALL-E, and Gemini.",
        llm=llm,
        verbose=True
    )

    # 4. משימות
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

    # המשימה החדשה: רק לכתוב את הפרומפט, לא לייצר תמונה
    task_prompt = Task(
        description="""
        1. Read the LinkedIn post created by the writer.
        2. Create a creative, high-quality image prompt (in English) that visualizes this topic.
        3. The style should be: "Modern, flat vector art, isometric style, tech colors (blue, purple, white)".
        4. FINAL OUTPUT FORMAT:
           Please output the LinkedIn Post FIRST, then add a separator line, and then the Image Prompt.
        """,
        expected_output="The LinkedIn Post followed by the Image Prompt.",
        agent=art_director,
        context=[task_write]
    )

    # 5. הרצה
    crew = Crew(
        agents=[researcher, writer, art_director],
        tasks=[task_research, task_write, task_prompt],
        process=Process.sequential
    )
    
    return crew.kickoff()

# ====================================================
# ממשק המשתמש
# ====================================================
if st.button("🚀 צור פוסט + פרומפט"):
    if "sk-" not in anthropic_key: # בדיקה פשוטה
        st.error("נא להזין מפתחות API תקינים בסרגל הצד")
    else:
        with st.spinner('הצוות עובד: חוקר -> כותב -> מנסח פרומפט לתמונה...'):
            try:
                result = run_crew()
                st.success("התהליך הסתיים!")
                
                # הצגת התוצאה
                st.markdown("### 📝 הפוסט והפרומפט שלך:")
                st.markdown(result)
                
                st.info("💡 טיפ: העתק את הטקסט באנגלית (הפרומפט) והדבק אותו בצ'אט של Gemini כדי לקבל תמונה.")
            except Exception as e:
                st.error(f"שגיאה: {e}")