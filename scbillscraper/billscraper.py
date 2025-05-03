import requests
import pdfplumber
import json
import time
import pandas as pd
import re
from datetime import datetime

# --- PDF Scraping and Text Extraction ---
def scrape_pdf(bill_number, session):
    url = f"https://www.scstatehouse.gov/billsearch.php?billnumbers={bill_number}&session={session}&summary=B&PRINT=1"
    try:
        print(f"Downloading PDF for Bill {bill_number}...")
        response = requests.get(url, timeout=10)
        
        # Check for 404 errors
        if response.status_code == 404:
            print(f"Bill {bill_number} does not exist at the given URL.")
            return None
        
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

        return {"bill_number": str(bill_number).zfill(4), "session": session, "text": text, "url": url}

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
        "history": [],
        "bill_url": bill.get("url", ""),  # Add the URL to the data
        "current_status": "No history"  # Default status in case no history is found
    }

    # Skip the first line (which is the date and time)
    lines = lines[1:] if len(lines) > 0 and re.match(r"\w{3}\s\d{2},\s\d{4}", lines[0]) else lines

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

# --- Save Parsed CSV Only ---
flat_data = []
for bill in results:
    # Parse the PDF text to get the structured data
    parsed_data = parse_pdf_text(bill)

    # Get fiscal impact for each bill
    fiscal_impact = check_fiscal_impact(session, bill["bill_number"])

    # Add parsed data and fiscal impact to the flat_data list
    flat_data.append({
        "bill_number": bill["bill_number"],
        "session": bill["session"],
        "format": bill.get("format", "unknown"),
        "text": bill.get("text", "")[:500],  # Preview only the first 500 characters of text
        "bill_url": bill.get("url", ""),  # Add the bill's URL
        "fiscal_impact": fiscal_impact,  # Add the fiscal impact
        "current_status": parsed_data["current_status"]  # Add the current status
    })

df = pd.DataFrame(flat_data)
parsed_csv_filename = f"sc_bills_parsed_session_{session}.csv"
df.to_csv(parsed_csv_filename, index=False)

print(f"Saved: {parsed_csv_filename}")
