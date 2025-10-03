from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import json
import os
from ytj_scraper import YTJCompanyScraper
from openai import OpenAI
from threading import Thread

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

agent_status = {
    'is_running': False,
    'progress': 0,
    'total': 0,
    'current_company': ''
}

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
        main_business_line = params.get('main_business_line')
        
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
                if main_business_line:
                    company_bl_code = result.get('main_business_line_code', '')
                    # Check if it matches exactly or starts with the code (for subcategories)
                    if not (company_bl_code == main_business_line or company_bl_code.startswith(main_business_line)):
                        print(f"  Skipping {result['name']} - business line {company_bl_code} doesn't match filter {main_business_line}")
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
                    model="gpt-4-turbo-preview",  # Latest GPT-4 model
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

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current scraping status"""
    print("Status endpoint called")  # Debug logging
    return jsonify({
        'scraping': scraping_status,
        'agent': agent_status
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