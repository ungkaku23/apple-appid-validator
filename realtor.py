import requests
from bs4 import BeautifulSoup
import json
import pandas as pd


def get_headers():
    headers = {'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                   'accept-encoding': 'gzip, deflate, sdch, br',
                   'accept-language': 'en-GB,en;q=0.8,en-US;q=0.6,ml;q=0.4',
                   'cache-control': 'max-age=0',
                   'upgrade-insecure-requests': '1',
                   'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36'}
    return headers
    
def get_list_info(search_results):
    #print(len(search_results))
    for properties in search_results:
        # print(properties)
        address = f'{properties["location"]["address"]["line"]} , {properties["location"]["address"]["state"]} , {properties["location"]["address"]["postal_code"]}'
        #print(address)
        # property_info = properties.get('hdpData', {}).get('homeInfo')
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

        data = {'address': address,
                'city': city,
                'state': state,
                'postal_code': postal_code,
                'price': price,
                'facts and features': info,
                # 'real estate provider': broker,
                'url': property_url,
                # 'title': title
                }
        #print(data)
        csv_data.append(data)
#checks if property are listed or not
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
        get_pages = soup.find_all("a", class_ = "item btn")
        #print(get_pages[-2].text)
        pages = int(get_pages[-2].text)
        print(f'Found {pages} Pages')
    except:
        pages = 1
        print("Found 1 Page")
    return pages

#init
csv_data = []
ask = input("Please input zipcode or location - ")
filename = f'output {ask}.csv'
url = f'https://www.realtor.com/realestateandhomes-search/{ask.replace(" ","_")}'
r = requests.get(url, headers = get_headers())
soup = BeautifulSoup(r.content,"lxml")

#START FETCHING RESULTS 
check = get_page_status(soup)
page = get_number_of_pages(soup)
if check:
    for i in range(page):
        print(f'Page {i + 1} of {page}')
        if i == 0:
            get_list_info(check)
        else:
            url = f'https://www.realtor.com/realestateandhomes-search/{ask.replace(" ","_")}/pg-{i + 1}'
            r = requests.get(url, headers = get_headers())
            soup = BeautifulSoup(r.content,"lxml")
            check = get_page_status(soup)
            get_list_info(check)
            
print(f"Data is saved to {filename} and {len(csv_data)} Results Found")
#print(len(csv_data))
df = pd.DataFrame(csv_data)
df.to_csv(filename , index=False)