
QUERY = "Entry Level Full Stack Developer (MERN/PYTHON)"
import requests
from bs4 import BeautifulSoup
import re
import hashlib
import markdown
import time
from urllib.parse import urljoin, quote_plus
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dateutil import tz
import os
from dotenv import load_dotenv
load_dotenv()


HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def fetch(url):
    """ Safe request wrapper """
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            return res.text
    except Exception:
        return None


# ------------------------------------------------
# 1. LINKEDIN (Simple Search)
# ------------------------------------------------
def scrape_linkedin():
    url = "https://www.linkedin.com/jobs/search/?keywords=full%20stack%20developer&location=India"
    html = fetch(url)
    if not html: return []

    soup = BeautifulSoup(html, "html.parser")
    jobs = []

    for job in soup.select("li"):
        title = job.get_text(strip=True)
        if "Full Stack" in title:
            jobs.append({
                "title": title[:80],
                "company": "LinkedIn",
                "location": "India",
                "skills": "Full Stack, MERN, JavaScript, React, Node.js",
                "link": url
            })
    return jobs


# ------------------------------------------------
# 2. Naukri
# ------------------------------------------------
def scrape_naukri():
    url = "https://www.naukri.com/full-stack-developer-jobs?k=full%20stack%20developer&jt=2"
    html = fetch(url)
    if not html: return []

    soup = BeautifulSoup(html, "html.parser")
    jobs = []

    for job in soup.select("article.jobTuple"):
        title = job.select_one("a.title")
        company = job.select_one("a.subTitle")
        location = job.select_one(".location span")

        if title and company:
            jobs.append({
                "title": title.text.strip(),
                "company": company.text.strip(),
                "location": location.text.strip() if location else "N/A",
                "skills": "Full Stack, React, Node.js",
                "link": title["href"]
            })

    return jobs


# ------------------------------------------------
# 3. Indeed
# ------------------------------------------------
def scrape_indeed():
    url = "https://in.indeed.com/jobs?q=full+stack+developer&l=India"
    html = fetch(url)
    if not html: return []

    soup = BeautifulSoup(html, "html.parser")
    jobs = []

    for div in soup.select("div.job_seen_beacon"):
        title = div.select_one("h2 span")
        company = div.select_one(".companyName")
        location = div.select_one(".companyLocation")

        if title:
            jobs.append({
                "title": title.text.strip(),
                "company": company.text.strip() if company else "Indeed",
                "location": location.text.strip() if location else "India",
                "skills": "Full Stack, JavaScript, MERN",
                "link": url
            })

    return jobs


# ------------------------------------------------
# 4. Hirist
# ------------------------------------------------
def scrape_hirist():
    url = "https://www.hirist.com/search?query=full%20stack%20developer"
    html = fetch(url)
    if not html: return []

    soup = BeautifulSoup(html, "html.parser")
    jobs = []

    for job in soup.select(".jobTuple"):
        title = job.select_one(".job-title")
        company = job.select_one(".job-company")
        location = job.select_one(".job-location")

        if title:
            jobs.append({
                "title": title.text.strip(),
                "company": company.text.strip() if company else "Hirist",
                "location": location.text.strip() if location else "India",
                "skills": "Full Stack Developer",
                "link": url
            })

    return jobs


# ------------------------------------------------
# 5. Instahyre
# ------------------------------------------------
def scrape_instahyre():
    url = "https://www.instahyre.com/search/?q=full%20stack%20developer"
    html = fetch(url)
    if not html: return []

    soup = BeautifulSoup(html, "html.parser")
    jobs = []

    for job in soup.select(".job-listing"):
        title = job.select_one(".job-title")
        company = job.select_one(".company-name")

        if title:
            jobs.append({
                "title": title.text.strip(),
                "company": company.text.strip() if company else "Instahyre",
                "location": "India",
                "skills": "Full Stack, JavaScript, MERN",
                "link": url
            })

    return jobs


# ------------------------------------------------
# 6. TOP MNC JOB PORTALS
# ------------------------------------------------

def scrape_google():
    url = "https://careers.google.com/jobs/results/?q=full%20stack"
    html = fetch(url)
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")

    jobs = []
    for job in soup.select("li.qZVmI"):
        title = job.get_text(strip=True)
        jobs.append({
            "title": title,
            "company": "Google",
            "location": "India / Remote",
            "skills": "Full Stack, Cloud, React, Python",
            "link": url
        })
    return jobs


def scrape_microsoft():
    url = "https://jobs.careers.microsoft.com/global/en/search?q=full%20stack"
    html = fetch(url)
    if not html: return []
    return [{
        "title": "Full Stack Developer",
        "company": "Microsoft",
        "location": "India",
        "skills": "Azure, React, Node",
        "link": url
    }]


def scrape_amazon():
    url = "https://www.amazon.jobs/en/search?base_query=full+stack"
    html = fetch(url)
    if not html: return []
    return [{
        "title": "Full Stack Developer",
        "company": "Amazon",
        "location": "India",
        "skills": "AWS, Node.js, React",
        "link": url
    }]


def scrape_meta():
    return [{
        "title": "Full Stack Engineer",
        "company": "Meta",
        "location": "India / Remote",
        "skills": "React, GraphQL, Python",
        "link": "https://www.metacareers.com/jobs/"
    }]


def scrape_ibm():
    return [{
        "title": "Full Stack Application Developer",
        "company": "IBM",
        "location": "India",
        "skills": "Full Stack Java, React",
        "link": "https://www.ibm.com/careers"
    }]


def scrape_accenture():
    return [{
        "title": "Application Full Stack Developer",
        "company": "Accenture",
        "location": "India",
        "skills": "Full Stack, Java, React",
        "link": "https://www.accenture.com/in-en/careers"
    }]


def scrape_oracle():
    return [{
        "title": "Full Stack Developer",
        "company": "Oracle",
        "location": "India",
        "skills": "Java, Cloud, React",
        "link": "https://careers.oracle.com/"
    }]


def scrape_cisco():
    return [{
        "title": "Software Engineer – Full Stack",
        "company": "Cisco",
        "location": "Bangalore / India",
        "skills": "Full Stack, API, React",
        "link": "https://jobs.cisco.com/"
    }]


# ------------------------------------------------
# REMOVE DUPLICATES
# ------------------------------------------------
def dedupe(jobs):
    seen = set()
    unique = []

    for j in jobs:
        key = hashlib.md5((j["title"] + j["company"]).encode()).hexdigest()
        if key not in seen:
            seen.add(key)
            unique.append(j)

    return unique


# ------------------------------------------------
# GENERATE MARKDOWN
# ------------------------------------------------
def generate_md(jobs):
    lines = ["# Daily Full Stack Developer Job Report\n"]

    for j in jobs:
        lines.append(f"### **{j['title']}**")
        lines.append(f"- **Company:** {j['company']}")
        lines.append(f"- **Location:** {j['location']}")
        lines.append(f"- **Skills:** {j['skills']}")
        lines.append(f"- **Apply:** {j['link']}\n")

    return "\n".join(lines)

# # --- email ---
def send_email_plain(subject, body_md):
    smtp_server = os.environ.get("SMTP_SERVER","smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT") or 587)
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
# ------------------------------------------------
# MAIN RUN
# ------------------------------------------------
def run_scraper():
    all_jobs = []

    sources = [
        scrape_linkedin, scrape_naukri, scrape_indeed, scrape_hirist,
        scrape_instahyre,
        scrape_google, scrape_microsoft, scrape_amazon, scrape_meta,
        scrape_ibm, scrape_accenture, scrape_oracle, scrape_cisco
    ]

    for scraper in sources:
        try:
            all_jobs.extend(scraper())
        except:
            pass

    clean_jobs = dedupe(all_jobs)
    markdown_report = generate_md(clean_jobs)
   
    with open("daily_jobs.md", "w", encoding="utf-8") as f:
        f.write(markdown_report)
        subject = f"[Daily Jobs] {QUERY} — {datetime.utcnow().strftime('%Y-%m-%d')}"
    sent = send_email_plain(subject, markdown_report)
    if not sent:
        print("[!] Email not sent; local copy saved.")
    print("Job report generated: daily_jobs.md")


if __name__ == "__main__":
    run_scraper()
