"""
NIKE 2019 FORENSIC ANALYSIS - WEB SCRAPING EDITION
==================================================
This version SCRAPES the SEC website directly using Playwright
- No API calls, no downloads
- Real web scraping with browser automation
- Extracts data directly from SEC.gov HTML pages
- Parses Form 4s, 10-Ks, 10-Qs from live web pages
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import logging
import re
from collections import Counter

from playwright.async_api import async_playwright, Page
from bs4 import BeautifulSoup


class Nike2019WebScraperAnalysis:
    """
    REAL web scraping forensic analysis.
    Scrapes SEC.gov directly using Playwright browser automation.
    """
    
    def __init__(self):
        self.company_name = "Nike Inc."
        self.cik = "0000320187"
        self.ticker = "NKE"
        self.start_date = "2019-01-01"
        self.end_date = "2019-12-31"
        
        # SEC EDGAR URLs
        self.sec_search_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={self.cik}&type=&dateb=&owner=exclude&count=100&search_text="
        
        # Data storage
        self.filings: List[Dict] = []
        self.form4_transactions: List[Dict] = []
        self.financial_data: Dict[str, Any] = {}
        
        # Violations
        self.violations: Dict[str, List] = {
            'late_form4': [],
            'zero_dollar_transactions': [],
            'suspicious_patterns': [],
            'benford_violations': []
        }
        
        self.total_damages = 0.0
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_dir = Path("forensic_reports/nike_2019_webscraper/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"webscraper_analysis_{timestamp}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s | %(levelname)-8s | %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.log_file = log_file
    
    async def run_webscraper_analysis(self):
        """Execute web scraping forensic analysis"""
        self.logger.info("="*120)
        self.logger.info("NIKE INC. - WEB SCRAPING FORENSIC ANALYSIS")
        self.logger.info("="*120)
        self.logger.info(f"Company: {self.company_name}")
        self.logger.info(f"CIK: {self.cik}")
        self.logger.info(f"Period: {self.start_date} to {self.end_date}")
        self.logger.info(f"Method: LIVE WEB SCRAPING (Playwright)")
        self.logger.info("="*120)
        self.logger.info("")
        
        start_time = datetime.now()
        
        async with async_playwright() as playwright:
            # Launch browser
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()
            
            try:
                # Phase 1: Scrape filing list from SEC
                await self.phase1_scrape_filing_list(page)
                
                # Phase 2: Scrape Form 4 documents
                await self.phase2_scrape_form4_documents(page)
                
                # Phase 3: Analyze Form 4 transactions
                await self.phase3_analyze_form4_violations()
                
                # Phase 4: Scrape financial statements
                await self.phase4_scrape_financial_statements(page)
                
                # Phase 5: Benford's Law analysis
                await self.phase5_benfords_law()
                
                # Phase 6: Generate report
                await self.phase6_generate_report()
                
                duration = (datetime.now() - start_time).total_seconds()
                
                self.logger.info("")
                self.logger.info("="*120)
                self.logger.info(f"✅ WEB SCRAPING ANALYSIS COMPLETE - Duration: {duration:.2f} seconds")
                self.logger.info("="*120)
                
                return {
                    'status': 'SUCCESS',
                    'duration_seconds': duration,
                    'filings_scraped': len(self.filings),
                    'form4_transactions': len(self.form4_transactions),
                    'total_violations': sum(len(v) for v in self.violations.values())
                }
                
            finally:
                await browser.close()
    
    async def phase1_scrape_filing_list(self, page: Page):
        """Phase 1: Scrape filing list from SEC.gov"""
        self.logger.info("─"*120)
        self.logger.info("PHASE 1: SCRAPING SEC.GOV FOR FILING LIST")
        self.logger.info("─"*120)
        
        # Navigate to SEC EDGAR search page
        url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={self.cik}&type=&dateb=&owner=exclude&count=100"
        self.logger.info(f"→ Navigating to: {url}")
        
        await page.goto(url, wait_until="domcontentloaded")
        await asyncio.sleep(2)  # Let page load
        
        # Get HTML content
        html = await page.content()
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find the filings table
        filing_table = soup.find('table', {'class': 'tableFile2'})
        
        if not filing_table:
            self.logger.warning("⚠ Could not find filings table")
            return
        
        # Parse each row
        rows = filing_table.find_all('tr')[1:]  # Skip header
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) < 4:
                continue
            
            try:
                filing_type = cells[0].text.strip()
                filing_date = cells[3].text.strip()
                
                # Check if in 2019
                if self.start_date <= filing_date <= self.end_date:
                    # Get document link
                    doc_link = cells[1].find('a')
                    if doc_link:
                        doc_url = "https://www.sec.gov" + doc_link['href']
                        
                        self.filings.append({
                            'form_type': filing_type,
                            'filing_date': filing_date,
                            'document_url': doc_url,
                            'scraped': False
                        })
            
            except Exception as e:
                self.logger.debug(f"Error parsing row: {e}")
        
        # Count by type
        form_counts = Counter(f['form_type'] for f in self.filings)
        
        self.logger.info(f"✓ Scraped {len(self.filings)} filings from SEC.gov")
        self.logger.info("")
        self.logger.info("Filing Breakdown:")
        for form_type, count in sorted(form_counts.items()):
            self.logger.info(f"  • {form_type}: {count}")
        self.logger.info("")
    
    async def phase2_scrape_form4_documents(self, page: Page):
        """Phase 2: Scrape Form 4 documents from SEC.gov"""
        self.logger.info("─"*120)
        self.logger.info("PHASE 2: SCRAPING FORM 4 DOCUMENTS FROM SEC.GOV")
        self.logger.info("─"*120)
        
        form4_filings = [f for f in self.filings if f['form_type'] == '4']
        self.logger.info(f"→ Scraping {len(form4_filings)} Form 4 documents...")
        self.logger.info("")
        
        for i, filing in enumerate(form4_filings, 1):
            try:
                # Navigate to filing page
                await page.goto(filing['document_url'], wait_until="domcontentloaded")
                await asyncio.sleep(0.5)  # Rate limiting
                
                # Get HTML
                html = await page.content()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract transaction data from HTML tables
                transactions = self._parse_form4_html(soup, filing)
                self.form4_transactions.extend(transactions)
                filing['scraped'] = True
                
                if i % 10 == 0:
                    self.logger.info(f"  Progress: {i}/{len(form4_filings)} scraped...")
            
            except Exception as e:
                self.logger.warning(f"  ⚠ Error scraping {filing['document_url']}: {e}")
        
        self.logger.info("")
        self.logger.info(f"✓ Scraped {len([f for f in form4_filings if f['scraped']])} Form 4 documents")
        self.logger.info(f"✓ Extracted {len(self.form4_transactions)} transactions from web pages")
        self.logger.info("")
    
    def _parse_form4_html(self, soup: BeautifulSoup, filing: Dict) -> List[Dict]:
        """Parse Form 4 HTML to extract transaction data"""
        transactions = []
        
        try:
            # Look for transaction tables in the HTML
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                
                for row in rows:
                    cells = row.find_all('td')
                    
                    # Look for rows with transaction data
                    # Form 4s typically have: Date, Code, Shares, Price, etc.
                    if len(cells) >= 4:
                        try:
                            # Try to extract numeric values
                            numbers = []
                            for cell in cells:
                                text = cell.text.strip()
                                # Look for numbers
                                matches = re.findall(r'[\d,]+\.?\d*', text)
                                for match in matches:
                                    try:
                                        num = float(match.replace(',', ''))
                                        numbers.append(num)
                                    except:
                                        pass
                            
                            # If we found shares and price, create transaction
                            if len(numbers) >= 2:
                                shares = numbers[0]
                                price = numbers[1] if len(numbers) > 1 else 0.0
                                
                                if shares > 0:
                                    transactions.append({
                                        'filing_date': filing['filing_date'],
                                        'transaction_date': filing['filing_date'],  # Simplified
                                        'shares': shares,
                                        'price_per_share': price,
                                        'total_value': shares * price,
                                        'filing_url': filing['document_url']
                                    })
                        except:
                            pass
        
        except Exception as e:
            self.logger.debug(f"HTML parse error: {e}")
        
        return transactions
    
    async def phase3_analyze_form4_violations(self):
        """Phase 3: Analyze scraped Form 4 transactions"""
        self.logger.info("─"*120)
        self.logger.info("PHASE 3: ANALYZING SCRAPED FORM 4 TRANSACTIONS")
        self.logger.info("─"*120)
        
        if not self.form4_transactions:
            self.logger.warning("⚠ No transactions extracted from web scraping")
            self.logger.info("")
            return
        
        zero_dollar_count = 0
        high_value_count = 0
        
        for txn in self.form4_transactions:
            # Check for zero-dollar transactions
            if txn['price_per_share'] < 0.01 and txn['shares'] > 0:
                self.violations['zero_dollar_transactions'].append({
                    'transaction': txn,
                    'severity': 'HIGH',
                    'statute': '17 CFR § 240.16a-3'
                })
                zero_dollar_count += 1
            
            # Check for unusually high-value transactions
            if txn['total_value'] > 10_000_000:  # >$10M
                self.violations['suspicious_patterns'].append({
                    'transaction': txn,
                    'reason': 'Unusually large transaction value',
                    'value': txn['total_value']
                })
                high_value_count += 1
        
        self.logger.info(f"✓ Analyzed {len(self.form4_transactions)} scraped transactions")
        self.logger.info(f"  • Zero-dollar transactions: {zero_dollar_count}")
        self.logger.info(f"  • High-value transactions (>$10M): {high_value_count}")
        self.logger.info("")
    
    async def phase4_scrape_financial_statements(self, page: Page):
        """Phase 4: Scrape 10-K/10-Q financial statements"""
        self.logger.info("─"*120)
        self.logger.info("PHASE 4: SCRAPING FINANCIAL STATEMENTS")
        self.logger.info("─"*120)
        
        financial_filings = [f for f in self.filings if f['form_type'] in ['10-K', '10-Q']]
        self.logger.info(f"→ Scraping {len(financial_filings)} financial statements...")
        self.logger.info("")
        
        for filing in financial_filings:
            try:
                # Navigate to filing
                await page.goto(filing['document_url'], wait_until="domcontentloaded")
                await asyncio.sleep(1)
                
                # Get HTML
                html = await page.content()
                
                # Extract numbers
                numbers = self._extract_numbers_from_html(html)
                
                self.financial_data[filing['form_type'] + '_' + filing['filing_date']] = {
                    'filing': filing,
                    'numbers': numbers
                }
                
                filing['scraped'] = True
                self.logger.info(f"  ✓ {filing['form_type']} {filing['filing_date']}: Extracted {len(numbers)} figures")
            
            except Exception as e:
                self.logger.warning(f"  ⚠ Error scraping {filing['document_url']}: {e}")
        
        self.logger.info("")
    
    def _extract_numbers_from_html(self, html: str) -> List[int]:
        """Extract financial figures from HTML"""
        numbers = []
        
        # Remove HTML tags
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text()
        
        # Find dollar amounts
        patterns = [
            r'\$\s*([\d,]+)',
            r'\(\s*([\d,]+)\s*\)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    num = int(match.replace(',', ''))
                    if 1000 <= num <= 100_000_000_000:
                        numbers.append(num)
                except:
                    pass
        
        return numbers[:50]  # Limit to first 50
    
    async def phase5_benfords_law(self):
        """Phase 5: Benford's Law analysis"""
        self.logger.info("─"*120)
        self.logger.info("PHASE 5: BENFORD'S LAW ANALYSIS ON SCRAPED DATA")
        self.logger.info("─"*120)
        
        all_numbers = []
        for data in self.financial_data.values():
            all_numbers.extend(data['numbers'])
        
        if len(all_numbers) < 30:
            self.logger.warning("⚠ Insufficient data for Benford's Law")
            self.logger.info("")
            return
        
        # Benford's Law expected distribution
        benford_expected = {
            '1': 0.301, '2': 0.176, '3': 0.125, '4': 0.097,
            '5': 0.079, '6': 0.067, '7': 0.058, '8': 0.051, '9': 0.046
        }
        
        # Count first digits
        first_digits = Counter(str(abs(n))[0] for n in all_numbers if n != 0)
        total = sum(first_digits.values())
        
        # Chi-square test
        chi_square = 0.0
        for digit, expected_prob in benford_expected.items():
            observed = first_digits.get(digit, 0)
            expected = expected_prob * total
            if expected > 0:
                chi_square += ((observed - expected) ** 2) / expected
        
        critical_value = 15.507
        
        self.logger.info(f"→ Analyzed {len(all_numbers)} figures from scraped documents")
        self.logger.info(f"  • Chi-square: {chi_square:.3f}")
        self.logger.info(f"  • Critical value: {critical_value}")
        
        if chi_square > critical_value:
            self.violations['benford_violations'].append({
                'chi_square': chi_square,
                'critical_value': critical_value,
                'severity': 'HIGH'
            })
            self.logger.info(f"  ❌ VIOLATION: Deviation from Benford's Law")
        else:
            self.logger.info(f"  ✓ Conforms to Benford's Law")
        
        self.logger.info("")
    
    async def phase6_generate_report(self):
        """Phase 6: Generate report"""
        self.logger.info("─"*120)
        self.logger.info("PHASE 6: GENERATING WEB SCRAPING FORENSIC REPORT")
        self.logger.info("─"*120)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_dir = Path("forensic_reports/nike_2019_webscraper")
        report_dir.mkdir(parents=True, exist_ok=True)
        
        # JSON report
        json_file = report_dir / f"webscraper_analysis_{timestamp}.json"
        report_data = {
            'metadata': {
                'company': self.company_name,
                'cik': self.cik,
                'method': 'WEB SCRAPING (Playwright)',
                'timestamp': datetime.now().isoformat()
            },
            'summary': {
                'total_filings_scraped': len(self.filings),
                'form4_transactions_extracted': len(self.form4_transactions),
                'financial_statements_scraped': len(self.financial_data),
                'total_violations': sum(len(v) for v in self.violations.values())
            },
            'filings': self.filings,
            'transactions': self.form4_transactions,
            'violations': self.violations
        }
        
        json_file.write_text(json.dumps(report_data, indent=2, default=str), encoding='utf-8')
        self.logger.info(f"✓ JSON report: {json_file}")
        
        # Text report
        txt_file = report_dir / f"webscraper_report_{timestamp}.txt"
        lines = [
            "="*120,
            "NIKE INC. - WEB SCRAPING FORENSIC ANALYSIS REPORT",
            "="*120,
            "",
            "METHODOLOGY: LIVE WEB SCRAPING",
            "─"*120,
            "This analysis used Playwright browser automation to scrape SEC.gov directly.",
            "No API calls were made. All data extracted from live HTML pages.",
            "",
            f"Total Filings Scraped: {len(self.filings)}",
            f"Form 4 Transactions Extracted: {len(self.form4_transactions)}",
            f"Financial Statements Scraped: {len(self.financial_data)}",
            f"Total Violations Detected: {sum(len(v) for v in self.violations.values())}",
            "",
            "="*120,
            "END OF REPORT",
            "="*120
        ]
        
        txt_file.write_text('\n'.join(lines), encoding='utf-8')
        self.logger.info(f"✓ Text report: {txt_file}")
        self.logger.info("")


async def main():
    """Main execution"""
    analyzer = Nike2019WebScraperAnalysis()
    result = await analyzer.run_webscraper_analysis()
    print(f"\n{'='*120}")
    print(f"Status: {result['status']}")
    print(f"Duration: {result.get('duration_seconds', 0):.2f} seconds")
    print(f"{'='*120}\n")
    return result


if __name__ == '__main__':
    asyncio.run(main())

