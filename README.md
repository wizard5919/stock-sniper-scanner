# Stock Sniper Scanner

A Streamlit app that ranks stocks based on trend, VWAP behavior, EMA alignment, relative volume, and trend efficiency.

## Features
- Best Call Candidates
- Best Put Candidates
- Choppy / Avoid list
- Custom watchlist input
- Intraday scanner using Yahoo Finance
- Clean score-based ranking

## Project structure
```text
stock_sniper_scanner/
├── app.py
├── requirements.txt
├── .gitignore
├── README.md
└── src/
    ├── __init__.py
    ├── config.py
    ├── data.py
    ├── indicators.py
    └── scanner.py
```

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
streamlit run app.py
```

## Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit - Streamlit stock scanner"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/stock-sniper-scanner.git
git push -u origin main
```

## Suggested repo names
- stock-sniper-scanner
- trendflow-scanner
- momentum-sniper-app
- vwap-trend-scanner

## Notes
This starter project is based on the scanner logic you shared and refactors it into a clean Streamlit app structure.
