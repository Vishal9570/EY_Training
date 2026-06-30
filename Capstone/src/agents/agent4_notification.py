from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from plyer import notification

scheduler = BackgroundScheduler()


def desktop_notification(title, message):

    notification.notify(
        title=title,
        message=message,
        timeout=10
    )


def schedule_day_plan(events):

    """
    events = [
        {
            "time":"07:30",
            "activity":"Poha with curd",
            "notes":"Healthy Indian breakfast",
            "category":"meal"
        }
    ]
    """

    if not scheduler.running:
        scheduler.start()

    for event in events:

        try:

            event_time = datetime.strptime(
                event["time"],
                "%H:%M"
            )

            today = datetime.now()

            run_time = today.replace(
                hour=event_time.hour,
                minute=event_time.minute,
                second=0,
                microsecond=0
            )

            # Skip past events
            if run_time < today:
                continue

            scheduler.add_job(
                desktop_notification,
                trigger="date",
                run_date=run_time,
                args=[
                    f"⏰ {event['activity']}",
                    event["notes"]
                ],
                id=f"{event['time']}_{event['activity']}",
                replace_existing=True
            )

            print(f"Notification scheduled for {run_time}")

        except Exception as e:

            print(e)