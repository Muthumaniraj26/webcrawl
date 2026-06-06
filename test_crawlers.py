import logging
import sys

from main import CRAWLER_MAP
from utils import save_listings
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestRunner")

def test_crawler(site_name: str, city: str, category: str):
    logger.info(f"=== Testing crawler: {site_name} ===")
    
    crawler_cls = CRAWLER_MAP.get(site_name)
    if not crawler_cls:
        logger.error(f"Crawler '{site_name}' not found in mapping.")
        return
        
    config.MAX_RESULTS_PER_SEARCH = 2  # Keep it small for testing
    
    try:
        crawler = crawler_cls(city=city, category=category)
        results = crawler.run()
        
        logger.info(f"Crawler run finished. Found {len(results)} records.")
        
        if results:
            print("\nSample Record Data:")
            first_biz = results[0]
            for key, val in first_biz.model_dump().items():
                print(f"  {key}: {val}")
                
            # Save test results
            save_listings(results, filename=f"test_{site_name}_output")
            logger.info("Test listing successfully exported!")
        else:
            logger.warning(f"No results returned for {site_name}. This might be due to blocking, empty listings, or parser issues.")
            
    except Exception as e:
        logger.exception(f"Exception during {site_name} test: {e}")

if __name__ == "__main__":
    # Test Yellowpages as it is the easiest to verify publicly
    test_site = "yellowpages"
    test_city = "Noida"
    test_category = "Spa Consultants"
    
    if len(sys.argv) > 1:
        test_site = sys.argv[1]
    if len(sys.argv) > 2:
        test_city = sys.argv[2]
    if len(sys.argv) > 3:
        test_category = sys.argv[3]
        
    test_crawler(test_site, test_city, test_category)
