#!/usr/bin/env python3
"""
GPU Scraper - Main Orchestrator
Coordinates scraping across multiple UK marketplaces for GPU listings
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from config.settings import ScraperConfig
from scrapers.ebay_scraper import EBayScraper
from scrapers.facebook_scraper import FacebookScraper
from scrapers.gumtree_scraper import GumtreeScraper
from data.standardizer import GPUDataStandardizer
from export.excel_exporter import ExcelExporter
from utils.compliance_checker import ComplianceChecker
from utils.logger import setup_logging


class GPUScraper:
    def __init__(self, config_path: str = "config/settings.yaml"):
        self.config = ScraperConfig(config_path)
        self.standardizer = GPUDataStandardizer()
        self.exporter = ExcelExporter()
        self.compliance_checker = ComplianceChecker()
        
        self.scrapers = {
            'ebay': EBayScraper(self.config),
            'facebook': FacebookScraper(self.config),
            'gumtree': GumtreeScraper(self.config)
        }
        
        setup_logging(self.config.log_level, self.config.log_file)
        self.logger = logging.getLogger(__name__)

    async def check_compliance(self) -> Dict[str, Dict[str, Any]]:
        """Check robots.txt and ToS compliance for all target sites"""
        self.logger.info("Checking compliance for all target sites...")
        
        sites = {
            'ebay': 'https://www.ebay.co.uk',
            'facebook': 'https://www.facebook.com/marketplace',
            'gumtree': 'https://www.gumtree.com'
        }
        
        compliance_results = {}
        for site_name, url in sites.items():
            try:
                result = await self.compliance_checker.check_site_compliance(url)
                compliance_results[site_name] = result
                
                if not result['robots_allowed']:
                    self.logger.warning(f"{site_name}: Robots.txt disallows scraping")
                if result['tos_concerns']:
                    self.logger.warning(f"{site_name}: ToS concerns found: {result['tos_concerns']}")
                    
            except Exception as e:
                self.logger.error(f"Failed to check compliance for {site_name}: {e}")
                compliance_results[site_name] = {'error': str(e)}
        
        return compliance_results

    async def scrape_all_sites(self) -> List[Dict[str, Any]]:
        """Coordinate scraping across all enabled marketplaces"""
        self.logger.info("Starting GPU scraping across all marketplaces...")
        
        all_listings = []
        
        for scraper_name, scraper in self.scrapers.items():
            if not self.config.is_scraper_enabled(scraper_name):
                self.logger.info(f"Skipping {scraper_name} (disabled in config)")
                continue
                
            try:
                self.logger.info(f"Scraping {scraper_name}...")
                listings = await scraper.scrape_gpu_listings()
                
                for listing in listings:
                    listing['source'] = scraper_name
                    listing['scraped_at'] = datetime.now().isoformat()
                
                all_listings.extend(listings)
                self.logger.info(f"Found {len(listings)} listings from {scraper_name}")
                
            except Exception as e:
                self.logger.error(f"Error scraping {scraper_name}: {e}")
                continue
        
        return all_listings

    def standardize_data(self, raw_listings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Standardize and clean the scraped data"""
        self.logger.info(f"Standardizing {len(raw_listings)} raw listings...")
        
        standardized_listings = []
        for listing in raw_listings:
            try:
                standardized = self.standardizer.standardize_listing(listing)
                if standardized:
                    standardized_listings.append(standardized)
            except Exception as e:
                self.logger.warning(f"Failed to standardize listing: {e}")
                continue
        
        self.logger.info(f"Successfully standardized {len(standardized_listings)} listings")
        return standardized_listings

    def remove_duplicates(self, listings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate listings based on URL and title similarity"""
        self.logger.info("Removing duplicate listings...")
        
        seen_urls = set()
        unique_listings = []
        
        for listing in listings:
            url = listing.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_listings.append(listing)
        
        removed_count = len(listings) - len(unique_listings)
        self.logger.info(f"Removed {removed_count} duplicate listings")
        
        return unique_listings

    async def run_scraper(self) -> str:
        """Main orchestrator method - runs the complete scraping pipeline"""
        start_time = datetime.now()
        self.logger.info(f"Starting GPU scraper at {start_time}")
        
        try:
            # Check compliance first
            compliance_results = await self.check_compliance()
            self.logger.info("Compliance check completed")
            
            # Scrape all sites
            raw_listings = await self.scrape_all_sites()
            
            if not raw_listings:
                self.logger.warning("No listings found across all sites")
                return "No data scraped"
            
            # Standardize data
            standardized_listings = self.standardize_data(raw_listings)
            
            # Remove duplicates
            final_listings = self.remove_duplicates(standardized_listings)
            
            # Export to Excel
            output_file = self.exporter.export_to_excel(
                final_listings, 
                compliance_results
            )
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            self.logger.info(f"Scraping completed in {duration}")
            self.logger.info(f"Final dataset: {len(final_listings)} unique GPU listings")
            self.logger.info(f"Output saved to: {output_file}")
            
            return output_file
            
        except Exception as e:
            self.logger.error(f"Scraper failed: {e}")
            raise


async def main():
    """Entry point for the GPU scraper"""
    try:
        scraper = GPUScraper()
        output_file = await scraper.run_scraper()
        print("Scraping completed successfully!")
        print(f"Output saved to: {output_file}")
        
    except Exception as e:
        print(f"Scraper failed: {e}")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())