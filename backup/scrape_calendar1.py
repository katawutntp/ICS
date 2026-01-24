from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
import re

options = webdriver.ChromeOptions()
options.add_argument("--headless")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

driver.get("https://www.devillegroups.com/allcalendar/?s=1758")
time.sleep(8)

results = []

# ===== ดึง iframe ทั้งหมด =====
iframes = driver.find_elements(By.TAG_NAME, "iframe")
print("จำนวน iframe:", len(iframes))

for iframe in iframes:
    src = iframe.get_attribute("src")

    if "cld.php" not in src:
        continue

    # ===== ดึง hId จาก src =====
    match = re.search(r"hId=(\d+)", src)
    h_id = match.group(1) if match else "unknown"

    house_name = f"Villa ID {h_id}"

    # ===== เข้า iframe =====
    driver.switch_to.frame(iframe)
    time.sleep(1)

    try:
        # ===== เดือน =====
        month = driver.find_element(
            By.XPATH,
            "//*[contains(text(),'256')]"
        ).text.strip()

        # ===== ช่องที่ติดจอง (สีแดง) =====
        booked_cells = driver.find_elements(
            By.XPATH,
            "//*[contains(@class,'red') or contains(@class,'book')]"
        )

        for cell in booked_cells:
            day = cell.text.strip()
            if day.isdigit():
                results.append({
                    "ชื่อบ้าน": house_name,
                    "เดือน": month,
                    "วันที่": int(day),
                    "สถานะ": "ติดจอง"
                })

    except Exception as e:
        print("ERROR in iframe:", src, e)

    driver.switch_to.default_content()

driver.quit()

df = pd.DataFrame(results)
df.to_csv("booking_result.csv", index=False, encoding="utf-8-sig")

print(df)
