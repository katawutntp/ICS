from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
import re
from datetime import datetime
from dateutil.relativedelta import relativedelta

# ===== CONFIG =====
MONTH_TO_SCRAPE = 3   # 👈 จำนวนเดือนที่ต้องการ
MAX_HOUSES =   0     # 👈 จำนวนบ้านที่ต้องการดึง (0 = ทั้งหมด)
URL = "https://www.devillegroups.com/allcalendar/?s=1758"
BASE_IFRAME_URL = "https://www.devillegroups.com/allcalendar/cld.php"
# ==================

options = webdriver.ChromeOptions()
options.add_argument("--headless")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

# ===== เข้าหน้าหลักเพื่อดึงรายชื่อบ้านทั้งหมด =====
print("🔄 กำลังโหลดหน้าหลัก...")
driver.get(URL)
time.sleep(8)

results = []

# ===== ดึงข้อมูลบ้านทั้งหมดจาก HTML =====
html = driver.page_source

# หา pattern: <h6>(DV-xxxx)<br>ชื่อบ้าน</h6>...<iframe src="cld.php?hId=xxxx"
pattern = r'<h6>\(DV-(\d+)\)<br>([^<]+)</h6>.*?src="cld\.php\?hId=(\d+)"'
matches = re.findall(pattern, html, re.DOTALL)

houses = []
seen_ids = set()  # เก็บ hId ที่เจอแล้วเพื่อไม่ให้ซ้ำ

for dv_id, name, h_id in matches:
    if h_id in seen_ids:
        print(f"  ⚠️ ข้าม (ซ้ำ): hId={h_id}")
        continue
    seen_ids.add(h_id)
    
    house_name = name.strip()
    houses.append({
        'id': h_id,
        'name': house_name,
        'dv_code': f'DV-{dv_id}'
    })
    print(f"  🏠 พบบ้าน: {house_name} (DV-{dv_id}, hId={h_id})")

print(f"\n📊 พบบ้านทั้งหมด: {len(houses)} หลัง")

if not houses:
    print("❌ ไม่พบข้อมูลบ้าน")
    driver.quit()
    exit()

# จำกัดจำนวนบ้านถ้าตั้งค่าไว้
if MAX_HOUSES > 0:
    houses = houses[:MAX_HOUSES]
    print(f"🔧 จำกัดดึงแค่ {MAX_HOUSES} หลังแรก")

# ===== วนดึงข้อมูลแต่ละบ้าน =====
start_date = datetime.now()
total_houses = len(houses)

for house_idx, house in enumerate(houses, 1):
    h_id = house['id']
    house_name = house['name']
    dv_code = house['dv_code']
    
    print(f"\n{'='*50}")
    print(f"🏠 [{house_idx}/{total_houses}] กำลังดึง: {house_name} ({dv_code})")
    print(f"{'='*50}")
    
    for i in range(MONTH_TO_SCRAPE):
        try:
            target_date = start_date + relativedelta(months=i)
            ym = target_date.strftime("%Y-%m")
            calendar_url = f"{BASE_IFRAME_URL}?ym={ym}&hId={h_id}"
            
            driver.get(calendar_url)
            time.sleep(2)  # รอให้ AJAX โหลดข้อมูล booking

            wait = WebDriverWait(driver, 10)

            # ===== อ่านชื่อเดือน =====
            try:
                month_el = wait.until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//th[contains(text(),'256') or contains(text(),'257')]")
                    )
                )
                month_text = month_el.text.strip()
                # แยกเอาเฉพาะบรรทัดที่มีเดือน
                for line in month_text.split("\n"):
                    if "256" in line or "257" in line:
                        month_text = line.strip()
                        break
            except:
                month_text = ym
            
            # ===== ดึงวันที่ติดจอง (สีแดง = booking) =====
            booked_cells = driver.find_elements(
                By.XPATH,
                "//td[contains(@class,'booking') or contains(@style,'red')]"
            )

            booked_count = 0
            booked_days = []  # เก็บวันที่ติดจอง
            for cell in booked_cells:
                day = cell.text.strip()
                if day.isdigit():
                    booked_days.append(int(day))
                    results.append({
                        "ชื่อบ้าน": house_name,
                        "รหัส": dv_code,
                        "เดือน": month_text,
                        "วันที่": int(day),
                        "สถานะ": "ติดจอง"
                    })
                    booked_count += 1
            
            # แสดงวันที่ที่ดึงได้
            if booked_days:
                days_str = ', '.join(map(str, sorted(booked_days)))
                print(f"  📅 {month_text}: {booked_count} วัน → [{days_str}]")
            else:
                print(f"  📅 {month_text}: ว่าง ✓")

        except Exception as e:
            print(f"  ⛔ Error ({ym}): {e}")

driver.quit()

# ===== Export =====
df = pd.DataFrame(results)
df.to_csv("booking_result.csv", index=False, encoding="utf-8-sig")

print(f"\n{'='*50}")
print(f"✅ เสร็จสิ้น!")
print(f"📊 รวมข้อมูล: {len(results)} รายการ จาก {len(houses)} บ้าน")
print(f"💾 บันทึกไฟล์: booking_result.csv")
print(f"{'='*50}")
print(df.head(20))
