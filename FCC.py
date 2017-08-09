import requests
from bs4 import BeautifulSoup

class FCCGeocoder:
    def __init__(self, lat,lng):
        request = "http://data.fcc.gov/api/block/find?latitude="+str(lat)+"&longitude="+str(lng)
        request_content = BeautifulSoup(requests.get(request).content,'xml')
        self.tract = request_content.Block['FIPS'][5:11]
        self.countyName = request_content.County['name']
        self.countyCode = request_content.County['FIPS']
        self.stateName = request_content.State['name']
        self.stateCode = request_content.State['FIPS']
        self.fips = request_content.Block['FIPS']
