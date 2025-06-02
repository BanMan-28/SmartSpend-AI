import streamlit as st
import sqlite3
import hashlib
from datetime import datetime, timedelta
import re
from langchain.schema import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
import json
from langchain.prompts import (
    PromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate,
)

from langchain_core.output_parsers import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough

from rich.console import Console
from rich.markdown import Markdown

# Constants
API_KEY = "Your Gemini flash API  Key "
DB_FILE = "spending_tracker.db"

# Initialize chat model
chat_model = ChatGoogleGenerativeAI(
    api_key=API_KEY, model="gemini-1.5-flash", temperature=0.6
)
console = Console()

conversation = []

# Updated System Message
SYSTEM_MESSAGE = """You are SmartSpend AI, a friendly and helpful chatbot designed to assist users with a variety of queries, 
    while specializing in financial analysis for students. You are conversational, approachable, 
    and can respond to both general and finance-related topics.

    When engaging with users, keep the following in mind:
    
    Do not provide any information other than financial analysis and general finance realted questions of students.
    
    You can also do general chatting related to finance
    
    If you are asked any questions other than your field just say - "I don't Know" politely.
    
    Do not give any placeholders for links and other thing
    
    Do not give a budget in the chat answer until it is not asked specifically. 

    1. **General Queries:**
       - Respond warmly to greetings like "Hey" or "Hello"
       - Provide thoughtful, positive, and conversational responses
       - If unsure about intent, politely ask for clarification

    2. **Financial Analysis:**
       - Categorize spending into:
         - Essential Expenses (rent, utilities, groceries)
         - Educational Expenses (tuition, books, supplies)
         - Discretionary Expenses (dining, entertainment)
         - Savings
       - Provide actionable insights and budgeting advice
       - Use the 50/30/20 Rule framework

    3. **Response Format:**
       - Use friendly, conversational tone
       - Structure with markdown headings
       - Include bullet points for clarity
       - Add tables for data analysis when relevant

    4. **Conversation Flow:**
       - Maintain context from previous messages
       - Reference past information when relevant
       - Ask follow-up questions when needed
       **context**:{context}
       **question**:{question}
       
       tier1_cities = [
    "Mumbai", "Delhi", "Bengaluru", "Chennai", "Kolkata",
    "Hyderabad", "Pune", "Ahmedabad", "Gurugram", "Noida"
]

tier2_cities = [
    "Jaipur", "Lucknow", "Chandigarh", "Indore", "Kochi",
    "Nagpur", "Coimbatore", "Bhubaneswar", "Vadodara", "Visakhapatnam"
]

If the user asks the expenses planner specifying the city:
- If it exists in tier1_cities, give the budget plan according to a tier 1 city in India
- If it exists in tier2_cities, give the budget plan according to a tier 2 city in India
- Else give the expenses according to a tier3 city in India

If the user does not specify the city give the a planner according to the tier2 city and ask - "If you need a planner according to your location, please specify the city"

       
       Provide the proper fromatted and user friendly answers
       """


system_prompt = SystemMessagePromptTemplate(
    prompt=PromptTemplate(
        input_variables=["context"],
        template=SYSTEM_MESSAGE,
    )
)

human_prompt = HumanMessagePromptTemplate(
    prompt=PromptTemplate(
        input_variables=["question"],
        template="{question}",
    )
)

messages = [system_prompt, human_prompt]

prompt_template = ChatPromptTemplate(
    input_variables=["context", "question"],
    messages=messages,
)

basic_info_model = (
    {"context": RunnablePassthrough(), "question": RunnablePassthrough()}
    | prompt_template
    | chat_model
    | StrOutputParser()
)

# Database Functions
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create existing tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total_money REAL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT,
            amount REAL,
            timestamp TEXT
        )
    """)
    
    # Add new conversations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            timestamp TEXT,
            user_message TEXT,
            bot_response TEXT,
            context TEXT
        )
    """)
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    
    # cursor.execute("DROP TABLE IF EXISTS users;")

    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", ("users",))
    table = cursor.fetchone()
    print(table)

    
    # Ensure one user record exists
    cursor.execute("INSERT OR IGNORE INTO user_data (id, total_money) VALUES (1, 0)")
    conn.commit()
    conn.close()
    
# Initialize database and session state
init_db()
    
def hash_password(password: str) -> str:
    """Hash password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def register_user():
    """Handle user registration using SQLite."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    username = st.session_state.register_username_tab
    password = st.session_state.register_password_tab
    if not username or not password:
        st.error("Username and password cannot be empty!")
        return
    try:
        cursor.execute("SELECT 1 FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            st.error("Username already exists!")
            conn.close()
            return
    
        hashed_password = hash_password(password)
        created_at = datetime.now().isoformat()
    
        cursor.execute(
        "INSERT INTO users (username, password, created_at) VALUES (?, ?, ?)",
            (username, hashed_password, created_at)
        )
        conn.commit()
        conn.close()

        st.success("Registration successful! Please login.")
    except Exception as E:
        print(Exception),
        st.error("Error Occurred")

def login_user():
    """Handle user login using SQLite."""
    username = st.session_state.login_username_tab
    password = st.session_state.login_password_tab

    if not username or not password:
        st.error("Username and password cannot be empty!")
        return
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Fetch user details from the database
    cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()

    st.success(user)

    if not user:
        st.error("Invalid username or password!")
        return

    # Check the hashed password
    hashed_password = user[0]
    password = hash_password(password)
    if hashed_password == password:
        st.success("Login successful!")
        st.session_state.is_logged_in = True
        st.session_state.current_user = username
    else:
        st.error("Invalid username or password!")

def get_total_money():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT total_money FROM user_data WHERE id = 1")
    total_money = cursor.fetchone()[0]
    conn.close()
    return total_money

def update_total_money(amount):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE user_data SET total_money = ? WHERE id = 1", (amount,))
    conn.commit()
    conn.close()

def add_to_balance(amount):
    current_balance = get_total_money()
    new_balance = current_balance + amount
    update_total_money(new_balance)

def add_expense(description, amount):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO expenses (description, amount, timestamp) VALUES (?, ?, ?)", 
                  (description, amount, timestamp))
    conn.commit()
    conn.close()

def get_expenses():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT description, amount, timestamp FROM expenses")
    expenses = cursor.fetchall()
    conn.close()
    return expenses

def get_last_10_expenses():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT description, amount, timestamp
        FROM expenses
        ORDER BY timestamp DESC
        LIMIT 10
    """)
    expenses = cursor.fetchall()
    conn.close()
    return expenses

def parse_nlp_input(user_input):
    user_input = user_input.lower()
    today = datetime.now()
    parsed_data = {"action": None, "description": None, "amount": None, "start_date": None, "end_date": None}

    expense_match = re.search(r"spent\s+(\d+)\s+on\s+(.*?)\s+(today|yesterday|(\d+)\s+days ago)", user_input)
    if expense_match:
        parsed_data["action"] = "add_expense"
        parsed_data["amount"] = float(expense_match.group(1))
        parsed_data["description"] = expense_match.group(2)
        if expense_match.group(3) == "today":
            parsed_data["start_date"] = parsed_data["end_date"] = today
        elif expense_match.group(3) == "yesterday":
            yesterday = today - timedelta(days=1)
            parsed_data["start_date"] = parsed_data["end_date"] = yesterday
        elif expense_match.group(4):
            days_ago = int(expense_match.group(4))
            parsed_data["start_date"] = parsed_data["end_date"] = today - timedelta(days=days_ago)
    
    return parsed_data

# Chat Functions
def init_session_state():
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    if 'context' not in st.session_state:
        st.session_state.context = {}
    if 'message_sent' not in st.session_state:
        st.session_state.message_sent = False
    if 'login_username' not in st.session_state:
        st.session_state.login_username = False
    if 'is_logged_in' not in st.session_state:
        st.session_state.is_logged_in = False
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None

def save_conversation(session_id, user_message, bot_response):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    context = json.dumps(st.session_state.context)
    
    cursor.execute("""
        INSERT INTO conversations 
        (session_id, timestamp, user_message, bot_response, context)
        VALUES (?, ?, ?, ?, ?)
    """, (session_id, timestamp, user_message, bot_response, context))
    
    conn.commit()
    conn.close()

def get_chat_response(user_input):
    expenses = get_expenses()
    total_spent = sum(expense[1] for expense in expenses)
    initial_money = get_total_money() + total_spent
    
    context = f"""
    Initial money: ₹{initial_money}
    Total spent: ₹{total_spent}
    Current balance: ₹{get_total_money()}
    
    Expense breakdown:
    {chr(10).join(f'- {desc}: ₹{amt}' for desc, amt, _ in expenses)}
    """
    
    final_prompt = prompt_template.format(
        context=context, question=user_input
    )
    
    response = basic_info_model.invoke(final_prompt)
    
    return response

def process_chat_message(user_input):
    if user_input:
        # Check for expense-related commands
        parsed_input = parse_nlp_input(user_input)
        
        if parsed_input["action"] == "add_expense":
            amount = parsed_input["amount"]
            description = parsed_input["description"]
            
            if amount > get_total_money():
                return "❌ Insufficient funds! Please check your balance."
            
            update_total_money(get_total_money() - amount)
            add_expense(description, amount)
            return f"✅ Added expense: {description} - ₹{amount:.2f}"
        
        # Regular chat processing
        st.session_state.conversation_history.append({"user": user_input})
        response = get_chat_response(user_input)
        st.session_state.conversation_history.append({"assistant": response})
        
        save_conversation(
            session_id=str(hash(datetime.now())),
            user_message=user_input,
            bot_response=response
        )
        
        return response
    return None

# UI Components
def render_chat_interface():
    st.markdown("""
        <style>
        .chat-message {
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
            position: relative;
        }
        .user-message {
            background-color: #292323;
        }
        .bot-message {
            background-color: #292323;
        }
        .stButton>button {
            background-color: #2a9d8f;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 8px 16px;
        }
        .stButton>button:hover {
            background-color: #21867a;
        }
        </style>
    """, unsafe_allow_html=True)
    
    chat_container = st.container()
    
    with chat_container:
        for message in st.session_state.conversation_history:
            with st.container():
                col1, col2 = st.columns([1, 9])
                with col1:
                    st.markdown("👤" if "user" in message else "🤖")
                with col2:
                    st.markdown(
                        f"<div class='chat-message {'user-message' if 'user' in message else 'bot-message'}'>"
                        f"{message['user'] if 'user' in message else message['assistant']}</div>",
                        unsafe_allow_html=True
                    )

def main():
    st.set_page_config(
        page_title="SmartSpend AI",
        page_icon="💰",
        layout="wide"
    )
    
    init_session_state()
    
    # Check login state
    if not st.session_state.get("is_logged_in", False):
        st.markdown(
            """
            <h1>💰 SmartSpend AI</h1>
            <p class="byline">Your 24/7 bot for all financial records and advice.</p>
            <hr style="border: 1px solid #2a9d8f;">
            """,
            unsafe_allow_html=True
        )
        
        st.sidebar.title("🔐 Login/Register")
        
        tab_login, tab_register = st.tabs(["🔑 Login", "📝 Register"])
        
        with tab_login:
            with st.form(key='login_form'):
                st.text_input("Username", key="login_username_tab")
                st.text_input("Password", type="password", key="login_password_tab")
                submit_login = st.form_submit_button("Login")
                
                if submit_login:
                    login_user()  # Call your login function
                    if st.session_state.get("is_logged_in", False):
                        st.success("🎉 Login successful!")
                        st.rerun()
        
        with tab_register:
            with st.form(key='register_form'):
                st.text_input("Username", key="register_username_tab")
                st.text_input("Password", type="password", key="register_password_tab")
                submit_register = st.form_submit_button("Register")
                
                if submit_register:
                    register_user()  # Call your register function
                    if st.session_state.get("registration_successful", False):
                        st.success("✅ Registration successful! You can now log in.")
    
    else:
        # Main application content after login
        st.markdown(
            """
            <h1>💰 SmartSpend AI</h1>
            <p class="byline">Your 24/7 bot for all financial records and advice.</p>
            <hr style="border: 1px solid #2a9d8f;">
            """,
            unsafe_allow_html=True
        )
        
        # Sidebar
        st.sidebar.title("💳 Expense Drawer")
        st.sidebar.write(f"Welcome, {st.session_state.get('current_user', 'User')}!")
        
        st.sidebar.write("Here are your last 10 expenses:")
        last_10_expenses = get_last_10_expenses()
        if not last_10_expenses:
            st.sidebar.write("No expenses recorded yet.")
        else:
            for desc, amt, ts in last_10_expenses:
                st.sidebar.write(f"- {desc}: ₹{amt} (on {ts})")
        
        # Initialize money if not set
        total_money = get_total_money()
        if total_money == 0:
            st.sidebar.write("Set your initial balance:")
            user_money = st.sidebar.number_input("Enter amount:", min_value=0.0, step=100.0)
            if st.sidebar.button("Save Balance"):
                update_total_money(user_money)
                st.sidebar.success(f"Initial balance set to ₹{user_money:.2f}")
                st.rerun()
        else:
            st.sidebar.write(f"Current Balance: ₹{total_money:.2f}")
        
        # Main content tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["💬 Chat", "💸 Add Expense", "💰 Add Balance", "📊 Analysis", "💡 Savings Advice"])
        
        with tab1:
            render_chat_interface()
            
            with st.form(key='chat_form', clear_on_submit=True):
                user_input = st.text_input("Type your message here...", key="chat_input")
                submit_button = st.form_submit_button("Send")
                
                if submit_button and user_input:
                    response = process_chat_message(user_input)
                    if response:
                        st.rerun()
        
        with tab2:
            with st.form(key='expense_form', clear_on_submit=True):
                expense_description = st.text_input("Description:")
                expense_amount = st.number_input("Amount (₹):", min_value=0.0, step=100.0)
                submit_expense = st.form_submit_button("Add Expense")
                
                if submit_expense:
                    if expense_amount > get_total_money():
                        st.error("❌ Insufficient funds! Please check your balance.")
                    else:
                        update_total_money(get_total_money() - expense_amount)
                        add_expense(expense_description, expense_amount)
                        st.success(f"✅ Added: {expense_description} - ₹{expense_amount:.2f}")
                        st.rerun()

        with tab3:
            with st.form(key='balance_form', clear_on_submit=True):
                add_amount = st.number_input("Amount to Add (₹):", min_value=0.0, step=100.0)
                submit_balance = st.form_submit_button("Add to Balance")
                
                if submit_balance and add_amount > 0:
                    add_to_balance(add_amount)
                    st.success(f"✅ Added ₹{add_amount:.2f} to your balance")
                    st.rerun()
        
        with tab4:
            if st.button("Analyze Spending"):
                expenses = get_expenses()
                if not expenses:
                    st.info("No expenses recorded yet.")
                else:
                    with st.spinner("Analyzing your spending..."):
                        ai_response = get_chat_response("Please analyze my spending patterns and provide insights.")
                        st.markdown(ai_response)
        
        with tab5:
            if st.button("Get Savings Advice"):
                with st.spinner("Generating savings advice..."):
                    ai_response = get_chat_response("Please suggest ways to save better based on my spending patterns.")
                    st.markdown(ai_response)



if __name__ == "__main__":
    main()