from bs4 import BeautifulSoup
import requests
import json
import re
import time
from selenium import webdriver
import random
import urllib.request
import sys
import pandas as pd
import threading
from math import floor
import locale
from FCC import FCCGeocoder


#This is used to return the results (above 30 days, and below the average home price for the tract)
#Thread1 geocodes the houses that are labeled "Recently Sold" on zillow
#Thread2 geocodes the houses that are labeled "For Sale" on Zillow
def results(city, state, min_price,max_price,forSale=True):
    locale.setlocale(locale.LC_ALL, 'en_US')
    DisplayedListings = []
    PossibleListings = getHomesFromCities(city,state,min_price,max_price,forSale=True)
    SoldHouses = getHomesFromCities(city,state,forSale = False)
    MainThreads = []
    start = time.time()
    thread1 = threading.Thread(target=Geocode,args=(SoldHouses,))
    thread2 = threading.Thread(target=Geocode,args=(PossibleListings,))
    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()
    end=time.time()
    print("Geocoding all addresses took : " + str(end-start))

    SoldFrame = pd.DataFrame(SoldHouses)
    for item in PossibleListings:
        print(item['Days'])
        Area = SoldFrame.loc[SoldFrame['tract']==item['tract']]
        print("Median for Tract is: "+ str(Area['price'].median()))
        print("Price of listing is " + str(item['price']))
        if(len(Area['price']) != 0):
            item['median_area_price'] = int(Area['price'].median())
            if((int(item['price']) < item['median_area_price']) & (int(item['Days'].split(' ')[0])) >= 30):
                item['price'] = locale.format("%d",item['price'],grouping=True)
                item['median_area_price'] = locale.format("%d",item['median_area_price'],grouping=True)
                DisplayedListings.append(item)
            elif(int(item['price']) < item['median_area_price']):
                item['price'] = locale.format("%d",item['price'],grouping=True)
                item['median_area_price'] = locale.format("%d",item['median_area_price'],grouping=True)
                DisplayedListings.append(item)
            elif((int(item['Days'].split(' ')[0])) >= 30):
                item['price'] = locale.format("%d",item['price'],grouping=True)
                item['median_area_price'] = locale.format("%d",item['median_area_price'],grouping=True)
                DisplayedListings.append(item)


    print(len(DisplayedListings))

    return(DisplayedListings)


#This function, as well as GeocodeHelper, manages the threads and geocoding for the scraped listings
def Geocode(SoldHouses) :
    StepSize = floor(len(SoldHouses)/10)
    left = len(SoldHouses) - StepSize
    chunks = [SoldHouses[i:i+StepSize] for i in range(0,len(SoldHouses),StepSize)]

    threads = []
    for i in range(len(chunks)):
        t = threading.Thread(target=GeocodeHelper,args=(chunks[i],SoldHouses,i,StepSize))
        threads.append(t)
        t.start()

    for i in range(len(threads)):
        threads[i].join()



#This function does the actual geocoding (getting the tract from the FCC api)
def GeocodeHelper(Houses,outList,chunks_index,StepSize):
    for i in range(len(Houses)) :
        Lat = Houses[i]['lattitude']
        Long = Houses[i]['longitude']
        tract_long = requests.get("http://data.fcc.gov/api/block/find?latitude="+str(Lat)+"&longitude="+str(Long))
        Long = BeautifulSoup(tract_long.content,'xml').Block
        tract = Long['FIPS'][5:11]
        Houses[i]['tract'] = tract
        outList[StepSize*chunks_index + i]= Houses[i]

#Used for User-Agent spoofing
def chooseHeader():
    HeaderList = [
        {'User-Agent':
            'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'},
        {'User-Agent':
            'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1'},
        {'User-Agent':
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.75.14 (KHTML, like Gecko) Version/7.0.3 Safari/7046A194A'},
        {'User-Agent':
            'Opera/9.80 (X11; Linux i686; Ubuntu/14.10) Presto/2.12.388 Version/12.16'}
    ]
    index = random.randint(0,3)

    return(HeaderList[index])

#Function used to scrape a 'page' of listings on Zillow.com. Gets the address, lattitude, longitude, price,
#and number of days on zillow (if available from the card)
def getHomesHelper(Houses,forSale):
    house_data = {}
    HouseList=[]
    days_on_zillow = None

    for house in Houses:
        address = house.find("span",{'itemprop':"streetAddress"}).text
        postCode = house.find("span",{'itemprop':"postalCode"}).text
        days_on_zillow = house.find('span',{'class':'zsg-photo-card-notification'},text=re.compile('(.*) days on Zillow'))
        if(forSale & (days_on_zillow is None)): continue
        status = house.find('span',{'class':'zsg-photo-card-status'}).text
        if(forSale):
            if(status == 'House For Sale'):
                price = house.find("span",{'class':'zsg-photo-card-price'}).text.strip('$').replace(',','')
            elif(status=='Forclosed'):
                price = house.find("span",{'class':'zsg-photo-card-info'}).text.split(" ")[2].strip('$').replace('K','000').replace('M','0000')
            elif(status=='Lot/Land For Sale'):
                price = house.find("span",{'class':'zsg-photo-card-price'}).text.strip('$').replace(',','')
            else:
                continue

        else:
            price= house.find("span",{'class':'zsg-photo-card-status'}).text.split(' ')[1]
            if(price != '') :
                price = int(price.strip('$').replace(',','').replace('.','').replace("M",'0000'))
            else:
                continue
        Lat = house.find('meta',{'itemprop':'latitude'})['content']
        Long = house.find('meta',{'itemprop':'longitude'})['content']
        if(forSale & (days_on_zillow is not None)):
            house_data = {'address':address,'postalCode':postCode,'price':int(price),'forSale':True,'Days':days_on_zillow.text,
                'lattitude':Lat,'longitude':Long}
        else:
            house_data = {'address':address,'postalCode':postCode,'lattitude':Lat,'longitude':Long,'price':int(price),'forSale':False}

        if(house_data):
            print(address + 'Added')
            HouseList.append(house_data)

    return(HouseList)
#Manages the type of homes to look for (for sale or recently_sold) as well as the number of pages
#to scrape through.
def getHomesFromCities(city,state,min_price=None,max_price=None,days=None,forSale=True):
    city_list = city.split(" ")

    if(forSale):
        zillow_url = "https://www.zillow.com/homes/for_sale/"
        if(len(city_list) == 1):
            zillow_url = zillow_url + city_list[0] + "-" + state

        else:
            for i in range(len(city_list)) :
                zillow_url = zillow_url + city_list[i]+'-'

            zillow_url = zillow_url + state

    else:
        zillow_url = "https://www.zillow.com/homes/recently_sold/"
        if(len(city_list)==1):
            zillow_url = zillow_url+city_list[0]+"-"+state
        else:
            for i in len(city_list) :
                zillow_url = zillow_url+"-"+city_list[i]
            zillow_url= zillow_url+"-"+state


    print(zillow_url)
    head = chooseHeader()
    request=requests.get(zillow_url,headers=head)
    page = BeautifulSoup(request.content,"html.parser")
    page_links = page.findAll('ol',{'class':"zsg-pagination"})
    Home_List=[]
    if(len(page_links) != 0):
        num_pages = page_links[0]('li')
        max_pages = num_pages[len(num_pages) - 2].text
        Houses = page.findAll('article')

        for i in range(int(max_pages)):
            print('Page:')
            print(i)
            if((i + 1) > 1):
                request = requests.get(zillow_url + "/"+ str(i+1) + "_p/",headers=chooseHeader())
                page = BeautifulSoup(request.content,'html.parser')
                Houses = page.findAll("article")
                Home_List+=getHomesHelper(Houses,forSale)
            else:
                Home_List+=getHomesHelper(Houses,forSale)

    else:
        Houses=page.findAll('article')
        Home_List+=getHomesHelper(Houses,forSale)



    return(Home_List)
