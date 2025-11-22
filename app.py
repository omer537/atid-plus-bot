import streamlit as st
import google.generativeai as genai

# --- הגדרות דף ---
st.set_page_config(page_title="עתיד + | מערכת תכנון שיעור", page_icon="🟢🔵", layout="centered")

# !!! שים כאן את המפתח שלך !!!
GOOGLE_API_KEY = "AIzaSyC_k0wykusqS8mXPwBg4xd2FcZno5S5Ci0"

MAX_QUESTIONS = 5

# --- הגדרת האייקונים (הנקודות) ---
bot_avatar = "🟢"  # נקודה ירוקה לבוט
user_avatar = "🔵"  # נקודה כחולה למורה

# --- עיצוב CSS נקי ומותאם ---
st.markdown("""
<style>
    /* פונטים ויישור לימין לכל הדף */
    html, body, [class*="css"] {
        font-family: 'Segoe UI', Helvetica, Arial, sans-serif;
    }
    .stChatMessage, .stMarkdown, p, div, input, h1, h2, h3, h4 {
        direction: rtl;
        text-align: right;
    }

    /* עיצוב בועת המורה (משתמש) */
    .stChatMessage.user {
        flex-direction: row-reverse;
        background-color: #e3f2fd; /* כחול בהיר מאוד */
        border-radius: 15px;
        border: 1px solid #bbdefb;
    }

    /* עיצוב בועת הבוט (עתיד+) */
    .stChatMessage.assistant {
        background-color: #f1f8e9; /* ירוק בהיר מאוד/לבן */
        border-radius: 15px;
        border: 1px solid #dcedc8;
    }

    /* כותרת ממותגת */
    .branding-header {
        color: #1a237e; /* כחול כהה */
        font-weight: bold;
        font-size: 3rem;
        margin-bottom: 0;
        text-align: center;
        text-shadow: 1px 1px 2px #ccc;
    }
    .branding-sub {
        color: #2e7d32; /* ירוק */
        font-size: 1.3rem;
        text-align: center;
        margin-top: -10px;
        margin-bottom: 30px;
        font-weight: 500;
    }

    /* הסתרת אלמנטים טכניים של המערכת */
    .stDeployButton {display:none;}
    header {visibility: hidden;}
    p { margin-bottom: 0.8rem; line-height: 1.6; }
</style>
""", unsafe_allow_html=True)

if GOOGLE_API_KEY != "YOUR_API_KEY_HERE":
    genai.configure(api_key=GOOGLE_API_KEY)
    model_pro = genai.GenerativeModel('gemini-2.5-pro')
    model_flash = genai.GenerativeModel('gemini-2.5-flash')

# --- זיכרון (Session State) ---
if "stage" not in st.session_state:
    st.session_state.stage = "setup_name"
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "אהלן. ברוך הבא למערכת התכנון של עתיד+. איך קוראים לך?"}]
if "teacher_data" not in st.session_state:
    st.session_state.teacher_data = {"name": "", "location": "", "topic": "", "preferences": ""}
if "lesson_plan_text" not in st.session_state:
    st.session_state.lesson_plan_text = ""
if "question_count" not in st.session_state:
    st.session_state.question_count = 0

# --- הנחיות למודל (PROMPTS) ---

LESSON_FORMAT_PROMPT = """
אתה המומחה הפדגוגי של חברת "עתיד +".
המטרה: יצירת מערך שיעור מותאם אישית, עמוק ופרקטי.

**הנחיות "עשה ואל תעשה":**
1. **בלי כותרות פתיחה:** אל תכתוב "מגיש:...", התחל ישר מהתוכן.
2. **מבנה גמיש:** בחר את הסדר הכי נכון לנושא, אבל כלול את כל 9 המרכיבים.

**9 מרכיבי החובה:**
1. **המנוע המתמטי:** הסבר לוגי של המנגנון לפני הנוסחאות.
2. **החיבור למציאות:** דוגמה מודרנית אחת (טכנולוגיה/חברה).
3. **בגרות:** מספרי שאלונים וטיפ טקטי.
4. **הנרטיב (מהלך השיעור):** תיאור מהלך ההוראה (פתיחה -> מודלינג -> תרגול).
5. **ידע קודם:** מה נדרש ולמה.
6. **למצטיינים:** אתגר חשיבה או הרחבה אקדמית.
7. **המוקשים:** איפה התלמידים נופלים (Conceptual Pitfall).
8. **הפתרון למוקש:** איך מסבירים את זה נכון.
9. **השואו (פתיחה):** פתיחה חזקה עם לוח וטוש בלבד.

**התאמה אישית:**
התאם את המערך לדגשים המיוחדים שהמורה סיפק ({preferences}).

**סגנון:**
* Markdown לכותרות.
* שפה מקצועית ובגובה העיניים.

אל תענה על שאלה 10.
"""

SIMULATION_INSTRUCTIONS = f"""
אתה עמית מצוות "עתיד +" שמבצע וידוא מוכנות פדגוגי.
המטרה: לוודא שליטה במערך ובאסטרטגיה.

**הנחיות:**
1. **בלי חישובים:** אסור לשאול שאלות מתמטיות חישוביות.
2. **מיקוד פדגוגי:** שאל על הדוגמאות, המוקשים, והאנלוגיות שבמערך.
3. **כמות:** {MAX_QUESTIONS} שאלות סה"כ.
4. **סוג:** שאלות אמריקאיות קצרות.
"""


def check_user_intent_with_ai(user_text):
    if GOOGLE_API_KEY == "YOUR_API_KEY_HERE":
        return False
    prompt = f"""
    המשתמש הגיב למערך שיעור. תגובתו: "{user_text}".
    האם זה אישור (רוצה להתקדם)? ענה "APPROVE".
    האם זו בקשת תיקון/שינוי? ענה "REVISE".
    """
    try:
        response = model_flash.generate_content(prompt).text
        return "APPROVE" in response.strip().upper()
    except:
        return False


def generate_response(prompt, context="", use_fast_model=False):
    if GOOGLE_API_KEY == "YOUR_API_KEY_HERE":
        return "חסר מפתח API בקוד."

    active_model = model_flash if use_fast_model else model_pro

    # הזרקת העדפות המורה לפרומפט
    prefs = st.session_state.teacher_data.get("preferences", "")
    current_prompt = SIMULATION_INSTRUCTIONS if use_fast_model else LESSON_FORMAT_PROMPT.replace("{preferences}", prefs)

    history = [{"role": "user", "parts": [current_prompt]}]
    if context:
        history.append({"role": "user", "parts": [f"המסמך הנוכחי:\n{context}"]})

    if use_fast_model:
        recent_msgs = st.session_state.messages[-8:]
        for msg in recent_msgs:
            role = "user" if msg["role"] == "user" else "model"
            history.append({"role": role, "parts": [msg["content"]]})

    try:
        response = active_model.generate_content(history + [{"role": "user", "parts": [prompt]}])
        return response.text
    except Exception as e:
        return f"שגיאה: {str(e)}"


# --- UI (ממשק משתמש) ---

# כותרת ממותגת (טקסט מעוצב במקום תמונה)
st.markdown('<div class="branding-header">עתיד +</div>', unsafe_allow_html=True)
st.markdown('<div class="branding-sub">חינוך פורץ דרך</div>', unsafe_allow_html=True)
st.markdown("---")

# לולאת ההודעות עם האייקונים החדשים (🟢 / 🔵)
for msg in st.session_state.messages:
    current_avatar = bot_avatar if msg["role"] == "assistant" else user_avatar

    with st.chat_message(msg["role"], avatar=current_avatar):
        st.markdown(msg["content"])

# קלט
if user_input := st.chat_input("הקלד כאן..."):
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user", avatar=user_avatar):
        st.markdown(user_input)

    response_text = ""

    # --- לוגיקה ---

    if st.session_state.stage == "setup_name":
        st.session_state.teacher_data["name"] = user_input
        response_text = f"היי {user_input}, כיף שאתה איתנו. איפה אתה מלמד?"
        st.session_state.stage = "setup_location"

    elif st.session_state.stage == "setup_location":
        st.session_state.teacher_data["location"] = user_input
        response_text = "מעולה. על איזה נושא אנחנו בונים את השיעור היום?"
        st.session_state.stage = "setup_topic"

    elif st.session_state.stage == "setup_topic":
        st.session_state.teacher_data["topic"] = user_input
        response_text = "**מצוין.** לפני שאני בונה את המערך, האם יש לך דגשים מיוחדים?\n(למשל: כיתה מתקשה, קבוצה קטנה, דגש על חקר...)\nאם אין, פשוט כתוב 'אין'."
        st.session_state.stage = "planning"

    elif st.session_state.stage == "planning":
        st.session_state.teacher_data["preferences"] = user_input
        topic = st.session_state.teacher_data["topic"]

        with st.spinner("משקלל את הדגשים שלך ובונה מערך..."):
            full_request = f"הנושא: {topic}. דגשים מיוחדים: {user_input}. בנה את המערך המלא."
            ai_response = generate_response(full_request, use_fast_model=False)
            st.session_state.lesson_plan_text = ai_response
            response_text = ai_response + "\n\n---\n**איך יצא?** תרצה שנתקן משהו או שאפשר להתקדם?"
            st.session_state.stage = "approval"

    elif st.session_state.stage == "approval":
        is_approved = check_user_intent_with_ai(user_input)

        if is_approved:
            st.session_state.stage = "simulation_active"
            st.session_state.question_count = 1
            with st.spinner("סבבה, בוא נעשה בדיקה זריזה..."):
                q1 = generate_response(f"תתחיל את הסימולציה הפדגוגית. הצג שאלה 1 מתוך {MAX_QUESTIONS}.",
                                       context=st.session_state.lesson_plan_text, use_fast_model=True)
                response_text = f"**בדיקת מוכנות פדגוגית ({MAX_QUESTIONS} שאלות)**\n\n" + q1
        else:
            with st.spinner("אין בעיה, משפרים..."):
                ai_response = generate_response(f"הערת המשתמש: {user_input}. ערוך מחדש את המערך.",
                                                context=st.session_state.lesson_plan_text, use_fast_model=False)
                st.session_state.lesson_plan_text = ai_response
                response_text = ai_response + "\n\n**איך הגרסה הזו?**"

    elif st.session_state.stage == "simulation_active":
        if st.session_state.question_count < MAX_QUESTIONS:
            st.session_state.question_count += 1
            q_num = st.session_state.question_count
            with st.spinner("בודק..."):
                response_text = generate_response(f"תשובה: '{user_input}'. משוב קצר ושאלה פדגוגית {q_num}.",
                                                  context=st.session_state.lesson_plan_text, use_fast_model=True)
        else:
            with st.spinner("מסכם..."):
                feedback = generate_response(f"תשובה אחרונה: '{user_input}'. סיכום קצר.",
                                             context=st.session_state.lesson_plan_text, use_fast_model=True)
                response_text = feedback + "\n\n**סיימנו.**\nשאלה אחרונה: מה היעד האישי שלך לשיעור הזה?"
                st.session_state.stage = "final_question"

    elif st.session_state.stage == "final_question":
        final_doc = st.session_state.lesson_plan_text + f"\n\n**10. יעד אישי:**\n{user_input}"
        response_text = "התיעוד נשלח אליך למייל. המון בהצלחה! 🚀"
        st.balloons()
        st.session_state.stage = "finished"

    st.session_state.messages.append({"role": "assistant", "content": response_text})
    with st.chat_message("assistant", avatar=current_avatar):
        st.markdown(response_text)