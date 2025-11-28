import time
import json
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service

chromedriver_path = r"E:\chromedriver-win64\chromedriver-win64/chromedriver.exe"
service = Service(executable_path=chromedriver_path)


def plenzo_search(search_term):
    """
    Scrapes the 'Plenzo' source (Slickdeals) for the top 3 deals using Selenium.
    """
    # 1. Setup Search URL
    # Main search URL structure with specific forum choice (9 = Merchant/General)
    base_url = f"https://slickdeals.net/newsearch.php?forumchoice%5B%5D=9&q={search_term}&showposts=0"

    # 2. Configure Headless Chrome
    # These options make the scraper run in the background without opening a visible window.
    # To see the browser work, comment out the '--headless' line.
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    # Using a standard user agent to look like a real browser to prevent blocking
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    print(f"\n--- Welcome to Plenzo ---")
    print(f"Finding the best Black Friday Deal for: '{search_term}'...\n")

    # Initialize the driver (Selenium Manager handles the executable automatically in modern versions)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    results = []

    try:
        driver.get(base_url)
        
        # Wait up to 10 seconds for the 'resultRow' elements to appear
        wait = WebDriverWait(driver, 0)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "resultRow")))

        # 3. Find the first 3 items with class "resultRow"
        # As requested, we look for 'dealImg' and 'dealWrapper' subclasses
        deal_rows = driver.find_elements(By.CLASS_NAME, "resultRow")[:3]

        for index, row in enumerate(deal_rows):
            try:
                # A. Extract Image from subclass "dealImg"
                # The 'dealImg' div usually contains the <img> tag.
                img_container = row.find_element(By.CLASS_NAME, "dealImg")
                img_element = img_container.find_element(By.TAG_NAME, "img")
                
                # Check for lazy-loaded image attributes first
                image_url = img_element.get_attribute("data-original")
                if not image_url:
                    image_url = img_element.get_attribute("src")

                # B. Extract Title and Link from subclass "dealWrapper"
                # The 'dealWrapper' div contains the anchor tag with the title/href.
                wrapper = row.find_element(By.CLASS_NAME, "dealWrapper")
                
                # Usually the first <a> tag inside dealWrapper is the main deal link
                link_element = wrapper.find_element(By.TAG_NAME, "a") 
                
                title = link_element.text.strip()
                # Get the absolute URL (Selenium resolves relative URLs automatically)
                href = link_element.get_attribute("href")

                # Compile the deal object
                deal_obj = {
                    "rank": index + 1,
                    "title": title,
                    "link": href,
                    "imageUrl": image_url
                }
                results.append(deal_obj)

            except Exception as e:
                # If a specific row fails, we log it but continue to the next one
                # This prevents one bad ad/row from breaking the whole script
                # print(f"Skipping a row due to parse error: {e}") 
                continue

    except Exception as e:
        print(f"Error connecting to Plenzo data source: {e}")
    finally:
        # Always close the browser
        driver.quit()

    return results

if __name__ == "__main__":
    # Handle command line arguments or prompt user
    if len(sys.argv) > 1:
        term = " ".join(sys.argv[1:])
    else:
        term = input("Enter item to find deals for: ")
        
    if not term:
        term = "laptop" # Default fallback

    deals = plenzo_search(term)

    # Output the JSON array as requested
    print("\n--- Top 3 Plenzo Deals ---")
    print(json.dumps(deals, indent=2))