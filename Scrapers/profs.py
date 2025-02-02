import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import csv
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def clean_text(text):
    if not text:
        return ""
    text = text.strip()
    text = text.replace('\xa0', ' ')
    text = text.replace('\n', ' ')
    text = ' '.join(text.split())
    return text

def get_professors_data():
    base_url = "https://ensah.ma/apps/eservices"
    login_url = f"{base_url}/index.php"
    search_url = "https://ensah.ma/apps/eservices/internal/members/etudiant/recherchePersonnel.php"
    
    chrome_options = Options()
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--ignore-ssl-errors')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    driver = None
    try:
        print("Initializing Chrome driver...")
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(30)
        
        print("Accessing login page...")
        driver.get(login_url)
        time.sleep(2)  
        print("Filling login credentials...")
        username_field = driver.find_element(By.ID, 'login_username')
        password_field = driver.find_element(By.ID, 'login_password')
        
        username_field.send_keys('E142083821')
        password_field.send_keys('Azer1234*')
        time.sleep(3)  
        
        print("Submitting login form...")
        submit_button = driver.find_element(By.CSS_SELECTOR, 'button.btn.btn-primary.btn-user.btn-block[type="submit"]')
        submit_button.click()
        time.sleep(3) 
        print("Handling reCAPTCHA...")
        frames = driver.find_elements(By.TAG_NAME, "iframe")
        recaptcha_frame = None
        for frame in frames:
            if "recaptcha" in frame.get_attribute("src").lower():
                recaptcha_frame = frame
                break
        
        if not recaptcha_frame:
            print("reCAPTCHA frame not found!")
            return None
        
        driver.switch_to.frame(recaptcha_frame)
        
        print("Clicking reCAPTCHA checkbox...")
        checkbox = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "recaptcha-anchor"))
        )
        checkbox.click()
        time.sleep(2) 
        driver.switch_to.default_content()
        time.sleep(3)  
        print("Current URL after login:", driver.current_url)
        
        if 'Déconnexion' not in driver.page_source:
            print("Login failed!")
            print("Page source preview:", driver.page_source[:500])
            return None
            
        print("Login successful!")
        
        print("\nNavigating to personnel search page...")
        driver.get(search_url)
        time.sleep(3) 
        if 'recherchePersonnel' not in driver.current_url:
            print("Failed to access personnel search page!")
            print("Current URL:", driver.current_url)
            return None
        
        print("Successfully accessed personnel search page")
        
        print("Performing search...")
        search_buttons = driver.find_elements(By.CSS_SELECTOR, 'input[type="submit"]')
        if search_buttons:
            search_buttons[0].click()
            time.sleep(2)  
        else:
            print("Search button not found!")
            return None
        
        table = driver.find_element(By.ID, 'tableAffichage')
        if not table:
            print("Results table not found!")
            return None
        
        professors_data = []
        rows = table.find_elements(By.TAG_NAME, 'tr')[1:]  
        print(f"\nFound {len(rows)} rows in the table")
        
        for row in rows:
            try:
                cols = row.find_elements(By.TAG_NAME, 'td')
                if len(cols) >= 4:
                    nom = clean_text(cols[0].text)
                    prenom = clean_text(cols[1].text)
                    email = clean_text(cols[2].text)
                    
                    photo_url = ""
                    try:
                        img = cols[3].find_element(By.TAG_NAME, 'img')
                        photo_url = img.get_attribute('src')
                        if not photo_url.startswith('http'):
                            photo_url = f"{base_url}/{photo_url.lstrip('/')}"
                    except:
                        pass
                    
                    professor = {
                        'nom': nom,
                        'prenom': prenom,
                        'email': email,
                        'photo_url': photo_url
                    }
                    professors_data.append(professor)
            except Exception as e:
                print(f"Error processing row: {str(e)}")
                continue
        
        return professors_data
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return None
    
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def save_to_csv(data, filename='profs_data.csv'):
    if not data:
        return
    
    fieldnames = ['nom', 'prenom', 'email', 'photo_url']
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        print(f"\nData successfully saved to {filename}")
        
        print("\nProfessors Preview:")
        for item in data[:3]:  
            print(f"\nNom: {item['nom']}")
            print(f"Prénom: {item['prenom']}")
            print(f"Email: {item['email']}")
            print(f"Photo URL: {item['photo_url']}")
            
    except Exception as e:
        print(f"Error saving to CSV: {e}")



if __name__ == "__main__":
    print("Fetching professors data...")
    professors_data = get_professors_data()
    
    if professors_data:
        save_to_csv(professors_data)
        save_to_json(professors_data)
        print(f"\nTotal professors found: {len(professors_data)}")