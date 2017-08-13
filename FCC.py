import requests
from bs4 import BeautifulSoup
#class is a wrapper for the FCC geocoder API
#Each function gets a different peice of information about the residential address at the given lattitude and longitiude
class FCCGeocoder:
    def __init__(self, lat,lng):
        self.__request = "http://data.fcc.gov/api/block/find?latitude="+str(lat)+"&longitude="+str(lng)
        self.__request_content = BeautifulSoup(requests.get(self.__request).content,'xml')
    def getTract(self):
        return self.__request_content.Block['FIPS'][5:11]
    def getCountyName(self):
        return self.__request_content.County['name']
    def getCountyCode(self):
        return self.__request_content.County['FIPS']
    def getStateName(self):
        return self.__request_content.State['name']
    def getStateCode(self):
        return self.__request_content.State['FIPS']
    def getFIPS(self):
        return self.__request_content.Block['FIPS']
