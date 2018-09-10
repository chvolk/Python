from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup as BS
import re
import time
from random import randint
import psycopg2
import pdb

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
	driver = webdriver.Firefox()
	return driver

def get_and_store_data(driver):
	driver.get('https://influence.co/users/auth/instagram')
	driver.find_element_by_xpath('//*[@id="id_username"]').send_keys('chvolk')
	driver.find_element_by_xpath('//*[@id="id_password"]').send_keys('33459Fv')
	time.sleep(2)
	driver.find_element_by_xpath('/html/body/div/section/div/div/form/p[3]/input').click()
	time.sleep(5)

	keywords = [
	'Beauty',
	'Makeup',
	'Beauty Blogger',
	'Fashion',
	'Fitness',
	'Fashion blogger',
	'Blogger',
	'Health',
	'Mom',
	'Model',
	'Travel',
	'Healthy products',
	'Health and wellness',
	'Healthy skin',
	'Diet',
	'Trainer',
	'Fashion modeling',
	'Fashion photography',
	'Fashion blog',
	'Fitness models',
	'Fitness photography',
	'Fitness products',
	'Beauty brands',
	'Beauty influencer',
	'Makeup artist',
	'Makeup review',
	'Tutorials',
	'Shopping',
	'Sephora',
	'Skincare',
	'Skincare blogger',
	'Relationships',
	'Lifestyle',
	'Cosmetics',
	'Sunglasses',
	'Plus size apparel',
	'Skin Care',
	'Bodybuilding',
	'Photography',
	'Snapchat',
	'Portrait',
	'Weight loss',
	'Gadgets',
	'Electronic accessories',
	'Electronic Music'
	]

	ids = []
	for term in keywords:
		driver.get('https://influence.co/influencer_searches#advanced')
		driver.find_element_by_xpath('/html/body/div[1]/section[1]/div/div/div/div[1]/div[2]/form/div[1]/div[1]/span/span[1]/span/ul/li/input').send_keys(term)
		time.sleep(randint(2,6))
		driver.find_element_by_xpath('/html/body/div[1]/section[1]/div/div/div/div[1]/div[2]/form/div[1]/div[1]/span/span[1]/span/ul/li/input').send_keys(Keys.RETURN)
		time.sleep(randint(1,4))
		driver.find_element_by_xpath('/html/body/div[1]/section[1]/div/div/div/div[1]/div[2]/form/p/input').click()
		try:
			cat_id = re.search('[category_ids][]=(.*)&', driver.current_url)
		except Exception as e:
			cat_id = re.search('category_ids%5D%5B%5D=(.*)&is%', driver.current_url)
		ids.append(cat_id)
		time.sleep(randint(4,12))

	

	for item in ids:
		try:
			values_list = []
			cat_id = item.group(1).split('&')[0]
			if cat_id == '':
				cat_id = item.group(1).split('=')[1].split('&')[0]
			driver.get('https://influence.co/influencer_searches?utf8=%E2%9C%93&is%5Blimit%5D=3000&is%5Bsort_order%5D=reach_desc&is%5Bcategory_ids%5D%5B%5D=&is%5Bcategory_ids%5D%5B%5D={}&is%5Blocation_ids%5D%5B%5D=&is%5Bfollower_min%5D=&is%5Bfollower_max%5D=&is%5Bmin_fb_likes%5D=&is%5Bmax_fb_likes%5D=&is%5Bmin_twitter_followers%5D=&is%5Bmax_twitter_followers%5D=&is%5Bmin_erate%5D=&is%5Bmax_erate%5D=&is%5Bmin_ga_visitors%5D=&is%5Bmax_ga_visitors%5D=&is%5Bmin_pinterest_followers%5D=&is%5Bmax_pinterest_followers%5D=&is%5Bmin_age%5D=&is%5Bmax_age%5D=&is%5Bmin_rate%5D=&is%5Bmax_rate%5D=&is%5Bis_male%5D=0&is%5Bis_female%5D=0&is%5Bhas_media_kit%5D=0&is%5Bhas_ig_posts%5D=0&is%5Bhas_yt_posts%5D=0&is%5Bhas_pinterest_posts%5D=0&is%5Bhas_snapchat_posts%5D=0&is%5Bhas_google_analytics%5D=0&is%5Bonly_emails%5D=true&is%5Baccount_type%5D=influencer&is%5Bsearch_type%5D=advanced&is%5Bmin_reach%5D=10000&is%5Bmax_reach%5D=10000000&commit=Search'.format(cat_id))
			time.sleep(60)
			soup = BS(driver.page_source, 'html.parser')

			results = soup.find_all(class_='advanced-search-card clearfix')
			if results ==[]:
				time.sleep(30)
				soup = BS(driver.page_source, 'html.parser')
				results = soup.find_all(class_='advanced-search-card clearfix')
				if results == []:
					continue
			term = soup.find(class_='select2-selection__choice').text
			if term.startswith('×'):
				term = term[1:]
			for result in results:
				insta_url = 'instagram.com/' +result['href']
				name = result.h4.text.strip()
				info = result.find_all(class_='group-the-stat')
				reach = None
				rate = None
				followers = None
				engagement_rate = None
				for data in info:
					if 'Reach' in data.text:
						reach = data.find(class_='stat').text
					elif 'Starting Rate' in data.text:
						rate = data.find(class_='stat').text
					else:
						try:
							stats = data.find(class_='stat').text.split('|')
							followers = stats[0].strip()
							for stat in stats:
								if '%' in stat:
									engagement_rate = stats[1].strip().replace('%', '')
								else:
									continue
						except Exception as e:
							print(e)
							followers = None
							engagement_rate = None

				values_tuple = (
					term,
					name,
					insta_url,
					rate,
					reach,
					followers,
					engagement_rate
					)
				values_list.append(values_tuple)
		except Exception as e:
			print(e)
			pdb.set_trace()
		query = "INSERT INTO SCHEMA.TABLE (term, name, insta_url, rate, reach, followers, engagement_rate) VALUES (%s, %s, %s, %s, %s, %s, %s)"
		insert_records(query, values_list)

if __name__ == "__main__":
	driver = start_driver()
	get_and_store_data(driver)
	driver.quit()


