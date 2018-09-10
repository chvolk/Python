from bs4 import BeautifulSoup as BS
from selenium import webdriver
import pdb
import psycopg2
import time
from random import randint

base_url = 'https://www.scholarships.com/financial-aid/college-scholarships/scholarship-directory/'


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
	driver = webdriver.PhantomJS()
	return driver

def get_filters(driver):
	driver.get(base_url)
	time.sleep(randint(5,20))
	soup = BS(driver.page_source, 'html.parser')
	scholarship_filters = soup.find(id='ullist').find_all('li', recursive=False)

	filters_list = []
	for item in scholarship_filters:
		filters_list.append(item.text.strip().replace(' ','-').lower())

	return filters_list

def get_scholarships(driver, filters_list):
	scholarships_dict = {}
	for filter_item in filters_list:
		driver.get(base_url + filter_item)
		time.sleep(randint(5,20))
		current_url = driver.current_url
		soup = BS(driver.page_source, 'html.parser')
		subfilters = soup.find(id='ullist').find_all('li', recursive=False)
		subfilters_list = []

		for subfilter_item in subfilters:
			subfilters_list.append(subfilter_item.text.strip().replace(' ', '-').replace('&', 'and').replace('\'', '').replace('/', '-').lower())

		for subfilter_item in subfilters_list:
			try:
				driver.get(current_url + '/' + subfilter_item)
				time.sleep(randint(5,20))
				soup = BS(driver.page_source, 'html.parser')
				scholarship_results = soup.find(class_='scholarshiplistdirectory').tbody.find_all('tr', recursive=False)
				values_list = []

				for result in scholarship_results:
					scholarship_name = result.find(class_='scholtitle').text.strip()
					scholarship_link = result.find(class_='scholtitle').a['href']

					try:
						scholarship_amount = int(result.find(class_='scholamt').text.replace('$','').strip())
					except ValueError as e:
						scholarship_amount = None

					scholarship_due_date = result.find(class_='scholdd').text.strip()

					values_tuple = (
						filter_item,
						subfilter_item,
						scholarship_name,
						scholarship_amount,
						scholarship_due_date,
						scholarship_link
						)
					values_list.append(values_tuple)

				query = 'INSERT INTO SCHEMA.TABLE (category, subcategory, name, amount, due_date, link) VALUES (%s, %s, %s, %s, %s, %s)'
				insert_records(query, values_list)
			except Exception as e:
				continue

if __name__ == '__main__':
	driver = start_driver()
	filters_list = get_filters(driver)
	get_scholarships(driver, filters_list)	
	print('Complete')

