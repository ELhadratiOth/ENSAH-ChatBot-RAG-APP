import requests
from bs4 import BeautifulSoup
import re
import csv
from datetime import datetime
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('\xa0', ' ')
    text = text.replace('\u200b', '')
    text = re.sub(r'&[a-zA-Z]+;', ' ', text)
    text = re.sub(r'[^\w\s.,!?()-]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_date(date_text):
    match = re.search(r'Publié le (\d{2}/\d{2}/\d{4}) à (\d{2}:\d{2})', date_text)
    if match:
        return f"{match.group(1)} {match.group(2)}"
    return date_text

def clean_url(url):
    if not url:
        return ""
    
    url = re.sub(r'\.\./', '', url)
    
    # Remove any duplicate domains or paths
    url = url.replace('ensah.ma/ensah.ma', 'ensah.ma')
    url = url.replace('//public', '/public')
    url = url.replace('//files', '/files')
    
    # Handle article links
    if 'newsDetails.php' in url:
        if 'idNews=' in url:
            news_id = re.search(r'idNews=(\d+)', url)
            if news_id:
                return f"https://ensah.ma/public/newsDetails.php?idNews={news_id.group(1)}"
    
    # Handle file links (images and PDFs)
    if '/files/news/' in url or url.endswith(('.jpg', '.jpeg', '.pdf', '.png')):
        file_name = url.split('/')[-1]
        return f"https://ensah.ma/files/news/{file_name}"
    
    # Default case
    if not url.startswith('http'):
        url = f"https://ensah.ma/{url.lstrip('/')}"
    
    return url

def get_activity_content(url):
    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        content_div = soup.find('div', class_="box-content-inner clearfix")
        if not content_div:
            return "", {}, {}
            
        text_content = ""
        pdf_links = {}
        img_links = {}
        
        for p in content_div.find_all('p'):
            for element in p.children:
                if isinstance(element, str):
                    text_content += clean_text(element) + " "
                elif element.name == 'a':
                    href = element.get('href', '')
                    if href:
                        if href.endswith('.pdf'):
                            pdf_name = clean_text(element.get_text()) or "Document PDF associée"
                            pdf_link = clean_url(href)
                            if pdf_link:
                                pdf_links[pdf_name] = pdf_link
                        else:
                            text_content += clean_text(element.get_text()) + " " + href + " "
            text_content += "\n"
            
        img_tags = content_div.find_all('img')
        for img in img_tags:
            img_name = img.get('alt', '') or "Image"
            img_src = img.get('src', '')
            if img_src and not img_src.endswith('.png'): 
                img_src = clean_url(img_src)
                if img_src:
                    img_links[clean_text(img_name)] = img_src
                    
        text_content = ' '.join(line.strip() for line in text_content.split('\n') if line.strip())
                
        return text_content, pdf_links, img_links
        
    except Exception as e:
        print(f"Error fetching activity content: {e}")
        return "", {}, {}

def get_scientific_activities():
    url = "https://ensah.ma/public/activitesScientifiques.php"
    
    structured_data = []
    
    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        activity_articles = soup.find_all('div', class_="list-event-item")
        
        for article in activity_articles:
            content_box = article.find('div', class_="box-content-inner")
            if not content_box:
                continue
                

            
            date_div = content_box.find('span', class_="event-date")
            date_text = extract_date(date_div.get_text()) if date_div else ""
            
            title_elem = content_box.find('h5', class_="event-title")
            if title_elem and title_elem.find('a'):
                title = clean_text(title_elem.find('a').get_text())
                link = clean_url(title_elem.find('a').get('href', ''))
                
                if title and date_text and link:
                    content, pdf_links, img_links = get_activity_content(link)
                    
                    pdf_links_str = '; '.join([f"{k}: {v}" for k, v in pdf_links.items()])
                    img_links_str = '; '.join([f"{k}: {v}" for k, v in img_links.items()])
                    
                    structured_data.append({
                        'title': "titre de l'activité scientifique " + title,
                        'date': "date de l'activité " + date_text,
                        'link': "le lien de l'activité " + link,
                        'description': "description de l'activité " + content if content else "",
                        'pdf_links':  pdf_links_str if pdf_links_str else "",
                        'img_links': img_links_str if img_links_str else ""
                    })
        
        return structured_data
    
    except requests.RequestException as e:
        print(f"An error occurred during the request: {e}")
        return None
    except Exception as e:
        print(f"An error occurred while parsing: {e}")
        return None

def save_to_csv(data, filename='scientific_activities.csv'):
    if not data:
        return
    
    fieldnames = ['title', 'date', 'link', 'description', 'pdf_links', 'img_links']
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writerows(data)
        print(f"\nData successfully saved to {filename}")
        print("\nActivities Preview:")
        for item in data[:3]:
            print(f"\nTitle: {item['title']}")
            print(f"Date: {item['date']}")
            print(f"Link: {item['link']}")
            if item['pdf_links']:
                print(f"PDF Links: {item['pdf_links']}")
            if item['img_links']:
                print(f"Image Links: {item['img_links']}")
    except Exception as e:
        print(f"Error saving to CSV: {e}")

if __name__ == "__main__":
    content = get_scientific_activities()
    if content:
        save_to_csv(content)