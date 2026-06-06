import logging
from typing import List
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

from crawler_base import BaseCrawler
from models import BusinessDetail
import config

logger = logging.getLogger("IndiamartCrawler")

class IndiamartCrawler(BaseCrawler):
    def run(self) -> List[BusinessDetail]:
        results = []
        try:
            page = self.setup_browser()
            
            # Format URL: https://dir.indiamart.com/search.mp?ss={category}&cq={city}
            search_query = quote_plus(self.category)
            city_query = quote_plus(self.city)
            url = f"https://dir.indiamart.com/search.mp?ss={search_query}&cq={city_query}"
            
            logger.info(f"Navigating to Indiamart: {url}")
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            self.random_delay(3, 5)
            
            # Scroll to load listings
            logger.info("Scrolling down Indiamart listings...")
            for _ in range(2):
                page.keyboard.press("PageDown")
                self.random_delay(0.5, 1.2)
                
            html_content = page.content()
            soup = BeautifulSoup(html_content, "lxml")
            
            # Check cards. Indiamart cards typically use class 'lst_crd', 'card', or list elements
            cards = soup.select(".lst_crd") or soup.select(".card") or soup.select(".r-box")
            if not cards:
                # Fallback: check elements containing company links
                cards = [el.parent.parent.parent for el in soup.select(".companyname")]
                
            logger.info(f"Found {len(cards)} listings on Indiamart.")
            
            for index, card in enumerate(cards[:config.MAX_RESULTS_PER_SEARCH]):
                try:
                    # Company Name
                    name_el = card.select_one(".companyname") or card.select_one(".company-name") or card.select_one("span.company-link")
                    name = name_el.get_text(strip=True) if name_el else ""
                    if not name:
                        continue
                        
                    # Detail URL
                    link_el = name_el.find("a") if hasattr(name_el, "find") else None
                    if not link_el:
                        link_el = card.select_one("a[href*='indiamart.com/']") or card.select_one(".companyname a")
                    detail_url = ""
                    if link_el and link_el.has_attr("href"):
                        detail_url = link_el["href"]
                        if detail_url.startswith("//"):
                            detail_url = "https:" + detail_url
                            
                    # Address / City
                    addr_el = card.select_one(".address") or card.select_one(".locality") or card.select_one(".city-name")
                    address = addr_el.get_text(strip=True) if addr_el else ""
                    
                    # Phone
                    phone = ""
                    tel_el = card.select_one("a[href^='tel:']")
                    if tel_el and tel_el.has_attr("href"):
                        phone = tel_el["href"].replace("tel:", "").strip()
                        
                    # If phone not found, check call button text or attributes
                    if not phone:
                        call_el = card.select_one("[class*='call'], [class*='phone'], [class*='mob']")
                        if call_el:
                            phone = call_el.get_text(strip=True)
                            # Strip out text non-digits except +
                            phone = "".join([c for c in phone if c.isdigit() or c == "+"])
                            if len(phone) < 8:  # Not a real number
                                phone = ""
                                
                    # Product Names / Services
                    product_els = card.select(".prd-name") or card.select(".item-title") or card.select("h3")
                    products = [p.get_text(strip=True) for p in product_els if p.get_text(strip=True)]
                    
                    # Price Range
                    price_el = card.select_one(".price") or card.select_one(".prd-price")
                    price_range = price_el.get_text(strip=True) if price_el else ""
                    
                    # Website (often lists external company website if available)
                    website = ""
                    web_el = card.select_one("a[href^='http']:not([href*='indiamart.com'])")
                    if web_el and web_el.has_attr("href"):
                        website = web_el["href"]
                        
                    # Rating
                    rating_val = None
                    rating_el = card.select_one(".rating-stars") or card.select_one(".rt-stars")
                    if rating_el:
                        # Sometimes ratings are encoded in star style or text
                        try:
                            rating_val = float(rating_el.get_text(strip=True))
                        except ValueError:
                            pass
                            
                    # Business Type
                    business_type = ""
                    type_el = card.select_one(".business-type") or card.select_one(".expt")
                    if type_el:
                        business_type = type_el.get_text(strip=True)
                        
                    item = BusinessDetail(
                        source_url=detail_url or url,
                        company_name=name,
                        industry_type=self.category,
                        business_type=business_type,
                        country="India",
                        city=self.city,
                        address=address,
                        primary_contact=phone,
                        services_products=products,
                        price_range=price_range,
                        website=website,
                        rating=rating_val
                    )
                    results.append(item)
                    logger.info(f"Scraped Indiamart listing: {name} | Phone: {phone}")
                    
                except Exception as card_ex:
                    logger.error(f"Error parsing Indiamart card {index}: {card_ex}")
                    
        except Exception as e:
            logger.error(f"Error in IndiamartCrawler run: {e}")
        finally:
            self.close_browser()
            
        return results
