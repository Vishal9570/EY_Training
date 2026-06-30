def fallback_suggestions(user_profile: dict, preferences: dict):
    diseases = (user_profile.get("diseases") or "").lower()
    notes = []
    if "sugar" in diseases:
        notes.append("Keep meals balanced and avoid high-sugar snacks.")
    if "bp" in diseases:
        notes.append("Prefer low-salt food and include light walking or yoga.")
    if "heart" in diseases:
        notes.append("Avoid intense workout without professional medical advice.")
    if user_profile.get("disability"):
        notes.append("Adjust workout intensity based on comfort and mobility.")
    if not notes:
        notes.append("Maintain hydration, regular meals, and consistent sleep routine.")
    return {
        "agent": "Agent 3 - Feedback / Fallback",
        "model": "Ollama/Crew style local fallback",
        "suggestions": notes
    }
