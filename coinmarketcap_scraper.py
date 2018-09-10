import psycopg2
import requests
from bs4 import BeautifulSoup as BS
import datetime
import logging

logging.basicConfig(
    Level=logging.INFO,
    filename='log/cmc_scraper.log',
    format='%(asctime)s %(name)s %(levelname)s %(message)s'
    )

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
                logging.info("INSERTED INTO DB")
                    
        except Exception as err:
            logging.exception("EXCEPTION: " + err)
            db.rollback()
            pass
        finally:
            cur.close()
            db.close()

def get_cmc_data():
    """
    Get Coin Market Cap data
    """
    temp = requests.get('https://coinmarketcap.com/all/views/all/') 
    soup = BS(temp.content, 'html.parser')
    table = soup.find(id='currencies-all')
    results = table.tbody.find_all('tr', recursive=False)
    return results

def parse_and_upload(results):
    """
    Inserts a list of values into a database

    param results: a list of results from coinmarketcap.com
    type results: list
    """
    final_results = []
    values_list = []
    for count, result in enumerate(results):
        coin_name = result.find(class_='no-wrap currency-name').text.replace('\n', '').replace('  ', '').strip()
        symbol = result.find(class_='text-left').text.replace('\n', '').replace('  ', '').strip()
        market_cap = result.find(class_='no-wrap market-cap text-right').text.replace('\n', '').replace('  ', '').replace('$','').replace('*','').replace(',','').strip()
        price = result.find(class_='price').text.replace('\n', '').replace('  ', '').replace('$','').replace(',','').replace('*','').strip()
        circulating_supply = result.find_all(class_='no-wrap text-right')[1].text.replace('\n', '').replace('  ', '').replace(',','').replace('$','').replace('*','').strip()
        volume = result.find(class_='volume').text.replace('\n', '').replace('  ', '').replace('$','').replace(',','').replace('*','').strip()

        if volume == 'Low Vol' or volume == '?':
            volume = None 
        if circulating_supply == '?':
            circulating_supply = None
        if price == '?':
            price = None
        if market_cap == '?':
            market_cap = None

        try:
            try:
                one_hour_change = result.find(class_='no-wrap percent-1h positive_change text-right').text.replace('\n', '').replace('  ', '').replace('%','').strip()
            except AttributeError as e:
                try:
                    one_hour_change = result.find(class_='no-wrap percent-1h negative_change text-right').text.replace('\n', '').replace('  ', '').replace('%','').strip()
                except AttributeError as e:
                    one_hour_change = None
            try:
                twenty_four_hour_change = result.find(class_='no-wrap percent-24h positive_change text-right').text.replace('\n', '').replace('  ', '').replace('%','').strip()
            except AttributeError as e:
                try:
                    twenty_four_hour_change = result.find(class_='no-wrap percent-24h negative_change text-right').text.replace('\n', '').replace('  ', '').replace('%','').strip()
                except AttributeError as e:
                    twenty_four_hour_change = None
            try:
                seven_day_change = result.find(class_='no-wrap percent-7d positive_change text-right').text.replace('\n', '').replace('  ', '').replace('%','').strip()
            except AttributeError as e:
                try:
                    seven_day_change = result.find(class_='no-wrap percent-7d negative_change text-right').text.replace('\n', '').replace('  ', '').replace('%','').strip()
                except AttributeError as e:
                    seven_day_change = None
        except Exception as e:
            logging.exception(e)
            one_hour_change = None
            twenty_four_hour_change = None
            seven_day_change = None

        time_collected = datetime.datetime.utcnow()

        values_tuple = (
            coin_name,
            symbol,
            market_cap,
            price,
            circulating_supply,
            volume,
            one_hour_change,
            twenty_four_hour_change,
            seven_day_change,
            time_collected
            )

        values_list.append(values_tuple)

    insert_statement = "INSERT INTO SCHEMA.TABLE (coin_name, symbol, market_cap, price, circulating_supply, volume, one_hour_change, twenty_four_hour_change, seven_day_change, time_collected) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    insert_records(insert_statement, values_list)

if __name__ == "__main__":
    logging.info('Program started')
    results = get_cmc_data()
    parse_and_upload(results)
    logging.info('Program complete')
        