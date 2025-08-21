# SC Bill Scraper

A project for scraping South Carolina legislative bill data, saving it into structured formats, and visualizing/searching bills through a web UI.  
It includes a **Python scraper** for extracting bill information and a **Next.js frontend** for displaying and interacting with the data.

## 🚀 Features
- 📑 Scrape SC legislative bills with Python  
- 💾 Store parsed results as CSV  
- ☁️ Upload scraped data to Firebase  
- 🌐 Modern Next.js + TypeScript frontend  
- 🎨 UI built with TailwindCSS + Shadcn/UI components  
- ⚙️ GitHub Actions workflows for automation  

## 📂 Project Structure
```
scbillscraper-main/
├── scbillscraper/
│   └── billscraper.py           # Python scraper
├── upload_to_firebase.py        # Script to upload CSV data to Firebase
├── sc_bills_parsed_session_126.csv # Example parsed data
├── .github/workflows/           # GitHub Actions CI/CD
│   ├── main.yml
│   └── upload.yml
```

## 🛠️ Setup & Usage

### 1. Python Scraper
1. Create a virtual environment and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the scraper:
   ```bash
   python scbillscraper/billscraper.py
   ```
   This generates a `sc_bills_parsed_session_XXX.csv` file.

3. (Optional) Upload data to Firebase:
   ```bash
   python upload_to_firebase.py
   ```

### 2. Next.js Frontend
1. Navigate to the frontend directory:
   ```bash
   cd src
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start development server:
   ```bash
   npm run dev
   ```
4. Build for production:
   ```bash
   npm run build && npm start
   ```

## 📦 Tech Stack
- **Python** (scraping + Firebase upload)  
- **Next.js 13** + **TypeScript** (frontend)  
- **TailwindCSS** + **Shadcn/UI** (UI)  
- **Firebase** (data storage)  
- **GitHub Actions** (automation)  

## 📄 License
This project is licensed under the MIT License — feel free to use and modify.
