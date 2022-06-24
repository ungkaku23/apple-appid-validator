from pickle import TRUE
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from selenium import webdriver
from selenium.common import exceptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
import time
import os
import re

chrome_options = webdriver.ChromeOptions()
#options.headless = True 
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--no-sandbox")
chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
browser = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options)

class Item(BaseModel):
    appid: Optional[str] = ""

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'accept-encoding': 'gzip, deflate, sdch, br',
    'accept-language': 'en-GB,en;q=0.8,en-US;q=0.6,ml;q=0.4',
    'cache-control': 'max-age=0',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36'
}

@app.post("/appid-validator/")
async def search_realtor(item: Item):
    browser.get('https://appleid.apple.com/account')
    try:
        app_email = item.appid
        EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")
        if not EMAIL_REGEX.match(app_email):
            print("invalid email format")
            return {
                'result': 'email format error, please submit valid email address'
            }
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
                return {
                    'result': 'valid'
                }
            else:
                print("Invalid APPID")
                return {
                    'result': 'invalid'
                }
    except TimeoutException:
        print("Not found form")
        return {
            'result': 'network connection timeout, please try again'
        }
