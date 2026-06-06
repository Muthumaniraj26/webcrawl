import logging
import requests
from urllib.parse import quote_plus, urlparse, parse_qs
from typing import List

from crawler_base import BaseCrawler
from models import BusinessDetail
import config

logger = logging.getLogger("YelpCrawler")

class YelpCrawler(BaseCrawler):
    def run(self) -> List[BusinessDetail]:
        # If API key is provided, use the official Yelp API
        if config.YELP_API_KEY:
            logger.info("YELP_API_KEY found. Scraping Yelp using official Fusion API.")
            return self.run_via_api()
        else:
            logger.info("YELP_API_KEY not found. Attempting Playwright scraping.")
            return self.run_via_playwright()

    def run_via_api(self) -> List[BusinessDetail]:
        results = []
        try:
            headers = {
                "Authorization": f"Bearer {config.YELP_API_KEY}",
                "accept": "application/json"
            }
            
            # Yelp search endpoint
            search_url = "https://api.yelp.com/v3/businesses/search"
            params = {
                "term": self.category,
                "location": f"{self.city}, India" if self.city in ["Mumbai", "Pune", "Ahmedabad", "Surat", "Hyderabad", "Jaipur", "Delhi", "Noida", "Gurugram", "Bengaluru"] else self.city,
                "limit": config.MAX_RESULTS_PER_SEARCH
            }
            
            response = requests.get(search_url, headers=headers, params=params, timeout=15)
            if response.status_code != 200:
                logger.error(f"Yelp API returned error {response.status_code}: {response.text}")
                return results
                
            data = response.json()
            businesses = data.get("businesses", [])
            logger.info(f"Yelp API returned {len(businesses)} businesses.")
            
            for idx, biz in enumerate(businesses):
                biz_id = biz.get("id")
                # To get website URL, we need to call Yelp Details API
                details_url = f"https://api.yelp.com/v3/businesses/{biz_id}"
                
                website = ""
                try:
                    # Small delay to respect API limits
                    self.random_delay(0.2, 0.5)
                    det_resp = requests.get(details_url, headers=headers, timeout=10)
                    if det_resp.status_code == 200:
                        det_data = det_resp.json()
                        website = det_data.get("attributes", {}).get("business_website", "") or det_data.get("website", "")
                except Exception as det_ex:
                    logger.warning(f"Failed to fetch details for {biz.get('name')}: {det_ex}")
                
                loc = biz.get("location", {})
                address_str = ", ".join(loc.get("display_address", []))
                
                categories_str = ", ".join([c.get("title", "") for c in biz.get("categories", [])])
                
                item = BusinessDetail(
                    source_url=biz.get("url", ""),
                    company_name=biz.get("name", ""),
                    industry_type=categories_str or self.category,
                    country=loc.get("country", "IN"),
                    city=loc.get("city", self.city),
                    zipcode=loc.get("zip_code", ""),
                    address=address_str,
                    primary_contact=biz.get("display_phone", "") or biz.get("phone", ""),
                    rating=biz.get("rating"),
                    reviews_count=biz.get("review_count"),
                    website=website
                )
                results.append(item)
                logger.info(f"API Scraped: {item.company_name} | Phone: {item.primary_contact}")
                
        except Exception as e:
            logger.error(f"Error in Yelp API execution: {e}")
            
        return results

    def run_via_playwright(self) -> List[BusinessDetail]:
        results = []
        try:
            page = self.setup_browser()
            search_query = quote_plus(self.category)
            city_query = quote_plus(self.city)
            url = f"https://www.yelp.com/search?find_desc={search_query}&find_loc={city_query}"
            
            logger.info(f"Navigating to: {url}")
            page.goto(url, wait_until="networkidle", timeout=45000)
            self.random_delay(3, 5)
            
            # Check for Cloudflare/CAPTCHA challenge
            if "challenge" in page.title().lower() or "cloudflare" in page.content().lower():
                logger.warning("Cloudflare challenge page detected. Yelp scraping might be blocked. Consider using Yelp Fusion API.")
                
            # Find business listing containers
            # Typical selectors: 'div[data-testid="serp-ia-card"]', 'li.border-color--default__09f24__NPAKY'
            listing_links = []
            
            # Yelp links usually starts with /biz/
            links = page.query_selector_all("a[href^='/biz/']")
            for l in links:
                href = l.get_attribute("href")
                if href and "/biz/" in href:
                    # Strip URL parameters to keep it clean
                    clean_href = href.split("?")[0]
                    full_href = "https://www.yelp.com" + clean_href
                    if full_href not in listing_links:
                        listing_links.append(full_href)
                        
            logger.info(f"Found {len(listing_links)} unique Yelp business detail URLs.")
            
            # Scraping details pages
            for index, d_url in enumerate(listing_links[:config.MAX_RESULTS_PER_SEARCH]):
                try:
                    logger.info(f"Parsing details [{index+1}/{len(listing_links)}]: {d_url}")
                    page.goto(d_url, wait_until="domcontentloaded", timeout=30000)
                    self.random_delay(2, 4)
                    
                    # Company Name
                    name_el = page.query_selector("h1")
                    name = name_el.inner_text().strip() if name_el else ""
                    if not name:
                        continue
                        
                    # Phone
                    phone_el = page.query_selector("p:has-text('Phone number') + p") or page.query_selector("a[href^='tel:']")
                    phone = phone_el.inner_text().strip() if phone_el else ""
                    if phone.startswith("tel:"):
                        phone = phone.replace("tel:", "")
                        
                    # Website
                    website = ""
                    web_el = page.query_selector("p:has-text('Business website') + p a") or page.query_selector("a[href^='/biz_redir']")
                    if web_el:
                        web_href = web_el.get_attribute("href")
                        if web_href:
                            if web_href.startswith("/biz_redir"):
                                # Extract url parameter
                                parsed_url = urlparse(web_href)
                                q_params = parse_qs(parsed_url.query)
                                if 'url' in q_params:
                                    website = q_params['url'][0]
                            else:
                                website = web_href
                                
                    # Address
                    address = ""
                    address_el = page.query_selector("address")
                    if address_el:
                        address = address_el.inner_text().replace("\n", ", ").strip()
                        
                    # Rating
                    rating_val = None
                    rating_el = page.query_selector("div[aria-label*='star rating']")
                    if rating_el:
                        aria_label = rating_el.get_attribute("aria-label")
                        if aria_label:
                            try:
                                rating_val = float(aria_label.split()[0])
                            except ValueError:
                                pass
                                
                    # Reviews
                    reviews_count = None
                    reviews_el = page.query_selector("a[href='#reviews']") or page.query_selector("span:has-text('reviews')")
                    if reviews_el:
                        try:
                            rev_text = reviews_el.inner_text().split()[0].replace(",", "").replace("(", "").replace(")", "")
                            reviews_count = int(rev_text)
                        except ValueError:
                            pass
                            
                    # Social links and email (not directly visible on Yelp biz pages typically)
                    fb_url = ""
                    ig_url = ""
                    li_url = ""
                    
                    item = BusinessDetail(
                        source_url=d_url,
                        company_name=name,
                        industry_type=self.category,
                        country="India" if any(c in self.city for c in ["Mumbai", "Pune", "Ahmedabad", "Surat", "Hyderabad", "Jaipur", "Delhi", "Noida", "Gurugram", "Bengaluru"]) else "United States",
                        city=self.city,
                        address=address,
                        primary_contact=phone,
                        rating=rating_val,
                        reviews_count=reviews_count,
                        website=website,
                        facebook_url=fb_url,
                        instagram_url=ig_url,
                        linkedin_url=li_url
                    )
                    results.append(item)
                    logger.info(f"Scraped: {name} | Phone: {phone}")
                    
                except Exception as ex:
                    logger.error(f"Error scraping Yelp detail page {d_url}: {ex}")
                    
        except Exception as e:
            logger.error(f"Error in Yelp Playwright runner: {e}")
        finally:
            self.close_browser()
            
        return results
