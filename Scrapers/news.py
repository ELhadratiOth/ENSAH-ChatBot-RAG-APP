import requests
from bs4 import BeautifulSoup
import re
import csv
from datetime import datetime
import urllib3

# Disable SSL warnings
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

def map_category(category):
    category_mapping = {
        'cond': 'condoléance',
        'event-2': 'evenement',
        'recrut': 'recrutement'
    }
    return category_mapping.get(category, category)

def clean_url(url):
    if not url:
        return ""
    
    url = re.sub(r'\.\./', '', url)
    
    if 'newsDetails.php' in url:
        match = re.search(r'public/newsDetails\.php\?.*$', url)
        if match:
            path = match.group(0)
            return f"https://ensah.ma/{path}"
    
    if not url.startswith('http'):
        url = f"https://ensah.ma/{url.lstrip('/')}"
    
    return url

def get_article_content(url):
    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        content_div = soup.find('div', class_="box-content-inner clearfix")
        if not content_div:
            return "", {}, {}
            
        # Get all text content including links
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
        print(f"Error fetching article content: {e}")
        return "", {}, {}

def get_ensah_news():
    url = "https://ensah.ma/public/actualiteGrdPub.php"
    
    structured_data = []
    
    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        news_articles = soup.find_all('div', class_="list-event-item")
        
        for article in news_articles:
            content_box = article.find('div', class_="box-content-inner")
            if not content_box:
                continue
                
            img = content_box.find('img')
            category = img['src'].split('/')[-1].split('.')[0] if img else ""
            category = clean_text(category)
            category = map_category(category)
            
            date_div = content_box.find('span', class_="event-date")
            date_text = extract_date(date_div.get_text()) if date_div else ""
            
            title_elem = content_box.find('h5', class_="event-title")
            if title_elem and title_elem.find('a'):
                title = clean_text(title_elem.find('a').get_text())
                link = clean_url(title_elem.find('a').get('href', ''))
                
                if title and date_text and link:
                    content, pdf_links, img_links = get_article_content(link)
                    
                    pdf_links_str = '; '.join([f"{k}: {v}" for k, v in pdf_links.items()])
                    img_links_str = '; '.join([f"{k}: {v}" for k, v in img_links.items()])
                    
                    structured_data.append({
                        'category': "categorie d'article " + category,
                        'title': "titre de l'article " + title,
                        'date': "date de l'article " + date_text,
                        'link': "le lien de l'article " + link,
                        'description': "description de l'article " + content if content else "",
                        'pdf_links': "liens PDF " + pdf_links_str if pdf_links else "",
                        'img_links': "liens images " + img_links_str if img_links else ""
                    })
        
        return structured_data
    
    except requests.RequestException as e:
        print(f"An error occurred during the request: {e}")
        return None
    except Exception as e:
        print(f"An error occurred while parsing: {e}")
        return None

def save_to_csv(data, filename='news_data.csv'):
    if not data:
        return
    
    fieldnames = ['category', 'title', 'date', 'link', 'description', 'pdf_links', 'img_links']
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writerows(data)
        print(f"\nData successfully saved to {filename}")
        print("\nNews Preview:")
        for item in data[:3]:
            print(f"\nCategory: {item['category']}")
            print(f"Title: {item['title']}")
            print(f"Date: {item['date']}")
            print(f"Link: {item['link']}")
            if item['pdf_links']:
                print(f"PDF Links: {item['pdf_links']}")
            if item['img_links']:
                print(f"Image Links: {item['img_links']}")
    except Exception as e:
        print(f"Error saving to CSV: {e}")

if __name__ == "__main__":
    content = get_ensah_news()
    
    if content:
        save_to_csv(content)