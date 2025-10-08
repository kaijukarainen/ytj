"""
Finder.fi validation and data extraction service with enhanced rate limiting bypass
"""
import requests
from bs4 import BeautifulSoup
import time
import re
import json
from urllib.parse import unquote
import random
from services.cache_service import load_finder_cache, save_finder_cache
from utils.export_utils import export_to_csv


# Rotating User Agents
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0',
]


def get_rotating_headers():
    """Get headers with rotating user agent"""
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'fi-FI,fi;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0',
        'Referer': 'https://www.google.com/'
    }


def validate_company_on_finder(company, cache=None, retry_delay=5, session=None):
    """Check if company exists on finder.fi and extract comprehensive details
    
    Args:
        company: Company dict with name and business_id
        cache: Optional cache dict
        retry_delay: Seconds to wait between retries (default 5)
        session: Optional requests session for connection reuse
    """
    try:
        company_name = company.get('name', '')
        business_id = company.get('business_id', '')
        
        # Check cache first
        if cache and business_id in cache:
            print(f"\n{'='*60}")
            print(f"Using cached data for: {company_name}")
            print(f"{'='*60}\n")
            return cache[business_id]
        
        # Create session if not provided
        if not session:
            session = requests.Session()
        
        # Search finder.fi for the company
        search_url = f"https://www.finder.fi/search?what={requests.utils.quote(company_name)}&sort=RELEVANCE_desc&page=1"
        
        # Use rotating headers
        headers = get_rotating_headers()
        
        print(f"\n{'='*60}")
        print(f"Validating: {company_name}")
        print(f"  Search URL: {search_url}")
        print(f"  User-Agent: {headers['User-Agent'][:50]}...")
        
        # Try up to 3 times if we get 202
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Add random delay before request (human-like behavior)
                time.sleep(random.uniform(0.5, 1.5))
                
                response = session.get(search_url, headers=headers, timeout=15)
                
                if response.status_code == 202:
                    wait_time = retry_delay * (attempt + 1)
                    print(f"  ⚠ Got 202 (rate limited), waiting {wait_time} seconds... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    # Rotate user agent for retry
                    headers = get_rotating_headers()
                    continue
                    
                if response.status_code != 200:
                    print(f"  ✗ Search failed (status {response.status_code})")
                    return None
                    
                # Success!
                break
                
            except requests.exceptions.Timeout:
                print(f"  ⚠ Request timeout (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(5)
                    headers = get_rotating_headers()
                    continue
                else:
                    print(f"  ✗ Failed after {max_retries} attempts")
                    return None
                    
        else:
            # All retries exhausted
            print(f"  ✗ Search failed after {max_retries} attempts (rate limited)")
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all links with "yhteystiedot" in href
        results = soup.find_all('a', href=lambda x: x and 'yhteystiedot' in x if x else False)
        
        if not results:
            print(f"  ✗ No company detail links found on Finder.fi")
            return None
        
        print(f"  Found {len(results)} potential company links")
        
        # Extract and normalize company name for matching
        company_name_normalized = company_name.lower().replace(' oy', '').replace(' ab', '').replace(',', '').strip()
        company_name_with_hyphen = company_name_normalized
        company_name_no_hyphen = company_name_normalized.replace('-', ' ')
        
        company_words = [w for w in company_name_no_hyphen.split() if len(w) > 2]
        
        # Try to find exact match
        best_match = None
        best_score = 0
        
        for idx, link in enumerate(results[:10]):
            href = link.get('href', '')
            
            parts = href.split('/')
            company_url_part = None
            
            try:
                yhteystiedot_idx = parts.index('yhteystiedot')
                if yhteystiedot_idx >= 2:
                    company_url_part = parts[yhteystiedot_idx - 2]
            except (ValueError, IndexError):
                for part in parts:
                    if '+' in part and 'yhteystiedot' not in part and len(part) > 5:
                        company_url_part = part
                        break
            
            if not company_url_part:
                continue
            
            company_url_part = unquote(company_url_part)
            url_company_name_original = company_url_part.replace('+', ' ').lower()
            url_company_name_original = url_company_name_original.replace(' oy', '').replace(' ab', '').strip()
            url_company_name_no_hyphen = url_company_name_original.replace('-', ' ')
            
            # Check business ID in URL
            if business_id and business_id.replace('-', '') in href:
                best_match = link
                best_score = 100
                print(f"  ✓ Perfect match by business ID in URL")
                break
            
            # Try exact match
            if url_company_name_original == company_name_with_hyphen:
                best_match = link
                best_score = 100
                break
            
            # Score based on word matching
            url_words = url_company_name_no_hyphen.split()
            matches = sum(1 for word in company_words if word in url_words)
            
            if len(company_words) > 0:
                score = (matches / len(company_words)) * 100
                
                if len(url_words) == len(company_words):
                    score += 10
                
                if url_company_name_no_hyphen == company_name_no_hyphen:
                    score = 100
                
                if score > best_score:
                    best_score = score
                    best_match = link
        
        if best_match and best_score >= 60:
            company_link = best_match
            print(f"  ✓ Best match selected with {best_score:.1f}% confidence")
        else:
            print(f"  ✗ No good match found (best score: {best_score:.1f}%)")
            return None
        
        # Navigate to company page
        company_url = 'https://www.finder.fi' + company_link['href']
        print(f"  Company page: {company_url}")
        
        # Random delay + rotate headers
        time.sleep(random.uniform(1.0, 2.0))
        headers = get_rotating_headers()
        
        company_response = session.get(company_url, headers=headers, timeout=10)
        
        if company_response.status_code != 200:
            print(f"  ✗ Failed to load company page (status {company_response.status_code})")
            return None
        
        company_soup = BeautifulSoup(company_response.text, 'html.parser')
        
        # Initialize data structure
        finder_data = {
            'finder_url': company_url,
            'verified_on_finder': True,
            'basic_info': {},
            'financials': {},
            'contact': {},
            'key_people': []
        }
        
        # Extract data
        finder_data = _extract_company_data(company_soup, finder_data)
        
        # Log what we found
        print(f"\n  Extracted data:")
        print(f"    Basic Info: {len(finder_data['basic_info'])} fields")
        for key, value in finder_data['basic_info'].items():
            print(f"      {key}: {value}")
        
        print(f"    Financials: {len(finder_data['financials'])} fields")
        for key, value in finder_data['financials'].items():
            print(f"      {key}: {value}")
        
        print(f"    Contact: {len(finder_data['contact'])} fields")
        for key, value in finder_data['contact'].items():
            print(f"      {key}: {value}")
        
        print(f"    Key People: {len(finder_data['key_people'])} found")
        for person in finder_data['key_people']:
            print(f"      {person.get('name', 'Unknown')} - {person.get('title', '')}")
        
        # Clean up empty sections
        finder_data['basic_info'] = {k: v for k, v in finder_data['basic_info'].items() if v}
        finder_data['financials'] = {k: v for k, v in finder_data['financials'].items() if v}
        finder_data['contact'] = {k: v for k, v in finder_data['contact'].items() if v}
        
        has_data = (finder_data['basic_info'] or 
                   finder_data['financials'] or 
                   finder_data['contact'] or 
                   finder_data['key_people'])
        
        if has_data:
            print(f"  ✓ Successfully extracted Finder.fi data")
        else:
            print(f"  ⚠ Found page but extracted no data")
        
        print(f"{'='*60}\n")
        
        return finder_data
        
    except Exception as e:
        print(f"  ✗ Error validating on finder.fi: {e}")
        import traceback
        traceback.print_exc()
        return None


def _extract_company_data(company_soup, finder_data):
    """Extract company data using multiple strategies"""
    
    # Extract employees with improved patterns
    _extract_employees(company_soup, finder_data)
    
    # Extract financial data with year
    _extract_financials(company_soup, finder_data)
    
    # STRATEGY 1: Definition lists
    definition_lists = company_soup.find_all('dl')
    for dl in definition_lists:
        dts = dl.find_all('dt')
        dds = dl.find_all('dd')
        
        for dt, dd in zip(dts, dds):
            key = dt.get_text(strip=True)
            value = dd.get_text(strip=True)
            _map_field_to_data(key, value, finder_data)
    
    # STRATEGY 2: Tables
    tables = company_soup.find_all('table')
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                key = cells[0].get_text(strip=True)
                value = cells[1].get_text(strip=True)
                _map_field_to_data(key, value, finder_data)
    
    # STRATEGY 3: Selectors
    _extract_with_selectors(company_soup, finder_data)
    
    # STRATEGY 4: Key people
    _extract_key_people(company_soup, finder_data)
    
    # STRATEGY 5: Text-based extraction
    _extract_from_text(company_soup, finder_data)
    
    return finder_data


def _extract_employees(soup, finder_data):
    """Extract employee count with improved patterns"""
    # Look for employee count with emoji or icons
    page_text = soup.get_text()
    
    # Pattern 1: 👥 33 or similar
    emoji_pattern = r'👥\s*(\d+)'
    match = re.search(emoji_pattern, page_text)
    if match:
        finder_data['basic_info']['employees'] = match.group(1)
        print(f"    Found employees (emoji): {match.group(1)}")
        return
    
    # Pattern 2: Henkilöstö: 33
    text_pattern = r'Henkilöstö[:\s]+(\d+[-\s]?\d*)'
    match = re.search(text_pattern, page_text, re.IGNORECASE)
    if match:
        finder_data['basic_info']['employees'] = match.group(1).strip()
        print(f"    Found employees (text): {match.group(1)}")
        return
    
    # Pattern 3: Look in specific elements
    for elem in soup.find_all(['div', 'span', 'p'], text=re.compile(r'(henkilöstö|työntekijä|employees)', re.I)):
        text = elem.get_text()
        numbers = re.findall(r'\d+', text)
        if numbers:
            finder_data['basic_info']['employees'] = numbers[0]
            print(f"    Found employees (element): {numbers[0]}")
            return


def _extract_financials(soup, finder_data):
    """Extract financial data with year information"""
    page_text = soup.get_text()
    
    # Pattern 1: 💰 Revenue: 239 000
    revenue_emoji_pattern = r'💰\s*[Rr]evenue[:\s]*([0-9\s,.]+(?:EUR|€|miljoonaa|tuhatta)?)'
    match = re.search(revenue_emoji_pattern, page_text)
    if match:
        finder_data['financials']['revenue'] = match.group(1).strip()
        print(f"    Found revenue (emoji): {match.group(1)}")
    
    # Pattern 2: Liikevaihto: 239 000
    if not finder_data['financials'].get('revenue'):
        revenue_pattern = r'Liikevaihto[:\s]+([0-9\s,.]+\s*(?:EUR|€|miljoonaa|tuhatta)?)'
        match = re.search(revenue_pattern, page_text, re.IGNORECASE)
        if match:
            finder_data['financials']['revenue'] = match.group(1).strip()
            print(f"    Found revenue (text): {match.group(1)}")
    
    # Pattern 3: 📊 Operating Profit: 24,7%
    profit_emoji_pattern = r'📊\s*[Oo]perating [Pp]rofit[:\s]*([0-9,.-]+\s*%?)'
    match = re.search(profit_emoji_pattern, page_text)
    if match:
        finder_data['financials']['operating_profit'] = match.group(1).strip()
        print(f"    Found operating profit (emoji): {match.group(1)}")
    
    # Pattern 4: Liikevoitto: 24,7%
    if not finder_data['financials'].get('operating_profit'):
        profit_pattern = r'Liikevoitto[:\s]+([0-9,.-]+\s*%?)'
        match = re.search(profit_pattern, page_text, re.IGNORECASE)
        if match:
            finder_data['financials']['operating_profit'] = match.group(1).strip()
            print(f"    Found operating profit (text): {match.group(1)}")
    
    # Extract financial year
    year_pattern = r'Tilikausi[:\s]+(\d{1,2}[./]\d{1,2}[./])?(\d{4})'
    match = re.search(year_pattern, page_text, re.IGNORECASE)
    if match:
        finder_data['financials']['financial_year'] = match.group(2)
        print(f"    Found financial year: {match.group(2)}")
    
    # Alternative year pattern: (2023) or 2023
    if not finder_data['financials'].get('financial_year'):
        # Look near revenue/profit mentions
        for line in page_text.split('\n'):
            if any(word in line.lower() for word in ['liikevaihto', 'revenue', 'liikevoitto', 'profit']):
                year_match = re.search(r'\(?(20\d{2})\)?', line)
                if year_match:
                    finder_data['financials']['financial_year'] = year_match.group(1)
                    print(f"    Found financial year (context): {year_match.group(1)}")
                    break


def _map_field_to_data(key, value, finder_data):
    """Map Finnish field names to data structure"""
    if 'Liikevaihto' in key or 'Turnover' in key:
        finder_data['financials']['revenue'] = value
    elif 'Henkilöstö' in key or 'Employees' in key:
        finder_data['basic_info']['employees'] = value
    elif 'Perustettu' in key or 'Founded' in key:
        finder_data['basic_info']['founded'] = value
    elif 'Liikevoitto' in key or 'Operating profit' in key:
        finder_data['financials']['operating_profit'] = value
    elif 'Tilikausi' in key or 'Financial year' in key:
        finder_data['financials']['financial_year'] = value
    elif 'Y-tunnus' in key or 'Business ID' in key:
        finder_data['basic_info']['business_id'] = value
    elif 'Osoite' in key or 'Address' in key:
        finder_data['contact']['address'] = value
    elif 'Puhelin' in key or 'Phone' in key:
        finder_data['contact']['phone'] = value
    elif 'Kotisivu' in key or 'Website' in key:
        finder_data['contact']['website'] = value
    elif 'Sähköposti' in key or 'Email' in key:
        finder_data['contact']['email'] = value


def _extract_with_selectors(company_soup, finder_data):
    """Extract using CSS selectors"""
    # Revenue
    revenue_selectors = [
        'div[data-field="revenue"]',
        'div.company-revenue',
        'span.revenue-value'
    ]
    for selector in revenue_selectors:
        element = company_soup.select_one(selector)
        if element and not finder_data['financials'].get('revenue'):
            finder_data['financials']['revenue'] = element.get_text(strip=True)
            break
    
    # Employees
    employee_selectors = [
        'div[data-field="employees"]',
        'div.company-employees',
        'span.employee-count'
    ]
    for selector in employee_selectors:
        element = company_soup.select_one(selector)
        if element and not finder_data['basic_info'].get('employees'):
            finder_data['basic_info']['employees'] = element.get_text(strip=True)
            break


def _extract_key_people(company_soup, finder_data):
    """Extract key people/management"""
    people_sections = company_soup.find_all(['div', 'section'], 
        text=re.compile(r'Johto|Hallitus|Toimitusjohtaja|Management|Board', re.IGNORECASE))
    
    for section in people_sections:
        parent = section.find_parent()
        if parent:
            person_containers = parent.find_all(['div', 'li'], class_=re.compile(r'person|contact|member'))
            
            for container in person_containers[:10]:
                person = {}
                
                name_elem = container.find(['h3', 'h4', 'strong', 'span'], class_=re.compile(r'name'))
                if name_elem:
                    person['name'] = name_elem.get_text(strip=True)
                
                title_elem = container.find(['span', 'p', 'div'], class_=re.compile(r'title|role|position'))
                if title_elem:
                    person['title'] = title_elem.get_text(strip=True)
                
                email_elem = container.find('a', href=re.compile(r'^mailto:'))
                if email_elem:
                    person['email'] = email_elem['href'].replace('mailto:', '')
                
                if person.get('name'):
                    finder_data['key_people'].append(person)


def _extract_from_text(company_soup, finder_data):
    """Extract data from page text as fallback"""
    page_text = company_soup.get_text()
    
    # Extract revenue if not found
    if not finder_data['financials'].get('revenue'):
        revenue_pattern = r'Liikevaihto[:\s]+([0-9\s,.]+\s*(?:EUR|€|miljoonaa|tuhatta)?)'
        revenue_match = re.search(revenue_pattern, page_text, re.IGNORECASE)
        if revenue_match:
            finder_data['financials']['revenue'] = revenue_match.group(1).strip()
    
    # Extract employees if not found
    if not finder_data['basic_info'].get('employees'):
        employee_pattern = r'Henkilöstö[:\s]+([0-9\s,.-]+)'
        employee_match = re.search(employee_pattern, page_text, re.IGNORECASE)
        if employee_match:
            finder_data['basic_info']['employees'] = employee_match.group(1).strip()
    
    # Extract founded year if not found
    if not finder_data['basic_info'].get('founded'):
        founded_pattern = r'Perustettu[:\s]+([0-9]{4})'
        founded_match = re.search(founded_pattern, page_text, re.IGNORECASE)
        if founded_match:
            finder_data['basic_info']['founded'] = founded_match.group(1).strip()


def run_finder_validation(leads, validation_status, scraping_status, config=None):
    """Background task to validate leads on finder.fi with caching
    
    Args:
        leads: List of company leads to validate
        validation_status: Status dict for tracking progress
        scraping_status: Status dict for storing results
        config: Optional dict with settings like {'retry_delay': 5, 'between_delay': 4}
    """
    try:
        # Get configuration or use defaults
        retry_delay = config.get('retry_delay', 5) if config else 5
        between_delay = config.get('between_delay', 4) if config else 4
        
        validation_status['is_running'] = True
        validation_status['progress'] = 0
        validation_status['total'] = len(leads)
        validation_status['validated_count'] = 0
        validation_status['removed_count'] = 0
        
        # Load cache
        cache = load_finder_cache()
        print(f"Loaded cache with {len(cache)} entries")
        print(f"Using retry delay: {retry_delay}s, between request delay: {between_delay}s")
        
        validated_leads = []
        cache_updated = False
        
        # Create persistent session for connection reuse
        session = requests.Session()
        
        for idx, lead in enumerate(leads):
            validation_status['current_company'] = lead['name']
            validation_status['progress'] = idx + 1
            
            print(f"\n[{idx + 1}/{len(leads)}] Validating: {lead['name']}")
            
            # Check if lead has email already
            has_email = (lead.get('contact_info', {}).get('emails') or 
                        any(c.get('email') for c in lead.get('contact_info', {}).get('contacts', [])))
            
            # Check on finder.fi (with cache and session reuse)
            finder_data = validate_company_on_finder(lead, cache, retry_delay, session)
            
            # Update cache if we got new data
            if finder_data and lead.get('business_id'):
                cache[lead['business_id']] = finder_data
                cache_updated = True
            
            # Keep lead if: has email OR found on finder (or both)
            if has_email or finder_data:
                if finder_data:
                    lead['finder_data'] = finder_data
                validated_leads.append(lead)
                validation_status['validated_count'] += 1
                
                if has_email and finder_data:
                    print(f"  ✓ Kept (has email + found on finder)")
                elif has_email:
                    print(f"  ✓ Kept (has email)")
                else:
                    print(f"  ✓ Kept (found on finder)")
            else:
                # Remove only if NO email AND NOT found on finder
                validation_status['removed_count'] += 1
                print(f"  ✗ Removed (no email + not found on finder)")
            
            # Configurable delay with randomization (more human-like)
            delay = random.uniform(between_delay, between_delay + 2)
            time.sleep(delay)
        
        # Close session
        session.close()
        
        # Save updated cache
        if cache_updated:
            save_finder_cache(cache)
            print(f"\n✓ Cache updated with {len(cache)} total entries")
        
        # Save validated results
        print(f"\n{'='*60}")
        print(f"Validation complete!")
        print(f"  Total leads: {len(leads)}")
        print(f"  Validated (kept): {validation_status['validated_count']}")
        print(f"  Removed: {validation_status['removed_count']}")
        print(f"{'='*60}\n")
        
        # Save as JSON
        with open('companies_leads_validated.json', 'w', encoding='utf-8') as f:
            json.dump(validated_leads, f, ensure_ascii=False, indent=2)
        
        # Also export to CSV
        export_to_csv(validated_leads, 'companies_leads_validated.csv')
        
        scraping_status['results'] = validated_leads
        validation_status['is_running'] = False
        
    except Exception as e:
        print(f"Error in validation: {e}")
        import traceback
        traceback.print_exc()
        validation_status['is_running'] = False
        validation_status['error'] = str(e)
        