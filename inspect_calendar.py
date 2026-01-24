from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

options = webdriver.ChromeOptions()
options.add_argument("--headless")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get("https://www.devillegroups.com/allcalendar/?s=1758")
time.sleep(8)

iframes = driver.find_elements(By.TAG_NAME, "iframe")
for iframe in iframes:
    src = iframe.get_attribute("src")
    if src and "cld.php" in src:
        print("Found iframe:", src)
        driver.switch_to.frame(iframe)
        break

html = driver.page_source
with open("calendar_html.txt", "w", encoding="utf-8") as f:
    f.write(html)
print("Saved to calendar_html.txt")
driver.quit()
