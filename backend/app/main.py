import uuid
import io
import logging
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, File, UploadFile, Form, Depends, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from rembg import remove
from PIL import Image

from app.database import engine, get_db, Base
from app.schemas import ClothingItemRead, OutfitRequest, UsageStats
from app import crud
from app.clip_service import get_clip_tagger
from app.outfit_recommender import get_outfit_recommender
from app.models import SavedOutfit
from app.llm_service import get_llm_service


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


VALID_CATEGORIES = ["shirt", "pants", "shorts", "hoodie"]


Base.metadata.create_all(bind=engine)


app = FastAPI(title="Digital Wardrobe API", version="1.0.0")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/api/clothing-items/", response_model=ClothingItemRead)
async def create_clothing_item(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    category: str = Form(...),
    db: Session = Depends(get_db)
):
   
    if category not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Must be one of: {', '.join(VALID_CATEGORIES)}"
        )
    
  
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    
    unique_filename = f"{uuid.uuid4()}.png"
    
   
    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")
    
    try:
        
        STANDARD_WIDTH = 800
        STANDARD_HEIGHT = 1000
        PADDING_PERCENT = 0.15  
        
       
        output_bytes = remove(
            content,
            alpha_matting=True,
            alpha_matting_foreground_threshold=240,
            alpha_matting_background_threshold=10,
            alpha_matting_erode_size=10
        )
        
        processed_image = Image.open(io.BytesIO(output_bytes))
        
        
        if processed_image.mode != 'RGBA':
            processed_image = processed_image.convert('RGBA')
        
       
        pixels = processed_image.load()
        width, height = processed_image.size
        for y in range(height):
            for x in range(width):
                r, g, b, a = pixels[x, y]
                if a < 30:
                    pixels[x, y] = (0, 0, 0, 0)
        
        logger.info("✓ Background completely removed with enhanced transparency")
        
        max_width = int(STANDARD_WIDTH * (1 - (PADDING_PERCENT * 2)))
        max_height = int(STANDARD_HEIGHT * (1 - (PADDING_PERCENT * 2)))
        
        img_width, img_height = processed_image.size
        width_ratio = max_width / img_width
        height_ratio = max_height / img_height
        scale_ratio = min(width_ratio, height_ratio)  # Use smaller ratio to fit within bounds
        
        new_width = int(img_width * scale_ratio)
        new_height = int(img_height * scale_ratio)
        resized_image = processed_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        transparent_background = Image.new('RGBA', (STANDARD_WIDTH, STANDARD_HEIGHT), (0, 0, 0, 0))
        
        x_offset = (STANDARD_WIDTH - new_width) // 2
        y_offset = (STANDARD_HEIGHT - new_height) // 2
        
        transparent_background.paste(resized_image, (x_offset, y_offset), mask=resized_image.split()[3])
        
        file_path = UPLOADS_DIR / unique_filename
        transparent_background.save(file_path, 'PNG', quality=95, optimize=True)
        
        logger.info(f"✓ Saved with complete transparency: {unique_filename}")
        
    except Exception as e:
        print(f"Warning: Background removal failed, saving original: {e}")
        file_path = UPLOADS_DIR / unique_filename
        file_path.write_bytes(content)
    clip_tags = None
    try:
        logger.info("Starting CLIP analysis for auto-tagging...")
        clip_tagger = get_clip_tagger()
        
        processed_image = Image.open(file_path)
        clip_tags = clip_tagger.analyze_clothing_item(processed_image)
        logger.info(f"CLIP analysis complete. Detected tags: {clip_tags.get('tags', [])}")
        
    except Exception as e:
        
        logger.warning(f"CLIP analysis failed (continuing without tags): {e}")
        clip_tags = None
    
    try:
        relative_path = f"uploads/{unique_filename}"
        item = crud.create_clothing_item(
            db, 
            name=name, 
            category=category, 
            image_path=relative_path,
            clip_tags=clip_tags
        )
        logger.info(f"Successfully created clothing item ID {item.id} in database")
        return item
    except Exception as e:
        logger.error(f"Error creating clothing item in database: {e}")
        
        file_path = UPLOADS_DIR / unique_filename
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to save item to database: {str(e)}")


@app.get("/api/clothing-items/", response_model=List[ClothingItemRead])
async def get_clothing_items(
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    items = crud.get_clothing_items(db)
    if category:
        if category not in VALID_CATEGORIES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category. Must be one of: {', '.join(VALID_CATEGORIES)}"
            )
        items = [item for item in items if item.category == category]
    return items


@app.patch("/api/clothing-items/{item_id}")
async def update_clothing_item(
    item_id: int,
    category: str = None,
    db: Session = Depends(get_db)
):
    item = crud.get_clothing_item_by_id(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    if category and category not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Must be one of: {', '.join(VALID_CATEGORIES)}"
        )
    
    try:
        if category:
            item.category = category
        db.commit()
        db.refresh(item)
        logger.info(f"Successfully updated item ID {item_id}")
        return item
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating item ID {item_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update item: {str(e)}")


@app.delete("/api/clothing-items/{item_id}")
async def delete_clothing_item(item_id: int, db: Session = Depends(get_db)):
    """Delete a clothing item and its image file."""
    item = crud.get_clothing_item_by_id(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    if item.image_path.startswith("uploads/"):
        image_file = Path(item.image_path)
        if image_file.exists():
            try:
                image_file.unlink()
            except Exception as e:
                print(f"Warning: Failed to delete image file: {e}")
                
    try:
        deleted = crud.delete_clothing_item(db, item_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Item not found")
        logger.info(f"Successfully deleted item ID {item_id} from database")
        return {"message": "Item deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting item ID {item_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete item: {str(e)}")


@app.post("/api/outfits/suggest")
async def suggest_outfit(
    request: OutfitRequest,
    db: Session = Depends(get_db)
):
    try:
        recommender = get_outfit_recommender()
        
        filters = {}
        if request.season:
            filters['season'] = request.season
        
        outfit = recommender.generate_outfit(
            db=db,
            user_request=request.request,
            filters=filters if filters else None
        )
        
        return outfit
        
    except Exception as e:
        error_msg = str(e)
        
        
        if "Rate limit exceeded" in error_msg or "budget limit" in error_msg.lower():
            raise HTTPException(status_code=429, detail=error_msg)
        
        logger.error(f"Error generating outfit: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate outfit: {error_msg}")


@app.get("/api/outfits/usage", response_model=UsageStats)
async def get_outfit_usage():
    
    try:
        recommender = get_outfit_recommender()
        stats = recommender.get_usage_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting usage stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/outfits/save")
async def save_outfit(
    outfit_data: dict = Body(...),
    db: Session = Depends(get_db)
):
   
    try:
        # Extract data
        gender = outfit_data.get('gender', 'female')
        original_request = outfit_data.get('original_request', '')
        outfit = outfit_data.get('outfit', {})
        
        # Generate creative name using LLM
        llm_service = get_llm_service()
        name_prompt = f"""Generate a short, creative, and catchy name (2-4 words max) for this outfit:
Request: {original_request}
Description: {outfit.get('description', '')}

Examples: "Summer Breeze", "Office Chic", "Casual Friday", "Date Night Glam"

Respond with ONLY the outfit name, nothing else."""

        try:
            response = llm_service.client.chat.completions.create(
                model=llm_service.model,
                messages=[{"role": "user", "content": name_prompt}],
                temperature=0.8,
                max_tokens=20
            )
            outfit_name = response.choices[0].message.content.strip().strip('"\'')
            
            
            cost = llm_service._estimate_cost(
                response.usage.prompt_tokens,
                response.usage.completion_tokens
            )
            llm_service.usage_tracker.record_request(cost)
        except:
            
            outfit_name = f"Outfit {datetime.now().strftime('%b %d')}"
        
    
        saved_outfit = SavedOutfit(
            name=outfit_name,
            description=outfit.get('description'),
            gender=gender,
            top_id=outfit.get('top', {}).get('item', {}).get('id') if outfit.get('top') else None,
            bottom_id=outfit.get('bottom', {}).get('item', {}).get('id') if outfit.get('bottom') else None,
            additional_items=[item.get('item', {}).get('id') for item in outfit.get('additional', [])],
            original_request=original_request,
            outfit_data=outfit_data
        )
        
        db.add(saved_outfit)
        db.commit()
        db.refresh(saved_outfit)
        
        logger.info(f"Saved outfit: {outfit_name} (ID: {saved_outfit.id})")
        
        return {
            "id": saved_outfit.id,
            "name": saved_outfit.name,
            "message": "Outfit saved successfully!"
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving outfit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/outfits/saved")
async def get_saved_outfits(db: Session = Depends(get_db)):
    """Get all saved outfits."""
    try:
        outfits = db.query(SavedOutfit).order_by(SavedOutfit.created_at.desc()).all()
        return [{
            "id": outfit.id,
            "name": outfit.name,
            "description": outfit.description,
            "gender": outfit.gender,
            "created_at": outfit.created_at.isoformat(),
            "outfit_data": outfit.outfit_data
        } for outfit in outfits]
    except Exception as e:
        logger.error(f"Error fetching saved outfits: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/outfits/saved/{outfit_id}")
async def delete_saved_outfit(outfit_id: int, db: Session = Depends(get_db)):
    """Delete a saved outfit."""
    try:
        outfit = db.query(SavedOutfit).filter(SavedOutfit.id == outfit_id).first()
        if not outfit:
            raise HTTPException(status_code=404, detail="Outfit not found")
        
        db.delete(outfit)
        db.commit()
        
        return {"message": "Outfit deleted successfully"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting outfit: {e}")
        raise HTTPException(status_code=500, detail=str(e))

