from fastapi import APIRouter, HTTPException
from datetime import date
from app.models import DayPlanRequest, FeedbackRequest, UpdatePlanRequest
from app.models import DayPlanRequest, FeedbackRequest
from app.services.auth_service import get_user_by_id
from app.agents.agent2_analyser import analyse_user_history
from app.agents.agent3_feedback import fallback_suggestions
from app.agents.agent1_day_planner import generate_day_plan_with_gpt
from app.agents.agent4_notification import schedule_day_plan
from app.services.history_service import save_plan, get_history, save_feedback
from app.services.notification_service import schedule_optional_sms
from app.agents.agent2_preference_verifier import verify_plan_with_agent2
from app.models import DayPlanRequest, FeedbackRequest, FinalizePlanRequest
from app.agents.agent2_finalizer import finalize_plan_with_agent2
from app.agents.agent3_validator import validate_final_plan
router = APIRouter(tags=["Planner"])


@router.post("/planner/generate")
def generate_plan(req: DayPlanRequest):
    user = get_user_by_id(req.user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    profile = {
        "name": user["name"],
        "email": user["email"],
        "phone": user["phone"],
        "height": user["height"],
        "weight": user["weight"],
        "gender": user["gender"],
        "age": user["age"],
        "profession": user["profession"],
        "diseases": user["diseases"],
        "disability": user["disability"],
    }

    prefs = {
        "wake_time": req.wake_time,
        "sleep_time": req.sleep_time,
        "diet_type": req.diet_type,
        "fitness_type": req.fitness_type,
        "workout_duration": req.workout_duration,
        "extra_preferences": req.preferences or {},
    }

    # Agent 2: history analysis
    analysis = analyse_user_history(req.user_id)

    # Agent 3: fallback / safety suggestions
    fallback = fallback_suggestions(profile, prefs)

    # Agent 1: day plan generation
    # events = generate_day_plan_with_gpt(
    #     profile,
    #     prefs,
    #     analysis,
    #     fallback
    # )

    events = generate_day_plan_with_gpt(profile, prefs, analysis, fallback)

    verification = verify_plan_with_agent2(profile, prefs, events)

    if not verification.get("is_valid"):
        events = generate_day_plan_with_gpt(
            profile,
            prefs,
            analysis,
            fallback,
            correction_prompt=verification.get("correction_prompt", "")
        )

        verification = verify_plan_with_agent2(profile, prefs, events)

    validation_errors = validate_plan_constraints(
        events,
        req.wake_time,
        req.sleep_time,
        req.diet_type
    )

    # Agent 4: desktop notification scheduler
    notification_result = schedule_day_plan(events)

    # Optional SMS placeholder
    sms_notification = schedule_optional_sms(req.phone, events)

    plan_id = save_plan(
        req.user_id,
        str(date.today()),
        req.wake_time,
        req.sleep_time,
        req.diet_type,
        req.fitness_type,
        req.workout_duration,
        events,
        {
            "agent2": analysis,
            "agent3": fallback,
            "desktop_notification": notification_result,
            "sms_notification": sms_notification,
        },
    )

    return {
        "plan_id": plan_id,
        "date": str(date.today()),
        "user_id": req.user_id,
        "events": events,
        "agent_analysis": {
            "agent1": "Azure OpenAI GPT-4o if configured, otherwise local fallback",
            "agent2": analysis,
            "agent3": fallback,
            "agent4": notification_result,
        },
        "notification": {
            "desktop": notification_result,
            "sms": sms_notification,
        },
    }


@router.get("/history/{user_id}")
def history(user_id: int, limit: int = 10):
    return {
        "user_id": user_id,
        "entries": get_history(user_id, limit)
    }


@router.post("/feedback")
def feedback(req: FeedbackRequest):
    save_feedback(
        req.user_id,
        req.plan_id,
        req.rating,
        req.comments or ""
    )

    return {
        "message": "Feedback saved successfully"
    }

def validate_plan_constraints(events, wake_time, sleep_time, diet_type):
    errors = []

    wake_minutes = int(wake_time.split(":")[0]) * 60 + int(wake_time.split(":")[1])
    sleep_minutes = int(sleep_time.split(":")[0]) * 60 + int(sleep_time.split(":")[1])

    for event in events:
        event_time = event.get("time", "")

        try:
            event_minutes = int(event_time.split(":")[0]) * 60 + int(event_time.split(":")[1])
        except Exception:
            errors.append(f"Invalid time format for activity: {event.get('activity')}")
            continue

        if event_minutes < wake_minutes:
            errors.append(
                f"{event.get('activity')} at {event_time} is before wake-up time {wake_time}"
            )

        activity = str(event.get("activity", "")).lower()

        if diet_type == "Veg":
            non_veg_words = ["chicken", "egg", "fish", "mutton", "meat"]
            for word in non_veg_words:
                if word in activity:
                    errors.append(
                        f"Non-veg item '{word}' found in Veg plan: {event.get('activity')}"
                    )

    return errors


@router.post("/planner/update")
def update_plan(req: UpdatePlanRequest):
    user = get_user_by_id(req.user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    validation_errors = validate_plan_constraints(
        req.events,
        req.wake_time,
        req.sleep_time,
        req.diet_type
    )

    analysis = {
        "message": "User manually edited the generated day plan.",
        "updated_by": "user",
        "validation_errors": validation_errors
    }

    plan_id = save_plan(
        req.user_id,
        str(date.today()),
        req.wake_time,
        req.sleep_time,
        req.diet_type,
        req.fitness_type,
        req.workout_duration,
        req.events,
        {
            "update_type": "user_edit",
            "analysis": analysis
        }
    )

    return {
        "message": "Plan updated successfully",
        "old_plan_id": req.plan_id,
        "new_plan_id": plan_id,
        "user_id": req.user_id,
        "events": req.events,
        "validation_errors": validation_errors
    }

@router.post("/planner/finalize")
def finalize_plan(req: FinalizePlanRequest):
    user = get_user_by_id(req.user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    profile = {
        "name": user["name"],
        "email": user["email"],
        "phone": user["phone"],
        "height": user["height"],
        "weight": user["weight"],
        "gender": user["gender"],
        "age": user["age"],
        "profession": user["profession"],
        "diseases": user["diseases"],
        "disability": user["disability"],
    }

    prefs = {
        "wake_time": req.wake_time,
        "sleep_time": req.sleep_time,
        "diet_type": req.diet_type,
        "fitness_type": req.fitness_type,
        "workout_duration": req.workout_duration,
        "extra_preferences": req.preferences or {},
    }

    # Agent 2 finalises user-edited plan
    final_events = finalize_plan_with_agent2(
        profile,
        prefs,
        req.events
    )

    # Agent 3 validates final plan
    validation = validate_final_plan(
        prefs,
        final_events
    )

    # If validation fails, return errors and still show final plan
    new_plan_id = save_plan(
        req.user_id,
        str(date.today()),
        req.wake_time,
        req.sleep_time,
        req.diet_type,
        req.fitness_type,
        req.workout_duration,
        final_events,
        {
            "update_type": "user_edit_finalised",
            "agent2": "Finalised user edits",
            "agent3_validation": validation,
        },
    )

    return {
        "message": "Plan finalised successfully",
        "old_plan_id": req.plan_id,
        "new_plan_id": new_plan_id,
        "user_id": req.user_id,
        "events": final_events,
        "validation": validation,
    }

# from fastapi import APIRouter, HTTPException
# from datetime import date
# from app.models import DayPlanRequest, FeedbackRequest
# from app.services.auth_service import get_user_by_id
# from app.agents.agent2_analyser import analyse_user_history
# from app.agents.agent3_feedback import fallback_suggestions
# from app.agents.agent1_day_planner import generate_day_plan_with_gpt
# from app.services.history_service import save_plan, get_history, save_feedback
# from app.services.notification_service import schedule_optional_sms
# from app.agents.agent4_notification import schedule_day_plan
# router = APIRouter(tags=["Planner"])


# @router.post("/planner/generate")
# def generate_plan(req: DayPlanRequest):
#     user = get_user_by_id(req.user_id)
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")

#     profile = {k: user[k] for k in ["name", "email", "phone", "height", "weight", "gender", "age", "profession", "diseases", "disability"]}
#     prefs = {
#         "wake_time": req.wake_time,
#         "sleep_time": req.sleep_time,
#         "diet_type": req.diet_type,
#         "fitness_type": req.fitness_type,
#         "workout_duration": req.workout_duration,
#         "extra_preferences": req.preferences or {}
#     }
#     analysis = analyse_user_history(req.user_id)
#     fallback = fallback_suggestions(profile, prefs)
#     events = generate_day_plan_with_gpt(profile, prefs, analysis, fallback)
#     notification = schedule_optional_sms(req.phone, events)
#     plan_id = save_plan(req.user_id, str(date.today()), req.wake_time, req.sleep_time, req.diet_type, req.fitness_type, req.workout_duration, events, {"agent2": analysis, "agent3": fallback, "notification": notification})

#     return {
#         "plan_id": plan_id,
#         "date": str(date.today()),
#         "user_id": req.user_id,
#         "events": events,
#         "agent_analysis": {
#             "agent1": "Azure OpenAI GPT-4o if configured, otherwise local fallback",
#             "agent2": analysis,
#             "agent3": fallback
#         },
#         "notification": notification
#     }


# @router.get("/history/{user_id}")
# def history(user_id: int, limit: int = 10):
#     return {"user_id": user_id, "entries": get_history(user_id, limit)}


# @router.post("/feedback")
# def feedback(req: FeedbackRequest):
#     save_feedback(req.user_id, req.plan_id, req.rating, req.comments or "")
#     return {"message": "Feedback saved successfully"}
