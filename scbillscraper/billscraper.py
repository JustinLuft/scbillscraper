import requests
import pdfplumber
import json
import time
import pandas as pd
import re
from datetime import datetime

# --- PDF Scraping and Text Extraction ---
def scrape_pdf(bill_number, session):
    url = f"https://www.scstatehouse.gov/sess{session}/bills/{bill_number}/{bill_number}.pdf"
    try:
        print(f"Downloading PDF for Bill {bill_number}...")
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an exception if the request fails

        # Save the PDF locally
        pdf_filename = f"bill_{bill_number}.pdf"
        with open(pdf_filename, 'wb') as f:
            f.write(response.content)
        print(f"PDF for Bill {bill_number} downloaded successfully.")

        # Extract text from the PDF using pdfplumber
        with pdfplumber.open(pdf_filename) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
                else:
                    print(f"Warning: No text found on page {page.page_number}")

        if not text:
            print(f"No text extracted from Bill {bill_number}.")
        else:
            print(f"Text extracted from Bill {bill_number}: {text[:200]}...")  # Preview the first 200 characters of text

        return {"bill_number": str(bill_number).zfill(4), "session": session, "text": text}

    except Exception as e:
        print(f"Error downloading or processing PDF for Bill {bill_number}: {e}")
        return None

# --- PDF Text Parsing ---
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
        if re.match(r"^[SH]\*?\s?\d+", line):  # e.g. "S*0001" or "S 0003"
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

    # Find current status (latest date)
    if data["history"]:
        latest = max(data["history"], key=lambda x: x["date_obj"] or datetime.min)
        data["current_status"] = f"{latest['date']} {latest['chamber']} {latest['action']}"
    else:
        data["current_status"] = "No history"

    return data

# --- Scrape Each Bill ---
session = 126
results = []

for i in range(1, 5):  # Modify this range based on the number of bills you want to scrape
    print(f"Scraping bill {i}...")
    result = scrape_pdf(i, session)

    if result is None or "INVALID BILL" in result["text"]:
        print(f"Stopping at bill {i} (invalid or missing).")
        break  # Stop scraping if the bill is invalid

    results.append(result)
    time.sleep(1)  # Optional: be polite to the server

# --- Fiscal Impact Checker ---
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

# --- Save Original JSON and CSV ---
json_filename = f"sc_bills_session_{session}.json"
with open(json_filename, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

flat_data = []
for bill in results:
    flat_data.append({
        "bill_number": bill["bill_number"],
        "session": bill["session"],
        "format": bill.get("format", "unknown"),
        "text": bill.get("text", "")[:500]  # preview only
    })

df = pd.DataFrame(flat_data)
csv_filename = f"sc_bills_session_{session}.csv"
df.to_csv(csv_filename, index=False)

# --- Parse Each Bill into Structured Data ---
parsed_bills = []

for item in results:
    text = item.get('text', '')
    lines = text.split('\n')
    session = item.get('session', 'N/A')

    # Bill Name and Number
    bill_name_match = re.search(r'(S\*?\d{4}|H\*?\d{4})', text)
    bill_name = bill_name_match.group(1) if bill_name_match else 'N/A'
    bill_number = re.sub(r'\D', '', bill_name) if bill_name != 'N/A' else item.get('bill_number', 'N/A')

    # Extract UPPERCASE summary block after "Summary:"
    upper_block = []
    summary_start = False
    for line in lines:
        if line.startswith("Summary:"):
            summary_start = True
            continue
        if summary_start:
            if line.strip().isupper():
                upper_block.append(line.strip())
            else:
                break
    bill_summary = ' '.join(upper_block).strip() if upper_block else 'N/A'

    # Extract lowercase or date-based status lines
    status_lines = []
    found_summary = False
    for line in lines:
        if line.startswith("Summary:"):
            found_summary = True
            continue
        if found_summary:
            if line.strip().islower() or re.match(r'^\d{2}/\d{2}/\d{2}', line.strip()):
                status_lines.append(line.strip())

    # Fiscal impact column
    has_fiscal = check_fiscal_impact(session, bill_number)

    # Append parsed bill
    parsed_bills.append({
        "bill_session": session,
        "bill_name": bill_name,
        "bill_number": bill_number,
        "bill_summary": bill_summary,
        "bill_status": status_lines[-1] if status_lines else 'N/A',
        "hasFiscal": has_fiscal
    })

# --- Save Parsed Output Locally ---
parsed_json_filename = f"sc_bills_parsed_session_{session}.json"
with open(parsed_json_filename, "w", encoding="utf-8") as f:
    json.dump(parsed_bills, f, ensure_ascii=False, indent=2)

parsed_df = pd.DataFrame(parsed_bills)
parsed_csv_filename = f"sc_bills_parsed_session_{session}.csv"
parsed_df.to_csv(parsed_csv_filename, index=False)

print(f"Saved: {parsed_json_filename} and {parsed_csv_filename}")
