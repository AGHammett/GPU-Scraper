#!/usr/bin/env python3
"""
Quick structure test for GPU Scraper
Tests file structure and basic syntax without importing dependencies
"""

import os
import sys
from pathlib import Path


def test_file_structure():
    """Test that all required files exist"""
    print("Testing file structure...")
    
    required_files = [
        'src/main.py',
        'src/__init__.py',
        'config/settings.py',
        'config/__init__.py',
        'scrapers/base_scraper.py',
        'scrapers/ebay_scraper.py',
        'scrapers/facebook_scraper.py',
        'scrapers/gumtree_scraper.py',
        'scrapers/__init__.py',
        'data/standardizer.py',
        'data/__init__.py',
        'export/excel_exporter.py',
        'export/__init__.py',
        'utils/compliance_checker.py',
        'utils/logger.py',
        'utils/__init__.py',
        'config/settings.yaml',
        'requirements.txt',
        'README.md'
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path}")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n⚠️  Missing files: {len(missing_files)}")
        return False
    else:
        print("   ✅ All required files present")
        return True


def test_python_syntax():
    """Test Python syntax of main files"""
    print("\n🐍 Testing Python syntax...")
    
    python_files = [
        'src/main.py',
        'config/settings.py',
        'scrapers/base_scraper.py',
        'scrapers/ebay_scraper.py',
        'scrapers/facebook_scraper.py',
        'scrapers/gumtree_scraper.py',
        'data/standardizer.py',
        'export/excel_exporter.py',
        'utils/compliance_checker.py',
        'utils/logger.py'
    ]
    
    syntax_errors = []
    
    for file_path in python_files:
        if Path(file_path).exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    source = f.read()
                compile(source, file_path, 'exec')
                print(f"   ✅ {file_path}")
            except SyntaxError as e:
                print(f"   ❌ {file_path}: Syntax error at line {e.lineno}")
                syntax_errors.append((file_path, str(e)))
            except Exception as e:
                print(f"   ⚠️  {file_path}: {e}")
        else:
            print(f"   ⏭️  {file_path}: File not found")
    
    if syntax_errors:
        print(f"\n⚠️  Syntax errors found in {len(syntax_errors)} files")
        return False
    else:
        print("   ✅ All Python files have valid syntax")
        return True


def test_configuration():
    """Test configuration file validity"""
    print("\n⚙️  Testing configuration...")
    
    config_file = Path('config/settings.yaml')
    
    if config_file.exists():
        try:
            import yaml
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Check required sections
            required_sections = ['enabled_scrapers', 'scraping_limits', 'gpu_targets', 'authentication']
            
            for section in required_sections:
                if section in config:
                    print(f"   ✅ {section} section present")
                else:
                    print(f"   ❌ {section} section missing")
                    return False
            
            print("   ✅ Configuration file is valid")
            return True
            
        except ImportError:
            print("   ⚠️  PyYAML not installed, skipping config validation")
            return True
        except Exception as e:
            print(f"   ❌ Configuration error: {e}")
            return False
    else:
        print("   ❌ Configuration file not found")
        return False


def show_project_overview():
    """Show project overview"""
    print("\n📋 GPU Scraper Project Overview")
    print("-" * 40)
    
    components = {
        "Main Orchestrator": "src/main.py - Coordinates the entire scraping process",
        "Configuration": "config/settings.py - Manages settings and authentication",
        "Base Scraper": "scrapers/base_scraper.py - Common scraping functionality",
        "eBay Scraper": "scrapers/ebay_scraper.py - eBay UK marketplace scraper", 
        "Facebook Scraper": "scrapers/facebook_scraper.py - Facebook Marketplace scraper",
        "Gumtree Scraper": "scrapers/gumtree_scraper.py - Gumtree UK scraper",
        "Data Standardizer": "data/standardizer.py - Normalizes GPU data across sources",
        "Excel Exporter": "export/excel_exporter.py - Exports data to Excel with charts",
        "Compliance Checker": "utils/compliance_checker.py - Checks robots.txt and ToS",
        "Logger": "utils/logger.py - Logging configuration"
    }
    
    for component, description in components.items():
        print(f"   📄 {component}: {description}")
    
    print(f"\n🎯 Features:")
    print(f"   • Scrapes GPU listings from eBay, Facebook Marketplace, and Gumtree")
    print(f"   • Standardizes data across different marketplace formats")
    print(f"   • Exports results to Excel with multiple sheets and analysis")
    print(f"   • Checks compliance with robots.txt and Terms of Service")
    print(f"   • Configurable rate limiting and scraping targets")
    print(f"   • Supports NVIDIA RTX, AMD RX, and Intel Arc GPUs")


def main():
    """Main test function"""
    print("GPU Scraper Quick Structure Test")
    print("=" * 45)
    
    # Test file structure
    structure_ok = test_file_structure()
    
    # Test Python syntax
    syntax_ok = test_python_syntax()
    
    # Test configuration
    config_ok = test_configuration()
    
    # Show overview
    show_project_overview()
    
    print("\n" + "=" * 45)
    if structure_ok and syntax_ok and config_ok:
        print("✅ Quick tests passed! Project structure looks good.")
        print("\n💡 Next steps:")
        print("   1. Install dependencies: pip install -r requirements.txt")
        print("   2. Run full test: python test_pipeline.py")
        print("   3. Start scraping: python src/main.py")
        return 0
    else:
        print("❌ Some structural issues found. Please review above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)