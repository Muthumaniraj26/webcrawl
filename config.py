import os

# Target lists as defined in the requirements
CITIES = [
    "Mumbai", "Pune", "Ahmedabad", "Surat", "Hyderabad", 
    "Jaipur", "Delhi", "Noida", "Gurugram", "Bengaluru"
]

CATEGORIES = [
    "Hotel Kit Suppliers",
    "Cleaning and Hotel Supplier shops wholesalers",
    "disposable cutlery",
    "Housekeeping Services",
    "Hospitality Consultants",
    "Spa Equipement Suppliers",
    "Spa Consultants"
]

# Scraping settings
HEADLESS = True  # Set to False to debug browser interactions
REQUEST_TIMEOUT = 30000  # ms
PAGE_DELAY = 3  # seconds to wait between page loads/actions to prevent blocking
MAX_RESULTS_PER_SEARCH = 20  # Limit per city/category combination to prevent massive runs

# Output configurations
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Proxy configuration (Optional: USER can fill this in)
# Example format: "http://username:password@proxy.example.com:8080"
PROXY_SERVER = None 

# API Keys (Optional: USER can fill this in for Yelp Fusion or Firecrawl)
YELP_API_KEY = None
FIRECRAWL_API_KEY = None

# List of rotating user agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"
]
