# -*- coding: utf-8 -*-
"""
Day 6: Python Automation Tools

Topics Covered:
1. File Organizer Automation
2. Web Scraping Automation
3. Email Alert Automation
4. argparse Example
5. schedule Example
6. subprocess Example
7. APScheduler Cron Example

Install required packages:
pip install requests beautifulsoup4 schedule apscheduler
"""

import os
import csv
import time
import shutil
import argparse
import smtplib
import subprocess
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText

import requests
import schedule
from bs4 import BeautifulSoup
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger


# ==========================================================
# 1. File Organizer Automation
# ==========================================================

EXT_MAP = {
    ".pdf": "PDFs",
    ".jpg": "Images",
    ".jpeg": "Images",
    ".png": "Images",
    ".csv": "Data",
    ".xlsx": "Data",
    ".xls": "Data",
    ".mp4": "Videos",
    ".txt": "TextFiles",
    ".docx": "Documents",
    ".py": "PythonFiles"
}


def organise(folder: str):
    src = Path(folder)

    if not src.exists():
        print("Folder does not exist.")
        return

    for file in src.iterdir():
        if file.is_file():
            folder_name = EXT_MAP.get(file.suffix.lower(), "Other")
            destination = src / folder_name
            destination.mkdir(exist_ok=True)

            shutil.move(str(file), str(destination / file.name))
            print(f"Moved {file.name} → {folder_name}/")


# ==========================================================
# 2. Web Scraping Automation
# ==========================================================

def scrape_quotes() -> list:
    url = "https://quotes.toscrape.com"

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    quotes = []

    for quote in soup.select(".quote")[:5]:
        quotes.append({
            "text": quote.find("span", class_="text").text,
            "author": quote.find("small").text,
            "scraped_at": datetime.now().isoformat()
        })

    return quotes


def save_to_csv(rows, path="quotes.csv"):
    file_exists = Path(path).exists()

    with open(path, "a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["text", "author", "scraped_at"]
        )

        if not file_exists:
            writer.writeheader()

        writer.writerows(rows)

    print(f"Saved {len(rows)} rows into {path}")


# ==========================================================
# 3. Email Alert Automation
# ==========================================================

def send_alert(subject: str, body: str, to: str, gmail_user: str, app_pw: str):
    message = MIMEText(body)
    message["Subject"] = subject
    message["From"] = gmail_user
    message["To"] = to

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_user, app_pw)
        server.send_message(message)

    print("Email alert sent successfully.")


# ==========================================================
# 4. schedule Example
# ==========================================================

def job_scrape():
    data = scrape_quotes()
    save_to_csv(data)
    print(f"[{datetime.now():%H:%M:%S}] Scraping job completed.")


def job_report():
    print(f"[{datetime.now():%H:%M:%S}] Daily report generated.")


def run_schedule_demo():
    schedule.every(10).seconds.do(job_scrape)
    schedule.every().day.at("08:00").do(job_report)

    print("Schedule demo started for 35 seconds...")

    deadline = time.time() + 35

    while time.time() < deadline:
        schedule.run_pending()
        time.sleep(1)

    print("Schedule demo completed.")


# ==========================================================
# 5. subprocess Example
# ==========================================================

def run_subprocess_command(command: str):
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True
    )

    print("Command Output:")
    print(result.stdout)

    if result.stderr:
        print("Command Error:")
        print(result.stderr)


# ==========================================================
# 6. APScheduler Cron Example
# ==========================================================

def run_apscheduler_demo():
    scheduler = BackgroundScheduler()

    scheduler.add_job(
        job_scrape,
        "interval",
        seconds=15,
        id="scraper"
    )

    scheduler.add_job(
        job_report,
        CronTrigger(day_of_week="mon-fri", hour=7, minute=30),
        id="daily_report"
    )

    scheduler.start()

    print("APScheduler started. Jobs:")

    for job in scheduler.get_jobs():
        print(f"{job.id} — next run: {job.next_run_time}")

    time.sleep(40)

    scheduler.shutdown()
    print("APScheduler stopped.")


# ==========================================================
# 7. argparse Main Function
# ==========================================================

def main():
    parser = argparse.ArgumentParser(
        description="Day 6 Python Automation Tools"
    )

    parser.add_argument(
        "--organise",
        help="Organise files in the given folder path"
    )

    parser.add_argument(
        "--scrape",
        action="store_true",
        help="Scrape quotes and save into CSV"
    )

    parser.add_argument(
        "--schedule-demo",
        action="store_true",
        help="Run schedule demo"
    )

    parser.add_argument(
        "--subprocess",
        help="Run a command using subprocess"
    )

    parser.add_argument(
        "--apscheduler-demo",
        action="store_true",
        help="Run APScheduler demo"
    )

    args = parser.parse_args()

    if args.organise:
        organise(args.organise)

    elif args.scrape:
        data = scrape_quotes()
        save_to_csv(data)

    elif args.schedule_demo:
        run_schedule_demo()

    elif args.subprocess:
        run_subprocess_command(args.subprocess)

    elif args.apscheduler_demo:
        run_apscheduler_demo()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()