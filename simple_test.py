#!/usr/bin/env python3
"""
Simple structure test for GPU Scraper
"""

import os
from pathlib import Path


def test_files():
    """Test that core files exist"""
    print("Testing file structure...")
    
    files = [
        'src/main.py',
        'config/settings.py',
        'scrapers/base_scraper.py',
        'scrapers/ebay_scraper.py', 
        'scrapers/facebook_scraper.py',
        'scrapers/gumtree_scraper.py',
        'data/standardizer.py',
        'export/excel_exporter.py',
        'utils/compliance_checker.py',
        'utils/logger.py',
        'config/settings.yaml',
        'requirements.txt'
    ]
    
    all_exist = True
    for f in files:
        if Path(f).exists():
            print(f"  OK: {f}")
        else:
            print(f"  MISSING: {f}")
            all_exist = False
    
    return all_exist


def main():
    print("GPU Scraper Structure Test")
    print("=" * 30)
    
    if test_files():
        print("\nSUCCESS: All core files present")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Run scraper: python src/main.py")
    else:
        print("\nERROR: Some files are missing")


if __name__ == "__main__":
    main()