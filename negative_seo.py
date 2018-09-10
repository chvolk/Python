# -*- coding: utf-8 -*-
from selenium import webdriver
import time
import random
import pdb
from bs4 import BeautifulSoup as BS
from selenium.webdriver.common.keys import Keys
import pickle
from fake_useragent import UserAgent


def start_driver():
    ua = UserAgent()

    headers = { 'Accept':'*/*',
        'Accept-Encoding':'gzip, deflate, sdch',
        'Accept-Language':'en-US,en;q=0.8',
        'Cache-Control':'max-age=0',
        'User-Agent': ua.random
    }

    for key, value in enumerate(headers):
        webdriver.DesiredCapabilities.PHANTOMJS['phantomjs.page.customHeaders.{}'.format(key)] = value

    profile = webdriver.FirefoxProfile()
    profile.set_preference("general.useragent.override", "whatever you want")
    # service_args = [
    #     '--proxy=proxy-nl.privateinternetaccess.com:1080',
    #     '--proxy-type=socks5',
    #     '--proxy-auth=x7263643:dYt9RksFwx', # I enter real user name and pass here
    #     ]

    # driver = webdriver.PhantomJS(service_args=service_args)
    driver = webdriver.Firefox(profile)
    pickle.dump( driver.get_cookies() , open("cookies.pkl","wb"))
    return driver

def run_negative_seo(driver, link_text):
    driver.get('https://www.google.com')
    print('    Navigated to Google. Searching for term...')
    query = 'Garage door torsion springs'
    # pdb.set_trace()
    # gb_8 gbi4s1  gbgs4 gbgs5 gbi5 gbd5 gbx4
    try:
        search_box = driver.find_element_by_id('gs_lc0')
        for char in query:
            time.sleep(random.uniform(.05,.27))
            search_box.send_keys(char)
            time.sleep(random.uniform(.05,.3))
        search_box.send_keys(Keys.RETURN)
        print('    Submitting query...')
    except Exception as e:
        try:
            search_box = driver.find_element_by_name('q')
            for char in query:
                time.sleep(random.uniform(.05,.27))
                search_box.send_keys(char)
                time.sleep(random.uniform(.05,.3))
            search_box.send_keys(Keys.RETURN)
            print('    Submitting query...')
        except Exception as e:
            try:
                search_box = driver.find_element_by_id('lst-ib')
                for char in query:
                    time.sleep(random.uniform(.05,.27))
                    search_box.send_keys(char)
                    time.sleep(random.uniform(.05,.3))
                search_box.send_keys(Keys.RETURN)
                print('    Submitting query...')
            except Exception as e:
                try:
                    search_box = driver.find_element_by_xpath('/html/body/center/form/table/tbody/tr/td[2]/div/input')
                    for char in query:
                        time.sleep(random.uniform(.05,.27))
                        search_box.send_keys(char)
                        time.sleep(random.uniform(.05,.3))
                    search_box.send_keys(Keys.RETURN)
                    print('    Submitting query...')
                except Exception as e:
                    pdb.set_trace()


    

    for i in range(1, 500):
        driver.execute_script("window.scrollTo(0, {})".format(str(i)))
    time.sleep(random.uniform(.05,2))
    driver.find_element_by_link_text(link_text).click()

    print('    Navigating to {}'.format(link_text))

    time.sleep(random.uniform(1,4))

    print('    Navigating around comptetitor site...')

    for i in range(1, 700):
        scroll_count = i
        driver.execute_script("window.scrollTo(0, {})".format(str(i)))  

    time.sleep(random.uniform(1,3))  

    for i in range(scroll_count, 0, -1):
        driver.execute_script("window.scrollTo(0, {})".format(str(i)))

    aga_links = [
    'Weather Stripping',
    'Garage Door Springs',
    'Hinges | Door Brackets',
    'Garage Door Rollers',
    'Stainless Steel Hardware',
    'Cable | Cable Sets',
    'Bearings | Bearing Plates',
    'Door Track | Hardware',
    'Pulleys | Cable Drums',
    'Garage Door Locks',
    'Torsion Shaft | Couplers',
    'Leaf | Spring Bumpers',
    'Truck Door Parts',
    'Opener Transmitters | Receivers',
    'Opener Controls',
    'Chain Hoists',
    'Tools',
    'Loading Dock Equipment'
    ]

    driver.find_element_by_link_text(random.choice(aga_links)).click()

    time.sleep(random.uniform(3,8))  

    for i in range(1, 300):
        driver.execute_script("window.scrollTo(0, {})".format(str(i)))

    print('    Competitor site visit complete. Navigating back to Google...')
    driver.execute_script("window.history.go(-1)")

    time.sleep(random.uniform(1,3))

    driver.execute_script("window.history.go(-1)")

    time.sleep(random.uniform(1,2))

    for i in range(500, 700):
        driver.execute_script("window.scrollTo(0, {})".format(str(i)))
    print('    Navigating to GDN...')
    driver.find_element_by_partial_link_text('ᐅ Garage Door').click()

    time.sleep(random.uniform(3,5))

    for i in range(1, 400):
        driver.execute_script("window.scrollTo(0, {})".format(str(i)))

    time.sleep(random.uniform(12,24))

    print('    GDN site visit complete. Exiting...')
    driver.quit()

if __name__ == "__main__":
    link_text = 'Garage Door Torsion Springs - American Garage Door Supply'
    print('Initiating driver...')
    driver = start_driver()
    print('Driver initiated. Commencing NSEO:')
    run_negative_seo(driver, link_text)
    print('NSEO Complete.')
    driver.quit()
