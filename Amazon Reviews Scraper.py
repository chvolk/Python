# -*- coding: utf-8 -*-
#Gonna need html for parsing source code   
from lxml import html
#Need JSON for loading old data if you want to (or saving data to a json)  
import json
#Requests is amazing for loading source code from a site quickly
import requests
#This is just an annoying warning that I wanted to suppress in this code
from requests.packages.urllib3.exceptions import InsecureRequestWarning
#Need this for talking to a Postgres DB
import psycopg2
#Need this for converting written dates to something usable in code
from dateutil import parser as dateparser
#Use this to have the code wait for a while when you need it to
from time import sleep
#Selenium is the most powerful tool here. Used for web testing and browsing
from selenium import webdriver
#Regex is amazing. You'll need it all the time for parsing and cleaing text
import re
#BeautifulSoup is the best tool for parsing HTML
from bs4 import BeautifulSoup as BS
#This is the python debugger add a 'pdb.set_trace()' wherever your code is breaking to find out what is wrong
import pdb
#Great tool for sentiment analysis
from textblob import TextBlob
#Tool for adding a random user agent to a webdriver
from fake_useragent import UserAgent
#Used to get command line arguments (among many other uses). In this case, used to get an Amazon search term as a command line arg
import sys


def get_search_term():
    """
    gets the Amazon search term from a command line argu
    """
    try:
        args = sys.argv[1:]
        search_term = ''
        for arg in args:
            try:
                search_term = search_term + arg + ' '
            except Exception as e:
                print(e)
                break
        search_term = search_term.replace(' ', '+').strip()
    except Exception as e:
        search_term = None
    return search_term

def postgres_ref_db_connection():
    """
    Set up the postgres connection
    """
    return psycopg2.connect(host='HOST',
                          user='USERNAME',
                          password='PASSWORD',
                          database='DB_NAME',
                          port=5432)

def insert_records(insert_statement, values):
    """
    Inserts a list of values into a database

    param insert_statement: The SQL query used to insert a row of data
    type insert_statement: string representing a SQL query
    param values: the list of tuples to insert into the database
    type values: list containing a tuple
    """
    if len(values) > 0:
        db = postgres_ref_db_connection()

        cur = db.cursor()
        try:
            if len(values) >= 1:
                cur.executemany(insert_statement, values)
                db.commit()
                print("INSERTED INTO DB")
                    
        except Exception as err:
            print("EXCEPTION")
            print(err)
            db.rollback()
            pass
        finally:
            cur.close()
            db.close()

def start_driver():
    """
    starts up a webdriver (you can add as many features and arguments to the driver as you want)
    """
    driver = webdriver.Firefox()
    return driver

def get_asins(driver, search_term):
    """
    Gets a list of product identification IDs for use in scraping reviews

    param driver: The browser used to go to Amazon and collect data
    type driver: selenium webdriver
    param search_term: A search term for Amazon
    type driver: string
    """
    base_url = 'https://www.amazon.com/s/ref=nb_sb_ss_c_1_7?url=search-alias%3Daps&field-keywords=' + search_term
    driver.get(base_url)
    soup = BS(driver.page_source, 'html.parser')
    page_count = int(soup.find(class_='pagnDisabled').text)
    asins = []
    for page in range(2,page_count+1):
        soup = BS(driver.page_source, 'html.parser')
        table = soup.find(id='s-results-list-atf').find_all('li')
        for item in table:
            try:
                asins.append(item['data-asin'])
            except Exception as e:
                continue
        print(len(asins))
        driver.get(base_url + '&page=' + str(page))
    asins = list(set(asins))
    print('Found ' + str(len(asins)) + ' unique ASINS')
    return asins

def ParseReviews(asin):
    """
    Parse the first page of reviews and collect data

    param asin: asin for an Amazon product
    type asin: string
    """
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    try:
        ua = UserAgent()
        amazon_url  = 'http://www.amazon.com/dp/'+asin
        headers = {'User-Agent': ua.random}
        page = requests.get(amazon_url,headers = headers,verify=False)
        page_response = page.text

        parser = html.fromstring(page_response)
        XPATH_AGGREGATE = '//span[@id="acrCustomerReviewText"]'
        XPATH_REVIEW_SECTION_1 = '//div[contains(@id,"reviews-summary")]'
        XPATH_REVIEW_SECTION_2 = '//div[@data-hook="review"]'

        XPATH_AGGREGATE_RATING = '//table[@id="histogramTable"]//tr'
        XPATH_PRODUCT_NAME = '//h1//span[@id="productTitle"]//text()'
        XPATH_PRODUCT_PRICE  = '//span[@id="priceblock_ourprice"]/text()'
        
        raw_product_price = parser.xpath(XPATH_PRODUCT_PRICE)
        product_price = ''.join(raw_product_price).replace(',','')

        raw_product_name = parser.xpath(XPATH_PRODUCT_NAME)
        product_name = ''.join(raw_product_name).strip()
        total_ratings  = parser.xpath(XPATH_AGGREGATE_RATING)
        reviews = parser.xpath(XPATH_REVIEW_SECTION_1)
        if not reviews:
            reviews = parser.xpath(XPATH_REVIEW_SECTION_2)
        ratings_dict = {}
        reviews_list = []
        
        if not reviews:
            raise ValueError('unable to find reviews in page')

        #grabing the rating  section in product page
        for ratings in total_ratings:
            extracted_rating = ratings.xpath('./td//a//text()')
            if extracted_rating:
                rating_key = extracted_rating[0] 
                raw_raing_value = extracted_rating[1]
                rating_value = raw_raing_value
                if rating_key:
                    ratings_dict.update({rating_key:rating_value})
        
        #Parsing individual reviews
        for review in reviews:
            XPATH_RATING  = './/i[@data-hook="review-star-rating"]//text()'
            XPATH_REVIEW_HEADER = './/a[@data-hook="review-title"]//text()'
            XPATH_REVIEW_POSTED_DATE = './/span[@data-hook="review-date"]//text()'
            XPATH_REVIEW_TEXT_1 = './/div[@data-hook="review-collapsed"]//text()'
            XPATH_REVIEW_TEXT_2 = './/div//span[@data-action="columnbalancing-showfullreview"]/@data-columnbalancing-showfullreview'
            XPATH_REVIEW_COMMENTS = './/span[@data-hook="review-comment"]//text()'
            XPATH_AUTHOR  = './/span[contains(@class,"profile-name")]//text()'
            XPATH_REVIEW_TEXT_3  = './/div[contains(@id,"dpReviews")]/div/text()'
            
            raw_review_author = review.xpath(XPATH_AUTHOR)
            raw_review_rating = review.xpath(XPATH_RATING)
            raw_review_header = review.xpath(XPATH_REVIEW_HEADER)
            raw_review_posted_date = review.xpath(XPATH_REVIEW_POSTED_DATE)
            raw_review_text1 = review.xpath(XPATH_REVIEW_TEXT_1)
            raw_review_text2 = review.xpath(XPATH_REVIEW_TEXT_2)
            raw_review_text3 = review.xpath(XPATH_REVIEW_TEXT_3)

            #cleaning data
            author = ' '.join(' '.join(raw_review_author).split())
            review_rating = ''.join(raw_review_rating).replace('out of 5 stars','')
            review_header = ' '.join(' '.join(raw_review_header).split())

            try:
                review_posted_date = dateparser.parse(''.join(raw_review_posted_date)).strftime('%d %b %Y')
            except:
                review_posted_date = None
            review_text = ' '.join(' '.join(raw_review_text1).split())

            #grabbing hidden comments if present
            if raw_review_text2:
                json_loaded_review_data = json.loads(raw_review_text2[0])
                json_loaded_review_data_text = json_loaded_review_data['rest']
                cleaned_json_loaded_review_data_text = re.sub('<.*?>','',json_loaded_review_data_text)
                full_review_text = review_text+cleaned_json_loaded_review_data_text
            else:
                full_review_text = review_text
            if not raw_review_text1:
                full_review_text = ' '.join(' '.join(raw_review_text3).split())

            raw_review_comments = review.xpath(XPATH_REVIEW_COMMENTS)
            review_comments = ''.join(raw_review_comments)
            review_comments = re.sub('[A-Za-z]','',review_comments).strip()
            review_dict = {
                                'review_comment_count':review_comments,
                                'review_text':full_review_text,
                                'review_posted_date':review_posted_date,
                                'review_header':review_header,
                                'review_rating':review_rating,
                                'review_author':author
                            }
            reviews_list.append(review_dict)

        data = {
                    'ratings':ratings_dict,
                    'reviews':reviews_list,
                    'url':amazon_url,
                    'price':product_price,
                    'name':product_name
                }
        return data
    except Exception:
        pass
            
def ReadAsin(asins):
    """
    Go through extracted reviews, organize the data, and perform sentiment analysis

    param asins: A list of amazon product IDs
    type asins: list of strings
    """

    extracted_data = []
    for asin in asins:
        print("Downloading and processing page http://www.amazon.com/dp/"+asin)
        extracted_data.append(ParseReviews(asin))
        sleep(5)
    f = open('data.json','w')
    json.dump(extracted_data,f,indent=4)

    values_list = []
    #Use this if loading from a JSON
    # extracted_data = json.load(open('data.json'))
    for data in extracted_data:
        try:
            name = data['name']
            url = data['url']
            price = float(data['price'].replace('$',''))
            try:
                five = data['ratings']['5 star'].replace('%', '')
            except Exception as e:
                five = None
            try:
                four = data['ratings']['4 star'].replace('%', '')
            except Exception as e:
                four = None
            try:
                three = data['ratings']['3 star'].replace('%', '')
            except Exception as e:
                three = None
            try:
                two = data['ratings']['2 star'].replace('%', '')
            except Exception as e:
                two = None
            try:
                one = data['ratings']['1 star'].replace('%', '')
            except Exception as e:
                one = None
            reviews = data['reviews']
            for review in reviews:  
                review_added = review['review_posted_date']
                review_text = review['review_text']
                review_header = review['review_header']
                author = review['review_author']
                rating = review['review_rating']
                sentiment, sentiment_level = get_sentiment(review_text)

            values_tuple = (
                url,
                name,
                price,
                five,
                four,
                three,
                two,
                one,
                author,
                review_text,
                sentiment,
                sentiment_level,
                review_added
                )
            values_list.append(values_tuple)
        except Exception as e:
            continue

    query = "INSERT INTO SCHEMA.TABLE (url, product_name, price, five_star, four_star, three_star, two_star, one_star, author, review, sentiment, sentiment_level, review_added) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    insert_records(query, values_list)

def clean_text(text):
    """
    Clean up text and remove the nonsense

    param text: review text
    type text: string
    """
    return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", text).split())

def get_sentiment(review):
    """
    Get sentiment analysis from a review

    param review: An Amazon product review
    type review: string
    """
    analysis = TextBlob(clean_text(review))
    if analysis.sentiment.polarity > 0:
        return 'positive', analysis.sentiment.polarity
    elif analysis.sentiment.polarity == 0:
        return 'neutral', analysis.sentiment.polarity
    else:
        return 'negative', analysis.sentiment.polarity

if __name__ == '__main__':
    search_term = get_search_term()
    if search_term is not None:
        driver = start_driver()
        asins = get_asins(driver, search_term)
        ReadAsin(asins)
        driver.quit()
    else:
        print('A search term is required. Add it after the python command (ex. python amazon_reviews_scraper.py dental floss')



















