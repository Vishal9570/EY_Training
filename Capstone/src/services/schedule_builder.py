from datetime import datetime, timedelta
import re


def add_minutes(time_str: str, minutes: int) -> str:
    base = datetime.strptime(time_str, "%H:%M")
    return (base + timedelta(minutes=minutes)).strftime("%H:%M")


def to_minutes(time_str: str) -> int:
    h, m = time_str.split(":")
    return int(h) * 60 + int(m)


def minutes_to_time(minutes: int) -> str:
    minutes = minutes % (24 * 60)
    h = minutes // 60
    m = minutes % 60
    return f"{h:02d}:{m:02d}"


def parse_office_time(office_text: str):
    """
    Supports:
    - 9 AM to 7 PM
    - office 9am - 7pm
    - 09:30 to 18:30
    - 10 to 6
    """

    text = (office_text or "").lower().strip()

    if not text:
        return None

    # Case 1: 9 AM to 7 PM
    matches = re.findall(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)", text)

    if len(matches) >= 2:
        start_h = int(matches[0][0])
        start_m = int(matches[0][1] or 0)
        start_ampm = matches[0][2]

        end_h = int(matches[1][0])
        end_m = int(matches[1][1] or 0)
        end_ampm = matches[1][2]

        if start_ampm == "pm" and start_h != 12:
            start_h += 12
        if start_ampm == "am" and start_h == 12:
            start_h = 0

        if end_ampm == "pm" and end_h != 12:
            end_h += 12
        if end_ampm == "am" and end_h == 12:
            end_h = 0

        return {
            "start": f"{start_h:02d}:{start_m:02d}",
            "end": f"{end_h:02d}:{end_m:02d}",
        }

    # Case 2: 09:30 to 18:30
    matches_24h = re.findall(r"(\d{1,2}):(\d{2})", text)

    if len(matches_24h) >= 2:
        start_h = int(matches_24h[0][0])
        start_m = int(matches_24h[0][1])
        end_h = int(matches_24h[1][0])
        end_m = int(matches_24h[1][1])

        return {
            "start": f"{start_h:02d}:{start_m:02d}",
            "end": f"{end_h:02d}:{end_m:02d}",
        }

    # Case 3: office 10 to 6
    nums = re.findall(r"\b(\d{1,2})\b", text)

    if len(nums) >= 2:
        start_h = int(nums[0])
        end_h = int(nums[1])

        # Simple assumption for office:
        # start is AM, end is PM
        if start_h < 12:
            start_h = start_h

        if end_h <= 12:
            end_h += 12

        return {
            "start": f"{start_h:02d}:00",
            "end": f"{end_h:02d}:00",
        }

    return None


def build_fixed_schedule(
    wake_time: str,
    sleep_time: str,
    fitness_type: str,
    workout_duration: str,
    office_time: str = "",
):
    breakfast_time = add_minutes(wake_time, 120)
    lunch_time = add_minutes(breakfast_time, 240)
    tea_time = add_minutes(lunch_time, 240)
    dinner_time = add_minutes(tea_time, 180)
    workout_time = add_minutes(tea_time, 60)

    office = parse_office_time(office_time)

    if office:
        office_start = to_minutes(office["start"])
        office_end = to_minutes(office["end"])

        workout_candidate = to_minutes(workout_time)
        dinner_candidate = to_minutes(dinner_time)

        # If workout falls inside office time, move it after office.
        if office_start <= workout_candidate <= office_end:
            workout_time = minutes_to_time(office_end + 15)

        # Dinner should not happen inside office time.
        # Keep dinner after office, usually after workout.
        if office_start <= dinner_candidate <= office_end:
            dinner_time = minutes_to_time(office_end + 90)

        # If user wrote gym/workout after office, force workout after office.
        office_text = office_time.lower()
        if "gym after office" in office_text or "workout after office" in office_text:
            workout_time = minutes_to_time(office_end + 15)
            dinner_time = minutes_to_time(office_end + 105)

    workout_label = (
        "Gym workout"
        if fitness_type == "Gym"
        else "Yoga session"
        if fitness_type == "Yoga"
        else "Gym + yoga"
    )

    return {
        "wake": wake_time,
        "breakfast": breakfast_time,
        "lunch": lunch_time,
        "tea": tea_time,
        "workout": workout_time,
        "dinner": dinner_time,
        "reading": add_minutes(dinner_time, 60),
        "meditation": add_minutes(dinner_time, 105),
        "sleep": sleep_time,
        "workout_label": workout_label,
        "workout_duration": workout_duration,
        "office": office,
    }