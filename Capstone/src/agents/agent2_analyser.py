from app.services.history_service import get_history


def analyse_user_history(user_id: int):
    history = get_history(user_id, limit=5)
    if not history:
        return {
            "agent": "Agent 2 - Analyser",
            "model": "Groq optional / local fallback",
            "summary": "No previous history found. Plan will use signup profile and current preferences.",
            "recommendations": []
        }
    latest = history[0]
    return {
        "agent": "Agent 2 - Analyser",
        "model": "Groq optional / local fallback",
        "summary": f"Found {len(history)} previous plan(s).",
        "recommendations": [
            f"Previous diet preference was {latest.get('diet_type')}.",
            f"Previous fitness preference was {latest.get('fitness_type')}."
        ]
    }
