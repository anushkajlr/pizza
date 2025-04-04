import ssl
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from datetime import datetime, timedelta
import requests
# Ensure SSL module is properly loaded
try:
    ssl.create_default_context()
except ImportError:
    print("SSL module is not available. Ensure your Python installation includes SSL support.")
    exit(1)

# URL of the reservation page
RESERVATION_URL = "https://www.tablecheck.com/en/shops/pizza-4ps-in-indiranagar/reserve"

# Set up Selenium WebDriver (Ensure you have ChromeDriver installed)
# CHROMEDRIVER_PATH = '/opt/homebrew/bin/chromedriver'  # Ensure environment compatibility
# service = Service(CHROMEDRIVER_PATH)
service = Service()
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Run in headless mode (no browser UI)
options.add_argument("--disable-gpu")  # Fixes some headless issues
options.add_argument("--no-sandbox")  # Bypass OS security restrictions
options.add_argument("--disable-dev-shm-usage")  # Prevents shared memory issues
options.add_argument("--remote-debugging-port=9222")  # Allow debugging in some environments

try:
    driver = webdriver.Chrome(service=service, options=options)
except OSError as e:
    print(f"OS Error initializing WebDriver: {e}")
    print("Ensure ChromeDriver is correctly installed and executable.")
    print("Try running with different Chrome options or update your ChromeDriver.")
    exit(1)
except Exception as e:
    print(f"Unexpected error initializing WebDriver: {e}")
    exit(1)




def check_reservation(num_adults=4, target_date=None):
    try:
        driver.get(RESERVATION_URL)
        time.sleep(5)

        # Select number of adults
        adults_dropdown = Select(driver.find_element(By.ID, "reservation_num_people_adult"))
        adults_dropdown.select_by_value(str(num_adults))
        time.sleep(2)

        # Determine target date (default: tomorrow)
        if not target_date:
            target_date = (datetime.now() +timedelta(days=5)).strftime("%Y-%m-%d")

        # Set date (bypassing readonly)
        date_input = driver.find_element(By.ID, "reservation_start_date")
        driver.execute_script("arguments[0].removeAttribute('readonly')", date_input)
        date_input.clear()
        date_input.send_keys(target_date)
        date_input.send_keys(Keys.RETURN)
        time.sleep(3)

        # Extract day of month for column match
        day_of_month = str(int(target_date.split("-")[2]))  # "5" from "2025-04-05"

        # Find correct column index in timetable
        day_headers = driver.find_elements(By.CSS_SELECTOR, "#timetable-body td[class^='wday']")
        target_col_index = -1
        for idx, header in enumerate(day_headers):
            try:
                date_num = header.find_element(By.CLASS_NAME, "date-num").text.strip()
                if date_num == day_of_month:
                    target_col_index = idx
                    break
            except:
                continue

        if target_col_index == -1:
            print(f"❌ Could not find {target_date} in the calendar.")
            return

        # Loop over rows to collect available time slots
        available_times = []
        timetable_rows = driver.find_elements(By.CSS_SELECTOR, "tr.timetable-row")
        for row in timetable_rows:
            time_label = row.find_element(By.CLASS_NAME, "time-left").text.strip()
            cells = row.find_elements(By.TAG_NAME, "td")

            if len(cells) > target_col_index:
                cell = cells[target_col_index]
                if "available" in cell.get_attribute("class"):
                    icon = cell.find_element(By.TAG_NAME, "i")
                    if "fa-circle-o" in icon.get_attribute("class"):
                        available_times.append(time_label)

        if available_times:
            print(f"✅ Slots available for {target_date}:")
            for t in available_times:
                print(f" - {t}")
            send_telegram_message(f"Reservation available for {num_adults} adults on {target_date}!\nAvailable times: {', '.join(available_times)}")
        else:
            pass
    except Exception as e:
        print("Error checking reservations:", e)
    finally:
        driver.quit()



BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": text
    }
    response = requests.post(url, data=data)
    print("Message sent!" if response.ok else "Failed to send message")



if __name__ == "__main__":
    check_reservation()