"""
Compliance checker for robots.txt and Terms of Service
Analyzes website policies to ensure ethical scraping practices
"""

import asyncio
import logging
import re
from typing import Dict, List, Any, Optional
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin, urlparse
import aiohttp


class ComplianceChecker:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Common ToS violation indicators
        self.tos_red_flags = [
            r'automated.*access.*prohibited',
            r'scraping.*not.*allowed',
            r'data.*mining.*forbidden',
            r'bots.*prohibited',
            r'crawling.*unauthorized',
            r'systematic.*downloading.*prohibited',
            r'robots.*not.*permitted',
            r'harvesting.*data.*illegal'
        ]
        
        # Rate limiting indicators
        self.rate_limit_indicators = [
            r'rate.*limit',
            r'requests.*per.*minute',
            r'api.*throttling',
            r'excessive.*requests'
        ]

    async def check_site_compliance(self, base_url: str) -> Dict[str, Any]:
        """
        Comprehensive compliance check for a website
        Returns analysis of robots.txt, ToS, and scraping policies
        """
        self.logger.info(f"Checking compliance for {base_url}")
        
        result = {
            'site': base_url,
            'robots_allowed': False,
            'robots_details': {},
            'tos_concerns': [],
            'rate_limits': [],
            'recommendations': []
        }
        
        try:
            # Check robots.txt
            robots_result = await self._check_robots_txt(base_url)
            result['robots_allowed'] = robots_result['allowed']
            result['robots_details'] = robots_result
            
            # Check Terms of Service
            tos_result = await self._analyze_terms_of_service(base_url)
            result['tos_concerns'] = tos_result['concerns']
            result['rate_limits'] = tos_result['rate_limits']
            
            # Generate recommendations
            result['recommendations'] = self._generate_recommendations(result)
            
        except Exception as e:
            self.logger.error(f"Compliance check failed for {base_url}: {e}")
            result['error'] = str(e)
        
        return result

    async def _check_robots_txt(self, base_url: str) -> Dict[str, Any]:
        """Check robots.txt compliance"""
        robots_url = urljoin(base_url, '/robots.txt')
        
        result = {
            'url': robots_url,
            'allowed': False,
            'crawl_delay': None,
            'disallowed_paths': [],
            'user_agent_specific': {},
            'raw_content': None
        }
        
        try:
            # Fetch robots.txt content
            async with aiohttp.ClientSession() as session:
                async with session.get(robots_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        content = await response.text()
                        result['raw_content'] = content
                        
                        # Parse with urllib robotparser
                        rp = RobotFileParser()
                        rp.set_url(robots_url)
                        rp.read()
                        
                        # Check general access
                        result['allowed'] = rp.can_fetch('*', base_url)
                        
                        # Extract crawl delay
                        delay_match = re.search(r'crawl-delay:\s*(\d+)', content, re.IGNORECASE)
                        if delay_match:
                            result['crawl_delay'] = int(delay_match.group(1))
                        
                        # Extract disallowed paths
                        disallow_matches = re.findall(r'disallow:\s*([^\s]+)', content, re.IGNORECASE)
                        result['disallowed_paths'] = disallow_matches
                        
                        # Check for user-agent specific rules
                        user_agents = re.findall(r'user-agent:\s*([^\s]+)', content, re.IGNORECASE)
                        for ua in set(user_agents):
                            if ua != '*':
                                result['user_agent_specific'][ua] = rp.can_fetch(ua, base_url)
                    
                    elif response.status == 404:
                        result['allowed'] = True  # No robots.txt means allowed
                        self.logger.info(f"No robots.txt found at {robots_url} - assuming allowed")
                    else:
                        self.logger.warning(f"HTTP {response.status} when fetching {robots_url}")
                        
        except Exception as e:
            self.logger.error(f"Failed to check robots.txt for {base_url}: {e}")
            result['allowed'] = True  # Assume allowed if we can't check
        
        return result

    async def _analyze_terms_of_service(self, base_url: str) -> Dict[str, Any]:
        """Analyze Terms of Service for scraping restrictions"""
        
        result = {
            'concerns': [],
            'rate_limits': [],
            'tos_urls_checked': []
        }
        
        # Common ToS page URLs to check
        tos_paths = [
            '/terms', '/terms-of-service', '/terms-of-use', '/tos',
            '/legal/terms', '/help/terms', '/policies/terms'
        ]
        
        async with aiohttp.ClientSession() as session:
            for path in tos_paths:
                tos_url = urljoin(base_url, path)
                
                try:
                    async with session.get(tos_url, timeout=aiohttp.ClientTimeout(total=15)) as response:
                        if response.status == 200:
                            content = await response.text()
                            result['tos_urls_checked'].append(tos_url)
                            
                            # Analyze content for restrictions
                            concerns = self._extract_tos_concerns(content)
                            result['concerns'].extend(concerns)
                            
                            # Look for rate limiting info
                            rate_limits = self._extract_rate_limits(content)
                            result['rate_limits'].extend(rate_limits)
                            
                            break  # Found ToS, no need to check others
                            
                except Exception as e:
                    self.logger.debug(f"Could not fetch {tos_url}: {e}")
                    continue
        
        if not result['tos_urls_checked']:
            self.logger.warning(f"Could not find Terms of Service for {base_url}")
        
        return result

    def _extract_tos_concerns(self, tos_content: str) -> List[str]:
        """Extract scraping-related concerns from ToS content"""
        concerns = []
        content_lower = tos_content.lower()
        
        for pattern in self.tos_red_flags:
            matches = re.findall(pattern, content_lower, re.IGNORECASE)
            if matches:
                concerns.append(f"ToS restriction found: {pattern}")
        
        # Look for specific scraping mentions
        if 'scraping' in content_lower or 'crawling' in content_lower:
            concerns.append("Terms explicitly mention scraping/crawling restrictions")
        
        if 'automated' in content_lower and 'prohibited' in content_lower:
            concerns.append("Automated access appears to be prohibited")
        
        return list(set(concerns))  # Remove duplicates

    def _extract_rate_limits(self, content: str) -> List[str]:
        """Extract rate limiting information from content"""
        rate_limits = []
        content_lower = content.lower()
        
        for pattern in self.rate_limit_indicators:
            if re.search(pattern, content_lower, re.IGNORECASE):
                rate_limits.append(f"Rate limiting mentioned: {pattern}")
        
        # Look for specific rate numbers
        rate_matches = re.findall(r'(\d+)\s*requests?\s*per\s*(minute|hour|day)', content_lower)
        for count, period in rate_matches:
            rate_limits.append(f"Rate limit: {count} requests per {period}")
        
        return rate_limits

    def _generate_recommendations(self, compliance_result: Dict[str, Any]) -> List[str]:
        """Generate scraping recommendations based on compliance analysis"""
        recommendations = []
        
        # Robots.txt recommendations
        if not compliance_result['robots_allowed']:
            recommendations.append("⚠️  Robots.txt disallows scraping - consider requesting permission")
        
        if compliance_result['robots_details'].get('crawl_delay'):
            delay = compliance_result['robots_details']['crawl_delay']
            recommendations.append(f"🕒 Respect crawl delay of {delay} seconds between requests")
        
        # ToS recommendations
        if compliance_result['tos_concerns']:
            recommendations.append("⚠️  Terms of Service contain scraping restrictions - review carefully")
        
        if compliance_result['rate_limits']:
            recommendations.append("📊 Rate limits specified - implement appropriate throttling")
        
        # General recommendations
        if compliance_result['robots_allowed'] and not compliance_result['tos_concerns']:
            recommendations.append("✅ Scraping appears to be allowed with proper rate limiting")
        
        recommendations.append("🤝 Always respect website resources and consider API alternatives")
        recommendations.append("📧 Consider contacting site owner for permission if unclear")
        
        return recommendations

    def save_compliance_report(self, results: Dict[str, Dict[str, Any]], output_path: str) -> None:
        """Save compliance analysis to a text report"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("GPU SCRAPER - COMPLIANCE ANALYSIS REPORT\n")
                f.write("=" * 50 + "\n\n")
                
                for site_name, result in results.items():
                    f.write(f"SITE: {site_name.upper()}\n")
                    f.write("-" * 30 + "\n")
                    
                    if 'error' in result:
                        f.write(f"❌ Error: {result['error']}\n\n")
                        continue
                    
                    f.write(f"Robots.txt Allowed: {'✅ Yes' if result['robots_allowed'] else '❌ No'}\n")
                    
                    if result['tos_concerns']:
                        f.write(f"⚠️  ToS Concerns ({len(result['tos_concerns'])}):\n")
                        for concern in result['tos_concerns']:
                            f.write(f"  - {concern}\n")
                    
                    if result['rate_limits']:
                        f.write(f"📊 Rate Limits ({len(result['rate_limits'])}):\n")
                        for limit in result['rate_limits']:
                            f.write(f"  - {limit}\n")
                    
                    f.write("💡 Recommendations:\n")
                    for rec in result['recommendations']:
                        f.write(f"  - {rec}\n")
                    
                    f.write("\n")
                
            self.logger.info(f"Compliance report saved to {output_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save compliance report: {e}")

    def get_site_specific_guidelines(self, site_name: str) -> List[str]:
        """
        Get site-specific scraping guidelines
        """
        guidelines = {
            'ebay': [
                "✅ eBay generally allows scraping for personal research use",
                "⚠️  Commercial use may require API access or permission",
                "🕒 Respect rate limits - max 1 request per 2 seconds recommended",
                "📋 Review eBay's Developer Program for API alternatives",
                "🎯 Focus on publicly available listing data only"
            ],
            'facebook': [
                "🚫 Facebook has strict anti-scraping measures",
                "🔐 Requires authentication which may violate ToS",
                "⚠️  High risk of IP blocking and account restrictions",
                "📱 Consider Facebook Marketing API for legitimate use cases",
                "🤖 Automated access is generally prohibited"
            ],
            'gumtree': [
                "✅ Generally more permissive for personal use scraping",
                "⚠️  Respect robots.txt directives",
                "🕒 Use reasonable delays between requests",
                "📧 Consider contacting for commercial use permission",
                "🏢 Avoid overloading their servers"
            ]
        }
        
        return guidelines.get(site_name.lower(), [
            "📋 Check robots.txt and Terms of Service",
            "🕒 Use appropriate request delays",
            "🤝 Respect website resources and bandwidth",
            "📧 Consider contacting site owners for permission"
        ])


# Example usage for testing compliance checker
async def test_compliance_checker():
    """Test the compliance checker with sample sites"""
    checker = ComplianceChecker()
    
    test_sites = {
        'ebay': 'https://www.ebay.co.uk',
        'gumtree': 'https://www.gumtree.com'
    }
    
    results = {}
    for name, url in test_sites.items():
        print(f"Checking {name}...")
        result = await checker.check_site_compliance(url)
        results[name] = result
        
        print(f"  Robots allowed: {result['robots_allowed']}")
        print(f"  ToS concerns: {len(result.get('tos_concerns', []))}")
        print(f"  Recommendations: {len(result.get('recommendations', []))}")
        print()
    
    checker.save_compliance_report(results, 'compliance_report.txt')


if __name__ == "__main__":
    asyncio.run(test_compliance_checker())