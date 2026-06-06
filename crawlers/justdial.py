import logging
from typing import List
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

from crawler_base import BaseCrawler
from models import BusinessDetail
from utils import decode_justdial_phone_classes
import config

logger = logging.getLogger("JustdialCrawler")

class JustdialCrawler(BaseCrawler):
    def run(self) -> List[BusinessDetail]:
        results = []
        try:
            page = self.setup_browser()
            
            # Format URL: https://www.justdial.com/{city}/{category}
            # For Justdial, replacing spaces with dashes is common in URLs
            category_slug = self.category.replace(" ", "-")
            url = f"https://www.justdial.com/{self.city}/{category_slug}"
            
            logger.info(f"Navigating to Justdial: {url}")
            
            # Set a normal desktop user agent and extra headers to avoid immediate block
            page.set_extra_http_headers({
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.google.com/"
            })
            
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            self.random_delay(3, 5)
            
            # Scroll down to trigger lazy loading of elements
            logger.info("Scrolling down page to load lazy listings...")
            for _ in range(3):
                page.keyboard.press("PageDown")
                self.random_delay(0.5, 1.2)
            
            # Fetch HTML content and parse with BeautifulSoup for faster, easier traversing of structures
            html_content = page.content()
            soup = BeautifulSoup(html_content, "lxml")
            
            # Common Justdial listing card classes: li.cntanr, div.store-details, li.store-box
            cards = soup.select("li.cntanr") or soup.select(".store-details") or soup.select(".store-box")
            if not cards:
                # Fallback: check all list items or divs that have listing links
                cards = [el.parent.parent for el in soup.select("span.lng_cont_name")]
                
            logger.info(f"Found {len(cards)} listing containers on the page.")
            
            for index, card in enumerate(cards[:config.MAX_RESULTS_PER_SEARCH]):
                try:
                    # Name
                    name_el = card.select_one(".lng_cont_name") or card.select_one(".store-name a") or card.select_one("span[itemprop='name']")
                    name = name_el.get_text(strip=True) if name_el else ""
                    if not name:
                        continue
                        
                    # Detail URL
                    link_el = card.select_one("a[href*='/jd/']") or card.select_one(".store-name a") or card.select_one("a")
                    detail_url = ""
                    if link_el and link_el.has_attr("href"):
                        detail_url = link_el["href"]
                        if detail_url.startswith("/"):
                            detail_url = "https://www.justdial.com" + detail_url
                            
                    # Address / Locality
                    addr_el = card.select_one(".cont_fl_addr") or card.select_one(".address-info") or card.select_one(".cont_loc")
                    address = addr_el.get_text(strip=True) if addr_el else ""
                    
                    # Rating
                    rating_val = None
                    rating_el = card.select_one(".green-box") or card.select_one(".rt_num") or card.select_one(".ratings")
                    if rating_el:
                        try:
                            rating_val = float(rating_el.get_text(strip=True))
                        except ValueError:
                            pass
                            
                    # Reviews Count
                    reviews_count = None
                    reviews_el = card.select_one(".rt_count") or card.select_one(".lng_vote") or card.select_one(".votes")
                    if reviews_el:
                        try:
                            # Strip out non-numeric characters e.g. "120 Votes" -> 120
                            votes_text = "".join(filter(str.isdigit, reviews_el.get_text(strip=True)))
                            if votes_text:
                                reviews_count = int(votes_text)
                        except ValueError:
                            pass
                            
                    # Website
                    website = ""
                    web_el = card.select_one("a[href^='http']:not([href*='justdial.com'])")
                    if web_el and web_el.has_attr("href"):
                        website = web_el["href"]
                        
                    # Phone - Justdial phone numbers are obfuscated in spans
                    phone = ""
                    # 1. Try to find tel: link
                    tel_el = card.select_one("a[href^='tel:']")
                    if tel_el and tel_el.has_attr("href"):
                        phone = tel_el["href"].replace("tel:", "").strip()
                        
                    # 2. Decode obfuscated spans if tel link not present
                    if not phone:
                        phone_spans = card.select(".contact-info span") or card.select(".mobilesv") or card.select("span[class*='mobicon']")
                        if phone_spans:
                            class_list = []
                            for span in phone_spans:
                                # Collect classes of spans
                                if span.has_attr("class"):
                                    class_list.extend(span["class"])
                            phone = decode_justdial_phone_classes(class_list)
                            
                    # Construct listing
                    item = BusinessDetail(
                        source_url=detail_url or url,
                        company_name=name,
                        industry_type=self.category,
                        country="India",
                        city=self.city,
                        address=address,
                        primary_contact=phone,
                        rating=rating_val,
                        reviews_count=reviews_count,
                        website=website
                    )
                    results.append(item)
                    logger.info(f"Scraped Justdial listing: {name} | Phone: {phone}")
                    
                except Exception as card_ex:
                    logger.error(f"Error parsing Justdial card {index}: {card_ex}")
                    
        except Exception as e:
            logger.error(f"Error in JustdialCrawler run: {e}")
        finally:
            self.close_browser()
            
        return results
