#!/usr/bin/env python3
"""
Scrape daily contribution counts from GitHub's public contributions fragment
(the same HTML the profile page loads) and write data/contributions.json with
the raw days plus derived stats. No token needed.

Run every 6 hours by .github/workflows/update-profile-art.yml.
"""
import datetime
import json
import os
import re
import sys

import requests
from bs4 import BeautifulSoup

USERNAME = os.environ.get("GH_PROFILE_USER", "devgugga")
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "contributions.json")


def fetch_days():
    resp = requests.get(URL, headers={"User-Agent": "profile-readme-bot/1.0"}, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    tooltips = {t.get("for"): t.get_text(strip=True) for t in soup.find_all("tool-tip")}

    cells = soup.select("td.ContributionCalendar-day[data-date]")
    if not cells:
        sys.exit("no calendar cells found -- github markup may have changed")

    days = []
    for td in cells:
        text = tooltips.get(td.get("id"), "")
        m = re.match(r"([\d,]+) contribution", text)
        days.append({"date": td["data-date"], "count": int(m.group(1).replace(",", "")) if m else 0})
    days.sort(key=lambda d: d["date"])
    return days


def current_streak(days):
    i = len(days) - 1
    if days[i]["count"] == 0:
        i -= 1  # today isn't over yet -- don't break the streak on it
    n = 0
    while i >= 0 and days[i]["count"] > 0:
        n += 1
        i -= 1
    return n


def longest_streak(days):
    best = run = 0
    for d in days:
        run = run + 1 if d["count"] > 0 else 0
        best = max(best, run)
    return best


def build_data(days):
    total = sum(d["count"] for d in days)
    best = max(days, key=lambda d: d["count"])
    return {
        "username": USERNAME,
        "generated_at": datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "range": {"start": days[0]["date"], "end": days[-1]["date"]},
        "total_contributions": total,
        "active_days": sum(1 for d in days if d["count"] > 0),
        "current_streak": current_streak(days),
        "longest_streak": longest_streak(days),
        "best_day": best,
        "days": days,
    }


if __name__ == "__main__":
    data = build_data(fetch_days())
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(data, f, indent=2)
    print(f"wrote {OUT_PATH}: {data['total_contributions']} contributions, "
          f"streak {data['current_streak']} (longest {data['longest_streak']})")
