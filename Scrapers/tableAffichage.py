import requests
from bs4 import BeautifulSoup
import csv
import re
import urllib3
from urllib.parse import urljoin

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def clean_text(text):
    """Clean and normalize text."""
    if not text:
        return ""
    # Remove extra whitespace and normalize quotes
    text = " ".join(text.strip().split())
    # Remove any non-printable characters
    text = "".join(char for char in text if char.isprintable())
    return text

def extract_date(date_text):
    """Extract date from text in format DD/MM/YYYY HH:MM."""
    match = re.search(r'Publié le (\d{2}/\d{2}/\d{4}) à (\d{2}:\d{2})', date_text)
    if match:
        return f"{match.group(1)} {match.group(2)}"
    return ""

def extract_filiere_from_title(title):
    """Extract filiere from title text."""
    # Pattern to match filieres like GI1, GC2, TDIA1, etc.
    pattern = r'(?:GI|GC|ID|TDIA|GEER|GEE|GM|AP|CP)[1-3](?:\s+(?:HYD|BPC|GL|BI))?'
    match = re.search(pattern, title, re.IGNORECASE)
    if match:
        return match.group(0).lower()
    return None

def get_tableau_affichage():
    """Fetch and parse articles from tableau d'affichage."""
    base_url = "https://ensah.ma"
    url = f"{base_url}/public/tableauAffichage.php"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        print("Fetching data from tableau d'affichage...")
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        articles = []
        article_items = soup.find_all('div', class_='list-event-item')
        found_count = 0
        
        for item in article_items:
            # Get title
            title_element = item.find('h5', class_='event-title')
            if not title_element or not title_element.find('a'):
                continue
                
            title = clean_text(title_element.find('a').get_text())
            
            # Extract filiere from title
            filiere = extract_filiere_from_title(title)
            if not filiere:
                continue
                
            # Get date and author
            date_element = item.find('span', class_='event-date')
            if not date_element:
                continue
                
            date_text = date_element.get_text()
            author_match = re.search(r'par : (.+)$', date_text)
            
            # Get URL
            url_element = title_element.find('a')
            href = url_element.get('href', '') if url_element else ''
            if href:
                href = urljoin(base_url, href)
            
            article = {
                'title': "titre d'affichage: " + title,
                'date': "date d'affichage: " + extract_date(date_text),
                'author': "cordinateur de filiere : " + clean_text(author_match.group(1)) if author_match else "",
                'filieres': "filiere: " + filiere,
                'url': "lien pour consulter l'article: " + href 
            }
            
            articles.append(article)
            found_count += 1
            print(f"Found matching article ({filiere}): {article['title'][:50]}...")
            
            if found_count >= 20:
                break
                
        return articles
        
    except Exception as e:
        print(f"Error fetching tableau d'affichage: {e}")
        return []

def save_to_csv(data, filename='affichageTable.csv'):
    if not data:
        print("No data to save")
        return
    
    fieldnames = ['title', 'date', 'author', 'filieres', 'url']     
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                cleaned_row = {k: clean_text(str(v)) for k, v in row.items()}
                writer.writerow(cleaned_row)
        print(f"Data saved successfully to {filename}")
    except Exception as e:
        print(f"Error saving to CSV: {e}")

if __name__ == "__main__":
    articles = get_tableau_affichage()
    if articles:
        save_to_csv(articles)