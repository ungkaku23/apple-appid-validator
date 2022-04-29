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

@app.post("/zillow/")
async def create_item(item: Item):
    csv_data = []
    headers = {'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'accept-encoding': 'gzip, deflate, sdch, br',
            'accept-language': 'en-GB,en;q=0.8,en-US;q=0.6,ml;q=0.4',
            'cache-control': 'max-age=0',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36'}
    url = f"https://www.zillow.com/homes/for_sale/{item.zip_or_location}/1_p/?fromHomePage=true&shouldFireSellPageImplicitClaimGA=false&fromHomePageTab=buy"

    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.content, "lxml")
    pages = soup.find_all("li", {"aria-current": "page"})[-1].text.split("of ")[-1]
    print(f' Found {pages} pages')

    for i in range(int(pages)):
        print(f' Working on {i + 1} of {pages} pages')
        url = f"https://www.zillow.com/homes/for_sale/{item.zip_or_location}/{i+1}_p/?fromHomePage=true&shouldFireSellPageImplicitClaimGA=false&fromHomePageTab=buy"

        headers = {'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'accept-encoding': 'gzip, deflate, sdch, br',
                'accept-language': 'en-GB,en;q=0.8,en-US;q=0.6,ml;q=0.4',
                'cache-control': 'max-age=0',
                'upgrade-insecure-requests': '1',
                'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36'}

        r = requests.get(url, headers=headers)
        print(url)
        soup = BeautifulSoup(r.content, "lxml")
        #print(soup.find_all("li", {"aria-current":"page"})[-1].text.split("of ")) 

        j = soup.find(
            "script", {"data-zrr-shared-data-key": "mobileSearchPageStore"})

        j_data = str(j).split("--")[1]
        w_json = json.loads(j_data)
        #csv_data = []
        search_results = w_json.get('cat1').get(
            'searchResults').get('listResults', [])
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

            data = {'address': address,
                    'city': city,
                    'state': state,
                    'postal_code': postal_code,
                    'price': price,
                    'facts and features': info,
                    'real estate provider': broker,
                    'url': property_url,
                    'title': title}
            # print(data)
            csv_data.append(data)

    return csv_data