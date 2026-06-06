import os
import pandas as pd
import logging
from typing import List
from models import BusinessDetail

# Set up logging format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("crawler.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("CrawlerUtils")

def decode_justdial_phone_classes(class_list: List[str]) -> str:
    """
    Decodes Justdial's obfuscated phone number classes to digits.
    Justdial uses class names on span elements representing digits.
    """
    # Standard class-to-digit mapping for Justdial's font-obfuscated icons
    jd_digit_map = {
        'dc': '+',
        'fe': '(',
        'hg': ')',
        'kb': '-',
        'ji': '9',
        'lk': '8',
        'nm': '7',
        'po': '6',
        'rq': '5',
        'ts': '4',
        'vu': '3',
        'wx': '2',
        'yz': '1',
        'ab': '0'
    }
    
    digits = []
    for cls in class_list:
        # Check if the class is one of the mapped codes
        # Class names usually look like 'mobicon-ji' or 'icon-ji' or just 'ji'
        clean_cls = cls.split('-')[-1] if '-' in cls else cls
        if clean_cls in jd_digit_map:
            digits.append(jd_digit_map[clean_cls])
            
    return "".join(digits)

def save_listings(listings: List[BusinessDetail], filename: str = "business_listings"):
    """
    Saves a list of BusinessDetail models to CSV and Excel in the output directory.
    Uses pandas to format the structures neatly.
    """
    if not listings:
        logger.warning("No listings to save.")
        return
        
    os.makedirs("output", exist_ok=True)
    
    # Convert list of Pydantic models to dictionaries
    data = []
    for item in listings:
        d = item.model_dump()
        
        # Flatten services/products list into a comma-separated string
        if isinstance(d.get("services_products"), list):
            d["services_products"] = ", ".join(d["services_products"])
            
        # Flatten branch details into a readable string
        branches = d.get("branch_details", [])
        if branches:
            branch_strs = []
            for b in branches:
                branch_strs.append(f"{b.get('city')}: {b.get('address')} ({b.get('contact')})")
            d["branch_details"] = "; ".join(branch_strs)
        else:
            d["branch_details"] = ""
            
        data.append(d)
        
    df = pd.DataFrame(data)
    
    # Reorder columns to match requested layout
    desired_columns = [
        "company_name", "industry_type", "business_type", "country", "city", "area", "zipcode", "address",
        "primary_contact", "primary_email", "secondary_contact", "secondary_email",
        "services_products", "target_customer", "price_range", "num_branches", "branch_details",
        "rating", "reviews_count", "website", "facebook_url", "instagram_url", "linkedin_url", "source_url"
    ]
    
    # Keep only columns that exist, adding missing ones as blank
    for col in desired_columns:
        if col not in df.columns:
            df[col] = ""
            
    df = df[desired_columns]
    
    csv_path = os.path.join("output", f"{filename}.csv")
    xlsx_path = os.path.join("output", f"{filename}.xlsx")
    
    # Export
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    df.to_excel(xlsx_path, index=False)
    
    logger.info(f"Successfully saved {len(listings)} listings to:")
    logger.info(f" - CSV: {csv_path}")
    logger.info(f" - Excel: {xlsx_path}")
