# GPU Scraper Project - Claude Code Documentation

## Project Overview

A comprehensive web scraper for GPU listings across UK marketplaces (eBay, Facebook Marketplace, Gumtree). Built for defensive security research and price monitoring purposes only.

## Project Structure

```
GPU-Scraper/
├── src/                    # Main application
│   ├── main.py            # Main orchestrator and entry point
│   └── __init__.py
├── config/                 # Configuration management
│   ├── settings.py        # Configuration classes and YAML handling
│   ├── settings.yaml      # Main configuration file
│   └── __init__.py
├── scrapers/              # Marketplace scrapers
│   ├── base_scraper.py    # Common scraping functionality
│   ├── ebay_scraper.py    # eBay UK scraper
│   ├── facebook_scraper.py # Facebook Marketplace scraper
│   ├── gumtree_scraper.py # Gumtree UK scraper
│   └── __init__.py
├── data/                  # Data processing and standardization
│   ├── standardizer.py    # GPU data normalization and cleaning
│   └── __init__.py
├── export/                # Data export functionality
│   ├── excel_exporter.py  # Excel export with multiple sheets
│   └── __init__.py
├── utils/                 # Utilities and helpers
│   ├── compliance_checker.py # Robots.txt and ToS compliance
│   ├── logger.py          # Logging configuration
│   └── __init__.py
├── requirements.txt       # Python dependencies
├── README.md             # Basic project description
└── CLAUDE.md             # This documentation file
```

## Key Features

### 1. Multi-Marketplace Scraping
- **eBay UK**: Comprehensive scraping with category filtering and condition-based searches
- **Facebook Marketplace**: Basic implementation (requires authentication, has strict anti-bot measures)  
- **Gumtree UK**: Full scraping support with location-based filtering

### 2. Data Standardization
- Intelligent GPU model detection (NVIDIA RTX, AMD RX, Intel Arc)
- Price extraction and normalization
- Graphics card manufacturer identification (MSI, ASUS, Gigabyte, etc.)
- VRAM extraction (memory capacity)
- Condition standardization across marketplaces

### 3. Compliance & Ethics
- Robots.txt compliance checking
- Terms of Service analysis
- Rate limiting and respectful scraping practices
- Site-specific guidelines and recommendations

### 4. Data Export
- Excel export with multiple sheets (listings, summary, compliance, price analysis)
- CSV backup export
- Summary statistics and marketplace breakdown
- Price analysis with charts-ready data

### 5. Configuration Management
- YAML-based configuration
- Environment variable support for credentials
- Configurable scraping limits and targets
- GPU series and model targeting

## Installation & Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Settings**:
   - Edit `config/settings.yaml` for scraping preferences
   - Set environment variables for authentication (optional):
     ```bash
     set GPU_SCRAPER_FB_EMAIL=your_email@example.com
     set GPU_SCRAPER_FB_PASSWORD=your_password
     set GPU_SCRAPER_EBAY_API=your_api_key
     ```

3. **Test Installation**:
   ```bash
   python simple_test.py
   ```

## Usage

### Basic Usage
```bash
python src/main.py
```

### Testing Individual Components
```bash
# Test eBay scraper only
python scrapers/ebay_scraper.py

# Test data standardizer
python data/standardizer.py

# Test compliance checker
python utils/compliance_checker.py
```

## Configuration Options

Key settings in `config/settings.yaml`:

- **enabled_scrapers**: Which marketplaces to scrape
- **scraping_limits**: Rate limiting and result limits
- **gpu_targets**: Specific GPU series/models to target
- **authentication**: Credentials for sites requiring login
- **advanced**: Data quality thresholds and export options

## Compliance Notes

### eBay UK
- Generally allows scraping for personal research
- Respects robots.txt directives
- Implements 2-second delays between requests
- Focuses on publicly available listing data

### Facebook Marketplace  
- Has strict anti-scraping measures
- Requires authentication (may violate ToS)
- High risk of IP blocking
- Consider official Marketing API for legitimate use

### Gumtree UK
- More permissive for personal use
- Respects robots.txt
- Reasonable rate limiting implemented
- Good for price research

## Data Fields

Standardized output includes:
- `title`: Original listing title
- `marketplace`: Source marketplace  
- `standardized_price`: Cleaned numeric price
- `gpu_manufacturer`: NVIDIA, AMD, or Intel
- `gpu_series`: GPU series (RTX 40, RX 7000, etc.)
- `gpu_model`: Specific model (4070, 7800 XT, etc.)
- `vram_gb`: Video memory in GB
- `card_manufacturer`: Board partner (MSI, ASUS, etc.)
- `condition`: Standardized condition rating
- `location`: Seller location
- `url`: Direct link to listing

## Development Notes

### Architecture
- Async/await throughout for performance
- Modular design with clear separation of concerns
- Configuration-driven behavior
- Comprehensive error handling and logging

### Key Classes
- `GPUScraper`: Main orchestrator
- `BaseScraper`: Common scraping functionality  
- `GPUDataStandardizer`: Data normalization
- `ExcelExporter`: Multi-sheet Excel output
- `ComplianceChecker`: Ethics and policy validation
- `ScraperConfig`: Configuration management

### Testing
- Unit tests for individual components
- Integration test for full pipeline
- Compliance validation before scraping
- Data quality validation after processing

## Ethical Considerations

This scraper is designed for:
- ✅ Personal price research
- ✅ Market analysis and trends
- ✅ Academic research purposes
- ✅ Security research (defensive only)

NOT intended for:
- ❌ Commercial data reselling
- ❌ Automated purchasing/bidding
- ❌ Circumventing site security measures
- ❌ High-frequency scraping that impacts site performance

## Troubleshooting

### Common Issues
1. **Import errors**: Run `pip install -r requirements.txt`
2. **Encoding errors**: Ensure UTF-8 encoding in terminal
3. **Rate limiting**: Increase delays in `config/settings.yaml`
4. **Authentication failures**: Check environment variables

### Debug Mode
Enable detailed logging by setting `log_level: DEBUG` in config.

## Future Enhancements

Potential improvements:
- Selenium support for JavaScript-heavy sites
- Database storage for historical price tracking
- Email notifications for specific finds
- API endpoint for programmatic access
- Machine learning for better GPU identification
- Price trend analysis and alerts

## Commands Reference

```bash
# Install dependencies
pip install -r requirements.txt

# Run quick structure test  
python simple_test.py

# Run full pipeline test (requires dependencies)
python test_pipeline.py

# Start scraping
python src/main.py

# Test individual scrapers
python scrapers/ebay_scraper.py
python scrapers/gumtree_scraper.py

# Test compliance for specific site
python utils/compliance_checker.py
```

---

**Last Updated**: August 2025
**Project Status**: Complete and functional
**Maintenance**: Monitor for marketplace structure changes