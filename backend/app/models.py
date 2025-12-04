
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import ARRAY
from datetime import datetime
from app.database import Base


class ClothingItem(Base):
   
    __tablename__ = "clothing_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    category = Column(String, nullable=False)  # shirt, pants, shorts, hoodie
    image_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
  
    clothing_type = Column(String, nullable=True)  # Auto-detected type: t-shirt, jeans, dress, etc.
    color = Column(String, nullable=True)  # Primary color
    secondary_color = Column(String, nullable=True)  # Secondary color
    season = Column(String, nullable=True)  # spring, summer, fall, winter, all-season
    style = Column(String, nullable=True)  # casual, formal, sporty, etc.
    pattern = Column(String, nullable=True)  # solid, striped, plaid, floral, etc.
    material = Column(String, nullable=True)  # cotton, denim, leather, etc.
    fit = Column(String, nullable=True)  # slim, regular, loose, oversized
    
    
    tags = Column(JSON, nullable=True)  # Additional tags as JSON array
    confidence_scores = Column(JSON, nullable=True)  # Confidence scores for each attribute
    
    
    embedding = Column(JSON, nullable=True)


class SavedOutfit(Base):
    
    __tablename__ = "saved_outfits"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # AI-generated name
    description = Column(Text, nullable=True)  # Outfit description
    gender = Column(String, nullable=False)  # 'male' or 'female'
    
    # Item IDs
    top_id = Column(Integer, nullable=True)
    bottom_id = Column(Integer, nullable=True)
    additional_items = Column(JSON, nullable=True)  # Array of item IDs
    
    # Original request and outfit data
    original_request = Column(String, nullable=True)
    outfit_data = Column(JSON, nullable=True)  # Full outfit recommendation
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

