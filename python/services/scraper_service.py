"""
Scraping orchestration service
"""
from ytj_scraper import YTJCompanyScraper
from utils.export_utils import export_to_csv
import json


def run_scraper(params, scraping_status):
    """Background task to run the scraper"""
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
        