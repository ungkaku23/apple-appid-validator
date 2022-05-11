from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel

import requests
import json
from bs4 import BeautifulSoup
import pandas as pd
import re
import urllib.parse

# buy_type: rent, sale
# price_min, price_max : -1 default
# home_type: "" default    townhome, apartments, single-family-home
# beds : -1 default
# baths : -1 default

class Item(BaseModel):
    zip_or_location: Optional[str] = None
    page_index: Optional[int] = 1
    buy_type: Optional[str] = None 
    home_type: Optional[str] = None 
    price_min: Optional[int] = -1
    price_max: Optional[int] = -1
    beds: Optional[int] = -1
    baths: Optional[int] = -1

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
        address1 = ""
        try:
            address1 = properties.find("div", {"data-testid" : "card-address-1"}).text
        except:
            address1 = ""

        address2 = ""
        try:
            address2 = properties.find("div", {"data-testid" : "card-address-2"}).text
        except:
            address2 = ""

        address = f'{address1} {address2}'
        city = address2.split(", ")[0]
        state = address2.split(", ")[1].split(" ")[0]
        postal_code = address2.split(", ")[1].split(" ")[1]
        price = ""
        try:
            price = properties.find("div", {"data-testid" : "card-price"}).text
        except:
            price = ""
        
        bedrooms = ""
        try:
            bedrooms = properties.find("li", {"data-testid" : "property-meta-beds"}).find("span").text
        except:
            bedrooms = ""
        
        bathrooms = ""
        try:
            bathrooms = properties.find("li", {"data-testid" : "property-meta-baths"}).find("span").text
        except:
            bathrooms = ""
        
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
    location = item.zip_or_location.replace(" ","-").replace(",",",-") + "_rb"
    url = f"http://api.scraperapi.com?api_key=7cd363bccba24d9d1b8ea9d1b95308a6&url=https://www.zillow.com/homes/{location}/"
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.content, "lxml")

    j = soup.find("script", {"data-zrr-shared-data-key": "mobileSearchPageStore"})

    j_data = str(j).split("--")[1]
    w_json = json.loads(j_data)
    query_state = w_json.get("queryState")

    extra_condition = {
        "pagination": {},
        "usersSearchTerm": query_state["usersSearchTerm"],
        "mapBounds": query_state["mapBounds"],
        "regionSelection": query_state["regionSelection"],
        "isMapVisible": True,
        "filterState": {
            "beds": {
            "min": 0
            },
            "baths": {
            "min": 0
            },
            "fore": {
            "value": False
            },
            "mp": {},
            "ah": {
            "value": True
            },
            "auc": {
            "value": False
            },
            "nc": {
            "value": False
            },
            "fr": {
            "value": False
            },
            "fsbo": {
            "value": False
            },
            "cmsn": {
            "value": False
            },
            "fsba": {
            "value": False
            }
        },
        "isListVisible": True,
        "mapZoom": 13
    }

    if item.price_min != -1 and item.price_max != -1:
        extra_condition["filterState"]["mp"] = {
            "min": item.price_min,
            "max": item.price_max
        }
    if item.price_min == -1 and item.price_max != -1:
        extra_condition["filterState"]["mp"] = {
            "max": item.price_max
        }
    if item.price_min != -1 and item.price_max == -1:
        extra_condition["filterState"]["mp"] = {
            "min": item.price_min
        }

    if item.buy_type == "rent":
        extra_condition["filterState"]["fr"] = {
            "value": True
        }

    if item.home_type == "townhome":
        extra_condition["filterState"]["sf"] = {
            "value": False
        }
        extra_condition["filterState"]["apco"] = {
            "value": False
        }
        extra_condition["filterState"]["apa"] = {
            "value": False
        }
        extra_condition["filterState"]["con"] = {
            "value": False
        }
    if item.home_type == "apartments":
        extra_condition["filterState"]["sf"] = {
            "value": False
        }
        extra_condition["filterState"]["tow"] = {
            "value": False
        }
    if item.home_type == "single-family-home":
        extra_condition["filterState"]["apco"] = {
            "value": False
        }
        extra_condition["filterState"]["apa"] = {
            "value": False
        }
        extra_condition["filterState"]["con"] = {
            "value": False
        }
        extra_condition["filterState"]["tow"] = {
            "value": False
        }
    
    if item.beds != -1:
        extra_condition["filterState"]["beds"] = {
            "min": item.beds
        }
    
    if item.baths != -1:
        extra_condition["filterState"]["baths"] = {
            "min": item.baths
        }

    encoded_url = urllib.parse.quote(json.dumps(extra_condition, separators=(',', ':')), encoding='utf-8')

    url = f"http://api.scraperapi.com?api_key=7cd363bccba24d9d1b8ea9d1b95308a6&url=https://www.zillow.com/homes/1_p?searchQueryState={encoded_url}"

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
        url = f"http://api.scraperapi.com?api_key=7cd363bccba24d9d1b8ea9d1b95308a6&url=https://www.zillow.com/homes/{item.page_index}_p?searchQueryState={encoded_url}"

        r = requests.get(url, headers=headers)
        soup = BeautifulSoup(r.content, "lxml")

        j = soup.find("script", {"data-zrr-shared-data-key": "mobileSearchPageStore"})

        j_data = str(j).split("--")[1]
        w_json = json.loads(j_data)
        
        search_results = w_json.get('cat1').get('searchResults').get('listResults', [])
        for properties in search_results:
            link = properties.get('detailUrl')

            url = f"http://api.scraperapi.com?api_key=7cd363bccba24d9d1b8ea9d1b95308a6&url={link}"
            print(url)
            r = requests.get(url, headers=headers)
            soup = BeautifulSoup(r.content, "lxml")

            try:
                landlord_name = soup.find("span", {"class" : "ds-listing-agent-display-name"}).text
            except:
                landlord_name = ""

            try:
                landlord_company = soup.find("span", {"class" : "ds-listing-agent-business-name"}).text
            except:
                landlord_company = ""

            try:
                landlord_contact = soup.find("li", {"class" : "ds-listing-agent-info-text"}).text
            except:
                landlord_contact = ""

            try:
                imgs = []
                img_containers = soup.findAll("li", {"class" : "media-stream-tile"})
                for img_widget in img_containers:
                    imgs.append(img_widget.find("img")['src'])
            except:
                imgs = []
            
            address = properties.get('address')
            state = properties.get('addressState')
            zipcode = properties.get('addressZipcode')
            landlord_rent = properties.get('price')
            beds = properties.get('beds')
            baths = properties.get('baths')
            square_footage = properties.get('area')

            data = {
                'link': link,
                'address': address,
                'state': state,
                'zipcode': zipcode,
                'landlord_rent': landlord_rent,
                'landlord_name': landlord_name,
                'landlord_company': landlord_company,
                'landlord_contact': landlord_contact,
                'beds': beds,
                'baths': baths,
                'square_footage': square_footage,
                'imgs': imgs
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
    if item.buy_type == "rent":
        base_url = "https://www.realtor.com/apartments"
    
    price_condition = ""
    if item.price_min != -1 and item.price_max != -1:
        price_condition = f"price-{item.price_min}-{item.price_max}/"
    if item.price_min == -1 and item.price_max != -1:
        price_condition = f"price-na-{item.price_max}/"
    if item.price_min != -1 and item.price_max == -1:
        price_condition = f"price-{item.price_min}-na/"

    home_type_condition = ""
    if item.home_type != "":
        home_type_condition = f"type-{item.home_type}/"
    
    beds_condition = ""
    if item.beds != -1:
        beds_condition = f"beds-{item.beds}/"
    
    baths_condition = ""
    if item.baths != -1:
        baths_condition = f"baths-{item.baths}/"

    url = f"http://api.scraperapi.com?api_key=7cd363bccba24d9d1b8ea9d1b95308a6&url={base_url}/{location}/{beds_condition}{baths_condition}{home_type_condition}{price_condition}"
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
        if item.buy_type == "sale":
            if check:
                print(f'Page {item.page_index} of {pages}')
                if (item.page_index) == 1:
                    realtor_data = get_realtor_sale_list(check, realtor_data)
                else:
                    url = f'http://api.scraperapi.com?api_key=7cd363bccba24d9d1b8ea9d1b95308a6&url={base_url}/{location}/{beds_condition}{baths_condition}{home_type_condition}{price_condition}pg-{item.page_index}'
                    r = requests.get(url, headers = headers)
                    soup = BeautifulSoup(r.content,"lxml")
                    check = get_realtor_page_status(soup)
                    realtor_data = get_realtor_sale_list(check, realtor_data)
        else:
            print(f'Page {item.page_index} of {pages}')
            url = f'http://api.scraperapi.com?api_key=7cd363bccba24d9d1b8ea9d1b95308a6&url={base_url}/{location}/{beds_condition}{baths_condition}{home_type_condition}{price_condition}pg-{item.page_index}'
            r = requests.get(url, headers = headers)
            soup = BeautifulSoup(r.content,"lxml")
            realtor_data = get_realtor_rent_list(soup.find_all("div", {"class": "card-content"}), realtor_data)
    
    return {
        'data': realtor_data,
        'number_of_pages': pages,
        'page_index': item.page_index
    }
    