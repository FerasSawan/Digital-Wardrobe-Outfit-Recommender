
import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.models import ClothingItem

logger = logging.getLogger(__name__)


def create_clothing_item(
    db: Session,
    name: Optional[str],
    image_path: str,
    category: str,
    clip_tags: Optional[dict] = None
) -> ClothingItem:
   
    try:
        
        db_item = ClothingItem(
            name=name,
            image_path=image_path,
            category=category
        )
        
        if clip_tags:
            db_item.clothing_type = clip_tags.get("clothing_type")
            db_item.color = clip_tags.get("color")
            db_item.secondary_color = clip_tags.get("secondary_color")
            db_item.season = clip_tags.get("season")
            db_item.style = clip_tags.get("style")
            db_item.pattern = clip_tags.get("pattern")
            db_item.material = clip_tags.get("material")
            db_item.fit = clip_tags.get("fit")
            db_item.tags = clip_tags.get("tags")
            db_item.confidence_scores = clip_tags.get("confidence_scores")
            db_item.embedding = clip_tags.get("embedding")
        
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        logger.info(f"Created clothing item: ID={db_item.id}, category={category}, name={name}, tags={db_item.tags}")
        return db_item
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating clothing item: {e}")
        raise


def get_clothing_items(db: Session, category: Optional[str] = None) -> list[ClothingItem]:
    query = db.query(ClothingItem)
    if category:
        query = query.filter(ClothingItem.category == category)
    return query.order_by(ClothingItem.created_at.desc()).all()


def get_clothing_item_by_id(db: Session, item_id: int) -> ClothingItem | None:
    return db.query(ClothingItem).filter(ClothingItem.id == item_id).first()


def delete_clothing_item(db: Session, item_id: int) -> ClothingItem | None:
    try:
        db_item = db.query(ClothingItem).filter(ClothingItem.id == item_id).first()
        if db_item:
            db.delete(db_item)
            db.commit()
            logger.info(f"Deleted clothing item: ID={item_id}, category={db_item.category}, name={db_item.name}")
        return db_item
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting clothing item ID {item_id}: {e}")
        raise

