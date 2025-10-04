"""
AI-powered contact enrichment service
"""
from openai import OpenAI
import json
from utils.export_utils import export_to_csv


def run_agent_enrichment(leads, openai_api_key, agent_status, scraping_status):
    """Background task to enrich leads with ChatGPT agent"""
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
            
            # Use ChatGPT to find contact info and enrich with Finder.fi data
            finder_data = lead.get('finder_data', {})
            has_finder_data = finder_data and finder_data.get('verified_on_finder')
            
            # Build prompt with Finder.fi context if available
            base_prompt = f"""Find contact email addresses for this Finnish company:

Company: {lead['name']}
Business ID: {lead['business_id']}
Website: {lead.get('website', 'Not available')}
Address: {lead.get('address', {}).get('street', '')}, {lead.get('address', {}).get('city', '')}
"""

            if has_finder_data:
                # Add Finder.fi context
                basic_info = finder_data.get('basic_info', {})
                financials = finder_data.get('financials', {})
                
                base_prompt += f"""

VERIFIED COMPANY DATA FROM FINDER.FI:
- Founded: {basic_info.get('founded', 'Unknown')}
- Employees: {basic_info.get('employees', 'Unknown')}
- Revenue: {financials.get('revenue', 'Unknown')}
- Operating Profit: {financials.get('operating_profit', 'Unknown')}
- Financial Year: {financials.get('financial_year', 'Unknown')}
"""

            prompt = base_prompt + """

TASKS:
1. Find sales contact emails (myynti@, sales@)
2. Find general business email
3. Find key personnel emails (CEO, CTO, Sales Manager)
4. Based on company size and revenue, suggest best contact approach

Return ONLY a JSON object with this format:
{
  "emails": ["email1@company.fi", "email2@company.fi"],
  "contacts": [
    {
      "name": "Person Name",
      "title": "CEO",
      "email": "person@company.fi",
      "phone": "+358 XX XXX XXXX"
    }
  ],
  "enriched_insights": {
    "company_size": "Small/Medium/Large",
    "growth_stage": "Startup/Growth/Mature/Established",
    "best_contact_approach": "Direct to decision maker / Through sales team / etc",
    "priority_score": "High/Medium/Low"
  }
}

If you cannot find any contact information, return: {"emails": [], "contacts": [], "enriched_insights": null}
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