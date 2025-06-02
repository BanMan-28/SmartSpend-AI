💰 SmartSpend AI

**SmartSpend AI** is a Streamlit-based personal finance assistant that helps users—especially students—track expenses, manage their savings, and get intelligent, AI-driven financial advice. The application integrates a natural language chatbot (powered by Gemini 1.5 Flash via LangChain) with a local SQLite database to store user data and conversations.

---

📂 Project Structure

- `top1.py` – Main Streamlit application file. Handles user login/registration, chat logic, expense tracking, balance updates, and AI responses.
- `spending_tracker.db` – SQLite database file used to store user data, expenses, and chat conversations.
- `bot111.ipynb` – A testing notebook used for experiments and validating individual components before full integration.

---

🚀 Features

- **User Registration & Login** with hashed password storage.
- **Expense Tracking** categorized by date, amount, and description.
- **AI Chatbot Interface** powered by Google Gemini 1.5 Flash for financial analysis and general queries.
- **Budgeting Advice** based on Indian city tiers (Tier 1, 2, 3).
- **Natural Language Input Parsing** (e.g., “I spent 500 on food yesterday”).
- **Balance Management**: Add funds and track remaining money.
- **Spending Pattern Analysis & Savings Tips** using AI.

---

🧠 AI Functionality

The assistant:
- Understands context (e.g., location, financial patterns).
- Categorizes expenses by type (essential, educational, discretionary).
- Uses the **50/30/20 rule** for budgeting advice.
- Responds in a friendly and markdown-formatted style.

---

🛠️ Requirements

- Python 3.8+
- Streamlit
- SQLite3
- LangChain
- rich
- Google Generative AI Python SDK

---

📦 Installation & Running

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/yourrepo.git
   cd yourrepo

-> Install dependencies:
pip install -r requirements.txt

-> Add your Gemini API key in top1.py:
API_KEY = "Your Gemini flash API Key"

-> Run the application:
streamlit run top1.py

🧪 Testing
Use the bot111.ipynb Jupyter notebook to test database queries and logic independently before deploying updates to the main app.

🔒 Security
User passwords are hashed using SHA-256.

-> Conversations and financial records are stored locally in SQLite.

📌 Notes
Default financial planner assumes Tier 2 city unless specified.
Database tables auto-initialize on first run.
Handles basic NLP for spending input like “spent 500 on rent 2 days ago”.

Made with ❤️ by Manish Bansal
Contact: bansalmanish8889@gmail.com

