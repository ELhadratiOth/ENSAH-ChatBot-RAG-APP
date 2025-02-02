import requests
from bs4 import BeautifulSoup
import re
import csv
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('\xa0', ' ')
    text = text.replace('\u200b', '')
    text = re.sub(r'&[a-zA-Z]+;', ' ', text)
    text = text.strip()
    return text

def get_filiere_content(url, filiere_code):
    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Get title
        title = ""
        title_elem = soup.find('h2', class_="event-title")
        if title_elem:
            title = clean_text(title_elem.text)
            
        # Get coordinator info
        coordinator_name = ""
        coordinator_email = ""
        contact_div = soup.find('div', class_="event-contact")
        if contact_div:
            contact_info = contact_div.find_all('li')
            if len(contact_info) >= 2:
                coordinator_name = clean_text(contact_info[0].text)
                coordinator_email = clean_text(contact_info[1].text)
        
        # Get main content
        content = ""
        content_div = soup.find('div', class_=["right-event-content" , "textcontent"])
        if content_div:
            content = clean_text(content_div.get_text())
            
        modules_data = {
            "filiere": filiere_code,
            "semesters": {}
        }
        
        tabs = soup.find_all('div', class_="tab-pane")
        for tab in tabs:
            semester = ""
            if tab.get('id'):
                if 'section-1' in tab['id']:
                    semester = "S1"
                elif 'section-2' in tab['id']:
                    semester = "S2"
                elif 'section-3' in tab['id']:
                    semester = "S3"
                elif 'section-4' in tab['id']:
                    semester = "S4"
                elif 'section-5' in tab['id']:
                    semester = "S5-S6"
                    
            if semester:
                module_list = []
                for li in tab.find_all('li'):
                    module_name = clean_text(li.text)
                    if module_name:
                        module_list.append(module_name)
                if module_list:
                    modules_data["semesters"][semester] = module_list
        
        modules_json = json.dumps(modules_data, ensure_ascii=False)
        
        return {
            'title': title,
            'coordinator_name': coordinator_name,
            'coordinator_email': coordinator_email,
            'content': content,
            'modules_json': modules_json
        }
        
    except Exception as e:
        print(f"Error fetching filiere content: {e}")
        return None

def get_filieres():
    filieres_urls = {
        'cp': 'https://ensah.ma/public/cp.php',
        'gc': 'https://ensah.ma/public/gc.php',
        'gi': 'https://ensah.ma/public/gi.php',
        'id': 'https://ensah.ma/public/id.php',
        'tdia': 'https://ensah.ma/public/tdia.php',
        'geer': 'https://ensah.ma/public/geer.php',
        'gee': 'https://ensah.ma/public/gee.php',
        'gm': 'https://ensah.ma/public/gm.php'
    }
    
    structured_data = []
    modules_data = {}
    
    for filiere_code, url in filieres_urls.items():
        print(f"Fetching data for {filiere_code}...")
        content = get_filiere_content(url, filiere_code)
        
        if content:
            # CSV data
            data = {
                'code': filiere_code,
                'title': content['title'],
                'coordinator_name': content['coordinator_name'],
                'coordinator_email': content['coordinator_email'],
                'content': content['content']
            }
            structured_data.append(data)
            
            # JSON modules data
            modules_data[filiere_code] = json.loads(content['modules_json'])
    
    return structured_data, modules_data

def save_to_csv(data, filename='filieres_data.csv'):
    if not data:
        return
    
    fieldnames = ['code', 'title', 'coordinator_name', 'coordinator_email', 'content']
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writerows(data)
        print(f"\nData successfully saved to {filename}")
        print("\nFilières Preview:")
        for item in data[:3]:
            print(f"\nCode: {item['code']}")
            print(f"Title: {item['title']}")
            print(f"Coordinator: {item['coordinator_name']}")
            print(f"Email: {item['coordinator_email']}")
    except Exception as e:
        print(f"Error saving to CSV: {e}")

def save_modules_to_json(data, filename='filieres_modules.json'):
    if not data:
        return
    
    try:
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, ensure_ascii=False, indent=4)
        print(f"\nModules data successfully saved to {filename}")
    except Exception as e:
        print(f"Error saving modules to JSON: {e}")

if __name__ == "__main__":
    csv_data, modules_data = get_filieres()
    if csv_data and modules_data:
        save_to_csv(csv_data)
        save_modules_to_json(modules_data)