import logging
from typing import List
from urllib.parse import quote_plus

from crawler_base import BaseCrawler
from models import BusinessDetail
import config

logger = logging.getLogger("YellowpagesCrawler")

class YellowpagesCrawler(BaseCrawler):
    def run(self) -> List[BusinessDetail]:
        results = []
        try:
            page = self.setup_browser()
            
            # Format Search Query
            search_query = quote_plus(self.category)
            city_query = quote_plus(self.city)
            url = f"https://www.yellowpages.com/search?search_terms={search_query}&geo_location_terms={city_query}"
            
            logger.info(f"Navigating to: {url}")
            page.goto(url, wait_until="networkidle", timeout=45000)
            self.random_delay(2, 4)
            
            # Locate all results elements
            # Common selectors for Yellowpages: .search-results .result or div.result
            listing_elements = page.query_selector_all("div.result")
            logger.info(f"Found {len(listing_elements)} listing cards.")
            
            details_urls = []
            for element in listing_elements[:config.MAX_RESULTS_PER_SEARCH]:
                # Extract detail page link
                link_el = element.query_selector("a.business-name")
                if link_el:
                    href = link_el.get_attribute("href")
                    if href:
                        if href.startswith("/"):
                            href = "https://www.yellowpages.com" + href
                        details_urls.append(href)
            
            logger.info(f"Extracted {len(details_urls)} detail URLs to crawl.")
            
            for index, d_url in enumerate(details_urls):
                try:
                    logger.info(f"Parsing details [{index+1}/{len(details_urls)}]: {d_url}")
                    page.goto(d_url, wait_until="domcontentloaded", timeout=30000)
                    self.random_delay(1.5, 3)
                    
                    # Extract fields from detail page
                    # Business Name
                    name_el = page.query_selector("div.sales-info h1") or page.query_selector("h1.business-name")
                    name = name_el.inner_text().strip() if name_el else ""
                    if not name:
                        continue
                        
                    # Phone
                    phone_el = page.query_selector("p.phone") or page.query_selector("p.phone a") or page.query_selector("a.phone")
                    phone = phone_el.inner_text().strip() if phone_el else ""
                    
                    # Address / Location
                    address_el = page.query_selector("span.address") or page.query_selector("p.address") or page.query_selector("span.street-address")
                    address = address_el.inner_text().strip() if address_el else ""
                    
                    zip_el = page.query_selector("span.zip") or page.query_selector("span[itemprop='postalCode']")
                    zipcode = zip_el.inner_text().strip() if zip_el else ""
                    
                    # Try to parse zipcode from address if not found
                    if not zipcode and address:
                        words = address.split()
                        if words and words[-1].isdigit():
                            zipcode = words[-1]
                            
                    # Website
                    web_el = page.query_selector("a.website-link") or page.query_selector("a.track-visit-website")
                    website = web_el.get_attribute("href") if web_el else ""
                    
                    # Ratings and Reviews
                    rating_el = page.query_selector("div.rating-stars") or page.query_selector("span.rating")
                    rating_val = None
                    if rating_el:
                        # Yellowpages ratings are often in class name (e.g. "stars-four")
                        classes = rating_el.get_attribute("class")
                        if "one" in classes: rating_val = 1.0
                        elif "two" in classes: rating_val = 2.0
                        elif "three" in classes: rating_val = 3.0
                        elif "four" in classes: rating_val = 4.0
                        elif "five" in classes: rating_val = 5.0
                        
                    reviews_el = page.query_selector("span.count") or page.query_selector("a.reviews-count")
                    reviews_count = None
                    if reviews_el:
                        try:
                            rev_text = reviews_el.inner_text().replace("(", "").replace(")", "").strip()
                            reviews_count = int(rev_text)
                        except ValueError:
                            pass
                            
                    # Social Links (Yellowpages details pages sometimes link to socials)
                    fb_url = ""
                    ig_url = ""
                    li_url = ""
                    social_links = page.query_selector_all("div.social-links a, a.social-link")
                    for s_link in social_links:
                        s_href = s_link.get_attribute("href")
                        if s_href:
                            if "facebook.com" in s_href:
                                fb_url = s_href
                            elif "instagram.com" in s_href:
                                ig_url = s_href
                            elif "linkedin.com" in s_href:
                                li_url = s_href
                                
                    # Email: YP details page sometimes has a mail link or email button
                    email = ""
                    email_el = page.query_selector("a.email-business")
                    if email_el:
                        email_href = email_el.get_attribute("href")
                        if email_href and email_href.startswith("mailto:"):
                            email = email_href.replace("mailto:", "").split("?")[0].strip()
                            
                    # General categories / Industry Type
                    industry_el = page.query_selector("dd.categories") or page.query_selector("div.categories")
                    industry = industry_el.inner_text().strip() if industry_el else self.category
                    
                    # Create detail model
                    business = BusinessDetail(
                        source_url=d_url,
                        company_name=name,
                        industry_type=industry,
                        country="United States" if "yellowpages.com" in d_url else "India",
                        city=self.city,
                        zipcode=zipcode,
                        address=address,
                        primary_contact=phone,
                        primary_email=email,
                        rating=rating_val,
                        reviews_count=reviews_count,
                        website=website,
                        facebook_url=fb_url,
                        instagram_url=ig_url,
                        linkedin_url=li_url
                    )
                    results.append(business)
                    logger.info(f"Scraped: {name} | Phone: {phone}")
                    
                except Exception as ex:
                    logger.error(f"Error scraping detail page {d_url}: {ex}")
                    
        except Exception as e:
            logger.error(f"Error in YellowpagesCrawler run: {e}")
        finally:
            self.close_browser()
            
        return results
