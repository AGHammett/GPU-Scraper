#!/usr/bin/env python3
"""
GPU Scraper Pipeline Test
Tests the complete scraping pipeline with a limited scope
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.main import GPUScraper
from config.settings import ScraperConfig


async def test_pipeline():
    """Test the complete scraping pipeline"""
    print("🧪 Testing GPU Scraper Pipeline")
    print("=" * 40)
    
    try:
        # Create scraper with test configuration
        scraper = GPUScraper()
        
        # Test configuration loading
        print("✅ Configuration loaded successfully")
        print(f"   Enabled scrapers: {scraper.config.enabled_scrapers}")
        print(f"   Output directory: {scraper.config.output_dir}")
        print(f"   Log level: {scraper.config.log_level}")
        
        # Test compliance checking
        print("\n🔍 Testing compliance checks...")
        compliance_results = await scraper.check_compliance()
        
        for site, result in compliance_results.items():
            if 'error' in result:
                print(f"   ❌ {site}: {result['error']}")
            else:
                print(f"   {'✅' if result['robots_allowed'] else '❌'} {site}: Robots.txt {'allowed' if result['robots_allowed'] else 'disallowed'}")
                if result['tos_concerns']:
                    print(f"      ⚠️  ToS concerns: {len(result['tos_concerns'])}")
        
        # Test data standardizer
        print("\n📊 Testing data standardizer...")
        test_listing = {
            'title': 'NVIDIA RTX 4070 Gaming Graphics Card 12GB GDDR6X',
            'price': '£450.00',
            'condition': 'Used - Excellent',
            'marketplace': 'Test Market',
            'url': 'https://example.com/test'
        }
        
        standardized = scraper.standardizer.standardize_listing(test_listing)
        if standardized:
            print("   ✅ Data standardization working")
            print(f"      GPU: {standardized['gpu_manufacturer']} {standardized['gpu_model']}")
            print(f"      Price: £{standardized['standardized_price']}")
            print(f"      Confidence: {standardized['confidence_score']}")
        else:
            print("   ❌ Data standardization failed")
        
        # Test Excel exporter
        print("\n📁 Testing Excel exporter...")
        test_listings = [standardized] if standardized else []
        
        if test_listings:
            output_file = scraper.exporter.export_to_excel(test_listings, compliance_results)
            print(f"   ✅ Excel export successful: {output_file}")
            
            # Test summary report
            summary = scraper.exporter.create_summary_report(test_listings)
            print(f"   ✅ Summary report generated: {summary['total_listings']} listings")
        else:
            print("   ⚠️  No test data to export")
        
        # Limited scraping test (just check if scrapers initialize)
        print("\n🌐 Testing scraper initialization...")
        for name, scraper_instance in scraper.scrapers.items():
            if scraper.config.is_scraper_enabled(name):
                print(f"   ✅ {name} scraper initialized")
                
                # Test compliance notes for specific scrapers
                if hasattr(scraper_instance, 'get_compliance_notes'):
                    notes = scraper_instance.get_compliance_notes()
                    print(f"      📋 Compliance notes: {len(notes)} items")
            else:
                print(f"   ⏭️  {name} scraper disabled")
        
        print("\n🎉 Pipeline test completed successfully!")
        print("💡 To run a full scrape, execute: python src/main.py")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_imports():
    """Test all module imports"""
    print("📦 Testing module imports...")
    
    imports_to_test = [
        ('config.settings', 'ScraperConfig'),
        ('scrapers.ebay_scraper', 'EBayScraper'),
        ('scrapers.facebook_scraper', 'FacebookScraper'),
        ('scrapers.gumtree_scraper', 'GumtreeScraper'),
        ('data.standardizer', 'GPUDataStandardizer'),
        ('export.excel_exporter', 'ExcelExporter'),
        ('utils.compliance_checker', 'ComplianceChecker'),
        ('utils.logger', 'setup_logging')
    ]
    
    failed_imports = []
    
    for module_name, class_name in imports_to_test:
        try:
            module = __import__(module_name, fromlist=[class_name])
            getattr(module, class_name)
            print(f"   ✅ {module_name}.{class_name}")
        except ImportError as e:
            print(f"   ❌ {module_name}.{class_name}: {e}")
            failed_imports.append((module_name, class_name, str(e)))
        except AttributeError as e:
            print(f"   ❌ {module_name}.{class_name}: {e}")
            failed_imports.append((module_name, class_name, str(e)))
    
    if failed_imports:
        print(f"\n⚠️  {len(failed_imports)} import failures detected")
        return False
    else:
        print("   ✅ All imports successful")
        return True


def test_dependencies():
    """Test required dependencies"""
    print("📚 Testing dependencies...")
    
    required_packages = [
        'aiohttp', 'beautifulsoup4', 'pandas', 'openpyxl', 
        'yaml', 'lxml', 'aiofiles'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'yaml':
                import yaml
            elif package == 'beautifulsoup4':
                import bs4
            else:
                __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("   Run: pip install -r requirements.txt")
        return False
    else:
        print("   ✅ All dependencies available")
        return True


async def main():
    """Main test function"""
    print("🚀 GPU Scraper Pipeline Test Suite")
    print("=" * 50)
    
    # Test 1: Dependencies
    deps_ok = test_dependencies()
    print()
    
    # Test 2: Imports
    imports_ok = test_imports()
    print()
    
    # Test 3: Pipeline (only if previous tests passed)
    if deps_ok and imports_ok:
        pipeline_ok = await test_pipeline()
    else:
        print("⏭️  Skipping pipeline test due to previous failures")
        pipeline_ok = False
    
    print("\n" + "=" * 50)
    if deps_ok and imports_ok and pipeline_ok:
        print("🎉 All tests passed! GPU Scraper is ready to use.")
        return 0
    else:
        print("❌ Some tests failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)