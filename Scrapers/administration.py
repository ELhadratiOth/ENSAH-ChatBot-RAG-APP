import requests
from bs4 import BeautifulSoup
import re
import csv
from datetime import datetime

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text

def get_ensah_administration():
    url = "https://ensah.ma/public/administration.php"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    structured_data = []
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        content_div = soup.find('div', class_='textcontent')
        if content_div:
            description = content_div.find('p')
            if description:
                structured_data.append({
                    'type': 'administration',
                    'section': 'description',
                    'content': clean_text(description.get_text()),
                })
            
            direction_heading = content_div.find('h4', string=re.compile('Direction', re.IGNORECASE))
            if direction_heading and direction_heading.find_next('ul'):
                direction_list = direction_heading.find_next('ul').find_all('li')
                for item in direction_list:
                    structured_data.append({
                        'type': 'administration',
                        'section': 'direction',
                        'content': clean_text(item.get_text()),
                    })
            
            services_heading = content_div.find('h4', string=re.compile('Services administratifs', re.IGNORECASE))
            if services_heading and services_heading.find_next('ul'):
                services_list = services_heading.find_next('ul').find_all('li')
                for item in services_list:
                    structured_data.append({
                        'type': 'administration',
                        'section': 'service',
                        'content': clean_text(item.get_text()),
                    })
        
        return structured_data
    
    except requests.RequestException as e:
        print(f"An error occurred during the request: {e}")
        return None
    except Exception as e:
        print(f"An error occurred while parsing: {e}")
        return None

def save_to_csv(data, filename='admin_data.csv'):
    if not data:
        return
    
    fieldnames = ['type', 'section', 'content']
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writerows(data)
        print(f"Data successfully saved to {filename}")
    except Exception as e:
        print(f"Error saving to CSV: {e}")

if __name__ == "__main__":
    content = get_ensah_administration()
    
    if content:
        save_to_csv(content)
        
        print("\nData Preview:")
        for item in content:
            print(f"\nType: {item['type']}")
            print(f"Section: {item['section']}")
            print(f"Content: {item['content'][:150]}...")