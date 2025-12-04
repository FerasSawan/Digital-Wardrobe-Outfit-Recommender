import os
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class UsageTracker:
    
    def __init__(self):
        self.daily_count = 0
        self.hourly_count = 0
        self.monthly_cost = 0.0
        self.last_reset_day = datetime.now().date()
        self.last_reset_hour = datetime.now().hour
        self.monthly_reset = datetime.now().replace(day=1)
        
        # Load limits from env
        self.max_daily = int(os.getenv("LLM_MAX_REQUESTS_PER_DAY", "230"))
        self.max_hourly = int(os.getenv("LLM_MAX_REQUESTS_PER_HOUR", "10"))
        self.monthly_budget = float(os.getenv("LLM_MONTHLY_BUDGET_USD", "5.00"))
    
    def reset_if_needed(self):
        
        now = datetime.now()
        if now.date() > self.last_reset_day:
            self.daily_count = 0
            self.last_reset_day = now.date()
            logger.info("Daily usage counter reset")
    
        if now.hour != self.last_reset_hour:
            self.hourly_count = 0
            self.last_reset_hour = now.hour
        
        
        current_month_start = now.date().replace(day=1)
        if current_month_start > self.monthly_reset.date() if isinstance(self.monthly_reset, datetime) else self.monthly_reset:
            self.monthly_cost = 0.0
            self.monthly_reset = current_month_start
            logger.info(f"Monthly budget reset. New budget: ${self.monthly_budget}")
    
    def can_make_request(self) -> tuple[bool, str]:
        self.reset_if_needed()
        
      
        if self.monthly_cost >= self.monthly_budget:
            return False, f"Monthly budget limit reached (${self.monthly_budget:.2f})"
        
        
        if self.daily_count >= self.max_daily:
            return False, f"Daily request limit reached ({self.max_daily} requests)"
        
       
        if self.hourly_count >= self.max_hourly:
            return False, f"Hourly request limit reached ({self.max_hourly} requests)"
        return True, ""
    
    def record_request(self, cost: float):
        self.daily_count += 1
        self.hourly_count += 1
        self.monthly_cost += cost
        
        remaining_budget = self.monthly_budget - self.monthly_cost
        logger.info(
            f"LLM request recorded. "
            f"Cost: ${cost:.4f}, "
            f"Daily: {self.daily_count}/{self.max_daily}, "
            f"Hourly: {self.hourly_count}/{self.max_hourly}, "
            f"Monthly: ${self.monthly_cost:.2f}/${self.monthly_budget:.2f} "
            f"(${remaining_budget:.2f} remaining)"
        )
    
    def get_usage_stats(self) -> Dict:
        self.reset_if_needed()
        return {
            "daily_requests": self.daily_count,
            "daily_limit": self.max_daily,
            "hourly_requests": self.hourly_count,
            "hourly_limit": self.max_hourly,
            "monthly_cost_usd": round(self.monthly_cost, 2),
            "monthly_budget_usd": self.monthly_budget,
            "remaining_budget_usd": round(self.monthly_budget - self.monthly_cost, 2),
            "can_make_request": self.can_make_request()[0]
        }


class LLMService:
    MODEL_COSTS = {
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},  # per 1K tokens
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    }
    
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "openai")
        self.model = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
        self.usage_tracker = UsageTracker()
        
        if self.provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment variables")
            self.client = OpenAI(api_key=api_key)
            logger.info(f"LLM service initialized: {self.provider} - {self.model}")
        else:
            raise ValueError(f"Provider '{self.provider}' not yet implemented")
    
    def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        costs = self.MODEL_COSTS.get(self.model, self.MODEL_COSTS["gpt-3.5-turbo"])
        input_cost = (input_tokens / 1000) * costs["input"]
        output_cost = (output_tokens / 1000) * costs["output"]
        return input_cost + output_cost
    
    def _build_outfit_prompt(self, user_request: str, wardrobe_items: List[Dict]) -> str:
        
        items_text = ""
        for idx, item in enumerate(wardrobe_items, 1):
            items_text += f"\n{idx}. [{item['category'].upper()}] ID:{item['id']}"
            details = []
            if item.get('clothing_type'):
                details.append(f"Type: {item['clothing_type']}")
            if item.get('color'):
                details.append(f"Color: {item['color']}")
            if item.get('secondary_color'):
                details.append(f"Secondary: {item['secondary_color']}")
            if item.get('pattern'):
                details.append(f"Pattern: {item['pattern']}")
            if item.get('material'):
                details.append(f"Material: {item['material']}")
            if item.get('style'):
                details.append(f"Style: {item['style']}")
            if item.get('season'):
                details.append(f"Season: {item['season']}")
            if item.get('fit'):
                details.append(f"Fit: {item['fit']}")
            if item.get('name'):
                details.append(f"Name: {item['name']}")
            
            if details:
                items_text += " - " + ", ".join(details)
        
        prompt = f"""You are a professional fashion stylist helping someone choose an outfit from their wardrobe.

USER REQUEST: "{user_request}"

AVAILABLE WARDROBE ITEMS:{items_text}

YOUR TASK:
1. Select the best outfit combination that matches the user's request
2. Consider: season/weather, color coordination, style coherence, occasion appropriateness
3. Choose items that work well together
4. Provide styling tips

RESPOND IN THIS EXACT JSON FORMAT:
{{
  "outfit": {{
    "top": {{"id": <item_id>, "reason": "brief reason"}},
    "bottom": {{"id": <item_id>, "reason": "brief reason"}},
    "additional": [{{"id": <item_id>, "reason": "brief reason"}}],
    "description": "1-2 sentence outfit description",
    "styling_tips": "2-3 practical styling tips"
  }},
  "alternatives": [
    {{"top_id": <id>, "bottom_id": <id>, "reason": "why this is a good alternative"}}
  ],
  "confidence": "high/medium/low based on wardrobe fit"
}}

RULES:
- Only use IDs from the wardrobe above
- If no good match exists, suggest the closest option with lower confidence
- Keep responses concise but helpful
- Focus on practical fashion advice"""

        return prompt
    
    def generate_outfit_recommendation(
        self,
        user_request: str,
        wardrobe_items: List[Dict]
    ) -> Optional[Dict]:
        
        
        
        can_proceed, reason = self.usage_tracker.can_make_request()
        if not can_proceed:
            logger.warning(f"LLM request blocked: {reason}")
            raise Exception(f"Rate limit exceeded: {reason}")
        
        try:
            
            prompt = self._build_outfit_prompt(user_request, wardrobe_items)
            
            logger.info(f"Generating outfit for request: '{user_request}' with {len(wardrobe_items)} items")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional fashion stylist. Always respond in valid JSON format."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,  
                max_tokens=800,
                response_format={"type": "json_object"}
            )
            
           
            result_text = response.choices[0].message.content
            
            
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            cost = self._estimate_cost(input_tokens, output_tokens)
            
            self.usage_tracker.record_request(cost)
            
            import json
            result = json.loads(result_text)
            

            result['metadata'] = {
                'model': self.model,
                'cost_usd': round(cost, 4),
                'tokens_used': input_tokens + output_tokens,
                'usage_stats': self.usage_tracker.get_usage_stats()
            }
            
            logger.info(f"Outfit generated successfully. Cost: ${cost:.4f}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating outfit recommendation: {e}")
            raise
    
    def get_usage_stats(self) -> Dict:
        """Get current usage statistics."""
        return self.usage_tracker.get_usage_stats()



_llm_service = None

def get_llm_service() -> LLMService:
    """Get or create global LLM service instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service

