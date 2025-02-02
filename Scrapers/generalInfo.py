import requests
from bs4 import BeautifulSoup
import re
import csv
from datetime import datetime
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text

def get_ensah_content():
    # First URL - ENSAH website
    url1 = "https://ensah.ma/public/presentation.php"
    # Second URL - UAE website
    url2 = "https://www.uae.ac.ma/etablissements/ensah"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    structured_data = []
    
    try:
        # Scrape from ENSAH website
        response1 = requests.get(url1, headers=headers)
        response1.raise_for_status()
        soup1 = BeautifulSoup(response1.text, 'html.parser')
        
        # Get content from ENSAH website
        event_contact = soup1.find_all(class_='event-contact')
        right_event_content = soup1.find_all(class_='right-event-content')
        
        # Process presentation content
        for content in right_event_content:
            text = clean_text(content.get_text())
            structured_data.append({
                'type': 'presentation',
                'content': text,
                'source_url': url1,
                'date_extracted': datetime.now().strftime("%Y-%m-%d"),
                'section': 'main_content'
            })
        
        # Process contact information
        for contact in event_contact:
            text = clean_text(contact.get_text())
            structured_data.append({
                'type': 'contact',
                'content': text,
                'source_url': url1,
                'date_extracted': datetime.now().strftime("%Y-%m-%d"),
                'section': 'contact_info'
            })
        
        # Scrape from UAE website with SSL verification disabled
        response2 = requests.get(url2, headers=headers, verify=False)
        response2.raise_for_status()
        soup2 = BeautifulSoup(response2.text, 'html.parser')
        
        # Get statistics content
        statistics = soup2.find_all(class_='statics-chiffre')
        
        # Process statistics information
        for stat in statistics:
            text = clean_text(stat.get_text())
            # Try to get the label from parent or nearby elements
            label_elem = stat.find_previous(class_='statics-titre') or stat.find_parent().find(class_='statics-titre')
            label = clean_text(label_elem.get_text()) if label_elem else 'Statistics'
            
            structured_data.append({
                'type': 'statistics',
                'content': f"{label}: {text}",
                'source_url': url2,
                'date_extracted': datetime.now().strftime("%Y-%m-%d"),
                'section': 'statistics'
            })
        
        return structured_data
    
    except requests.RequestException as e:
        print(f"An error occurred during the request: {e}")
        return None
    except Exception as e:
        print(f"An error occurred while parsing: {e}")
        return None

def save_to_csv(data, filename='ensah_data.csv'):
    if not data:
        return
    
    # Define CSV columns
    fieldnames = ['type', 'section', 'content', 'source_url', 'date_extracted']
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        print(f"Data successfully saved to {filename}")
    except Exception as e:
        print(f"Error saving to CSV: {e}")

if __name__ == "__main__":
    content = get_ensah_content()
    if content:
        # Save to CSV
        save_to_csv(content)
        
        # Print preview of the data
        print("\nData Preview:")
        for item in content:
            print(f"\nType: {item['type']}")
            print(f"Section: {item['section']}")
            print(f"Content: {item['content'][:150]}...")