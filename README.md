# ZillowScraper
Scraper for the search page of Zillow.com, originally made for a Flask web app. <br />
scraper.results takes in the city and state as an argument, and returns a list of cities that:
  <br /> a) Have Days on Zillow availabe without accessing any other pages (e.g. home details)
  <br /> b) Have been on Zillow for more than 30 days
  <br /> c) Are below the median price of the respective housing Tract.
  
  
 Uses the FCC's API to find the census tract from the lattitude and longitude of the house.
