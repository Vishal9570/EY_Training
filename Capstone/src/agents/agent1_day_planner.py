# import json
# from typing import Dict, Any, List
# from openai import AzureOpenAI, OpenAIError
# from app.config import AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT, AZURE_OPENAI_API_VERSION
# from datetime import datetime, timedelta


# def add_minutes(time_str: str, minutes: int) -> str:
#     base = datetime.strptime(time_str, "%H:%M")
#     new_time = base + timedelta(minutes=minutes)
#     return new_time.strftime("%H:%M")


# # def _local_fallback_plan(wake_time, sleep_time, diet_type, fitness_type, workout_duration):
# #     workout_label = "Gym workout" if fitness_type == "Gym" else "Yoga session" if fitness_type == "Yoga" else "Gym + yoga"
# #     breakfast = "Poha with curd" if diet_type == "Veg" else "Boiled eggs with poha"
# #     lunch = "Dal, rice, roti, sabzi, salad" if diet_type == "Veg" else "Chicken curry, rice, salad"
# #     dinner = "Light khichdi and curd" if diet_type == "Veg" else "Grilled chicken with roti and salad"
# #     return [
# #         {"time": wake_time, "activity": "Wake up and drink water", "category": "wake", "duration_minutes": 15, "notes": "Start with hydration."},
# #         {"time": "07:30", "activity": breakfast, "category": "meal", "duration_minutes": 30, "notes": "Healthy breakfast."},
# #         {"time": "09:00", "activity": "Work / study focus block", "category": "work", "duration_minutes": 180, "notes": "Deep work session."},
# #         {"time": "13:00", "activity": lunch, "category": "meal", "duration_minutes": 45, "notes": "Balanced lunch."},
# #         {"time": "16:30", "activity": "Tea break and short walk", "category": "break", "duration_minutes": 20, "notes": "Avoid too much sugar."},
# #         {"time": "18:30", "activity": f"{workout_label} for {workout_duration}", "category": "workout", "duration_minutes": 60, "notes": "Keep intensity moderate."},
# #         {"time": "20:30", "activity": dinner, "category": "meal", "duration_minutes": 40, "notes": "Keep dinner light."},
# #         {"time": "21:30", "activity": "Book reading / meditation", "category": "reading", "duration_minutes": 30, "notes": "Reduce screen time."},
# #         {"time": sleep_time, "activity": "Sleep", "category": "sleep", "duration_minutes": 480, "notes": "Maintain consistent sleep."}
# #     ]


# def _local_fallback_plan(
#     wake_time: str,
#     sleep_time: str,
#     diet_type: str,
#     fitness_type: str,
#     workout_duration: str
# ):
#     workout_label = (
#         "Gym workout"
#         if fitness_type == "Gym"
#         else "Yoga session"
#         if fitness_type == "Yoga"
#         else "Gym + yoga"
#     )

#     breakfast = "Poha with curd" if diet_type == "Veg" else "Boiled eggs with poha"
#     lunch = "Dal, rice, roti, sabzi, salad" if diet_type == "Veg" else "Chicken curry, rice, salad"
#     dinner = "Light khichdi and curd" if diet_type == "Veg" else "Grilled chicken with roti and salad"

#     return [
#         {
#             "time": wake_time,
#             "activity": "Wake up and drink water",
#             "category": "wake",
#             "duration_minutes": 15,
#             "notes": "Start with hydration."
#         },
#         {
#             "time": add_minutes(wake_time, 45),
#             "activity": breakfast,
#             "category": "meal",
#             "duration_minutes": 30,
#             "notes": "Healthy breakfast."
#         },
#         {
#             "time": add_minutes(wake_time, 90),
#             "activity": "Work / study focus block",
#             "category": "work",
#             "duration_minutes": 180,
#             "notes": "Deep work session."
#         },
#         {
#             "time": add_minutes(wake_time, 240),
#             "activity": lunch,
#             "category": "meal",
#             "duration_minutes": 45,
#             "notes": "Balanced lunch."
#         },
#         {
#             "time": add_minutes(wake_time, 360),
#             "activity": "Tea break and short walk",
#             "category": "break",
#             "duration_minutes": 20,
#             "notes": "Avoid too much sugar."
#         },
#         {
#             "time": add_minutes(wake_time, 480),
#             "activity": f"{workout_label} for {workout_duration}",
#             "category": "workout",
#             "duration_minutes": 60,
#             "notes": "Keep intensity moderate."
#         },
#         {
#             "time": add_minutes(wake_time, 600),
#             "activity": dinner,
#             "category": "meal",
#             "duration_minutes": 40,
#             "notes": "Keep dinner light."
#         },
#         {
#             "time": add_minutes(wake_time, 660),
#             "activity": "Book reading / meditation",
#             "category": "reading",
#             "duration_minutes": 30,
#             "notes": "Reduce screen time."
#         },
#         {
#             "time": sleep_time,
#             "activity": "Sleep",
#             "category": "sleep",
#             "duration_minutes": 480,
#             "notes": "Maintain consistent sleep."
#         }
#     ]

# #def generate_day_plan_with_gpt(user_profile: Dict[str, Any], preferences: Dict[str, Any], analysis: Dict[str, Any], fallback: Dict[str, Any]) -> List[Dict[str, Any]]:
# def generate_day_plan_with_gpt(user_profile, preferences, analysis, fallback, correction_prompt: str = ""):    
#     wake_time = preferences["wake_time"]
#     sleep_time = preferences["sleep_time"]
#     diet_type = preferences["diet_type"]
#     fitness_type = preferences["fitness_type"]
#     workout_duration = preferences["workout_duration"]

#     if not AZURE_OPENAI_API_KEY or not AZURE_OPENAI_ENDPOINT:
#         return _local_fallback_plan(wake_time, sleep_time, diet_type, fitness_type, workout_duration)

#     client = AzureOpenAI(
#         api_key=AZURE_OPENAI_API_KEY,
#         azure_endpoint=AZURE_OPENAI_ENDPOINT,
#         api_version=AZURE_OPENAI_API_VERSION
#     )

#     prompt = f"""
# You are Agent 1 — Day Planner.
# Create a practical day plan for an Indian professional.

# User profile:
# {json.dumps(user_profile, indent=2)}

# Preferences:
# {json.dumps(preferences, indent=2)}

# Correction instructions from Agent 2:
# {correction_prompt}

# Agent 2 analysis:
# {json.dumps(analysis, indent=2)}

# Agent 3 safety/fallback suggestions:
# {json.dumps(fallback, indent=2)}

# Rules:
# 1. Make plan from wake-up to sleep.
# 2. Include Indian meals based on Veg/Non-Veg.
# 3. Include gym/yoga based on selected preference.
# 4. Include work blocks, meals, breaks, workout, reading, meditation and sleep.
# 5. If diseases include BP, Sugar, Heart, or disability, keep suggestions safe and general.
# 6. Do not provide medical diagnosis.
# 7. Return only valid JSON array. No markdown.
# 8. Use exactly these fields: time, activity, category, duration_minutes, notes.
# 9. Wake-up time must be the first activity.
# 10. Do not schedule any activity before wake-up time.
# 11. If user mentions office/work time, treat it as a blocked time window.
# 12. Do not schedule gym, yoga, dinner, reading, or personal activities during office time.
# 13. If user says "gym after office", schedule workout only after office end time.
# 14. If user says "gym before office", schedule workout only before office start time.
# 15. Dinner must not be scheduled during office time.
# 16. If sleep time is late, dinner should usually be around 20:00 to 21:30, unless user says otherwise.
# 17. Respect extra preferences exactly.
# 18. If user says "avoid roti at night", dinner should not contain roti.
# 19. If user says "add steamed chicken at night", dinner should contain steamed chicken or similar
# 20. If user says avoid any food item, do not include it.
# 21. Return only valid JSON array with these fields


# """

#     try:
#         response = client.chat.completions.create(
#             model=AZURE_OPENAI_DEPLOYMENT,
#             messages=[
#                 {"role": "system", "content": "Return only valid JSON. No markdown."},
#                 {"role": "user", "content": prompt}
#             ],
#             temperature=0.1
#         )
#         content = response.choices[0].message.content.strip()
#     except OpenAIError:
#         return _local_fallback_plan(wake_time, sleep_time, diet_type, fitness_type, workout_duration)

#     try:
#         return json.loads(content)
#     except Exception:
#         return _local_fallback_plan(wake_time, sleep_time, diet_type, fitness_type, workout_duration)



import json
import random
from openai import AzureOpenAI

from app.config import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_DEPLOYMENT,
    AZURE_OPENAI_API_VERSION,
)

from app.services.schedule_builder import build_fixed_schedule


def local_meal_fallback(diet_type: str):
    veg_meals = [
        {
            "breakfast": "Oats with banana, nuts and curd",
            "lunch": "Dal, brown rice, sabzi and salad",
            "tea": "Buttermilk with roasted chana",
            "dinner": "Paneer salad with quinoa"
        },
        {
            "breakfast": "Besan chilla with curd",
            "lunch": "Rajma, rice and salad",
            "tea": "Coconut water with fruits",
            "dinner": "Light khichdi with curd"
        },
        {
            "breakfast": "Muesli with milk and fruits",
            "lunch": "Chole, roti and salad",
            "tea": "Sprouts chaat",
            "dinner": "Tofu vegetable bowl"
        }
    ]

    non_veg_meals = [
        {
            "breakfast": "Omelette with toast and fruits",
            "lunch": "Chicken curry, brown rice and salad",
            "tea": "Buttermilk with roasted makhana",
            "dinner": "Steamed chicken with salad"
        },
        {
            "breakfast": "Boiled eggs with oats",
            "lunch": "Grilled chicken, dal and salad",
            "tea": "Coconut water with nuts",
            "dinner": "Chicken soup with vegetables"
        },
        {
            "breakfast": "Cornflakes with milk and boiled eggs",
            "lunch": "Egg curry, rice and salad",
            "tea": "Fruit bowl with peanuts",
            "dinner": "Grilled chicken with quinoa salad"
        }
    ]

    return random.choice(veg_meals if diet_type == "Veg" else non_veg_meals)


# def generate_meals_with_agent1(profile, prefs, schedule):
#     diet_type = prefs["diet_type"]
#     extra_preferences = prefs.get("extra_preferences", {})
#     user_notes = extra_preferences.get("notes", "")

#     if not AZURE_OPENAI_API_KEY or not AZURE_OPENAI_ENDPOINT:
#         return local_meal_fallback(diet_type)

#     client = AzureOpenAI(
#         api_key=AZURE_OPENAI_API_KEY,
#         azure_endpoint=AZURE_OPENAI_ENDPOINT,
#         api_version=AZURE_OPENAI_API_VERSION,
#     )

#     prompt = f"""
# You are Agent 1 — Meal Planner.

# Generate only meal names for this fixed schedule.

# User profile:
# {json.dumps(profile, indent=2)}

# User preferences:
# {json.dumps(prefs, indent=2)}

# Fixed meal times:
# {json.dumps(schedule, indent=2)}

# Rules:
# 1. Never repeat the exact same meal plan.
# 2. Create a healthy Indian meal plan.
# 3. Use different combinations each time.
# 4. Respect Veg/Non-Veg strictly.
# 5. Respect extra preferences strictly.
# 6. If user says avoid roti/rice/sugar, do not include it.
# 7. If user requests a dinner item, include it in dinner.
# 8. Include foods like oats, overnight oats, muesli, cornflakes, poha, upma, idli, dosa, besan chilla, sprouts, paneer, tofu, boiled eggs, omelette, grilled chicken, steamed chicken, brown rice, quinoa, dal, rajma, chole, vegetables, curd, fruits, nuts, buttermilk, coconut water, salad.
# 9. Return valid JSON only.

# JSON format:
# {{
#   "breakfast": "...",
#   "lunch": "...",
#   "tea": "...",
#   "dinner": "..."
# }}
# """

#     try:
#         response = client.chat.completions.create(
#             model=AZURE_OPENAI_DEPLOYMENT,
#             messages=[
#                 {"role": "system", "content": "Return only valid JSON. No markdown."},
#                 {"role": "user", "content": prompt},
#             ],
#             temperature=0.8,
#         )

#         return json.loads(response.choices[0].message.content.strip())

#     except Exception as e:
#         print("Agent 1 meal generation failed. Using fallback:", e)
#         return local_meal_fallback(diet_type)


# def generate_meals_with_agent1(profile, prefs, schedule):
#     diet_type = prefs["diet_type"]
#     extra_preferences = prefs.get("extra_preferences", {})
#     user_notes = extra_preferences.get("notes", "")

#     if not AZURE_OPENAI_API_KEY or not AZURE_OPENAI_ENDPOINT:
#         return local_meal_fallback(diet_type)

#     client = AzureOpenAI(
#         api_key=AZURE_OPENAI_API_KEY,
#         azure_endpoint=AZURE_OPENAI_ENDPOINT,
#         api_version=AZURE_OPENAI_API_VERSION,
#     )

#     prompt = f"""
# You are Agent 1 — Meal Planner.

# Your task is to generate meals for the user's day plan.

# User profile:
# {json.dumps(profile, indent=2)}

# Diet preference:
# {diet_type}

# User food preferences / instructions:
# {user_notes}

# Fixed schedule:
# {json.dumps(schedule, indent=2)}

# Important:
# - Treat the user's food preferences as mandatory instructions, not optional suggestions.
# - Understand the user's preference naturally.
# - If the user asks for specific food at dinner, include it in dinner.
# - If the user asks for specific food at lunch, include it in lunch.
# - If the user says avoid something, do not include it.
# - Respect Veg / Non-Veg strictly.
# - Generate a different healthy Indian meal plan each time.
# - Do not hardcode repeated meals.
# - Return only valid JSON.

# Return JSON exactly in this format:
# {{
#   "breakfast": "...",
#   "lunch": "...",
#   "tea": "...",
#   "dinner": "..."
# }}
# """

#     try:
#         response = client.chat.completions.create(
#             model=AZURE_OPENAI_DEPLOYMENT,
#             messages=[
#                 {
#                     "role": "system",
#                     "content": "You are a strict meal-planning agent. Return only valid JSON."
#                 },
#                 {
#                     "role": "user",
#                     "content": prompt
#                 }
#             ],
#             temperature=0.7
#         )

#         meals = json.loads(response.choices[0].message.content.strip())
#         return meals

#     except Exception as e:
#         print("Agent 1 meal generation failed. Using fallback:", e)
#         return local_meal_fallback(diet_type)

def generate_meals_with_agent1(profile, prefs, schedule):
    diet_type = prefs["diet_type"]
    extra_preferences = prefs.get("extra_preferences", {})
    user_notes = extra_preferences.get("notes", "")

    if not AZURE_OPENAI_API_KEY or not AZURE_OPENAI_ENDPOINT:
        return local_meal_fallback(diet_type)

    client = AzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_version=AZURE_OPENAI_API_VERSION,
    )

    prompt = f"""
You are Agent 1 — Meal Planner.

Your task is to generate meals for the user's day plan.

User profile:
{json.dumps(profile, indent=2)}

Diet preference:
{diet_type}

User mandatory food preferences / instructions:
{user_notes}

Fixed schedule:
{json.dumps(schedule, indent=2)}

Important:
- Treat the user's food preferences as mandatory instructions, not optional suggestions.
- Understand the user's preference naturally.
- If the user asks for specific food at dinner, include it in dinner.
- If the user asks for specific food at lunch, include it in lunch.
- If the user says avoid something, do not include it.
- Respect Veg / Non-Veg strictly.
- Generate a different healthy Indian meal plan each time.
- Do not hardcode repeated meals.
- Return only valid JSON.

CRITICAL:
- If user says "sea food in lunch", lunch must contain seafood, fish, prawn, or shrimp.
- If user says "grilled chicken for dinner", dinner must contain grilled chicken.
- If user says "roti for dinner", dinner must contain roti.
- If any mandatory instruction is not followed, the answer is invalid.

Return JSON exactly in this format:
{{
  "breakfast": "...",
  "lunch": "...",
  "tea": "...",
  "dinner": "..."
}}
"""

    try:
        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {
                    "role": "system",
                    "content": "You are a strict meal-planning agent. Return only valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2
        )

        meals = json.loads(response.choices[0].message.content.strip())
        return meals

    except Exception as e:
        print("Agent 1 meal generation failed. Using fallback:", e)
        return local_meal_fallback(diet_type)

def generate_day_plan_with_gpt(
    profile,
    prefs,
    analysis,
    fallback,
    correction_prompt: str = ""
):
    wake_time = prefs["wake_time"]
    sleep_time = prefs["sleep_time"]
    fitness_type = prefs["fitness_type"]
    workout_duration = prefs["workout_duration"]
    office_time = prefs.get("extra_preferences", {}).get("office_time", "")

    schedule = build_fixed_schedule(
        wake_time=wake_time,
        sleep_time=sleep_time,
        fitness_type=fitness_type,
        workout_duration=workout_duration,
        office_time=office_time,
    )

    meals = generate_meals_with_agent1(profile, prefs, schedule)

    events = [
        {
            "time": schedule["wake"],
            "activity": "Wake up and drink water",
            "category": "wake",
            "duration_minutes": 15,
            "notes": "Start your day with hydration."
        },
        {
            "time": schedule["breakfast"],
            "activity": meals["breakfast"],
            "category": "meal",
            "duration_minutes": 30,
            "notes": "Breakfast is scheduled 2 hours after wake-up."
        },
        {
            "time": schedule["lunch"],
            "activity": meals["lunch"],
            "category": "meal",
            "duration_minutes": 45,
            "notes": "Lunch is scheduled 4 hours after breakfast."
        },
        {
            "time": schedule["tea"],
            "activity": meals["tea"],
            "category": "break",
            "duration_minutes": 20,
            "notes": "Tea break is scheduled 4 hours after lunch."
        },
        {
            "time": schedule["workout"],
            "activity": f"{schedule['workout_label']} for {workout_duration}",
            "category": "workout",
            "duration_minutes": 60,
            "notes": "Workout is planned after tea break or after office if office time is provided."
        },
        {
            "time": schedule["dinner"],
            "activity": meals["dinner"],
            "category": "meal",
            "duration_minutes": 40,
            "notes": "Dinner is scheduled around 3 hours after tea break."
        },
        {
            "time": schedule["reading"],
            "activity": "Book reading",
            "category": "reading",
            "duration_minutes": 30,
            "notes": "Light reading after dinner."
        },
        {
            "time": schedule["meditation"],
            "activity": "Meditation",
            "category": "meditation",
            "duration_minutes": 15,
            "notes": "Short relaxation before sleep."
        },
        {
            "time": schedule["sleep"],
            "activity": "Sleep",
            "category": "sleep",
            "duration_minutes": 480,
            "notes": "Maintain consistent sleep routine."
        }
    ]

    return events