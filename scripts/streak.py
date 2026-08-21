#!/usr/bin/env python3
"""Generate a GitHub contribution streak card as a self-hosted SVG.

Replaces the third-party streak-stats service, which is slow on cold requests
and gets timed out by GitHub's image proxy. Everything here is computed from
the GitHub GraphQL API and committed as a static file, so the card always
loads instantly and can never break because someone else's server is busy.
"""
import json
import os
import subprocess
import sys
from datetime import date, datetime, timedelta

USER = os.environ.get("STREAK_USER", "Vikrant892")
OUT = os.environ.get("STREAK_OUT", "assets/streak.svg")

# Palette lifted from the previous card so the profile looks unchanged.
BG = "#0D1117"
BORDER = "#30363d"
ACCENT = "#2563eb"
TEXT = "#c9d1d9"
MUTED = "#8b949e"


def gh_graphql(query, **variables):
    cmd = ["gh", "api", "graphql", "-f", f"query={query}"]
    for k, v in variables.items():
        cmd += ["-f", f"{k}={v}"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        sys.exit(f"GraphQL call failed: {res.stderr.strip()}")
    return json.loads(res.stdout)


def contribution_years():
    q = '{ user(login: "%s") { contributionsCollection { contributionYears } } }' % USER
    d = gh_graphql(q)
    return d["data"]["user"]["contributionsCollection"]["contributionYears"]


def days_for_year(year):
    start = f"{year}-01-01T00:00:00Z"
    end = f"{year}-12-31T23:59:59Z"
    q = """
    { user(login: "%s") { contributionsCollection(from: "%s", to: "%s") {
        contributionCalendar { totalContributions
          weeks { contributionDays { date contributionCount } } } } } }
    """ % (USER, start, end)
    cal = gh_graphql(q)["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = {}
    for w in cal["weeks"]:
        for d in w["contributionDays"]:
            days[d["date"]] = d["contributionCount"]
    return cal["totalContributions"], days


def collect():
    total = 0
    all_days = {}
    for y in sorted(contribution_years()):
        t, days = days_for_year(y)
        total += t
        all_days.update(days)
    return total, all_days


def streaks(days):
    if not days:
        return (0, None, None), (0, None, None)
    today = date.today()
    keys = sorted(days)
    first = datetime.strptime(keys[0], "%Y-%m-%d").date()

    # Longest streak across the whole history.
    best = cur = 0
    best_end = cur_start = None
    best_start = None
    d = first
    while d <= today:
        k = d.isoformat()
        if days.get(k, 0) > 0:
            if cur == 0:
                cur_start = d
            cur += 1
            if cur > best:
                best, best_start, best_end = cur, cur_start, d
        else:
            cur = 0
        d += timedelta(days=1)

    # Current streak. Today counts if it already has contributions; if not, the
    # streak is still alive so long as yesterday does, because the day is not over.
    cur_len = 0
    cur_end = None
    anchor = today if days.get(today.isoformat(), 0) > 0 else today - timedelta(days=1)
    d = anchor
    while d >= first and days.get(d.isoformat(), 0) > 0:
        if cur_end is None:
            cur_end = d
        cur_len += 1
        d -= timedelta(days=1)
    cur_start_final = d + timedelta(days=1) if cur_len else None
    return (cur_len, cur_start_final, cur_end), (best, best_start, best_end)


def fmt(d):
    # %-d is not portable (fails on Windows), so strip the zero manually.
    return f"{d.day} {d.strftime('%b %Y')}" if d else ""


def rng(a, b):
    if not a:
        return "-"
    if a == b:
        return fmt(a)
    return f"{fmt(a)} - {fmt(b)}"


def build_svg(total, cur, best, first_day):
    cur_len, cur_a, cur_b = cur
    best_len, best_a, best_b = best
    total_range = f"{fmt(first_day)} - Present"

    def col(x, big, label, sub, accent=False):
        c = ACCENT if accent else TEXT
        return f"""
  <g transform="translate({x},0)">
    <text x="82" y="62" text-anchor="middle" font-size="34" font-weight="700" fill="{c}"
          font-family="Segoe UI, Ubuntu, sans-serif">{big}</text>
    <text x="82" y="88" text-anchor="middle" font-size="14" fill="{TEXT}"
          font-family="Segoe UI, Ubuntu, sans-serif">{label}</text>
    <text x="82" y="110" text-anchor="middle" font-size="11" fill="{MUTED}"
          font-family="Segoe UI, Ubuntu, sans-serif">{sub}</text>
  </g>"""

    ring = f"""
  <circle cx="247" cy="52" r="34" fill="none" stroke="{ACCENT}" stroke-width="4" />
  <text x="247" y="44" text-anchor="middle" font-size="26" font-weight="700" fill="{TEXT}"
        font-family="Segoe UI, Ubuntu, sans-serif">{cur_len}</text>
  <text x="247" y="62" text-anchor="middle" font-size="10" fill="{MUTED}"
        font-family="Segoe UI, Ubuntu, sans-serif">days</text>
  <text x="247" y="100" text-anchor="middle" font-size="14" fill="{ACCENT}"
        font-family="Segoe UI, Ubuntu, sans-serif">Current Streak</text>
  <text x="247" y="120" text-anchor="middle" font-size="11" fill="{MUTED}"
        font-family="Segoe UI, Ubuntu, sans-serif">{rng(cur_a, cur_b)}</text>"""

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="495" height="160" viewBox="0 0 495 160"
     role="img" aria-label="GitHub contribution streak for {USER}: {total} total contributions, current streak {cur_len} days, longest streak {best_len} days">
  <rect x="0.5" y="0.5" width="494" height="159" rx="6" fill="{BG}" stroke="{BORDER}" />
  <line x1="165" y1="28" x2="165" y2="132" stroke="{BORDER}" />
  <line x1="330" y1="28" x2="330" y2="132" stroke="{BORDER}" />
{col(0, total, "Total Contributions", total_range)}
{ring}
{col(330, best_len, "Longest Streak", rng(best_a, best_b))}
</svg>
"""


def main():
    total, days = collect()
    cur, best = streaks(days)
    # First day he actually contributed, not 1 Jan of his earliest active year.
    active = [d for d, c in days.items() if c > 0]
    first_day = datetime.strptime(min(active), "%Y-%m-%d").date() if active else None
    svg = build_svg(total, cur, best, first_day)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"total={total} current={cur[0]} longest={best[0]} -> {OUT}")


if __name__ == "__main__":
    main()
