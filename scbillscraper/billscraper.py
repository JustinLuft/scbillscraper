import requests
from bs4 import BeautifulSoup
import re
import json
import time
import pandas as pd
from datetime import datetime

def scrape_print_page(bill_number, session):
    # Simulated dummy PDF text for demo purposes
    return {
        "bill_number": str(bill_number).zfill(4),
        "session": session,
        "format": "PDF",
        "text": f"S*{str(bill_number).zfill(4)}\nSummary:\nEXAMPLE SUMMARY FOR BILL {bill_number}\n12/04/24 Senate Introduced and adopted"
    }

def parse_pdf_text(bill):
    lines = bill["text"].splitlines()
    data = {
        "bill_number": bill["bill_number"],
        "session": bill["session"],
        "format": bill["format"],
        "title_line": None,
        "summary_title": None,
        "summary_text": "",
        "history": [],
        "current_status": "No history"
    }

    for i, line in enumerate(lines):
        if re.match(r"^[SH]\*?\s?\d+", line):
            data["title_line"] = line.strip()
        elif line.startswith("Summary:"):
            summary_lines = []
            j = i + 1
            while j < len(lines) and not re.match(r"\d{2}/\d{2}/\d{2}", lines[j]):
                summary_lines.append(lines[j].strip())
                j += 1
            data["summary_text"] = " ".join(summary_lines)
        elif re.match(r"\d{2}/\d{2}/\d{2}", line.strip()):
            parts = line.strip().split(None, 2)
            if len(parts) == 3:
                date_str, chamber, action = parts
                try:
                    date_obj = datetime.strptime(date_str, "%m/%d/%y")
                except:
                    date_obj = None
                data["history"].append({
                    "date": date_str,
                    "date_obj": date_obj,
                    "chamber": chamber,
                    "action": action
                })

    if data["history"]:
        latest = max(data["history"], key=lambda x: x["date_obj"] or datetime.min)
        data["current_status"] = f"{latest['date']} {latest['chamber']} {latest['action']}"

    return data

def check_fiscal_impact(session, bill_number):
    url = f"https://www.scstatehouse.gov/fiscalimpact.php?type=BILL&session={session}&bill_number={str(bill_number).zfill(4)}"
    try:
        resp = requests.get(url, timeout=5)
        if "No Fiscal Impact Statements Returned" in resp.text:
            return "no"
        return "yes"
    except Exception as e:
        print(f"Error checking fiscal impact for bill {bill_number}: {e}")
        return "unknown"

# --- Scrape bills ---
session = 126
results = []

for i in range(1, 5):
    print(f"Scraping bill {i}...")
    result = scrape_print_page(i, session)
    if result is None or "INVALID BILL" in result["text"]:
        print(f"Stopping at bill {i} (invalid or missing).")
        break
    results.append(result)
    time.sleep(1)

# --- Save raw scraped data ---
with open(f"sc_bills_session_{session}.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

# --- Flat CSV preview ---
flat_data = [{
    "bill_number": bill["bill_number"],
    "session": bill["session"],
    "format": bill.get("format", "unknown"),
    "text": bill.get("text", "")[:500]
} for bill in results]
pd.DataFrame(flat_data).to_csv(f"sc_bills_session_{session}.csv", index=False)

# --- Parse structured fields ---
parsed_bills = []

for bill in results:
    parsed = parse_pdf_text(bill)
    bill_name = parsed["title_line"] or f"S*{bill['bill_number']}"
    bill_number = re.sub(r'\D', '', bill_name)
    has_fiscal = check_fiscal_impact(session, bill_number)

    parsed_bills.append({
        "bill_session": session,
        "bill_name": bill_name,
        "bill_number": bill_number,
        "bill_summary": parsed["summary_text"] or "N/A",
        "bill_status": parsed["current_status"],
        "hasFiscal": has_fiscal
    })

# --- Save structured data ---
with open(f"sc_bills_parsed_session_{session}.json", "w", encoding="utf-8") as f:
    json.dump(parsed_bills, f, ensure_ascii=False, indent=2)

pd.DataFrame(parsed_bills).to_csv(f"sc_bills_parsed_session_{session}.csv", index=False)
