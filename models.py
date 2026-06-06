from pydantic import BaseModel, Field
from typing import Optional, List

class BranchDetail(BaseModel):
    city: Optional[str] = Field(default="", description="City where branch is located")
    address: Optional[str] = Field(default="", description="Full address of the branch")
    contact: Optional[str] = Field(default="", description="Contact number of the branch")

class BusinessDetail(BaseModel):
    source_url: Optional[str] = Field(default="", description="URL of the listing source")
    company_name: Optional[str] = Field(default="", description="Business Name / Company Name")
    industry_type: Optional[str] = Field(default="", description="Industry Type")
    business_type: Optional[str] = Field(default="", description="Business Type (e.g. Wholesaler, Manufacturer, Service)")
    country: Optional[str] = Field(default="India", description="Country")
    city: Optional[str] = Field(default="", description="City")
    area: Optional[str] = Field(default="", description="Area / Locality")
    zipcode: Optional[str] = Field(default="", description="Zipcode")
    address: Optional[str] = Field(default="", description="Full Address")
    
    primary_contact: Optional[str] = Field(default="", description="Primary Contact Number")
    primary_email: Optional[str] = Field(default="", description="Primary Email")
    secondary_contact: Optional[str] = Field(default="", description="Secondary Contact Number")
    secondary_email: Optional[str] = Field(default="", description="Secondary Email")
    
    services_products: Optional[List[str]] = Field(default_factory=list, description="Services / Products offered")
    target_customer: Optional[str] = Field(default="", description="Target Customer / Target Industry")
    price_range: Optional[str] = Field(default="", description="Product Price Range / Service Price Range")
    
    num_branches: Optional[int] = Field(default=None, description="Number of Branches / Chains / Franchise")
    branch_details: Optional[List[BranchDetail]] = Field(default_factory=list, description="Branch Details (City, Address, Contact)")
    
    rating: Optional[float] = Field(default=None, description="Average Rating (e.g., 4.5)")
    reviews_count: Optional[int] = Field(default=None, description="Total count of reviews")
    
    website: Optional[str] = Field(default="", description="Company Website URL")
    facebook_url: Optional[str] = Field(default="", description="Facebook URL")
    instagram_url: Optional[str] = Field(default="", description="Instagram URL")
    linkedin_url: Optional[str] = Field(default="", description="LinkedIn URL")
