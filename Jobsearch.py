#!/usr/bin/env python3
"""
job_search.py
Searches multiple job sites for "Entry Level MERN Stack Developer" roles,
deduplicates, creates a markdown report, and emails it.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote_plus
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dateutil import tz
import hashlib

# CONFIG
QUERY = "Entry Level MERN Stack Developer"
LOC = ""  # leave blank for site-wide; can set e.g. "Bangalore"
SOURCES = ["indeed", "naukri", "hirist", "instahyre", "linkedin"]  # used to control which parsers run
RESULT_LIMIT_PER_SOURCE = 20

# --- helpers ---
def normalize_text(t):
    return re.sub(r'\s+', ' ', (t or '').strip())

def make_id(title, company, link):
    key = f"{title}|{company}|{link}"
    return hashlib.sha1(key.encode('utf-8')).hexdigest()

# --- site parsers ---
def parse_indeed():
    # Indeed basic search results (may vary by region)
    q = quote_plus(QUERY)
    url = f"https://www.indeed.com/jobs?q={q}&limit=20"
    r = requests.get(url, timeout=15, headers={"User-Agent": "job-bot/1.0"})
    soup = BeautifulSoup(r.text, "html.parser")
    jobs = []
    for card in soup.select("a[href*='/rc/clk'], a[href*='/pagead/']")[:RESULT_LIMIT_PER_SOURCE]:
        title = normalize_text(card.get_text(separator=" ", strip=True))
        link = urljoin("https://www.indeed.com", card.get('href'))
        # try to find company & location upward
        parent = card.find_parent()
        company = ""
        location = ""
        if parent:
            comp = parent.select_one(".company") or parent.select_one(".companyName")
            if comp:
                company = normalize_text(comp.get_text())
            loc = parent.select_one(".location") or parent.select_one(".companyLocation")
            if loc:
                location = normalize_text(loc.get_text())
        jobs.append({
            "title": title or "N/A",
            "company": company or "N/A",
            "location": location or "N/A",
            "link": link,
            "skills": guess_skills_from_title(title),
            "source": "Indeed"
        })
    return jobs

def parse_naukri():
    q = quote_plus(QUERY)
    url = f"https://www.naukri.com/{q}-jobs"
    r = requests.get(url, timeout=15, headers={"User-Agent": "job-bot/1.0"})
    soup = BeautifulSoup(r.text, "html.parser")
    jobs = []
    # Naukri uses jobTuple class
    for jt in soup.select("article.jobTuple, li.serpJob")[:RESULT_LIMIT_PER_SOURCE]:
        title_el = jt.select_one("a[href].title, a.jobTitle")
        if not title_el:
            continue
        title = normalize_text(title_el.get_text())
        link = title_el.get('href')
        comp = jt.select_one("a.subTitle, .companyInfo .ellipsis")
        company = normalize_text(comp.get_text()) if comp else "N/A"
        loc = jt.select_one(".location, .job-segment .ellipsis")
        location = normalize_text(loc.get_text()) if loc else "N/A"
        jobs.append({
            "title": title,
            "company": company,
            "location": location,
            "link": link,
            "skills": guess_skills_from_title(title),
            "source": "Naukri"
        })
    return jobs

def parse_hirist():
    q = quote_plus(QUERY)
    url = f"https://www.hirist.com/jobs?q={q}"
    r = requests.get(url, timeout=15, headers={"User-Agent": "job-bot/1.0"})
    soup = BeautifulSoup(r.text, "html.parser")
    jobs = []
    for card in soup.select(".job-listing, .job")[:RESULT_LIMIT_PER_SOURCE]:
        t = card.select_one(".job-title a, a.job-link")
        if not t:
            continue
        title = normalize_text(t.get_text())
        link = urljoin("https://www.hirist.com", t.get('href'))
        company = normalize_text(card.select_one(".company").get_text()) if card.select_one(".company") else "N/A"
        loc = normalize_text(card.select_one(".location").get_text()) if card.select_one(".location") else "N/A"
        jobs.append({
            "title": title, "company": company, "location": loc, "link": link,
            "skills": guess_skills_from_title(title), "source": "Hirist"
        })
    return jobs

def parse_instahyre():
    # Instahyre blocks bots sometimes; try basic search page
    q = quote_plus(QUERY)
    url = f"https://instahyre.com/search?q={q}"
    r = requests.get(url, timeout=15, headers={"User-Agent": "job-bot/1.0"})
    soup = BeautifulSoup(r.text, "html.parser")
    jobs = []
    for card in soup.select(".job-card, .job-list-item")[:RESULT_LIMIT_PER_SOURCE]:
        t = card.select_one("a[href].title")
        if not t:
            continue
        title = normalize_text(t.get_text())
        link = urljoin("https://instahyre.com", t.get('href'))
        company = normalize_text(card.select_one(".company").get_text()) if card.select_one(".company") else "N/A"
        loc = normalize_text(card.select_one(".location").get_text()) if card.select_one(".location") else "N/A"
        jobs.append({"title": title, "company": company, "location": loc, "link": link,
                     "skills": guess_skills_from_title(title), "source": "Instahyre"})
    return jobs

def parse_linkedin():
    # LinkedIn search pages are often behind login; attempt public search fallback
    q = quote_plus(QUERY)
    url = f"https://www.linkedin.com/jobs/search?keywords={q}"
    r = requests.get(url, timeout=15, headers={"User-Agent": "job-bot/1.0"})
    soup = BeautifulSoup(r.text, "html.parser")
    jobs = []
    for card in soup.select(".result-card, .jobs-search-results__list-item")[:RESULT_LIMIT_PER_SOURCE]:
        t = card.select_one("a[href].result-card__full-card-link, a.job-card-list__title")
        if not t:
            continue
        title = normalize_text(t.get_text())
        link = urljoin("https://www.linkedin.com", t.get('href'))
        company_el = card.select_one(".result-card__subtitle, .job-card-container__company-name")
        company = normalize_text(company_el.get_text()) if company_el else "N/A"
        loc_el = card.select_one(".job-result-card__location, .job-card-container__metadata-item")
        location = normalize_text(loc_el.get_text()) if loc_el else "N/A"
        jobs.append({"title": title, "company": company, "location": location, "link": link,
                     "skills": guess_skills_from_title(title), "source": "LinkedIn"})
    return jobs

# fallback skill guessing
def guess_skills_from_title(title):
    txt = (title or "").lower()
    skills = []
    candidates = ["react", "node", "express", "mongodb", "mern", "javascript", "html", "css", "next.js", "next", "git", "aws"]
    for c in candidates:
        if c in txt:
            skills.append(c.upper() if len(c) <= 4 else c.title())
    # always include MERN if words present
    if "mern" in txt:
        if "MERN" not in skills:
            skills.insert(0, "MERN")
    return ", ".join(skills) or "MERN, JavaScript"

# --- orchestrator ---
def collect_all():
    funcs = []
    mapping = {
        "indeed": parse_indeed,
        "naukri": parse_naukri,
        "hirist": parse_hirist,
        "instahyre": parse_instahyre,
        "linkedin": parse_linkedin
    }
    for s in SOURCES:
        f = mapping.get(s)
        if f:
            try:
                jobs = f()
                print(f"[+] {s}: found {len(jobs)}")
                funcs.extend(jobs)
            except Exception as e:
                print(f"[!] {s} parser error: {e}")
    # deduplicate
    seen = {}
    unique = []
    for j in funcs:
        idv = make_id(j.get('title'), j.get('company'), j.get('link'))
        if idv in seen:
            # merge sources if duplicate
            seen[idv]['source'] += f", {j.get('source')}"
        else:
            seen[idv] = j
            unique.append(j)
    return unique

# --- report generation ---
def make_markdown(jobs):
    now = datetime.utcnow().replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal())
    header = f"# Daily Job Report — {QUERY}\n\nGenerated: {now.strftime('%Y-%m-%d %H:%M %Z')}\n\n"
    lines = [header]
    for j in sorted(jobs, key=lambda x: x.get('company','')):
        lines.append(f"## {j.get('title')}\n")
        lines.append(f"- **Company:** {j.get('company')}\n")
        lines.append(f"- **Location:** {j.get('location')}\n")
        lines.append(f"- **Skills:** {j.get('skills')}\n")
        lines.append(f"- **Apply:** {j.get('link')}\n")
        lines.append(f"- **Source:** {j.get('source')}\n")
        lines.append("\n---\n")
    if not jobs:
        lines.append("No fresh jobs found today.\n")
    return "\n".join(lines)

# --- email ---
def send_email_plain(subject, body_md):
    smtp_server = os.environ.get("SMTP_SERVER","smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("EMAIL_USER")
    pwd = os.environ.get("EMAIL_PASS")
    recipient = os.environ.get("RECIPIENT_EMAIL")

    if not all([smtp_server, smtp_port, user, pwd, recipient]):
        print("[!] Missing SMTP config in environment variables.",smtp_server, smtp_port, user, pwd, recipient)
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = recipient

    # plain text + markdown for body
    part1 = MIMEText(body_md, "plain")
    msg.attach(part1)

    s = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
    try:
        s.starttls()
        s.login(user, pwd)
        s.sendmail(user, [recipient], msg.as_string())
        print("[+] Email sent to", recipient)
        return True
    finally:
        s.quit()

# --- main ---
import os
from dotenv import load_dotenv
load_dotenv()
def main():
    print("[*] Collecting jobs...")
    jobs = collect_all()
    print(f"[*] {len(jobs)} unique jobs collected.")
    md = make_markdown(jobs)
    # Save locally for debug
    with open("daily_jobs.md", "w", encoding="utf-8") as f:
        f.write(md)
    subject = f"[Daily Jobs] {QUERY} — {datetime.utcnow().strftime('%Y-%m-%d')}"
    sent = send_email_plain(subject, md)
    if not sent:
        print("[!] Email not sent; local copy saved.")

if __name__ == "__main__":
    main()
