import requests
from bs4 import BeautifulSoup
import json
import time

def scrape_shl_catalog():
    base_url = "https://www.shl.com/products/product-catalog/"
    catalog_data = []
    
    # The disguise: making our script look like a normal web browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5'
    }
    
    # We ONLY scrape table type 1 (Individual Test Solutions) as per assignment instructions
    start_offset = 0
    
    while True:
        print(f"Scraping Offset {start_offset}...")
        
        # Construct the paginated URL
        url = f"{base_url}?action_doFilteringForm=Search&f=1&start={start_offset}&type=1"
        
        try:
            # Added the headers to the request
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Failed to fetch {url}: {e}")
            break
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all rows that contain assessment data
        rows = soup.select('tr[data-entity-id], tr[data-course-id]')
        
        if not rows:
            print("No more rows found. Scraping complete.")
            break
            
        for row in rows:
            # Extract Title and URL
            title_elem = row.select_one('td.custom__table-heading__title a')
            if not title_elem:
                continue
                
            name = title_elem.text.strip()
            link = title_elem.get('href')
            full_url = f"https://www.shl.com{link}" if link.startswith('/') else link
            
            # Extract Test Types (the letter badges like P, K, A)
            test_type_elems = row.select('span.product-catalogue__key')
            test_types = [t.text.strip() for t in test_type_elems]
            
            # Build the dictionary
            assessment = {
                "name": name,
                "url": full_url,
                "test_type": ", ".join(test_types)
            }
            catalog_data.append(assessment)
        
        # Increment offset by 12 (as seen in the HTML pagination)
        start_offset += 12
        
        # Polite scraping: sleep to avoid overwhelming their server
        time.sleep(1.5)

    # Remove duplicates just in case
    unique_catalog = {item['name']: item for item in catalog_data}.values()
    
    # Save to JSON
    with open('data/catalog.json', 'w', encoding='utf-8') as f:
        json.dump(list(unique_catalog), f, indent=4, ensure_ascii=False)
        
    print(f"Saved {len(unique_catalog)} assessments to data/catalog.json")

if __name__ == "__main__":
    scrape_shl_catalog()