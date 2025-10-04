import requests
import json
import time
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse

class YTJCompanyScraper:
    def __init__(self):
        self.base_url = "https://avoindata.prh.fi/opendata-ytj-api/v3"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        # Domains to skip (business directories)
        self.skip_domains = [
            'finder.fi', 'fonecta.fi', 'kauppalehti.fi', 'asiakastieto.fi',
            'vastuugroup.fi', 'yrittajat.fi', 'wikipedia.org', 'linkedin.com',
            'facebook.com', 'yellow.fi', 'taloyritys.fi', 'suomenyritykset.fi',
            'dnb.com', 'bisnode.fi', 'prh.fi', 'ytj.fi', 'finder.com'
        ]
    
    def get_companies(self, main_business_line=None, location=None, company_form=None, page=1):
        """Fetch companies from YTJ API"""
        url = f"{self.base_url}/companies"
        params = {}
        
        if main_business_line:
            params['mainBusinessLine'] = main_business_line
        if location:
            params['location'] = location
        if company_form:
            params['companyForm'] = company_form
        if page > 1:
            params['page'] = page
        
        try:
            print(f"  API Request: {url}")
            print(f"  Parameters: {params}")
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            print(f"  Total results from API: {data.get('totalResults', 0)}")
            return data
        except Exception as e:
            print(f"Error fetching companies: {e}")
            return None
    
    def is_valid_website(self, url):
        """Check if URL is not a business directory"""
        if not url:
            return False
        url_lower = url.lower()
        return not any(domain in url_lower for domain in self.skip_domains)
    
    def normalize_url(self, url):
        """Add https:// if scheme is missing"""
        if not url:
            return None
        url = url.strip()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        return url
    
    def try_fetch_url(self, url):
        """Try to fetch URL, with fallback to www/non-www version"""
        if not url:
            return None
        
        url = self.normalize_url(url)
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response
        except:
            # Try alternate version (add/remove www)
            try:
                if '://www.' in url:
                    # Try without www
                    alternate_url = url.replace('://www.', '://')
                else:
                    # Try with www
                    alternate_url = url.replace('://', '://www.')
                
                response = self.session.get(alternate_url, timeout=10)
                response.raise_for_status()
                return response
            except:
                return None
    
    def duckduckgo_search(self, company_name):
        """Search for company website using DuckDuckGo, filtering out directories"""
        try:
            search_url = "https://html.duckduckgo.com/html/"
            # Search only company name for best results
            data = {'q': company_name}
            
            response = self.session.post(search_url, data=data, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find result links and filter out directories
            results = soup.find_all('a', class_='result__a')
            for result in results[:5]:  # Check first 5 results
                url = result.get('href')
                if self.is_valid_website(url):
                    return url
            
            return None
        except Exception as e:
            print(f"  Error searching for {company_name}: {e}")
            return None
    
    def is_sales_email(self, email):
        """Check if email is likely a sales/business contact"""
        email_lower = email.lower()
        
        # Skip generic customer service emails
        skip_keywords = ['info@', 'asiakaspalvelu@', 'customerservice@', 
                        'tuki@', 'support@', 'help@', 'helpdesk@']
        if any(keyword in email_lower for keyword in skip_keywords):
            return False
        
        # Prefer sales/business emails
        sales_keywords = ['myynti@', 'sales@', 'business@', 'b2b@', 
                         'yritys@', 'contact@', 'office@']
        if any(keyword in email_lower for keyword in sales_keywords):
            return True
        
        # Accept personal emails (firstname.lastname@)
        if re.match(r'^[a-z]+\.[a-z]+@', email_lower):
            return True
        
        return True  # Accept others by default
    
    def extract_email_domain(self, url):
        """Extract likely email domain from URL"""
        if not url:
            return None
        try:
            parsed = urlparse(url)
            domain = parsed.netloc or parsed.path
            # Remove www. prefix
            domain = domain.replace('www.', '')
            # Remove any path
            domain = domain.split('/')[0]
            return domain
        except:
            return None
    
    def extract_contact_info(self, url, company_name=None):
        """Scrape contact information from website"""
        if not url:
            return {}
        
        url = self.normalize_url(url)
        email_domain = self.extract_email_domain(url)
        
        contact_info = {
            'emails': [],
            'phones': [],
            'contacts': [],  # Structured contacts with name, title, email, phone
            'social_media': {}
        }
        
        try:
            response = self.try_fetch_url(url)
            if not response:
                return contact_info
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try to find contact page
            contact_links = []
            for link in soup.find_all('a', href=True):
                href_lower = link['href'].lower()
                text_lower = link.get_text().lower()
                if any(word in href_lower or word in text_lower for word in 
                       ['contact', 'yhteystiedot', 'kontakt', 'about', 'meistä', 'team', 'tiimi']):
                    full_url = requests.compat.urljoin(url, link['href'])
                    contact_links.append(full_url)
            
            # Scrape main page and contact page
            pages_to_scrape = [url] + contact_links[:2]
            all_text = ""
            all_soups = []
            
            for page_url in pages_to_scrape:
                try:
                    page_response = self.try_fetch_url(page_url)
                    if not page_response:
                        continue
                    page_soup = BeautifulSoup(page_response.text, 'html.parser')
                    all_soups.append(page_soup)
                    all_text += " " + page_soup.get_text()
                    
                    # Also check for mailto links
                    for mailto in page_soup.find_all('a', href=re.compile(r'^mailto:')):
                        email = mailto['href'].replace('mailto:', '').split('?')[0]
                        if self.is_sales_email(email):
                            contact_info['emails'].append(email)
                    
                except:
                    continue
            
            # Extract structured contact information (name, title, email, phone together)
            for soup_obj in all_soups:
                # Look for common patterns where contact info is grouped
                # Pattern 1: div/section containing name, title, email, phone
                for container in soup_obj.find_all(['div', 'section', 'article', 'li']):
                    container_html = str(container)
                    container_text = container.get_text(separator=' ', strip=True)
                    
                    # Check if this container has both email and name patterns
                    email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', container_text)
                    
                    if email_match:
                        email = email_match.group()
                        if not self.is_sales_email(email):
                            continue
                        
                        # Look for name (usually before email, capitalized words)
                        name_pattern = r'([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
                        name_match = re.search(name_pattern, container_text)
                        
                        # Look for title/role keywords
                        title_keywords = ['CEO', 'CTO', 'COO', 'Director', 'Manager', 'Head', 
                                        'Toimitusjohtaja', 'Johtaja', 'Päällikkö', 'Sales', 'Myynti']
                        title = None
                        for keyword in title_keywords:
                            if keyword.lower() in container_text.lower():
                                title = keyword
                                break
                        
                        # Look for phone in same container
                        phone_pattern = r'\+?358[\s-]?\d{1,2}[\s-]?\d{3,4}[\s-]?\d{3,4}|0\d{1,2}[\s-]?\d{3,4}[\s-]?\d{3,4}'
                        phone_match = re.search(phone_pattern, container_text)
                        
                        # If we found a name or title, save structured contact
                        if name_match or title:
                            contact = {
                                'name': name_match.group().strip() if name_match else None,
                                'title': title,
                                'email': email,
                                'phone': phone_match.group().strip() if phone_match else None
                            }
                            # Avoid duplicates
                            if contact not in contact_info['contacts']:
                                contact_info['contacts'].append(contact)
            
            # Find emails from text - prioritize emails from company domain
            emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', all_text)
            
            # Also find obfuscated emails like "sales (at) company.fi" or "sales[at]company.fi"
            obfuscated_pattern = r'\b([A-Za-z0-9._%+-]+)\s*[\(\[]\s*at\s*[\)\]]\s*([A-Za-z0-9.-]+\.[A-Z|a-z]{2,})\b'
            obfuscated_emails = re.findall(obfuscated_pattern, all_text, re.IGNORECASE)
            
            # Convert obfuscated emails to proper format
            for local, domain in obfuscated_emails:
                proper_email = f"{local}@{domain}"
                if proper_email not in emails:
                    emails.append(proper_email)
            
            # Separate emails by domain match
            domain_emails = []
            other_emails = []
            
            for email in emails:
                if not self.is_sales_email(email):
                    continue
                    
                # Check if email matches company domain
                if email_domain and email_domain in email:
                    if email not in domain_emails:
                        domain_emails.append(email)
                else:
                    if email not in other_emails:
                        other_emails.append(email)
            
            # Prioritize domain-matching emails
            contact_info['emails'] = (domain_emails + other_emails)[:5]
            
            # Find phone numbers (Finnish format)
            phones = re.findall(r'\+?358[\s-]?\d{1,2}[\s-]?\d{3,4}[\s-]?\d{3,4}', all_text)
            phones += re.findall(r'0\d{1,2}[\s-]?\d{3,4}[\s-]?\d{3,4}', all_text)
            contact_info['phones'] = list(set(phones))[:5]
            
            # Find social media links
            for soup_obj in all_soups:
                for link in soup_obj.find_all('a', href=True):
                    href = link['href']
                    if 'linkedin.com' in href and 'linkedin' not in contact_info['social_media']:
                        contact_info['social_media']['linkedin'] = href
                    elif 'facebook.com' in href and 'facebook' not in contact_info['social_media']:
                        contact_info['social_media']['facebook'] = href
                    elif ('twitter.com' in href or 'x.com' in href) and 'twitter' not in contact_info['social_media']:
                        contact_info['social_media']['twitter'] = href
                    elif 'instagram.com' in href and 'instagram' not in contact_info['social_media']:
                        contact_info['social_media']['instagram'] = href
            
        except Exception as e:
            print(f"  Error scraping {url}: {e}")
        
        return contact_info
    
    def process_company(self, company_data):
        """Process a single company"""
        result = {
            'business_id': company_data['businessId']['value'],
            'name': '',
            'company_form': '',
            'main_business_line': '',
            'main_business_line_code': '',
            'website': '',
            'address': {},
            'registration_date': company_data.get('registrationDate'),
            'status': company_data.get('status'),
            'contact_info': {}
        }
        
        # Get company name
        if company_data.get('names'):
            current_names = [n for n in company_data['names'] if n['version'] == 1]
            if current_names:
                result['name'] = current_names[0]['name']
        
        # Get company form
        if company_data.get('companyForms'):
            current_forms = [f for f in company_data['companyForms'] if f['version'] == 1]
            if current_forms and current_forms[0].get('descriptions'):
                result['company_form'] = current_forms[0]['descriptions'][0].get('description', '')
        
        # Get main business line
        if company_data.get('mainBusinessLine'):
            result['main_business_line_code'] = company_data['mainBusinessLine'].get('type', '')
            if company_data['mainBusinessLine'].get('descriptions'):
                result['main_business_line'] = company_data['mainBusinessLine']['descriptions'][0].get('description', '')
        
        # Get website from API
        if company_data.get('website'):
            api_website = company_data['website'].get('url', '')
            if self.is_valid_website(api_website):
                result['website'] = self.normalize_url(api_website)
        
        # Get address
        if company_data.get('addresses'):
            addr = company_data['addresses'][0]
            result['address'] = {
                'street': addr.get('street'),
                'post_code': addr.get('postCode'),
                'city': addr.get('postOffices', [{}])[0].get('city') if addr.get('postOffices') else None,
                'country': addr.get('country', 'FI')
            }
        
        return result
    
    def scrape_companies(self, main_business_line=None, location=None, 
                        company_form=None, max_companies=10, output_file='companies.json'):
        """Main scraping function"""
        all_results = []
        page = 1
        companies_processed = 0
        
        print(f"\n{'='*60}")
        print(f"Starting scrape with filters:")
        print(f"  Business Line Code: {main_business_line}")
        print(f"  Location: {location}")
        print(f"  Company Form: {company_form}")
        print(f"  Max Companies: {max_companies}")
        print(f"{'='*60}\n")
        
        while companies_processed < max_companies:
            print(f"Fetching page {page}...")
            data = self.get_companies(main_business_line, location, company_form, page)
            
            if not data or not data.get('companies'):
                print("No more companies found.")
                break
            
            total_results = data.get('totalResults', 0)
            companies = data['companies']
            
            print(f"Found {len(companies)} companies on this page (Total available: {total_results})\n")
            
            for company in companies:
                if companies_processed >= max_companies:
                    break
                
                result = self.process_company(company)
                
                # Filter by business line code if specified
                if main_business_line:
                    company_bl_code = result.get('main_business_line_code', '')
                    # Check if it matches exactly or starts with the code (for subcategories)
                    if not (company_bl_code == main_business_line or company_bl_code.startswith(main_business_line)):
                        print(f"  Skipping {result['name']} - business line {company_bl_code} doesn't match filter {main_business_line}")
                        continue
                
                print(f"[{companies_processed + 1}/{max_companies}] {result['name']}")
                print(f"  Business ID: {result['business_id']}")
                print(f"  Business Line: {result['main_business_line']} (Code: {result['main_business_line_code']})")
                
                # If no valid website in API, search for it
                if not result['website']:
                    print(f"  Searching for website...")
                    result['website'] = self.duckduckgo_search(result['name'])
                    time.sleep(2)  # Rate limiting for DuckDuckGo
                
                # Scrape contact info from website
                if result['website']:
                    print(f"  Website: {result['website']}")
                    print(f"  Scraping contact info...")
                    result['contact_info'] = self.extract_contact_info(result['website'], result['name'])
                    
                    if result['contact_info']['contacts']:
                        print(f"  ✓ Found {len(result['contact_info']['contacts'])} structured contact(s)")
                        for contact in result['contact_info']['contacts']:
                            if contact['name']:
                                print(f"    - {contact['name']}", end='')
                                if contact['title']:
                                    print(f" ({contact['title']})", end='')
                                print()
                    if result['contact_info']['emails']:
                        print(f"  ✓ Found {len(result['contact_info']['emails'])} email(s)")
                    if result['contact_info']['phones']:
                        print(f"  ✓ Found {len(result['contact_info']['phones'])} phone(s)")
                    
                    time.sleep(2)  # Rate limiting
                else:
                    print(f"  ✗ No website found")
                
                all_results.append(result)
                companies_processed += 1
                print()
            
            page += 1
            
            if companies_processed >= max_companies:
                break
        
        # Save to JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n{'='*60}")
        print(f"✓ Scraping complete!")
        print(f"  Saved {len(all_results)} companies to {output_file}")
        print(f"{'='*60}\n")
        
        return all_results