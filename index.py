from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel

import requests
import json
from bs4 import BeautifulSoup
import pandas as pd

# home_type: rent, sale (for zillow)

class Item(BaseModel):
    zip_or_location: Optional[str] = None
    page_index: Optional[int] = 1
    home_type: Optional[str] = None 

app = FastAPI()

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'accept-encoding': 'gzip, deflate, sdch, br',
    'accept-language': 'en-GB,en;q=0.8,en-US;q=0.6,ml;q=0.4',
    'cache-control': 'max-age=0',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36'
}

def get_realtor_page_status(soup_obj):
    s = soup_obj.find("script", id = "__NEXT_DATA__").text
    j = json.loads(s)
    try:
        #root - props - pageProps - searchResults - home_search - results
        search_list = j["props"]["pageProps"]["searchResults"]["home_search"]["results"]
    except KeyError:
        print("No Property Listing Found")
        search_list = []
    return search_list

def get_realtor_number_of_pages(soup_obj):
    try:
        get_pages = soup_obj.find_all("a", class_ = "item btn")
        #print(get_pages[-2].text)
        pages = int(get_pages[-2].text)
        print(f'Found {pages} Pages')
    except:
        pages = 1
        print("Found 1 Page")
    return pages

def get_realtor_sale_list(search_results, realtor_data):
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
        property_url = f'http://api.scraperapi.com?api_key=7cd363bccba24d9d1b8ea9d1b95308a6&url=https://www.realtor.com/realestateandhomes-detail/{properties["permalink"]}'
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

def get_realtor_rent_list(search_results, realtor_data):
    for properties in search_results:
        address = f'{properties.find("div", {"data-testid" : "card-address-1"}).text} {properties.find("div", {"data-testid" : "card-address-2"}).text}'
        city = properties.find("div", {"data-testid" : "card-address-2"}).text.split(", ")[0]
        state = properties.find("div", {"data-testid" : "card-address-2"}).text.split(", ")[1].split(" ")[0]
        postal_code = properties.find("div", {"data-testid" : "card-address-2"}).text.split(", ")[1].split(" ")[1]
        price = properties.find("div", {"data-testid" : "card-price"}).text
        bedrooms = properties.find("li", {"data-testid" : "property-meta-beds"}).find("span").text
        bathrooms = properties.find("li", {"data-testid" : "property-meta-baths"}).find("span").text
        area = ""
        try:
            area = properties.find("li", {"data-testid" : "property-meta-sqft"}).find("span", {"data-testid" : "meta-value"}).text
        except:
            area = ""
        
        info = f'{bedrooms} bds, {bathrooms} ba ,{area} sqft'
        # broker = properties.get('brokerName')
        property_url = f'http://api.scraperapi.com?api_key=7cd363bccba24d9d1b8ea9d1b95308a6&url=https://www.realtor.com{properties.find("a", {"data-testid" : "card-link"}).get("href")}'
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

def get_zillow_number_of_pages(soup_obj):
    try:
        pages = int(soup_obj.find_all("li", {"aria-current": "page"})[-1].text.split("of ")[-1])
        print(f'Found {pages} Pages')
    except:
        pages = 1
        print("Found 1 Page")
    return pages

@app.post("/zillow/")
async def search_zillow(item: Item):
    zillow_data = []
    location = item.zip_or_location.replace(" ","-").replace(",","_")
    url = f"http://api.scraperapi.com?api_key=7cd363bccba24d9d1b8ea9d1b95308a6&url=https://www.zillow.com/homes/for_{item.home_type}/{location}/1_p"

    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.content, "lxml")
    
    pages = get_zillow_number_of_pages(soup)
    print(f' Found {pages} pages')

    if item.page_index <= 0:
        return {
            'data': [],
            'number_of_pages': pages,
            'page_index': item.page_index
        }

    if item.page_index <= pages:
        print(f' Working on {item.page_index} of {pages} pages')
        url = f"http://api.scraperapi.com?api_key=7cd363bccba24d9d1b8ea9d1b95308a6&url=https://www.zillow.com/homes/for_{item.home_type}/{location}/{item.page_index}_p"

        r = requests.get(url, headers=headers)
        soup = BeautifulSoup(r.content, "lxml")

        j = soup.find("script", {"data-zrr-shared-data-key": "mobileSearchPageStore"})

        j_data = str(j).split("--")[1]
        w_json = json.loads(j_data)
        
        search_results = w_json.get('cat1').get('searchResults').get('listResults', [])
        for properties in search_results:
            # print(properties)
            address = properties.get('address')
            city = properties.get('addressCity')
            state = properties.get('addressState')
            postal_code = properties.get('addressZipcode')
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

    return {
        'data': zillow_data,
        'number_of_pages': pages,
        'page_index': item.page_index
    }

@app.post("/realtor/")
async def search_realtor(item: Item):
    realtor_data = []
    location = item.zip_or_location.replace(" ","-").replace(",","_")
    base_url = "https://www.realtor.com/realestateandhomes-search"
    if item.home_type == "rent":
        base_url = "https://www.realtor.com/apartments"

    url = f"http://api.scraperapi.com?api_key=7cd363bccba24d9d1b8ea9d1b95308a6&url={base_url}/{location}"
    print(url)
    
    r = requests.get(url, headers = headers)
    soup = BeautifulSoup(r.content,"lxml")

    #START FETCHING RESULTS 
    check = get_realtor_page_status(soup)
    pages = get_realtor_number_of_pages(soup)
    
    if item.page_index <= 0:
        return {
            'data': [],
            'number_of_pages': pages,
            'page_index': item.page_index
        }

    if item.page_index <= pages:
        if item.home_type == "sale":
            if check:
                print(f'Page {item.page_index} of {pages}')
                if item.page_index == 1:
                    realtor_data = get_realtor_sale_list(check, realtor_data)
                else:
                    url = f'http://api.scraperapi.com?api_key=7cd363bccba24d9d1b8ea9d1b95308a6&url={base_url}/{location}/pg-{item.page_index}'
                    r = requests.get(url, headers = headers)
                    soup = BeautifulSoup(r.content,"lxml")
                    check = get_realtor_page_status(soup)
                    realtor_data = get_realtor_sale_list(check, realtor_data)
        else:
            url = f'http://api.scraperapi.com?api_key=7cd363bccba24d9d1b8ea9d1b95308a6&url={base_url}/{location}/pg-{item.page_index}'
            r = requests.get(url, headers = headers)
            soup = BeautifulSoup(r.content,"lxml")
            realtor_data = get_realtor_rent_list(soup.find_all("div", {"class": "card-content"}), realtor_data)
    
    return {
        'data': realtor_data,
        'number_of_pages': pages,
        'page_index': item.page_index
    }
    