
import logging
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.models import ClothingItem
from app.llm_service import get_llm_service

logger = logging.getLogger(__name__)


class OutfitRecommender:
   
    
    def __init__(self):
        self.llm_service = get_llm_service()
    
    def _format_wardrobe_for_llm(self, items: List[ClothingItem]) -> List[Dict]:
        """Format wardrobe items for LLM consumption."""
        formatted_items = []
        
        for item in items:
            formatted_item = {
                'id': item.id,
                'category': item.category,
                'name': item.name,
                'clothing_type': item.clothing_type,
                'color': item.color,
                'secondary_color': item.secondary_color,
                'season': item.season,
                'style': item.style,
                'pattern': item.pattern,
                'material': item.material,
                'fit': item.fit,
                'image_path': item.image_path
            }
            formatted_items.append(formatted_item)
        
        return formatted_items
    
    def _enrich_outfit_with_items(
        self, 
        outfit_response: Dict, 
        items_dict: Dict[int, ClothingItem]
    ) -> Dict:
       
        enriched = {
            'request_fulfilled': True,
            'outfit': {},
            'alternatives': [],
            'metadata': outfit_response.get('metadata', {})
        }
        
        outfit = outfit_response.get('outfit', {})
        
        # Add top item
        if 'top' in outfit and outfit['top']:
            top_id = outfit['top'].get('id')
            if top_id and top_id in items_dict:
                enriched['outfit']['top'] = {
                    'item': self._item_to_dict(items_dict[top_id]),
                    'reason': outfit['top'].get('reason', '')
                }
        
        # Add bottom item
        if 'bottom' in outfit and outfit['bottom']:
            bottom_id = outfit['bottom'].get('id')
            if bottom_id and bottom_id in items_dict:
                enriched['outfit']['bottom'] = {
                    'item': self._item_to_dict(items_dict[bottom_id]),
                    'reason': outfit['bottom'].get('reason', '')
                }
        
        # Add additional items
        if 'additional' in outfit and outfit['additional']:
            enriched['outfit']['additional'] = []
            for add_item in outfit['additional']:
                add_id = add_item.get('id')
                if add_id and add_id in items_dict:
                    enriched['outfit']['additional'].append({
                        'item': self._item_to_dict(items_dict[add_id]),
                        'reason': add_item.get('reason', '')
                    })
        
        # Add description and tips
        enriched['outfit']['description'] = outfit.get('description', '')
        enriched['outfit']['styling_tips'] = outfit.get('styling_tips', '')
        
        # Add alternatives
        if 'alternatives' in outfit_response:
            for alt in outfit_response['alternatives']:
                top_id = alt.get('top_id')
                bottom_id = alt.get('bottom_id')
                
                alt_dict = {'reason': alt.get('reason', '')}
                
                if top_id and top_id in items_dict:
                    alt_dict['top'] = self._item_to_dict(items_dict[top_id])
                if bottom_id and bottom_id in items_dict:
                    alt_dict['bottom'] = self._item_to_dict(items_dict[bottom_id])
                
                if 'top' in alt_dict or 'bottom' in alt_dict:
                    enriched['alternatives'].append(alt_dict)
        
        # Add confidence
        enriched['confidence'] = outfit.get('confidence', 'medium')
        
        return enriched
    
    def _item_to_dict(self, item: ClothingItem) -> Dict:
        """Convert clothing item to dictionary."""
        return {
            'id': item.id,
            'name': item.name,
            'category': item.category,
            'image_path': item.image_path,
            'clothing_type': item.clothing_type,
            'color': item.color,
            'secondary_color': item.secondary_color,
            'season': item.season,
            'style': item.style,
            'pattern': item.pattern,
            'material': item.material,
            'fit': item.fit,
            'tags': item.tags
        }
    
    def generate_outfit(
        self,
        db: Session,
        user_request: str,
        filters: Optional[Dict] = None
    ) -> Dict:
       
        try:
            # Get all wardrobe items
            query = db.query(ClothingItem)
            
            # Apply filters if provided
            if filters:
                if 'season' in filters:
                    query = query.filter(ClothingItem.season == filters['season'])
                if 'style' in filters:
                    query = query.filter(ClothingItem.style == filters['style'])
                if 'category' in filters:
                    query = query.filter(ClothingItem.category == filters['category'])
            
            wardrobe_items = query.all()
            
            if not wardrobe_items:
                return {
                    'request_fulfilled': False,
                    'error': 'No items in wardrobe',
                    'message': 'Please add some clothing items to your wardrobe first.'
                }
            
            logger.info(f"Generating outfit from {len(wardrobe_items)} wardrobe items")
            
            # Format items for LLM
            formatted_items = self._format_wardrobe_for_llm(wardrobe_items)
            
            # Generate recommendation using LLM
            llm_response = self.llm_service.generate_outfit_recommendation(
                user_request=user_request,
                wardrobe_items=formatted_items
            )
            
            # Create items lookup dict
            items_dict = {item.id: item for item in wardrobe_items}
            
            # Enrich response with full item details
            enriched_response = self._enrich_outfit_with_items(llm_response, items_dict)
            
            logger.info(f"Outfit generated successfully for request: '{user_request}'")
            return enriched_response
            
        except Exception as e:
            logger.error(f"Error generating outfit: {e}")
            raise
    
    def get_usage_stats(self) -> Dict:
        return self.llm_service.get_usage_stats()


# Global instance
_outfit_recommender = None

def get_outfit_recommender() -> OutfitRecommender:
    """Get or create global outfit recommender instance."""
    global _outfit_recommender
    if _outfit_recommender is None:
        _outfit_recommender = OutfitRecommender()
    return _outfit_recommender

