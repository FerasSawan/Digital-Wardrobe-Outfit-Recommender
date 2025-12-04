
import logging
import torch
from PIL import Image
import open_clip
from typing import Dict, List, Tuple, Optional
import numpy as np

logger = logging.getLogger(__name__)


class CLIPTagger:


    CLOTHING_TYPES = [
        "t-shirt", "shirt", "polo shirt", "tank top", "blouse",
        "jeans", "pants", "trousers", "leggings", "chinos",
        "shorts", "bermuda shorts",
        "hoodie", "sweatshirt", "pullover",
        "jacket", "blazer", "coat", "cardigan",
        "dress", "skirt",
        "sweater", "vest"
    ]
    
    COLORS = [
        "black", "white", "gray", "grey",
        "red", "dark red", "maroon",
        "blue", "navy blue", "light blue", "royal blue",
        "green", "dark green", "olive",
        "yellow", "gold",
        "orange", "brown", "tan", "beige", "khaki",
        "pink", "purple", "violet",
        "cream", "ivory"
    ]
    
    SEASONS = [
        "spring clothing", "summer clothing", "fall clothing", "autumn clothing",
        "winter clothing", "all-season clothing"
    ]
    
    STYLES = [
        "casual", "formal", "business casual", "sporty", "athletic",
        "streetwear", "vintage", "preppy", "bohemian", "minimalist",
        "elegant", "edgy", "classic"
    ]
    
    PATTERNS = [
        "solid color", "plain", "striped", "horizontal stripes", "vertical stripes",
        "plaid", "checkered", "gingham",
        "floral", "polka dot", "geometric pattern",
        "tie-dye", "camouflage", "animal print"
    ]
    
    MATERIALS = [
        "cotton", "denim", "leather", "wool", "cashmere",
        "polyester", "silk", "linen", "fleece", "knit",
        "velvet", "suede", "nylon"
    ]
    
    FITS = [
        "slim fit", "fitted", "regular fit", "loose fit",
        "oversized", "relaxed fit", "tight fit", "tailored"
    ]
    
    def __init__(self):
      
        self.model = None
        self.preprocess = None
        self.tokenizer = None
        self._initialized = False
        
    def _lazy_init(self):
       
        if self._initialized:
            return
            
        try:
            logger.info("Loading CLIP model...")
            
            self.model, _, self.preprocess = open_clip.create_model_and_transforms(
                'ViT-B-32',
                pretrained='laion2b_s34b_b79k'
            )
            self.tokenizer = open_clip.get_tokenizer('ViT-B-32')
            
          
            self.model.eval()
            self._initialized = True
            logger.info("CLIP model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load CLIP model: {e}")
            raise
    
    def _get_top_predictions(
        self,
        image: Image.Image,
        categories: List[str],
        top_k: int = 3
    ) -> List[Tuple[str, float]]:
    
        self._lazy_init()
        
        try:
           
            image_input = self.preprocess(image).unsqueeze(0)
            
            
            text_inputs = self.tokenizer(categories)
            
           
            with torch.no_grad():
                # Don't use autocast for CPU to avoid BFloat16 issues
                image_features = self.model.encode_image(image_input)
                text_features = self.model.encode_text(text_inputs)
                
                
                image_features /= image_features.norm(dim=-1, keepdim=True)
                text_features /= text_features.norm(dim=-1, keepdim=True)
                
               
                similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)
                values, indices = similarity[0].topk(min(top_k, len(categories)))
            
            
            results = []
            for value, index in zip(values, indices):
                results.append((categories[index], float(value)))
            
            return results
            
        except Exception as e:
            logger.error(f"Error in zero-shot classification: {e}")
            return []
    
    def get_image_embedding(self, image: Image.Image) -> Optional[List[float]]:
       
        self._lazy_init()
        
        try:
            image_input = self.preprocess(image).unsqueeze(0)
            
            with torch.no_grad():
                
                image_features = self.model.encode_image(image_input)
                image_features /= image_features.norm(dim=-1, keepdim=True)
            
          
            embedding = image_features[0].float().cpu().numpy().tolist()
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    def analyze_clothing_item(self, image: Image.Image) -> Dict:
        
        logger.info("Starting CLIP analysis of clothing item")
        
        results = {
            "clothing_type": None,
            "color": None,
            "secondary_color": None,
            "season": None,
            "style": None,
            "pattern": None,
            "material": None,
            "fit": None,
            "tags": [],
            "confidence_scores": {},
            "embedding": None
        }
        
        try:
            # Get clothing type
            type_predictions = self._get_top_predictions(image, self.CLOTHING_TYPES, top_k=1)
            if type_predictions:
                results["clothing_type"] = type_predictions[0][0]
                results["confidence_scores"]["clothing_type"] = type_predictions[0][1]
                logger.info(f"Detected clothing type: {results['clothing_type']} ({type_predictions[0][1]:.2f})")
            
            # Get colors
            color_predictions = self._get_top_predictions(image, self.COLORS, top_k=2)
            if color_predictions:
                results["color"] = color_predictions[0][0]
                results["confidence_scores"]["color"] = color_predictions[0][1]
                if len(color_predictions) > 1 and color_predictions[1][1] > 0.15:  # Secondary color threshold
                    results["secondary_color"] = color_predictions[1][0]
                    results["confidence_scores"]["secondary_color"] = color_predictions[1][1]
                logger.info(f"Detected colors: {results['color']}, {results.get('secondary_color', 'N/A')}")
            
            # Get season
            season_predictions = self._get_top_predictions(image, self.SEASONS, top_k=1)
            if season_predictions:
                
                season = season_predictions[0][0].replace(" clothing", "")
                results["season"] = season
                results["confidence_scores"]["season"] = season_predictions[0][1]
                logger.info(f"Detected season: {season}")
            
          
            style_predictions = self._get_top_predictions(image, self.STYLES, top_k=1)
            if style_predictions:
                results["style"] = style_predictions[0][0]
                results["confidence_scores"]["style"] = style_predictions[0][1]
                logger.info(f"Detected style: {results['style']}")
          
            pattern_predictions = self._get_top_predictions(image, self.PATTERNS, top_k=1)
            if pattern_predictions:
                results["pattern"] = pattern_predictions[0][0]
                results["confidence_scores"]["pattern"] = pattern_predictions[0][1]
                logger.info(f"Detected pattern: {results['pattern']}")
       
            material_predictions = self._get_top_predictions(image, self.MATERIALS, top_k=1)
            if material_predictions:
                results["material"] = material_predictions[0][0]
                results["confidence_scores"]["material"] = material_predictions[0][1]
                logger.info(f"Detected material: {results['material']}")
          
            fit_predictions = self._get_top_predictions(image, self.FITS, top_k=1)
            if fit_predictions:
                results["fit"] = fit_predictions[0][0].replace(" fit", "")
                results["confidence_scores"]["fit"] = fit_predictions[0][1]
                logger.info(f"Detected fit: {results['fit']}")
            
            embedding = self.get_image_embedding(image)
            if embedding:
                results["embedding"] = embedding
                logger.info("Generated image embedding")
            
            tags = []
            if results["clothing_type"]:
                tags.append(results["clothing_type"])
            if results["color"]:
                tags.append(results["color"])
            if results["pattern"] and results["pattern"] not in ["solid color", "plain"]:
                tags.append(results["pattern"])
            if results["style"]:
                tags.append(results["style"])
            results["tags"] = tags
            
            logger.info(f"CLIP analysis complete. Tags: {tags}")
            
        except Exception as e:
            logger.error(f"Error during CLIP analysis: {e}")
            import traceback
            traceback.print_exc()
        
        return results



_clip_tagger = None

def get_clip_tagger() -> CLIPTagger:
    """Get or create global CLIP tagger instance."""
    global _clip_tagger
    if _clip_tagger is None:
        _clip_tagger = CLIPTagger()
    return _clip_tagger

