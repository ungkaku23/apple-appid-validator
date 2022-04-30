from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel

import requests
import json
from bs4 import BeautifulSoup
import pandas as pd

class Item(BaseModel):
    zip_or_location: Optional[str] = None

app = FastAPI()

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'accept-encoding': 'gzip, deflate, sdch, br',
    'accept-language': 'en-GB,en;q=0.8,en-US;q=0.6,ml;q=0.4',
    'cache-control': 'max-age=0',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36'
}

def get_page_status(soup_obj):
    s = soup_obj.find("script", id = "__NEXT_DATA__").text
    j = json.loads(s)
    try:
        #root - props - pageProps - searchResults - home_search - results
        search_list = j["props"]["pageProps"]["searchResults"]["home_search"]["results"]
    except :
        print("No Property Listing Found")
        exit()
    return search_list

def get_number_of_pages(soup_obj):
    try:
        get_pages = soup_obj.find_all("a", class_ = "item btn")
        #print(get_pages[-2].text)
        pages = int(get_pages[-2].text)
        print(f'Found {pages} Pages')
    except:
        pages = 1
        print("Found 1 Page")
    return pages

def get_list_info(search_results, realtor_data):
    for properties in search_results:
        address = f'{properties["location"]["address"]["line"]} , {properties["location"]["address"]["state"]} , {properties["location"]["address"]["postal_code"]}'
        city = properties["location"]["address"]["city"]
        state = properties["location"]["address"]["state"]
        postal_code = properties["location"]["address"]["postal_code"]
        price = properties["list_price"]
        bedrooms = properties["description"]["beds"]
        bathrooms = properties["description"]["baths"]
        area = properties["description"]["sqft"]
        info = f'{bedrooms} bds, {bathrooms} ba ,{area} sqft'
        # broker = properties.get('brokerName')
        property_url = f'https://www.realtor.com/realestateandhomes-detail/{properties["permalink"]}'
        # title = properties.get('statusText')

        data = {
            'address': address,
            'city': city,
            'state': state,
            'postal_code': postal_code,
            'price': price,
            'facts and features': info,
            # 'real estate provider': broker,
            'url': property_url,
            # 'title': title
        }
        realtor_data.append(data)

    return realtor_data

@app.post("/zillow/")
async def create_item(item: Item):
    zillow_data = []
    location = item.zip_or_location.replace(" ","-")
    url = f"https://www.zillow.com/homes/for_sale/{location}/1_p/?fromHomePage=true&shouldFireSellPageImplicitClaimGA=false&fromHomePageTab=buy"

    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.content, "lxml")
    print(soup.find_all("li", {"aria-current": "page"})[-1])
    pages = soup.find_all("li", {"aria-current": "page"})[-1].text.split("of ")[-1]
    print(f' Found {pages} pages')

    for i in range(int(pages)):
        print(f' Working on {i + 1} of {pages} pages')
        url = f"https://www.zillow.com/homes/for_sale/{location}/{i+1}_p/?fromHomePage=true&shouldFireSellPageImplicitClaimGA=false&fromHomePageTab=buy"

        r = requests.get(url, headers=headers)
        print(url)
        soup = BeautifulSoup(r.content, "lxml")

        j = soup.find("script", {"data-zrr-shared-data-key": "mobileSearchPageStore"})

        j_data = str(j).split("--")[1]
        w_json = json.loads(j_data)
        
        search_results = w_json.get('cat1').get('searchResults').get('listResults', [])
        for properties in search_results:
            address = properties.get('address')
            property_info = properties.get('hdpData', {}).get('homeInfo')
            city = property_info.get('city')
            state = property_info.get('state')
            postal_code = property_info.get('zipcode')
            price = properties.get('price')
            bedrooms = properties.get('beds')
            bathrooms = properties.get('baths')
            area = properties.get('area')
            info = f'{bedrooms} bds, {bathrooms} ba ,{area} sqft'
            broker = properties.get('brokerName')
            property_url = properties.get('detailUrl')
            title = properties.get('statusText')

            data = {
                'address': address,
                'city': city,
                'state': state,
                'postal_code': postal_code,
                'price': price,
                'facts and features': info,
                'real estate provider': broker,
                'url': property_url,
                'title': title
            }

            zillow_data.append(data)

    return zillow_data

@app.post("/realtor/")
async def create_item(item: Item):
    realtor_data = []
    location = item.zip_or_location.replace(" ","-").replace(",","_")
    url = f"https://www.realtor.com/realestateandhomes-search/{location}"
    
    r = requests.get(url, headers = headers)
    soup = BeautifulSoup(r.content,"lxml")
    check = get_page_status(soup)

    #START FETCHING RESULTS 
    check = get_page_status(soup)
    page = get_number_of_pages(soup)
    if check:
        for i in range(page):
            print(f'Page {i + 1} of {page}')
            if i == 0:
                realtor_data = get_list_info(check, realtor_data)
            else:
                url = f'https://www.realtor.com/realestateandhomes-search/{location}/pg-{i + 1}'
                r = requests.get(url, headers = headers)
                soup = BeautifulSoup(r.content,"lxml")
                check = get_page_status(soup)
                realtor_data = get_list_info(check, realtor_data)
    
    return realtor_data
    