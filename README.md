# Multi-Directory Business Directory Crawler

A highly modular and configurable Python crawling application designed to scrape and enrich business listings from **Justdial, Indiamart, Tradeindia, Yellowpages, and Yelp** for multiple categories and cities.

---

## Features

- **Pydantic Validation**: All output schemas are defined using Pydantic, ensuring clean and structured details. No synthetic data is generated; missing fields are left blank.
- **Bypassing Bot Mitigation**: Utilizes Chromium browser automation via Playwright with stealth patches (`playwright-stealth`) to bypass basic automation checks.
- **Justdial Phone Decoder**: Implements a mapper to decode Justdial's font-obfuscated phone digits.
- **Yelp API Fallback**: Includes support for Yelp Fusion API integration, which serves as a highly reliable fallback to prevent Cloudflare blocks.
- **Fail-safe Batch Saves**: Saves data incrementally. If a crawler crashes mid-run, all previously crawled data is preserved in the CSV/Excel files.

---

## Directory Structure

```
d:\crawl\
├── crawlers\
│   ├── justdial.py        # Justdial scraper
│   ├── indiamart.py        # Indiamart scraper
│   ├── tradeindia.py       # Tradeindia scraper
│   ├── yellowpages.py      # Yellowpages scraper
│   └── yelp.py             # Yelp scraper (Scraping + API fallback)
├── config.py               # Targets, proxy, and browser configurations
├── models.py               # Pydantic schemas (BusinessDetail, BranchDetail)
├── crawler_base.py         # Abstract base class & Playwright setups
├── utils.py                # Excel/CSV exporters & JD font decoders
├── main.py                 # Core CLI runner and orchestrator
├── test_crawlers.py        # Verification script for developers
├── requirements.txt        # Package dependencies
└── README.md               # User documentation
```

---

## Installation & Setup

1. **Install requirements**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Download browser binaries**:
   ```bash
   playwright install chromium
   ```

---

## Configuration

Open `config.py` to configure:
- Target `CITIES` and `CATEGORIES` to scrape.
- Proxy servers (`PROXY_SERVER`) to rotate IPs and prevent blocking.
- API keys (`YELP_API_KEY`) for Yelp Fusion API (highly recommended for Yelp data).

---

## How to Run

### 1. Test Verification
Before running a massive crawl, verify that selectors are working and the browser starts successfully by running the test script:
```bash
python test_crawlers.py [site_name] [city] [category]
```
*Example (Yellowpages)*:
```bash
python test_crawlers.py yellowpages Noida "Spa Consultants"
```

### 2. Full Crawl
To start the crawler for all sites, cities, and categories configured in `config.py`:
```bash
python main.py
```

### 3. Customized Runs
You can filter the run using command-line arguments:
- `--sites`: Space-separated list of target sites (choices: `justdial`, `indiamart`, `tradeindia`, `yellowpages`, `yelp`).
- `--cities`: Space-separated list of target cities.
- `--categories`: Space-separated list of target categories.
- `--limit`: Maximum results to pull per search combination (default: 20).
- `--output-name`: Output file name (default: `business_listings`).

*Example*:
```bash
python main.py --sites yellowpages yelp --cities Mumbai Pune --categories "Housekeeping Services" --limit 5 --output-name test_run
```

All final results are saved in the `output/` directory as both:
- `output/[output_name].csv`
- `output/[output_name].xlsx`
