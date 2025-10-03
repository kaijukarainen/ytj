from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import json
import os
from ytj_scraper import YTJCompanyScraper
from openai import OpenAI
from threading import Thread
import requests
from bs4 import BeautifulSoup
import time
import csv
from datetime import datetime
import re
from urllib.parse import unquote

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Add debug logging
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# Store scraping status
scraping_status = {
    'is_running': False,
    'progress': 0,
    'total': 0,
    'current_company': '',
    'results': []
}

validation_status = {
    'is_running': False,
    'progress': 0,
    'total': 0,
    'current_company': '',
    'validated_count': 0,
    'removed_count': 0
}

agent_status = {
    'is_running': False,
    'progress': 0,
    'total': 0,
    'current_company': ''
}

# Cache management functions
def load_finder_cache():
    """Load Finder.fi cache from file"""
    cache_file = 'finder_cache.json'
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_finder_cache(cache):
    """Save Finder.fi cache to file"""
    cache_file = 'finder_cache.json'
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving cache: {e}")

def export_to_csv(leads, filename='companies_leads.csv'):
    """Export leads to CSV format"""
    if not leads:
        return False
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            # Define CSV columns
            fieldnames = [
                'Company Name',
                'Business ID',
                'Business Line',
                'Business Line Code',
                'Website',
                'Street',
                'City',
                'Post Code',
                'Registration Date',
                'Status',
                # Finder.fi data
                'Verified on Finder',
                'Finder URL',
                'Founded',
                'Employees',
                'Revenue',
                'Operating Profit',
                'Financial Year',
                'Finder Address',
                'Finder Phone',
                'Finder Email',
                'Finder Website',
                'Key People Count',
                'Key People Names',
                # Contact info
                'Emails',
                'Phones',
                'Contact Names',
                'Contact Titles',
                'Contact Emails',
                'Contact Phones',
                'Social Media'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for lead in leads:
                # Extract basic info
                row = {
                    'Company Name': lead.get('name', ''),
                    'Business ID': lead.get('business_id', ''),
                    'Business Line': lead.get('main_business_line', ''),
                    'Business Line Code': lead.get('main_business_line_code', ''),
                    'Website': lead.get('website', ''),
                    'Street': lead.get('address', {}).get('street', ''),
                    'City': lead.get('address', {}).get('city', ''),
                    'Post Code': lead.get('address', {}).get('post_code', ''),
                    'Registration Date': lead.get('registration_date', ''),
                    'Status': lead.get('status', ''),
                }
                
                # Extract Finder.fi data
                finder_data = lead.get('finder_data', {})
                if finder_data:
                    row['Verified on Finder'] = 'Yes' if finder_data.get('verified_on_finder') else 'No'
                    row['Finder URL'] = finder_data.get('finder_url', '')
                    
                    basic_info = finder_data.get('basic_info', {})
                    row['Founded'] = basic_info.get('founded', '')
                    row['Employees'] = basic_info.get('employees', '')
                    
                    financials = finder_data.get('financials', {})
                    row['Revenue'] = financials.get('revenue', '')
                    row['Operating Profit'] = financials.get('operating_profit', '')
                    row['Financial Year'] = financials.get('financial_year', '')
                    
                    contact = finder_data.get('contact', {})
                    row['Finder Address'] = contact.get('address', '')
                    row['Finder Phone'] = contact.get('phone', '')
                    row['Finder Email'] = contact.get('email', '')
                    row['Finder Website'] = contact.get('website', '')
                    
                    key_people = finder_data.get('key_people', [])
                    row['Key People Count'] = len(key_people)
                    row['Key People Names'] = '; '.join([p.get('name', '') for p in key_people if p.get('name')])
                
                # Extract contact info
                contact_info = lead.get('contact_info', {})
                if contact_info:
                    emails = contact_info.get('emails', [])
                    row['Emails'] = '; '.join(emails)
                    
                    phones = contact_info.get('phones', [])
                    row['Phones'] = '; '.join(phones)
                    
                    contacts = contact_info.get('contacts', [])
                    if contacts:
                        row['Contact Names'] = '; '.join([c.get('name', '') for c in contacts if c.get('name')])
                        row['Contact Titles'] = '; '.join([c.get('title', '') for c in contacts if c.get('title')])
                        row['Contact Emails'] = '; '.join([c.get('email', '') for c in contacts if c.get('email')])
                        row['Contact Phones'] = '; '.join([c.get('phone', '') for c in contacts if c.get('phone')])
                    
                    social_media = contact_info.get('social_media', {})
                    social_links = [f"{k}: {v}" for k, v in social_media.items()]
                    row['Social Media'] = '; '.join(social_links)
                
                writer.writerow(row)
        
        print(f"✓ Exported {len(leads)} leads to {filename}")
        return True
        
    except Exception as e:
        print(f"Error exporting to CSV: {e}")
        return False

def validate_company_on_finder(company, cache=None):
    """Check if company exists on finder.fi and extract comprehensive details"""
    try:
        company_name = company.get('name', '')
        business_id = company.get('business_id', '')
        
        # Check cache first
        if cache and business_id in cache:
            print(f"\n{'='*60}")
            print(f"Using cached data for: {company_name}")
            print(f"{'='*60}\n")
            return cache[business_id]
        
        # Search finder.fi for the company
        search_url = f"https://www.finder.fi/search?what={requests.utils.quote(company_name)}&sort=RELEVANCE_desc&page=1"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fi-FI,fi;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        
        print(f"\n{'='*60}")
        print(f"Validating: {company_name}")
        print(f"  Search URL: {search_url}")
        
        # Try up to 3 times if we get 202
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get(search_url, headers=headers, timeout=15)
                
                if response.status_code == 202:
                    print(f"  ⚠ Got 202 (rate limited), waiting {5 * (attempt + 1)} seconds... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(5 * (attempt + 1))  # Exponential backoff: 5s, 10s, 15s
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
                    continue
                else:
                    print(f"  ✗ Failed after {max_retries} attempts")
                    return None
                    
        else:
            # All retries exhausted
            print(f"  ✗ Search failed after {max_retries} attempts (rate limited)")
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all links with "yhteystiedot" in href - these are company detail page links
        # URL structure: /category/Company+Name/City/yhteystiedot/id
        results = soup.find_all('a', href=lambda x: x and 'yhteystiedot' in x if x else False)
        
        if not results:
            print(f"  ✗ No company detail links found on Finder.fi")
            return None
        
        print(f"  Found {len(results)} potential company links")
        
        # Extract and normalize company name for matching
        company_name_normalized = company_name.lower().replace(' oy', '').replace(' ab', '').replace(',', '').strip()
        # Keep hyphens in original name for better matching
        company_name_with_hyphen = company_name_normalized
        # Also create version without hyphens for flexible matching
        company_name_no_hyphen = company_name_normalized.replace('-', ' ')
        
        company_words = [w for w in company_name_no_hyphen.split() if len(w) > 2]
        
        # Try to find exact match by analyzing the href
        best_match = None
        best_score = 0
        
        for idx, link in enumerate(results[:10]):  # Check first 10 results
            href = link.get('href', '')
            
            # Extract company name from URL
            # Format: /category/Company+Name/City/yhteystiedot/id
            # Example: /Metallituotteet/J-Metallikaluste+Oy/Kuopio/yhteystiedot/407476
            parts = href.split('/')
            
            # Find the company name part - it's between category and city, before yhteystiedot
            # The structure is: ['', 'category', 'Company+Name', 'City', 'yhteystiedot', 'id']
            company_url_part = None
            
            # Find yhteystiedot index
            try:
                yhteystiedot_idx = parts.index('yhteystiedot')
                # Company name is 2 positions before yhteystiedot (skip city)
                if yhteystiedot_idx >= 2:
                    company_url_part = parts[yhteystiedot_idx - 2]
            except (ValueError, IndexError):
                # Fallback: try to find any part that looks like a company name
                # (has + signs and is not 'yhteystiedot')
                for part in parts:
                    if '+' in part and 'yhteystiedot' not in part and len(part) > 5:
                        company_url_part = part
                        break
            
            if not company_url_part:
                continue
            
            # Convert URL format to text: "J-Metallikaluste+Oy" -> "j metallikaluste oy"
            # First replace + with space, but keep hyphens
            url_company_name_original = company_url_part.replace('+', ' ').lower()
            url_company_name_original = url_company_name_original.replace(' oy', '').replace(' ab', '').strip()
            
            # Also create version without hyphens for comparison
            url_company_name_no_hyphen = url_company_name_original.replace('-', ' ')
            
            print(f"  Candidate #{idx+1}:")
            print(f"    URL: {href}")
            print(f"    Extracted part: {company_url_part}")
            print(f"    URL name (original): {url_company_name_original}")
            print(f"    URL name (no hyphen): {url_company_name_no_hyphen}")
            print(f"    Search name (with hyphen): {company_name_with_hyphen}")
            print(f"    Search name (no hyphen): {company_name_no_hyphen}")
            
            # Also check if business ID is in the URL
            if business_id and business_id.replace('-', '') in href:
                best_match = link
                best_score = 100
                print(f"  ✓ Perfect match by business ID in URL")
                break
            
            # Try exact match first (with hyphens)
            if url_company_name_original == company_name_with_hyphen:
                best_match = link
                best_score = 100
                print(f"    Match score: 100.0% (exact match with hyphens)")
                break
            
            # Score based on word matching (without hyphens for flexibility)
            url_words = url_company_name_no_hyphen.split()
            matches = sum(1 for word in company_words if word in url_words)
            
            # Calculate match score (percentage of words matched)
            if len(company_words) > 0:
                score = (matches / len(company_words)) * 100
                
                # Bonus if URL has same number of words
                if len(url_words) == len(company_words):
                    score += 10
                
                # Bonus if exact match without hyphens
                if url_company_name_no_hyphen == company_name_no_hyphen:
                    score = 100
                
                print(f"    Match score: {score:.1f}% ({matches}/{len(company_words)} words)")
                
                if score > best_score:
                    best_score = score
                    best_match = link
        
        # Accept match if score is good enough
        if best_match and best_score >= 60:  # At least 60% match
            company_link = best_match
            print(f"  ✓ Best match selected with {best_score:.1f}% confidence")
        else:
            print(f"  ✗ No good match found (best score: {best_score:.1f}%)")
            return None
        
        # Navigate to company page using the link's href
        company_url = 'https://www.finder.fi' + company_link['href']
        print(f"  Company page: {company_url}")
        
        time.sleep(1)  # Rate limiting
        company_response = requests.get(company_url, headers=headers, timeout=10)
        
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
        
        # STRATEGY 1: Look for structured data in definition lists (dl/dt/dd)
        definition_lists = company_soup.find_all('dl')
        for dl in definition_lists:
            dts = dl.find_all('dt')
            dds = dl.find_all('dd')
            
            for dt, dd in zip(dts, dds):
                key = dt.get_text(strip=True)
                value = dd.get_text(strip=True)
                
                # Map Finnish labels to data fields
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
        
        # STRATEGY 2: Look for tables with company information
        tables = company_soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    
                    if 'Liikevaihto' in key:
                        finder_data['financials']['revenue'] = value
                    elif 'Henkilöstö' in key:
                        finder_data['basic_info']['employees'] = value
                    elif 'Perustettu' in key:
                        finder_data['basic_info']['founded'] = value
                    elif 'Tulos' in key or 'Liikevoitto' in key:
                        finder_data['financials']['operating_profit'] = value
        
        # STRATEGY 3: Look for divs with specific classes or data attributes
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
        
        # STRATEGY 4: Extract key people/management
        # Look for sections with titles like "Johto", "Henkilöstö", "Management"
        people_sections = company_soup.find_all(['div', 'section'], 
            text=re.compile(r'Johto|Hallitus|Toimitusjohtaja|Management|Board', re.IGNORECASE))
        
        for section in people_sections:
            # Look for person cards/entries in this section or its siblings
            parent = section.find_parent()
            if parent:
                person_containers = parent.find_all(['div', 'li'], class_=re.compile(r'person|contact|member'))
                
                for container in person_containers[:10]:  # Limit to 10 people
                    person = {}
                    
                    # Try to extract name
                    name_elem = container.find(['h3', 'h4', 'strong', 'span'], class_=re.compile(r'name'))
                    if name_elem:
                        person['name'] = name_elem.get_text(strip=True)
                    
                    # Try to extract title/role
                    title_elem = container.find(['span', 'p', 'div'], class_=re.compile(r'title|role|position'))
                    if title_elem:
                        person['title'] = title_elem.get_text(strip=True)
                    
                    # Try to extract email
                    email_elem = container.find('a', href=re.compile(r'^mailto:'))
                    if email_elem:
                        person['email'] = email_elem['href'].replace('mailto:', '')
                    
                    if person.get('name'):
                        finder_data['key_people'].append(person)
        
        # STRATEGY 5: Text-based extraction as fallback
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
        
        # Check if we found any useful data
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

def run_finder_validation(leads):
    """Background task to validate leads on finder.fi with caching"""
    global validation_status, scraping_status
    
    try:
        validation_status['is_running'] = True
        validation_status['progress'] = 0
        validation_status['total'] = len(leads)
        validation_status['validated_count'] = 0
        validation_status['removed_count'] = 0
        
        # Load cache
        cache = load_finder_cache()
        print(f"Loaded cache with {len(cache)} entries")
        
        validated_leads = []
        cache_updated = False
        
        for idx, lead in enumerate(leads):
            validation_status['current_company'] = lead['name']
            validation_status['progress'] = idx + 1
            
            print(f"\n[{idx + 1}/{len(leads)}] Validating: {lead['name']}")
            
            # Check if lead has email already
            has_email = (lead.get('contact_info', {}).get('emails') or 
                        any(c.get('email') for c in lead.get('contact_info', {}).get('contacts', [])))
            
            # Check on finder.fi (with cache)
            finder_data = validate_company_on_finder(lead, cache)
            
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
            
            # Longer delay to avoid rate limiting (4-6 seconds random)
            import random
            delay = random.uniform(4, 6)
            time.sleep(delay)
        
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

def run_scraper(params):
    """Background task to run the scraper"""
    global scraping_status
    
    try:
        scraping_status['is_running'] = True
        scraping_status['progress'] = 0
        scraping_status['results'] = []
        
        scraper = YTJCompanyScraper()
        
        # Custom scrape with progress tracking
        all_results = []
        page = 1
        companies_processed = 0
        max_companies = params['max_companies']
        main_business_line_filter = params.get('main_business_line')
        
        scraping_status['total'] = max_companies
        
        while companies_processed < max_companies:
            data = scraper.get_companies(
                params.get('main_business_line'),
                params.get('location'),
                params.get('company_form'),
                page
            )
            
            if not data or not data.get('companies'):
                break
            
            companies = data['companies']
            
            for company in companies:
                if companies_processed >= max_companies:
                    break
                
                result = scraper.process_company(company)
                
                # Filter by business line code if specified
                if main_business_line_filter:
                    company_bl_code = result.get('main_business_line_code', '')
                    # Check if it matches exactly or starts with the code (for subcategories)
                    if not (company_bl_code == main_business_line_filter or company_bl_code.startswith(main_business_line_filter)):
                        print(f"  Skipping {result['name']} - business line {company_bl_code} doesn't match filter {main_business_line_filter}")
                        continue
                
                scraping_status['current_company'] = result['name']
                
                # If no valid website in API, search for it
                if not result['website']:
                    result['website'] = scraper.duckduckgo_search(result['name'])
                
                # Scrape contact info from website
                if result['website']:
                    result['contact_info'] = scraper.extract_contact_info(result['website'], result['name'])
                
                all_results.append(result)
                companies_processed += 1
                scraping_status['progress'] = companies_processed
                scraping_status['results'] = all_results
            
            page += 1
        
        # Save to JSON
        output_file = params.get('output_file', 'companies_leads.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        
        # Also export to CSV
        csv_file = output_file.replace('.json', '.csv')
        export_to_csv(all_results, csv_file)
        
        scraping_status['is_running'] = False
        
    except Exception as e:
        print(f"Error in scraper: {e}")
        scraping_status['is_running'] = False
        scraping_status['error'] = str(e)

def run_agent_enrichment(leads, openai_api_key):
    """Background task to enrich leads with ChatGPT agent"""
    global agent_status
    
    try:
        agent_status['is_running'] = True
        agent_status['progress'] = 0
        agent_status['total'] = len(leads)
        
        client = OpenAI(api_key=openai_api_key)
        
        enriched_leads = []
        
        for idx, lead in enumerate(leads):
            agent_status['current_company'] = lead['name']
            agent_status['progress'] = idx + 1
            
            # Skip if already has good contact info
            existing_emails = lead.get('contact_info', {}).get('emails', [])
            existing_contacts = lead.get('contact_info', {}).get('contacts', [])
            
            has_valid_email = len(existing_emails) > 0 or any(c.get('email') for c in existing_contacts)
            
            if has_valid_email:
                enriched_leads.append(lead)
                continue
            
            # Use ChatGPT to find contact info
            prompt = f"""Find contact email addresses for this Finnish company:

Company: {lead['name']}
Business ID: {lead['business_id']}
Website: {lead.get('website', 'Not available')}
Address: {lead.get('address', {}).get('street', '')}, {lead.get('address', {}).get('city', '')}

Search for:
1. Sales contact email (myynti@, sales@)
2. General business email
3. Key personnel emails (CEO, CTO, Sales Manager)

Return ONLY a JSON object with this format:
{{
  "emails": ["email1@company.fi", "email2@company.fi"],
  "contacts": [
    {{
      "name": "Person Name",
      "title": "CEO",
      "email": "person@company.fi",
      "phone": "+358 XX XXX XXXX"
    }}
  ]
}}

If you cannot find any contact information, return: {{"emails": [], "contacts": []}}
"""
            
            try:
                response = client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that finds business contact information. Always return valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3
                )
                
                result_text = response.choices[0].message.content.strip()
                
                # Log the response
                print(f"\n{'='*60}")
                print(f"Company: {lead['name']}")
                print(f"ChatGPT Response:")
                print(result_text)
                print(f"{'='*60}\n")
                
                # Parse JSON from response
                if result_text.startswith('```json'):
                    result_text = result_text[7:]
                if result_text.endswith('```'):
                    result_text = result_text[:-3]
                result_text = result_text.strip()
                
                agent_result = json.loads(result_text)
                
                print(f"Parsed result: {json.dumps(agent_result, indent=2)}")
                
                # Merge results
                if 'contact_info' not in lead:
                    lead['contact_info'] = {}
                
                # Add found emails
                new_emails = agent_result.get('emails', [])
                lead['contact_info']['emails'] = list(set(existing_emails + new_emails))
                
                # Add found contacts
                new_contacts = agent_result.get('contacts', [])
                lead['contact_info']['contacts'] = existing_contacts + new_contacts
                
                # Check if we now have valid emails after enrichment
                has_email_after = len(lead['contact_info']['emails']) > 0 or any(c.get('email') for c in lead['contact_info']['contacts'])
                
                print(f"Updated lead emails: {lead['contact_info']['emails']}")
                print(f"Updated lead contacts: {len(lead['contact_info']['contacts'])} total")
                print(f"Has valid email: {has_email_after}")
                
                # Only add to enriched leads if we found valid contact info
                if has_email_after:
                    enriched_leads.append(lead)
                    print(f"✓ Added to enriched leads")
                else:
                    print(f"✗ Skipped - no valid email found")
                
            except Exception as e:
                print(f"Error processing {lead['name']}: {e}")
                import traceback
                traceback.print_exc()
                # Don't add leads that failed to process
        
        # Save enriched results (only leads with emails)
        print(f"\n{'='*60}")
        print(f"Total leads processed: {len(leads)}")
        print(f"Leads with valid emails: {len(enriched_leads)}")
        print(f"Leads removed (no email): {len(leads) - len(enriched_leads)}")
        print(f"{'='*60}\n")
        
        with open('companies_leads_enriched.json', 'w', encoding='utf-8') as f:
            json.dump(enriched_leads, f, ensure_ascii=False, indent=2)
        
        # Also export to CSV
        export_to_csv(enriched_leads, 'companies_leads_enriched.csv')
        
        scraping_status['results'] = enriched_leads
        agent_status['is_running'] = False
        
    except Exception as e:
        print(f"Error in agent: {e}")
        agent_status['is_running'] = False
        agent_status['error'] = str(e)

@app.route('/api/scrape', methods=['POST'])
def start_scrape():
    """Start scraping with given parameters"""
    if scraping_status['is_running']:
        return jsonify({'error': 'Scraping already in progress'}), 400
    
    params = request.json
    
    # Start scraping in background thread
    thread = Thread(target=run_scraper, args=(params,))
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': 'Scraping started', 'status': 'running'})

@app.route('/api/validate', methods=['POST'])
def validate_with_finder():
    """Validate leads with finder.fi"""
    if validation_status['is_running']:
        return jsonify({'error': 'Validation already running'}), 400
    
    data = request.json
    leads = data.get('leads', [])
    
    if not leads:
        return jsonify({'error': 'No leads provided'}), 400
    
    # Start validation in background thread
    thread = Thread(target=run_finder_validation, args=(leads,))
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': 'Validation started', 'status': 'running'})

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current scraping status"""
    print("Status endpoint called")  # Debug logging
    return jsonify({
        'scraping': scraping_status,
        'agent': agent_status,
        'validation': validation_status
    })

@app.route('/api/results', methods=['GET'])
def get_results():
    """Get current results"""
    return jsonify(scraping_status['results'])

@app.route('/api/enrich', methods=['POST'])
def enrich_with_agent():
    """Enrich leads with ChatGPT agent"""
    if agent_status['is_running']:
        return jsonify({'error': 'Agent already running'}), 400
    
    data = request.json
    leads = data.get('leads', [])
    openai_api_key = data.get('openai_api_key')
    
    if not openai_api_key:
        return jsonify({'error': 'OpenAI API key required'}), 400
    
    # Start agent in background thread
    thread = Thread(target=run_agent_enrichment, args=(leads, openai_api_key))
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': 'Agent enrichment started', 'status': 'running'})

@app.route('/api/download', methods=['GET'])
def download_results():
    """Download results as JSON file"""
    filename = request.args.get('filename', 'companies_leads.json')
    
    if os.path.exists(filename):
        return send_file(filename, as_attachment=True)
    else:
        return jsonify({'error': 'File not found'}), 404

@app.route('/api/download-csv', methods=['GET'])
def download_csv():
    """Download results as CSV file"""
    filename = request.args.get('filename', 'companies_leads.csv')
    
    # If CSV doesn't exist but JSON does, create it
    json_filename = filename.replace('.csv', '.json')
    if not os.path.exists(filename) and os.path.exists(json_filename):
        with open(json_filename, 'r', encoding='utf-8') as f:
            leads = json.load(f)
        export_to_csv(leads, filename)
    
    if os.path.exists(filename):
        return send_file(filename, as_attachment=True, mimetype='text/csv')
    else:
        return jsonify({'error': 'File not found'}), 404

@app.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """Clear Finder.fi cache"""
    try:
        cache_file = 'finder_cache.json'
        if os.path.exists(cache_file):
            os.remove(cache_file)
        return jsonify({'message': 'Cache cleared successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cache/stats', methods=['GET'])
def cache_stats():
    """Get cache statistics"""
    cache = load_finder_cache()
    return jsonify({
        'entries': len(cache),
        'size_kb': os.path.getsize('finder_cache.json') / 1024 if os.path.exists('finder_cache.json') else 0
    })

@app.route('/api/business-lines', methods=['GET'])
def get_business_lines():
    """Get business line codes from TOL 2025"""
    business_lines = [
        # A - MAATALOUS, METSÄTALOUS JA KALATALOUS
        {"code": "01", "name": "Kasvinviljely ja kotieläintalous, riistatalous ja niihin liittyvät palvelut"},
        {"code": "02", "name": "Metsätalous ja puunkorjuu"},
        {"code": "03", "name": "Kalastus ja vesiviljely"},
        
        # B - KAIVOSTOIMINTA JA LOUHINTA
        {"code": "05", "name": "Kivihiilen ja ruskohiilen kaivu"},
        {"code": "06", "name": "Raakaöljyn ja maakaasun tuotanto"},
        {"code": "07", "name": "Metallimalmien louhinta"},
        {"code": "08", "name": "Muu kaivostoiminta ja louhinta"},
        {"code": "09", "name": "Kaivostoimintaa palveleva toiminta"},
        
        # C - TEOLLISUUS
        {"code": "10", "name": "Elintarvikkeiden valmistus"},
        {"code": "11", "name": "Juomien valmistus"},
        {"code": "12", "name": "Tupakkatuotteiden valmistus"},
        {"code": "13", "name": "Tekstiilien valmistus"},
        {"code": "14", "name": "Vaatteiden valmistus"},
        {"code": "15", "name": "Nahan ja nahkatuotteiden valmistus"},
        {"code": "16", "name": "Sahatavaran sekä puu- ja korkkituotteiden valmistus"},
        {"code": "17", "name": "Paperin, paperi- ja kartonkituotteiden valmistus"},
        {"code": "18", "name": "Painaminen ja tallenteiden jäljentäminen"},
        {"code": "19", "name": "Koksin ja jalostettujen öljytuotteiden valmistus"},
        {"code": "20", "name": "Kemikaalien ja kemiallisten tuotteiden valmistus"},
        {"code": "21", "name": "Lääkeaineiden ja lääkkeiden valmistus"},
        {"code": "22", "name": "Kumi- ja muovituotteiden valmistus"},
        {"code": "23", "name": "Muiden ei-metallisten mineraalituotteiden valmistus"},
        {"code": "24", "name": "Metallien jalostus"},
        {"code": "25", "name": "Metallituotteiden valmistus"},
        {"code": "26", "name": "Tietokoneiden sekä elektronisten ja optisten tuotteiden valmistus"},
        {"code": "27", "name": "Sähkölaitteiden valmistus"},
        {"code": "28", "name": "Muiden koneiden ja laitteiden valmistus"},
        {"code": "29", "name": "Moottoriajoneuvojen, perävaunujen ja puoliperävaunujen valmistus"},
        {"code": "30", "name": "Muiden kulkuneuvojen valmistus"},
        {"code": "31", "name": "Huonekalujen valmistus"},
        {"code": "32", "name": "Muu valmistus"},
        {"code": "33", "name": "Koneiden ja laitteiden korjaus, huolto ja asennus"},
        
        # D - SÄHKÖ-, KAASU- JA LÄMPÖHUOLTO
        {"code": "35", "name": "Sähkö-, kaasu- ja lämpöhuolto, jäähdytysliiketoiminta"},
        
        # E - VESIHUOLTO, VIEMÄRI- JA JÄTEVESIHUOLTO
        {"code": "36", "name": "Veden otto, puhdistus ja jakelu"},
        {"code": "37", "name": "Viemäri- ja jätevesihuolto"},
        {"code": "38", "name": "Jätteen keruu, käsittely ja loppusijoitus"},
        {"code": "39", "name": "Maaperän ja vesistöjen kunnostus"},
        
        # F - RAKENTAMINEN
        {"code": "41", "name": "Talonrakentaminen"},
        {"code": "42", "name": "Maa- ja vesirakentaminen"},
        {"code": "43", "name": "Erikoistunut rakennustoiminta"},
        
        # G - TUKKU- JA VÄHITTÄISKAUPPA
        {"code": "45", "name": "Moottoriajoneuvojen kauppa, korjaus ja huolto"},
        {"code": "46", "name": "Tukkukauppa"},
        {"code": "47", "name": "Vähittäiskauppa"},
        
        # H - KULJETUS JA VARASTOINTI
        {"code": "49", "name": "Maaliikenne ja putkijohtokuljetus"},
        {"code": "50", "name": "Vesiliikenne"},
        {"code": "51", "name": "Ilmaliikenne"},
        {"code": "52", "name": "Varastointi ja liikennettä palveleva toiminta"},
        {"code": "53", "name": "Posti- ja kuriiritoiminta"},
        
        # I - MAJOITUS- JA RAVITSEMISTOIMINTA
        {"code": "55", "name": "Majoitus"},
        {"code": "56", "name": "Ravitsemistoiminta"},
        
        # J - INFORMAATIO JA VIESTINTÄ
        {"code": "58", "name": "Kustannustoiminta"},
        {"code": "59", "name": "Elokuva-, video- ja televisio-ohjelmatuotanto, äänitteiden ja musiikin kustantaminen"},
        {"code": "60", "name": "Radio- ja televisiotoiminta"},
        {"code": "61", "name": "Televiestintä"},
        {"code": "62", "name": "Ohjelmistot, konsultointi ja siihen liittyvä toiminta"},
        {"code": "6201", "name": "Ohjelmistojen suunnittelu ja valmistus"},
        {"code": "6202", "name": "Tietokoneiden konsultointi"},
        {"code": "6209", "name": "Muut tietotekniikkapalvelut"},
        {"code": "63", "name": "Tietopalvelutoiminta"},
        
        # K - RAHOITUS- JA VAKUUTUSTOIMINTA
        {"code": "64", "name": "Rahoituspalvelut"},
        {"code": "65", "name": "Vakuutus-, jälleenvakuutus- ja eläkevakuutustoiminta"},
        {"code": "66", "name": "Rahoitusta ja vakuuttamista palveleva toiminta"},
        
        # L - KIINTEISTÖALAN TOIMINTA
        {"code": "68", "name": "Kiinteistöalan toiminta"},
        
        # M - AMMATILLINEN, TIETEELLINEN JA TEKNINEN TOIMINTA
        {"code": "69", "name": "Lakiasiain- ja laskentatoimen palvelut"},
        {"code": "70", "name": "Pääkonttorien toiminta; liikkeenjohdon konsultointi"},
        {"code": "71", "name": "Arkkitehti- ja insinööripalvelut; tekninen testaus ja analysointi"},
        {"code": "72", "name": "Tieteellinen tutkimus ja kehittäminen"},
        {"code": "73", "name": "Mainostoiminta ja markkinatutkimus"},
        {"code": "74", "name": "Muut erikoistuneet palvelut liike-elämälle"},
        {"code": "75", "name": "Eläinlääkintäpalvelut"},
        
        # N - HALLINTO- JA TUKIPALVELUTOIMINTA
        {"code": "77", "name": "Vuokraus- ja leasingtoiminta"},
        {"code": "78", "name": "Työllistämistoiminta"},
        {"code": "79", "name": "Matkatoimistojen ja matkanjärjestäjien toiminta; varauspalvelut"},
        {"code": "80", "name": "Turvallisuus-, vartiointi- ja etsiväpalvelut"},
        {"code": "81", "name": "Kiinteistön- ja maisemanhoito"},
        {"code": "82", "name": "Hallinto- ja tukipalvelut liike-elämälle"},
        
        # O - JULKINEN HALLINTO JA MAANPUOLUSTUS
        {"code": "84", "name": "Julkinen hallinto ja maanpuolustus; pakollinen sosiaalivakuutus"},
        
        # P - KOULUTUS
        {"code": "85", "name": "Koulutus"},
        
        # Q - TERVEYS- JA SOSIAALIPALVELUT
        {"code": "86", "name": "Terveyspalvelut"},
        {"code": "86230", "name": "Hammaslääkäripalvelut"},
        {"code": "87", "name": "Sosiaalihuollon laitospalvelut"},
        {"code": "88", "name": "Sosiaalihuollon avopalvelut"},
        
        # R - TAITEET, VIIHDE JA VIRKISTYS
        {"code": "90", "name": "Kulttuuri- ja viihdetoiminta"},
        {"code": "91", "name": "Kirjastojen, arkistojen, museoiden ja muiden kulttuurilaitosten toiminta"},
        {"code": "92", "name": "Rahapeli- ja vedonlyöntitoiminta"},
        {"code": "93", "name": "Urheilutoiminta sekä huvi- ja virkistyspalvelut"},
        
        # S - MUU PALVELUTOIMINTA
        {"code": "94", "name": "Järjestöjen toiminta"},
        {"code": "95", "name": "Tietokoneiden, henkilökohtaisten ja kotitaloustavaroiden korjaus"},
        {"code": "96", "name": "Muut henkilökohtaiset palvelut"},
        
        # T - KOTITALOUKSIEN TOIMINTA
        {"code": "97", "name": "Kotitalouksien toiminta kotitaloustyöntekijöiden työnantajina"},
        {"code": "98", "name": "Kotitalouksien eriyttämätön toiminta tavaroiden ja palvelujen tuottamiseksi omaan käyttöön"},
        
        # U - KANSAINVÄLISTEN ORGANISAATIOIDEN TOIMINTA
        {"code": "99", "name": "Kansainvälisten organisaatioiden ja toimielinten toiminta"}
    ]
    return jsonify(business_lines)

if __name__ == '__main__':
    print("Starting Flask server on http://localhost:5001")
    app.run(debug=True, port=5001, host='0.0.0.0')