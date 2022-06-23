from selenium import webdriver
from selenium.common import exceptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
import pandas as pd
import time
import os
import re

options = webdriver.ChromeOptions()
#options.headless = True
options.add_argument("--window-size=1920,1080")
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
browser = webdriver.Chrome(options=options)
# browser = webdriver.Chrome('/usr/lib/chromium-browser/chromedriver')
browser.get('https://appleid.apple.com/account')
try:
    app_email = "rdp4099@gmail.com"
    EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")
    if not EMAIL_REGEX.match(app_email):
        print("invalid email")
    else:
        browser.get(browser.current_url)
        wait = WebDriverWait(browser, 25)
        element = wait.until(EC.presence_of_element_located((By.XPATH, "//input[contains(@type, 'email')]")))
        print("Found form")
        
        appid = browser.find_element(By.XPATH, "//input[contains(@type, 'email')]")

        appid.send_keys(app_email)

        appid.send_keys(Keys.RETURN)

        time.sleep(5)

        parent1 = appid.find_element(By.XPATH, "./..")
        parent2 = parent1.find_element(By.XPATH, "./..")

        if parent2.get_attribute("class") == " is-error":
            print("Valide APPID")
        else:
            print("Invalid APPID")
except TimeoutException:
    print("Not found form")