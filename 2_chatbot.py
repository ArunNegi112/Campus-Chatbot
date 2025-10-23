import streamlit as st
import os
from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from typing_extensions import TypedDict, Annotated

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="USAR Campus Chatbot",
    page_icon="🎓",
    layout="centered"
)

# Custom CSS for soothing and simplistic UI
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .main-header {
        font-size: 2.8rem;
        font-weight: 600;
        text-align: center;
        color: #2c3e50;
        margin-top: 1rem;
        margin-bottom: 0.3rem;
    }
    .sub-header {
        text-align: center;
        color: #7f8c8d;
        font-size: 1.1rem;
        margin-bottom: 2.5rem;
    }
    .stTextInput > div > div > input {
        border: 2px solid #3498db;
        border-radius: 10px;
        padding: 12px;
        font-size: 1rem;
    }
    .stButton > button {
        background-color: #3498db;
        color: white;
        border-radius: 10px;
        padding: 0.6rem 2rem;
        font-size: 1.1rem;
        border: none;
        width: 100%;
        transition: background-color 0.3s;
    }
    .stButton > button:hover {
        background-color: #2980b9;
    }
    .answer-box {
        background-color: #e8f4f8;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 5px solid #3498db;
        margin-top: 1.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .error-box {
        background-color: #fadbd8;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 5px solid #e74c3c;
        margin-top: 1.5rem;
    }
    .error-title {
        color: #c0392b;
        font-weight: bold;
        font-size: 1.1rem;
        margin-bottom: 0.5rem;
    }
    .error-message {
        color: #e74c3c;
        font-size: 1rem;
        margin-bottom: 0.5rem;
    }
    .error-code {
        background-color: #fff;
        padding: 0.5rem;
        border-radius: 5px;
        font-family: monospace;
        font-size: 0.9rem;
        color: #666;
        margin-top: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# State definitions
class State(TypedDict):
    question: str
    query: str
    result: str
    answer: str

class QueryOutput(TypedDict):
    query: Annotated[str, "Syntactically Valid SQL query"]

# Database connection with detailed error handling
@st.cache_resource
def get_database():
    try:
        password = os.getenv("DB_PASSWORD")
        if not password:
            return None, "DATABASE_PASSWORD_MISSING"
        db = SQLDatabase.from_uri(
            f"mysql+mysqlconnector://root:{password}@localhost/campus_schedule"
        )
        return db, None
    except Exception as e:
        return None, str(e)

# Initialize models with error handling
@st.cache_resource
def get_models():
    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return None, None, "GOOGLE_API_KEY_MISSING"
        query_model = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0)
        reply_model = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0.3)
        return query_model, reply_model, None
    except Exception as e:
        return None, None, str(e)

# Prompt templates
query_system_message = """
You are an AI assistant for Campus Chatbot. 
Your role is to convert natural language questions about classrooms, schedules, and resources into SQL queries.
Use the following table schema to guide your query construction:

{table_info}

Information of subjects: subject_code subject_name 
BS201 Linear Algebra and Numerical methods
ARI203 Artificial Intelligence and Its Applications 
ARI205 Computer Networks
ARI207 Analog Electronics
ARI209 Mechatronic Systems and Applications
HSAR211 Engineering Economics
ARI251 Artificial Intelligence Lab
ARI253 Electronics Lab
ARI255 Mechatronic Systems and Applications Lab
ARI257 Computer Networks Lab

Information of teachers: Teacher_name, subject
Hariya Ms. Teena: Engineering Economics 
Dr. Jyoti: Linear Algebra and Numerical methods
Tyagi Ms. Himani: Artificial Intelligence and Its Applications
Kumar Dr. Ashok: Computer Networks Lab
Arya Dr. Rajendra: Mechatronic Systems and Applications Lab
Hariya Ms. Teena: Engineering Economics
Batra Prof. Kriti: Analog Electronics
Bhatia Dr. Anshul: Computer Networks 

Instructions:
- Only output the SQL query, no extra text.
- Ensure it is valid SQL for MySQL.
- Do not assume columns not listed in the schema.
- Use proper formatting and quotes where necessary.
- The user may have typo in input question, fix that and then generate best query

Examples: 
1.  "question": "which teacher teaches mechatronics", 
    "query": "SELECT DISTINCT teacher_name FROM rooms_schedule WHERE subject_name LIKE '%Mechatronic%'"
"""

reply_system_message = """You are an AI assistant being used in college campus to help students in getting information about their schedules, rooms, resources and teachers etc..."""

reply_user_message = """
Given the user's question, a previous model has generated an SQL query.
Use the result of that query to answer the original question clearly.

User's original question: {user_question}
LLM generated SQL query: {query}
Result of that query: {result}
"""

# Core functions
def write_query(state: State, db, query_model):
    query_prompt_template = ChatPromptTemplate([
        ('system', query_system_message),
        ('user', "Question: {input}")
    ])
    
    prompt = query_prompt_template.invoke({
        'table_info': db.table_info,
        'input': state['question']
    })
    
    structured_output_model = query_model.with_structured_output(QueryOutput)
    query_output = structured_output_model.invoke(prompt)
    
    return {'query': query_output['query']}

def execute_query(state: State, db):
    try:
        execute_query_tool = QuerySQLDataBaseTool(db=db)
        result = execute_query_tool.invoke(state['query'])
        return {'result': result}
    except Exception as e:
        return {'result': f"Error executing query: {str(e)}"}

def generate_answer(state: State, reply_model):
    reply_prompt_template = ChatPromptTemplate([
        ('system', reply_system_message),
        ('user', reply_user_message)
    ])
    
    prompt = reply_prompt_template.invoke({
        'user_question': state['question'],
        'query': state['query'],
        'result': state['result']
    })
    
    response = reply_model.invoke(prompt)
    return {'answer': response.content}

def display_user_friendly_error(error_type, error_details):
    """Display errors in a user-friendly way with admin-friendly error codes"""
    st.markdown('<div class="error-box">', unsafe_allow_html=True)
    st.markdown('<div class="error-title">⚠️ Something went wrong</div>', unsafe_allow_html=True)
    
    if error_type == "DATABASE_PASSWORD_MISSING":
        st.markdown('<div class="error-message">The database password is not configured properly.</div>', unsafe_allow_html=True)
        st.markdown('<div style="color: #7f8c8d; margin-top: 0.5rem;">📋 <b>Please tell the admin:</b> "The DB_PASSWORD is missing in the environment file"</div>', unsafe_allow_html=True)
        st.markdown('<div class="error-code">Error Code: DB_001</div>', unsafe_allow_html=True)
    
    elif error_type == "GOOGLE_API_KEY_MISSING":
        st.markdown('<div class="error-message">The AI service is not configured properly.</div>', unsafe_allow_html=True)
        st.markdown('<div style="color: #7f8c8d; margin-top: 0.5rem;">📋 <b>Please tell the admin:</b> "The GOOGLE_API_KEY is missing in the environment file"</div>', unsafe_allow_html=True)
        st.markdown('<div class="error-code">Error Code: API_001</div>', unsafe_allow_html=True)
    
    elif "connection" in error_details.lower() or "connect" in error_details.lower():
        st.markdown('<div class="error-message">Unable to connect to the campus database.</div>', unsafe_allow_html=True)
        st.markdown('<div style="color: #7f8c8d; margin-top: 0.5rem;">📋 <b>Please tell the admin:</b> "Database connection failed - check if MySQL is running"</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="error-code">Error Code: DB_002<br>Technical details: {error_details}</div>', unsafe_allow_html=True)
    
    elif "api" in error_details.lower() or "quota" in error_details.lower():
        st.markdown('<div class="error-message">The AI service is temporarily unavailable.</div>', unsafe_allow_html=True)
        st.markdown('<div style="color: #7f8c8d; margin-top: 0.5rem;">📋 <b>Please tell the admin:</b> "Google API error - may need to check API key or quota"</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="error-code">Error Code: API_002<br>Technical details: {error_details}</div>', unsafe_allow_html=True)
    
    else:
        st.markdown('<div class="error-message">An unexpected error occurred while processing your question.</div>', unsafe_allow_html=True)
        st.markdown('<div style="color: #7f8c8d; margin-top: 0.5rem;">📋 <b>Please tell the admin:</b> "General application error - check logs"</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="error-code">Error Code: GEN_001<br>Technical details: {error_details}</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def main():
    # Header
    st.markdown('<div class="main-header">🎓 USAR Campus Chatbot</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Ask questions about schedules, rooms, teachers, and resources</div>', unsafe_allow_html=True)
    
    # Initialize database and models
    db, db_error = get_database()
    query_model, reply_model, model_error = get_models()
    
    # Check for initialization errors
    if db_error:
        display_user_friendly_error("DATABASE_ERROR" if db_error != "DATABASE_PASSWORD_MISSING" else db_error, db_error)
        st.stop()
    
    if model_error:
        display_user_friendly_error("MODEL_ERROR" if model_error != "GOOGLE_API_KEY_MISSING" else model_error, model_error)
        st.stop()
    
    # Add some spacing
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Input field
    question = st.text_input(
        "Your Question:",
        placeholder="e.g., When is the next Mechatronics lab?",
        label_visibility="collapsed",
        key="question_input"
    )
    
    # Submit button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        submit_button = st.button("🔍 Ask Question")
    
    # Process question
    if submit_button and question:
        try:
            # Initialize state
            state = {
                'question': question,
                'query': '',
                'result': '',
                'answer': ''
            }
            
            # Step 1: Generate SQL query
            with st.spinner("🤔 Understanding your question..."):
                state.update(write_query(state, db, query_model))
            
            # Step 2: Execute query
            with st.spinner("📚 Searching campus database..."):
                state.update(execute_query(state, db))
            
            # Step 3: Generate natural language answer
            with st.spinner("✍️ Preparing your answer..."):
                state.update(generate_answer(state, reply_model))
            
            # Display answer
            st.markdown('<div class="answer-box">', unsafe_allow_html=True)
            st.markdown(f"### 💡 Answer")
            st.markdown(state['answer'])
            st.markdown('</div>', unsafe_allow_html=True)
            
        except Exception as e:
            error_msg = str(e)
            display_user_friendly_error("PROCESSING_ERROR", error_msg)
    
    elif submit_button and not question:
        st.warning("⚠️ Please enter a question before clicking 'Ask Question'")

if __name__ == "__main__":
    main()