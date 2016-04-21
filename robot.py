import requests
from bs4 import BeautifulSoup
import json
from const import *
import asyncio
import aiohttp
from itertools import tee, islice

class City(object):
    def __init__(self, json_data):
        self.name = json_data['n']
        self.time = json_data['u']
        self.cid = json_data['x']
        self.pm25 = json_data['a']
        self.lat = json_data['g'][0]
        self.lng = json_data['g'][1]
        self.detail_data = {'pm25': self.pm25}

    def set_detail(self, detail_data):
        self.detail_data.update(detail_data)
        self.__dict__.update(detail_data)

def getCities():
    i = 0
    city_list = []
    while 1:
        r = requests.get(city_list_base_url + str(i))
        data = json.loads(r.text)
        for c in data['cities']:
            if isinstance(c['x'], int) and c['x'] >= 0:
                city_list.append(City(c))

        if len(data['cities']) == 0:
            return city_list
        i += 1

def uploadCities(city_list):
    for i, city in enumerate(city_list):
        print(i)
        content = "|".join([city.name, city.time, json.dumps(city.detail_data), str(city.cid)])
        payload = {"robot_id": robot_id, "lat": city.lat, "lng": city.lng, "content": content}
        r = requests.post(robot_id, data=payload)
        if r.status_code != 200:
            print(payload)

def getCityDetail(url):
    data = {}
    r = requests.get(url)
    soup = BeautifulSoup(r.text)
    for elem in soup.select(".tdcur"):
        try:
            name = detail_mapping[elem['id']]
            data[name] = elem.text
        except KeyError:
            pass
    return data

@asyncio.coroutine
def setCitiesDetail(city_list):
    count = 0
    for city in city_list:
        print(city.cid)
        r = yield from aiohttp.request("GET", detail_base_url + str(city.cid), headers=req_header)
        r_text = yield from r.read()
        soup = BeautifulSoup(r_text)
        detail_url = soup.select("a")[0]['href']
        detail_data = getCityDetail(detail_url)
        city.set_detail(detail_data)
        count += 1
        # print(city.cid, "end")
    print("c:", count)


def main():
    city_list = getCities()
    co_num = 100
    ll = [list(islice(it, i, None, co_num)) for i, it in enumerate(tee(city_list, co_num))]
    co = [
        setCitiesDetail(l) for l in ll
    ]
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait(co))
    pass

if __name__ == "__main__":
    main()
