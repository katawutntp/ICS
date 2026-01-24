from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import re

options = webdriver.ChromeOptions()
options.add_argument('--headless')
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get('https://www.devillegroups.com/allcalendar/?s=1758')
time.sleep(8)

# Save HTML for inspection
html = driver.page_source
with open('page_structure.html', 'w', encoding='utf-8') as f:
    f.write(html)

# หา iframes ทั้งหมด
iframes = driver.find_elements(By.TAG_NAME, 'iframe')
print(f'Found {len(iframes)} iframes total')

# หาชื่อบ้านจาก parent elements
houses = []
for i, iframe in enumerate(iframes):
    src = iframe.get_attribute('src') or ''
    if 'cld.php' in src:
        match = re.search(r'hId=(\d+)', src)
        if match:
            h_id = match.group(1)
            houses.append({'id': h_id, 'src': src})
            print(f'  [{i}] hId={h_id}')

print(f'\nTotal calendar iframes: {len(houses)}')
driver.quit()
