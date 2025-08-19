"""
GPU Data Standardization Module
Normalizes and cleans GPU listing data from various marketplaces
"""

import re
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass


@dataclass
class GPUInfo:
    manufacturer: str  # NVIDIA, AMD, Intel
    series: str       # RTX 40, RX 7000, Arc
    model: str        # 4070, 7800 XT, B580
    vram: Optional[int] = None  # GB
    card_manufacturer: Optional[str] = None  # MSI, ASUS, etc.
    confidence_score: float = 0.0


class GPUDataStandardizer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # NVIDIA GPU patterns
        self.nvidia_patterns = {
            # RTX 50 series
            r'rtx\s*50(\d{2})': ('NVIDIA', 'RTX 50', '50{group1}'),
            # RTX 40 series  
            r'rtx\s*40(\d{2})(?:\s*ti)?': ('NVIDIA', 'RTX 40', '40{group1}'),
            r'rtx\s*4(\d{3})(?:\s*ti)?': ('NVIDIA', 'RTX 40', '4{group1}'),
            # RTX 30 series
            r'rtx\s*30(\d{2})(?:\s*ti)?': ('NVIDIA', 'RTX 30', '30{group1}'),
            r'rtx\s*3(\d{3})(?:\s*ti)?': ('NVIDIA', 'RTX 30', '3{group1}'),
            # Legacy patterns
            r'geforce\s*rtx\s*(\d{4})(?:\s*ti)?': ('NVIDIA', 'RTX', '{group1}'),
        }
        
        # AMD GPU patterns
        self.amd_patterns = {
            # RX 7000 series
            r'rx\s*7(\d{3})\s*(xt|gre)?': ('AMD', 'RX 7000', '7{group1}{group2}'),
            r'radeon\s*rx\s*7(\d{3})\s*(xt|gre)?': ('AMD', 'RX 7000', '7{group1}{group2}'),
            # RX 6000 series
            r'rx\s*6(\d{3})\s*(xt|gre)?': ('AMD', 'RX 6000', '6{group1}{group2}'),
            r'radeon\s*rx\s*6(\d{3})\s*(xt|gre)?': ('AMD', 'RX 6000', '6{group1}{group2}'),
        }
        
        # Intel GPU patterns
        self.intel_patterns = {
            r'arc\s*(a\d{3}|b\d{3})': ('Intel', 'Arc', '{group1}'),
            r'intel\s*arc\s*(a\d{3}|b\d{3})': ('Intel', 'Arc', '{group1}'),
        }
        
        # VRAM patterns
        self.vram_patterns = [
            r'(\d+)\s*gb\s*vram',
            r'(\d+)\s*gb(?:\s*gddr\d*)?',
            r'(\d+)gb',
            r'vram:\s*(\d+)\s*gb',
        ]
        
        # Card manufacturer patterns
        self.manufacturer_patterns = {
            'MSI': [r'\bmsi\b', r'msi\s+gaming', r'msi\s+ventus'],
            'ASUS': [r'\basus\b', r'asus\s+rog', r'asus\s+tuf', r'asus\s+dual'],
            'Gigabyte': [r'\bgigabyte\b', r'gigabyte\s+gaming', r'gigabyte\s+aorus'],
            'EVGA': [r'\bevga\b', r'evga\s+ftw', r'evga\s+sc'],
            'Sapphire': [r'\bsapphire\b', r'sapphire\s+nitro', r'sapphire\s+pulse'],
            'PowerColor': [r'\bpowercolor\b', r'powercolor\s+red'],
            'XFX': [r'\bxfx\b', r'xfx\s+speedster'],
            'Zotac': [r'\bzotac\b', r'zotac\s+gaming'],
            'Palit': [r'\bpalit\b', r'palit\s+gamerock'],
            'Gainward': [r'\bgainward\b', r'gainward\s+phoenix'],
            'PNY': [r'\bpny\b'],
            'Inno3D': [r'\binno3d\b'],
            'Manli': [r'\bmanli\b'],
        }
        
        # Common price cleaning patterns
        self.price_patterns = [
            r'£(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*£',
            r'£\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)',
        ]

    def standardize_listing(self, raw_listing: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Standardize a raw listing into clean, structured data
        """
        try:
            title = raw_listing.get('title', '').strip()
            description = raw_listing.get('description', '').strip()
            price_text = raw_listing.get('price', '').strip()
            
            if not title:
                return None
            
            # Extract GPU information
            gpu_info = self.extract_gpu_info(title, description)
            if not gpu_info or gpu_info.confidence_score < 0.3:
                return None
            
            # Extract and clean price
            price = self.extract_price(price_text)
            
            # Build standardized listing
            standardized = {
                'title': title,
                'description': description,
                'price_text': price_text,
                'standardized_price': price,
                'gpu_manufacturer': gpu_info.manufacturer,
                'gpu_series': gpu_info.series,
                'gpu_model': gpu_info.model,
                'vram_gb': gpu_info.vram,
                'card_manufacturer': gpu_info.card_manufacturer,
                'confidence_score': gpu_info.confidence_score,
                'url': raw_listing.get('url'),
                'marketplace': raw_listing.get('marketplace', raw_listing.get('source')),
                'scraped_at': raw_listing.get('scraped_at'),
                'listing_type': raw_listing.get('listing_type'),
                'condition': self._standardize_condition(raw_listing.get('condition', '')),
                'location': raw_listing.get('location'),
                'seller_info': raw_listing.get('seller_info'),
                'is_sold': raw_listing.get('is_sold', False),
                'is_featured': raw_listing.get('is_featured', False),
                'shipping': raw_listing.get('shipping'),
                'posted_date': raw_listing.get('posted_date'),
                'image_url': raw_listing.get('image_url')
            }
            
            return standardized
            
        except Exception as e:
            self.logger.error(f"Failed to standardize listing: {e}")
            return None

    def extract_gpu_info(self, title: str, description: str = "") -> Optional[GPUInfo]:
        """
        Extract GPU information from title and description
        """
        text = f"{title} {description}".lower()
        
        # Try NVIDIA patterns
        gpu_info = self._match_nvidia_patterns(text)
        if gpu_info:
            return gpu_info
            
        # Try AMD patterns
        gpu_info = self._match_amd_patterns(text)
        if gpu_info:
            return gpu_info
            
        # Try Intel patterns
        gpu_info = self._match_intel_patterns(text)
        if gpu_info:
            return gpu_info
        
        return None

    def _match_nvidia_patterns(self, text: str) -> Optional[GPUInfo]:
        """Match NVIDIA GPU patterns"""
        for pattern, (manufacturer, series, model_template) in self.nvidia_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Build model name from template
                model = model_template.format(
                    group1=match.group(1) if match.lastindex >= 1 else '',
                    group2=match.group(2) if match.lastindex >= 2 else ''
                ).strip()
                
                # Handle TI variants
                if 'ti' in text:
                    model += ' Ti'
                
                gpu_info = GPUInfo(
                    manufacturer=manufacturer,
                    series=series,
                    model=model,
                    confidence_score=0.9
                )
                
                # Extract additional info
                gpu_info.vram = self._extract_vram(text)
                gpu_info.card_manufacturer = self._extract_card_manufacturer(text)
                
                return gpu_info
        
        return None

    def _match_amd_patterns(self, text: str) -> Optional[GPUInfo]:
        """Match AMD GPU patterns"""
        for pattern, (manufacturer, series, model_template) in self.amd_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                model = model_template.format(
                    group1=match.group(1) if match.lastindex >= 1 else '',
                    group2=f" {match.group(2).upper()}" if match.lastindex >= 2 and match.group(2) else ''
                ).strip()
                
                gpu_info = GPUInfo(
                    manufacturer=manufacturer,
                    series=series,
                    model=model,
                    confidence_score=0.9
                )
                
                gpu_info.vram = self._extract_vram(text)
                gpu_info.card_manufacturer = self._extract_card_manufacturer(text)
                
                return gpu_info
        
        return None

    def _match_intel_patterns(self, text: str) -> Optional[GPUInfo]:
        """Match Intel GPU patterns"""
        for pattern, (manufacturer, series, model_template) in self.intel_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                model = model_template.format(
                    group1=match.group(1).upper() if match.lastindex >= 1 else ''
                ).strip()
                
                gpu_info = GPUInfo(
                    manufacturer=manufacturer,
                    series=series,
                    model=model,
                    confidence_score=0.9
                )
                
                gpu_info.vram = self._extract_vram(text)
                gpu_info.card_manufacturer = self._extract_card_manufacturer(text)
                
                return gpu_info
        
        return None

    def _extract_vram(self, text: str) -> Optional[int]:
        """Extract VRAM amount in GB"""
        for pattern in self.vram_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    vram = int(match.group(1))
                    # Sanity check (GPUs typically have 1-24GB VRAM)
                    if 1 <= vram <= 24:
                        return vram
                except ValueError:
                    continue
        return None

    def _extract_card_manufacturer(self, text: str) -> Optional[str]:
        """Extract graphics card manufacturer"""
        for manufacturer, patterns in self.manufacturer_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return manufacturer
        return None

    def extract_price(self, price_text: str) -> Optional[float]:
        """Extract numeric price from text"""
        if not price_text:
            return None
        
        # Remove common price modifiers
        cleaned = re.sub(r'(ono|or best offer|obo|neg|negotiable)', '', price_text.lower())
        
        # Try price patterns in order of preference
        for pattern in self.price_patterns:
            match = re.search(pattern, cleaned)
            if match:
                try:
                    price_str = match.group(1).replace(',', '')
                    price = float(price_str)
                    
                    # Sanity check (reasonable GPU price range)
                    if 10 <= price <= 10000:
                        return price
                except ValueError:
                    continue
        
        return None

    def validate_gpu_targets(self, gpu_info: GPUInfo, config) -> bool:
        """
        Check if the GPU matches our target criteria
        """
        if not gpu_info:
            return False
        
        manufacturer = gpu_info.manufacturer.lower()
        model = gpu_info.model.lower()
        
        if manufacturer == 'nvidia':
            # Check for RTX 30/40/50 series
            for series in config.gpu_targets.nvidia_series:
                if series in model:
                    return True
        
        elif manufacturer == 'amd':
            # Check for RX 6000/7000 series
            for series in config.gpu_targets.amd_series:
                if series in model:
                    return True
        
        elif manufacturer == 'intel':
            # Check for specific Intel models
            for target_model in config.gpu_targets.intel_models:
                if target_model.lower() in model:
                    return True
        
        return False

    def _standardize_condition(self, condition: str) -> str:
        """
        Standardize condition descriptions across marketplaces
        """
        if not condition:
            return 'Unknown'
        
        condition_lower = condition.lower().strip()
        
        # Map various condition descriptions to standard ones
        condition_map = {
            'new': ['new', 'brand new', 'sealed', 'unopened', 'mint'],
            'like new': ['like new', 'excellent', 'very good', 'pristine', 'perfect'],
            'good': ['good', 'working', 'functional', 'used - good'],
            'fair': ['fair', 'average', 'used - fair', 'some wear'],
            'poor': ['poor', 'damaged', 'faulty', 'for parts', 'spares']
        }
        
        for standard_condition, variants in condition_map.items():
            for variant in variants:
                if variant in condition_lower:
                    return standard_condition.title()
        
        return condition.title()

    def get_standardization_stats(self, listings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get statistics about the standardization process
        """
        if not listings:
            return {}
        
        total_listings = len(listings)
        price_extracted = sum(1 for listing in listings if listing.get('standardized_price'))
        gpu_identified = sum(1 for listing in listings if listing.get('gpu_model'))
        vram_extracted = sum(1 for listing in listings if listing.get('vram_gb'))
        manufacturer_identified = sum(1 for listing in listings if listing.get('card_manufacturer'))
        
        return {
            'total_listings': total_listings,
            'price_extraction_rate': round(price_extracted / total_listings * 100, 1),
            'gpu_identification_rate': round(gpu_identified / total_listings * 100, 1),
            'vram_extraction_rate': round(vram_extracted / total_listings * 100, 1),
            'manufacturer_identification_rate': round(manufacturer_identified / total_listings * 100, 1),
            'avg_confidence_score': round(
                sum(listing.get('confidence_score', 0) for listing in listings) / total_listings, 2
            )
        }


# Test cases for the standardizer
def test_gpu_standardizer():
    """Test the GPU standardizer with sample data"""
    standardizer = GPUDataStandardizer()
    
    test_cases = [
        "NVIDIA GeForce RTX 4070 Ti 12GB GDDR6X Graphics Card",
        "AMD Radeon RX 7800 XT 16GB Gaming GPU",
        "MSI RTX 4090 Gaming X Trio 24GB",
        "ASUS ROG Strix RX 6700 XT 12GB",
        "Intel Arc B580 12GB Graphics Card",
        "Gigabyte RTX 3060 Ti 8GB Gaming OC",
        "Sapphire RX 7900 GRE 16GB Nitro+",
        "Zotac RTX 4060 8GB Twin Edge"
    ]
    
    for title in test_cases:
        gpu_info = standardizer.extract_gpu_info(title)
        if gpu_info:
            print(f"✅ {title}")
            print(f"   {gpu_info.manufacturer} {gpu_info.series} {gpu_info.model}")
            print(f"   VRAM: {gpu_info.vram}GB, Manufacturer: {gpu_info.card_manufacturer}")
            print(f"   Confidence: {gpu_info.confidence_score}")
        else:
            print(f"❌ {title}")
        print()


if __name__ == "__main__":
    test_gpu_standardizer()