"""
Export utilities for CSV and JSON
"""
import csv


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
                'Social Media',
                # AI Insights
                'AI Company Size',
                'AI Growth Stage',
                'AI Best Contact Approach',
                'AI Priority Score'
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
                
                # Extract AI insights
                ai_insights = lead.get('ai_insights', {})
                if ai_insights:
                    row['AI Company Size'] = ai_insights.get('company_size', '')
                    row['AI Growth Stage'] = ai_insights.get('growth_stage', '')
                    row['AI Best Contact Approach'] = ai_insights.get('best_contact_approach', '')
                    row['AI Priority Score'] = ai_insights.get('priority_score', '')
                
                writer.writerow(row)
        
        print(f"✓ Exported {len(leads)} leads to {filename}")
        return True
        
    except Exception as e:
        print(f"Error exporting to CSV: {e}")
        return False
    