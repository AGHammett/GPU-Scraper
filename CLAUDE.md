# CLAUDE.md - GPU Scraper Project Documentation

This file provides comprehensive guidance to Claude Code (claude.ai/code) when working with the GPU Scraper repository.

## Project Overview

GPUScraper is a web scraper designed to collect GPU sales data across UK marketplaces for defensive security research and price monitoring. The scraper targets eBay UK, Facebook Marketplace UK, Gumtree UK, and other relevant UK hardware marketplaces.

## Repository Structure

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

## Technical Specifications

### Core Technologies
- **Python 3.8+** with async/await support
- **Libraries**: requests, BeautifulSoup4, selenium (optional), pandas, openpyxl, aiohttp
- **Architecture**: Modular design with configuration-driven behavior
- **Data Format**: Excel with multiple sheets, CSV backup

### Key Classes & Modules
- `GPUScraper`: Main orchestrator coordinating all scrapers
- `BaseScraper`: Abstract base class for marketplace scrapers
- `GPUDataStandardizer`: Robust data normalization engine
- `ExcelExporter`: Multi-sheet Excel generation with charts
- `ComplianceChecker`: Ethics and robots.txt validation
- `ScraperConfig`: YAML-based configuration management

## Development Components

### 1. Main Orchestrator (`src/main.py`)
Coordinates the entire scraping pipeline:
- Loads configuration from YAML
- Initializes marketplace scrapers
- Manages concurrent scraping with rate limiting
- Aggregates and standardizes results
- Triggers data export

### 2. Marketplace Scrapers

#### eBay UK Scraper (`scrapers/ebay_scraper.py`)
- Search API integration (if API key available)
- Web scraping fallback with BeautifulSoup
- Handles both "Buy It Now" and auction listings
- Extracts: title, price, condition, seller info, images
- Category-based filtering for GPUs
- Proper pagination handling

#### Facebook Marketplace (`scrapers/facebook_scraper.py`)
- Authentication-based scraping (requires login)
- High anti-bot detection - use cautiously
- Location-based search within UK
- Consider using official Marketing API instead

#### Gumtree UK (`scrapers/gumtree_scraper.py`)
- Location-based filtering across UK regions
- Category navigation for computer components
- Seller contact information extraction
- More permissive scraping policies

### 3. Data Standardization Module (`data/standardizer.py`)

Robust GPU data extraction and normalization:

**GPU Model Detection**:
- Regex patterns for NVIDIA (RTX 40/30/20, GTX series)
- AMD detection (RX 7000/6000/5000 series)
- Intel Arc series recognition
- Handles variations: "RTX4070" vs "RTX 4070"

**Data Extraction**:
- VRAM extraction (4GB, 8GB, 12GB, 16GB, 24GB)
- Card manufacturer identification (MSI, ASUS, Gigabyte, EVGA, Zotac, etc.)
- Price normalization (removes £, handles "ONO", "or best offer")
- Condition standardization across marketplaces
- Confidence scoring for extracted data

**Test Cases Required**:
- Messy title parsing: "Gaming PC RTX4070ti MSI 16gb ram NOT 4080"
- Multiple GPU mentions: "Upgrade from 3060 to 4070"
- Non-standard formats: "nvidia geforce rtx four thousand seventy"

### 4. Excel Export Module (`export/excel_exporter.py`)

Production-ready Excel generation:

**Features**:
- Multiple sheets: Listings, Summary, Compliance, Price Analysis
- Conditional formatting for price ranges
- Auto-filters and sorting capabilities
- Summary statistics by GPU model
- Price trend charts (data prepared for Excel charts)
- Incremental updates with deduplication
- Timestamp and source tracking

**Error Handling**:
- File permission checks
- Large dataset pagination
- Memory-efficient processing
- Backup CSV generation

### 5. Compliance & Ethics (`utils/compliance_checker.py`)

Ensures ethical scraping:
- Robots.txt parsing and respect
- Terms of Service analysis
- Rate limiting enforcement
- User-agent rotation
- IP rotation support (if proxies configured)
- Scraping guidelines per marketplace

## Configuration (`config/settings.yaml`)

```yaml
scraping:
  enabled_scrapers:
    - ebay
    - gumtree
    # - facebook  # Requires authentication
  
  limits:
    max_results_per_site: 100
    request_delay_seconds: 2
    concurrent_requests: 3
    timeout_seconds: 30

gpu_targets:
  nvidia:
    - "RTX 4090"
    - "RTX 4080"
    - "RTX 4070"
    - "RTX 3080"
  amd:
    - "RX 7900 XTX"
    - "RX 7800 XT"
    - "RX 6800 XT"

authentication:
  facebook:
    email: ${GPU_SCRAPER_FB_EMAIL}
    password: ${GPU_SCRAPER_FB_PASSWORD}
  ebay:
    api_key: ${GPU_SCRAPER_EBAY_API}

export:
  format: excel
  include_charts: true
  deduplicate: true
  
advanced:
  min_confidence_score: 0.7
  log_level: INFO
  use_proxies: false
```

## Data Output Format

Standardized fields in exported data:

| Field | Description | Example |
|-------|-------------|---------|
| `title` | Original listing title | "MSI RTX 4070 Gaming X Trio 12GB" |
| `marketplace` | Source marketplace | "ebay_uk" |
| `standardized_price` | Numeric price in GBP | 549.99 |
| `gpu_manufacturer` | Chip manufacturer | "NVIDIA" |
| `gpu_series` | GPU generation | "RTX 40" |
| `gpu_model` | Specific model | "4070" |
| `vram_gb` | Video memory | 12 |
| `card_manufacturer` | Board partner | "MSI" |
| `condition` | Item condition | "Used - Like New" |
| `location` | Seller location | "London, UK" |
| `url` | Direct listing link | "https://..." |
| `scraped_at` | Timestamp | "2025-08-18 14:30:00" |
| `confidence_score` | Data quality score | 0.95 |

## Installation & Usage

### Quick Setup
```bash
# Clone repository
git clone <repository-url>
cd GPU-Scraper

# Install dependencies
pip install -r requirements.txt

# Configure settings
cp config/settings.yaml.example config/settings.yaml
# Edit settings.yaml with your preferences

# Set environment variables (optional)
export GPU_SCRAPER_FB_EMAIL=your_email@example.com
export GPU_SCRAPER_FB_PASSWORD=your_password
export GPU_SCRAPER_EBAY_API=your_api_key

# Run scraper
python src/main.py
```

### Testing Components
```bash
# Test project structure
python simple_test.py

# Test full pipeline
python test_pipeline.py

# Test individual scrapers
python scrapers/ebay_scraper.py
python scrapers/gumtree_scraper.py

# Test data standardization
python data/standardizer.py

# Check compliance for a site
python utils/compliance_checker.py
```

## Marketplace-Specific Guidelines

### eBay UK
- ✅ Generally allows personal research scraping
- ✅ Respects robots.txt
- ⚠️ Implement 2+ second delays
- 💡 Use official API if available

### Facebook Marketplace
- ❌ Strong anti-scraping measures
- ❌ May violate Terms of Service
- ⚠️ High risk of IP/account blocking
- 💡 Consider official Marketing API

### Gumtree UK
- ✅ More permissive for personal use
- ✅ Respects robots.txt
- ⚠️ Reasonable rate limiting required
- 💡 Good for price research

## Ethical Usage

### Approved Use Cases
- ✅ Personal price research and monitoring
- ✅ Academic market analysis
- ✅ Defensive security research
- ✅ Market trend analysis

### Prohibited Uses
- ❌ Commercial data reselling
- ❌ Automated purchasing/bidding bots
- ❌ Circumventing security measures
- ❌ High-frequency scraping causing server load

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Import errors | Run `pip install -r requirements.txt` |
| Encoding errors | Set terminal to UTF-8 encoding |
| Rate limiting | Increase delays in `config/settings.yaml` |
| Authentication fails | Check environment variables |
| No results | Verify GPU targets in config |
| Excel errors | Check write permissions, disk space |

### Debug Mode
Enable verbose logging:
```yaml
advanced:
  log_level: DEBUG
```

## Future Enhancements

- [ ] Selenium integration for JavaScript-heavy sites
- [ ] PostgreSQL/SQLite for historical data
- [ ] Email/Discord notifications for deals
- [ ] REST API for programmatic access
- [ ] ML-based GPU identification improvement
- [ ] Price prediction models
- [ ] Multi-currency support
- [ ] International marketplace expansion

## Development Workflow

1. **Check compliance** before adding new scrapers
2. **Test individually** before integration
3. **Validate data quality** with standardizer
4. **Monitor rate limits** during development
5. **Document marketplace-specific quirks**
6. **Update regex patterns** as new GPUs release

## Error Handling Strategy

- Use try/except blocks with specific exceptions
- Log errors with context for debugging
- Implement exponential backoff for retries
- Graceful degradation when scrapers fail
- Continue processing even with partial failures

## Performance Optimization

- Async/await for concurrent requests
- Connection pooling for HTTP clients
- Lazy loading for large datasets
- Incremental processing for exports
- Cache robots.txt checks

---

**Project Status**: Complete and functional  
**Last Updated**: August 2025  
**Maintenance Notes**: Monitor marketplace HTML structure changes monthly