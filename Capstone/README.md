# AI Day Planner New Project

Clean project based on your architecture. BMI removed.

## Features
- Signup / Login
- Profile: height, weight, gender, age, profession, disease, disability
- Day Planner after login
- Wake-up time, sleep time, diet, fitness type, workout duration
- Agent 1: Day Planner using Azure OpenAI GPT-4o if configured
- Agent 2: History analyser using local logic
- Agent 3: Feedback / fallback using local logic
- Plan history and feedback
- Optional SMS placeholder

## Run Backend
```bash
cd ai_day_planner_new
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Check: http://127.0.0.1:8000/docs

## Run Streamlit
Open second terminal:
```bash
cd ai_day_planner_new
venv\Scripts\activate
streamlit run streamlit_app/app.py
```

If Azure OpenAI key is missing, the app still returns a local fallback day plan.
