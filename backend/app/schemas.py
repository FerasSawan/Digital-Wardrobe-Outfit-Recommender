from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class ClothingItemBase(BaseModel):
    
    name: Optional[str] = None
    category: str


class ClothingItemRead(ClothingItemBase):
    id: int
    image_path: str
    created_at: datetime
    
  
    clothing_type: Optional[str] = None
    color: Optional[str] = None
    secondary_color: Optional[str] = None
    season: Optional[str] = None
    style: Optional[str] = None
    pattern: Optional[str] = None
    material: Optional[str] = None
    fit: Optional[str] = None
    tags: Optional[List[str]] = None
    confidence_scores: Optional[Dict[str, float]] = None
    

    class Config:
        from_attributes = True



class OutfitRequest(BaseModel):
    
    request: str  
    occasion: Optional[str] = None 
    weather: Optional[str] = None  
    season: Optional[str] = None  


class UsageStats(BaseModel):
    daily_requests: int
    daily_limit: int
    hourly_requests: int
    hourly_limit: int
    monthly_cost_usd: float
    monthly_budget_usd: float
    remaining_budget_usd: float
    can_make_request: bool

