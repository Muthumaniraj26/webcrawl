import logging
from typing import List
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

from crawler_base import BaseCrawler
from models import BusinessDetail
import config

logger = logging.getLogger("TradeindiaCrawler")

class TradeindiaCrawler(BaseCrawler):
    def run(self) -> List[BusinessDetail]:
        results = []
        try:
            page = self.setup_browser()
            
            # Format URL: https://www.tradeindia.com/search.html?keyword={category}&city={city}
            search_query = quote_plus(self.category)
            city_query = quote_plus(self.city)
            url = f"https://www.tradeindia.com/search.html?keyword={search_query}&city={city_query}"
            
            logger.info(f"Navigating to Tradeindia: {url}")
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            self.random_delay(3, 5)
            
            # Scroll to load listings
            logger.info("Scrolling down Tradeindia listings...")
            for _ in range(2):
                page.keyboard.press("PageDown")
                self.random_delay(0.5, 1.2)
                
            html_content = page.content()
            soup = BeautifulSoup(html_content, "lxml")
            
            # Cards could be divs with class "product-card", "card", "card-body", "supplier-card"
            cards = soup.select(".sc-19e58156-0 .card") or soup.select(".card")
            if not cards:
                # Fallback: check elements containing company links or supplier names
                cards = [el.parent.parent.parent for el in soup.select(".coy-name")]
                
            logger.info(f"Found {len(cards)} listings on Tradeindia.")
            
            for index, card in enumerate(cards[:config.MAX_RESULTS_PER_SEARCH]):
                try:
                    # Company Name
                    name_el = card.select_one(".coy-name") or card.select_one("[class*='company-name']")
                    name = name_el.get_text(strip=True) if name_el else ""
                    if not name:
                        continue
                        
                    # Detail URL
                    detail_url = ""
                    if name_el:
                        parent_a = name_el.find_parent("a")
                        if parent_a and parent_a.has_attr("href"):
                            detail_url = parent_a["href"]
                            if detail_url.startswith("//"):
                                detail_url = "https:" + detail_url
                            elif detail_url.startswith("/"):
                                detail_url = "https://www.tradeindia.com" + detail_url
                            
                    # Address / City
                    addr_el = card.select_one(".product_details span[color='#5E7384']") or card.select_one(".product_details span") or card.select_one("[class*='location']")
                    address = addr_el.get_text(strip=True) if addr_el else ""
                    
                    # Phone
                    phone = ""
                    tel_el = card.select_one("a[href^='tel:']")
                    if tel_el and tel_el.has_attr("href"):
                        phone = tel_el["href"].replace("tel:", "").strip()
                        
                    if not phone:
                        call_el = card.select_one(".call-btn") or card.select_one("[class*='call'], [class*='phone'], [class*='mob']")
                        if call_el:
                            phone = call_el.get_text(strip=True)
                            phone = "".join([c for c in phone if c.isdigit() or c == "+"])
                            if len(phone) < 8:
                                phone = ""
                                
                    # Product Names / Services
                    product_el = card.select_one(".card_title") or card.select_one("h2")
                    products = [product_el.get_text(strip=True)] if product_el else []
                    
                    # Price Range
                    price_el = card.select_one("[class*='price']") or card.select_one(".amt")
                    price_range = price_el.get_text(strip=True) if price_el else ""
                    
                    # Website
                    website = ""
                    web_el = card.select_one("a[href^='http']:not([href*='tradeindia.com'])")
                    if web_el and web_el.has_attr("href"):
                        website = web_el["href"]
                        
                    # Rating
                    rating_val = None
                    rating_el = card.select_one(".rating") or card.select_one(".star-rating")
                    if rating_el:
                        try:
                            rating_val = float(rating_el.get_text(strip=True))
                        except ValueError:
                            pass
                            
                    # Business Type
                    business_type = ""
                    for p in card.select(".product_details p"):
                        p_text = p.get_text(strip=True)
                        if "Business Type:" in p_text:
                            business_type = p_text.replace("Business Type:", "").strip()
                            break
                    if not business_type:
                        type_el = card.select_one(".biz-type") or card.select_one(".business-type")
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
                    logger.info(f"Scraped Tradeindia listing: {name} | Phone: {phone}")
                    
                except Exception as card_ex:
                    logger.error(f"Error parsing Tradeindia card {index}: {card_ex}")
                    
        except Exception as e:
            logger.error(f"Error in TradeindiaCrawler run: {e}")
        finally:
            self.close_browser()
            
        return results
