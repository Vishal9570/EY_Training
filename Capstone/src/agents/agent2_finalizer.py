import json
from openai import AzureOpenAI
from app.config import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_DEPLOYMENT,
    AZURE_OPENAI_API_VERSION,
)


def finalize_plan_with_agent2(profile, prefs, edited_events):
    """
    Agent 2 finalises user-edited plan.
    It respects user edits and adjusts remaining schedule logically.
    """

    if not AZURE_OPENAI_API_KEY or not AZURE_OPENAI_ENDPOINT:
        return edited_events

    client = AzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_version=AZURE_OPENAI_API_VERSION,
    )

    prompt = f"""
You are Agent 2 — Day Plan Finaliser.

The user has edited their generated day plan.
Your job is to finalise the schedule based on user changes.

User profile:
{json.dumps(profile, indent=2)}

User preferences:
{json.dumps(prefs, indent=2)}

User edited plan:
{json.dumps(edited_events, indent=2)}

Rules:
1. Respect the user's manual edits.
2. If user says lunch happened at 2 PM, keep lunch at 14:00.
3. If user says they had rice and dal instead of grilled chicken, update that meal.
4. If user office time is 9 AM to 7 PM, do not schedule gym during office time.
5. Workout should be before office or after office.
6. Do not schedule anything before wake-up time.
7. Sleep must remain near selected sleep time.
8. Keep the plan practical for an Indian working professional.
9. Return only valid JSON array.
10. Use exactly these fields:
time, activity, category, duration_minutes, notes.
"""

    try:
        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "Return only valid JSON. No markdown."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
        )

        return json.loads(response.choices[0].message.content.strip())

    except Exception as e:
        print("Agent 2 finalizer failed:", e)
        return edited_events