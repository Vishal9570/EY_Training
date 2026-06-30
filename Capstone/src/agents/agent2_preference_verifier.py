import json
from openai import AzureOpenAI
from app.config import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_DEPLOYMENT,
    AZURE_OPENAI_API_VERSION,
)


def verify_plan_with_agent2(profile: dict, prefs: dict, events: list) -> dict:
    """
    Agent 2 verifies whether Agent 1 followed user preferences.
    Returns:
    {
      "is_valid": true/false,
      "errors": [],
      "correction_prompt": "..."
    }
    """

    # If Azure is not configured, do simple rule fallback
    if not AZURE_OPENAI_API_KEY or not AZURE_OPENAI_ENDPOINT:
        return basic_verify(prefs, events)

    client = AzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_version=AZURE_OPENAI_API_VERSION,
    )

    prompt = f"""
You are Agent 2 — Preference and Constraint Verifier.

Your job is to check whether the generated day plan correctly follows the user's inputs.

User profile:
{json.dumps(profile, indent=2)}

User preferences:
{json.dumps(prefs, indent=2)}

Generated day plan:
{json.dumps(events, indent=2)}

Check these strictly:
1. No activity should be scheduled before wake_time.
2. Breakfast must be after wake_time.
3. Sleep activity should be close to sleep_time.
4. Diet preference must be respected.
5. Extra preferences must be respected.
   Example:
   - If user says "avoid roti at night", dinner should not contain roti.
   - If user says "add steamed chicken at night", dinner should contain steamed chicken or similar.
   - If user says "avoid rice", meals should not contain rice.
6. Fitness preference and workout duration must be respected.
7. Do not judge medically. Only verify schedule and preference alignment.

Return valid JSON only in this format:
{{
  "is_valid": true,
  "errors": [],
  "correction_prompt": ""
}}

If invalid:
{{
  "is_valid": false,
  "errors": [
    "Breakfast is scheduled before wake time",
    "Dinner does not include steamed chicken requested by user"
  ],
  "correction_prompt": "Regenerate the plan. Fix these issues: ..."
}}
"""

    try:
        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {
                    "role": "system",
                    "content": "You are a strict JSON-only verifier. Return only valid JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )

        content = response.choices[0].message.content.strip()
        return json.loads(content)

    except Exception as e:
        print("Agent 2 verifier failed. Using basic fallback:", e)
        return basic_verify(prefs, events)


def basic_verify(prefs: dict, events: list) -> dict:
    errors = []

    wake_time = prefs.get("wake_time", "06:00")
    diet_type = prefs.get("diet_type", "")
    notes = str(prefs.get("extra_preferences", {}).get("notes", "")).lower()

    def to_minutes(t):
        h, m = t.split(":")
        return int(h) * 60 + int(m)

    wake_mins = to_minutes(wake_time)

    for event in events:
        event_time = event.get("time", "")
        activity = str(event.get("activity", "")).lower()
        category = str(event.get("category", "")).lower()

        try:
            event_mins = to_minutes(event_time)
        except Exception:
            errors.append(f"Invalid time format: {event_time}")
            continue

        if category != "sleep" and event_mins < wake_mins:
            errors.append(f"{event.get('activity')} is before wake time {wake_time}")

        if diet_type == "Veg":
            non_veg_words = ["chicken", "egg", "fish", "mutton", "meat"]
            for word in non_veg_words:
                if word in activity:
                    errors.append(f"Non-veg item found in Veg plan: {event.get('activity')}")

    correction_prompt = ""
    if errors:
        correction_prompt = "Regenerate the plan and fix these issues: " + "; ".join(errors)

    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "correction_prompt": correction_prompt,
    }