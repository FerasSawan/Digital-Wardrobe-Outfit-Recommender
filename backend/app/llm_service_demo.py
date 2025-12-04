
import logging
from typing import Dict, List
import random

logger = logging.getLogger(__name__)


class DemoLLMService:
    
    def generate_outfit_recommendation(
        self,
        user_request: str,
        wardrobe_items: List[Dict]
    ) -> Dict:
        
        logger.info(f"[DEMO MODE] Generating outfit for: '{user_request}'")
        
      
        request_lower = user_request.lower()
        
        
        tops = [item for item in wardrobe_items if item['category'] in ['shirt', 'hoodie']]
        bottoms = [item for item in wardrobe_items if item['category'] in ['pants', 'shorts']]
        
       
        selected_top = tops[0] if tops else None
        selected_bottom = bottoms[0] if bottoms else None
        
        
        outfit = {}
        
        if selected_top:
            outfit['top'] = {
                'id': selected_top['id'],
                'reason': f"Perfect {selected_top.get('style', 'casual')} {selected_top.get('clothing_type', 'top')} for this occasion"
            }
        
        if selected_bottom:
            outfit['bottom'] = {
                'id': selected_bottom['id'],
                'reason': f"Comfortable {selected_bottom.get('color', '')} {selected_bottom.get('clothing_type', 'bottom')}"
            }
        
        outfit['description'] = f"A great outfit for {user_request}"
        outfit['styling_tips'] = "Keep it simple and comfortable. Accessorize minimally."
        outfit['confidence'] = "medium"
        
        response = {
            'outfit': outfit,
            'alternatives': [],
            'confidence': 'medium',
            'metadata': {
                'model': 'demo-mode',
                'cost_usd': 0.0,
                'tokens_used': 0,
                'note': 'This is a demo response. Add OpenAI credits to use real AI recommendations.'
            }
        }
        
        return response
    
    def get_usage_stats(self) -> Dict:
        return {
            'daily_requests': 0,
            'daily_limit': 999,
            'hourly_requests': 0,
            'hourly_limit': 999,
            'monthly_cost_usd': 0.0,
            'monthly_budget_usd': 5.0,
            'remaining_budget_usd': 5.0,
            'can_make_request': True,
            'demo_mode': True
        }

