import requests
from bs4 import BeautifulSoup
import re
import json
import time
import pandas as pd
from datetime import datetime

# --- You MUST define this function ---
def scrape_print_page(bill_number, session):
    # TODO: Replace this with your real scraping logic.
    # Here's a dummy response for demonstration.
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
        "format": "PDF",
        "title_line": None,
        "summary_title": None,
        "summary_text": "",
        "history": []
    }

    for i, line in enumerate(lines):
        if re.match(r"^[SH]\*?\s?\d+", line):
            data["title_line"] = line.strip()
        elif line.startswith("Summary:"):
            data["summary_title"] = line.replace("Summary:", "").strip()
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
    else:
        data["current_status"] = "No history"

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

# --- Start scraping ---
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

# --- Save raw data ---
with open(f"sc_bills_session_{session}.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

# --- Flatten preview CSV ---
flat_data = [{
    "bill_number": bill["bill_number"],
    "session": bill["session"],
    "format": bill.get("format", "unknown"),
    "text": bill.get("text", "")[:500]
} for bill in results]

pd.DataFrame(flat_data).to_csv(f"sc_bills_session_{session}.csv", index=False)

# --- Parse and structure data ---
parsed_bills = []

for item in results:
    text = item.get('text', '')
    lines = text.split('\n')
    session = item.get('session', 'N/A')
    bill_name_match = re.search(r'(S\*?\d{4}|H\*?\d{4})', text)
    bill_name = bill_name_match.group(1) if bill_name_match else 'N/A'
    bill_number = re.sub(r'\D', '', bill_name) if bill_name != 'N/A' else item.get('bill_number', 'N/A')

    upper_block = []
    summary_start = False
    for line in lines:
        if line.startswith("Summary:"):
            summary_start = True
            continue
        if summary_start and line.strip().isupper():
            upper_block.append(line.strip())
        else:
            break
    bill_summary = ' '.join(upper_block).strip() if upper_block else 'N/A'

    status_lines = []
    found_summary = False
    for line in lines:
        if line.startswith("Summary:"):
            found_summary = True
            continue
        if found_summary and (line.strip().islower() or re.match(r'^\d{2}/\d{2}/\d{2}', line.strip())):
            status_lines.append(line.strip())

    has_fiscal = check_fiscal_impact(session, bill_number)

    parsed_bills.append({
        "bill_session": session,
        "bill_name": bill_name,
        "bill_number": bill_number,
        "bill_summary": bill_summary,
        "bill_status": status_lines[-1] if status_lines else 'N/A',
        "hasFiscal": has_fiscal
    })

# --- Save structured output ---
with open(f"sc_bills_parsed_session_{session}.json", "w", encoding="utf-8") as f:
    json.dump(parsed_bills, f, ensure_ascii=False, indent=2)

pd.DataFrame(parsed_bills).to_csv(f"sc_bills_parsed_session_{session}.csv", index=False)
