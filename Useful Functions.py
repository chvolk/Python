import psycopg2
import time
import selenium
from selenium import webdriver
import openpyxl
from openpyxl import load_workbook
import subprocess
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from smtplib import SMTP
import smtplib
from bs4 import BeautifulSoup as BS
import datetime
from PyPDF2 import PdfFileWriter, PdfFileReader
from time import mktime
import sys
import os
import re
import pdb
import requests

class Useful_Functions:

    def __init__(self):
        pass

    def postgres_ref_db_connection():
        """
        Set up the postgres connection
        """
        return psycopg2.connect(host='HOST',
                              user='USERNAME',
                              password='PASSWORD',
                              database='DB_NAME',
                          port=5432)

    def get_records(query, columns):
        """
        gets the scholarship link from the database and zips it into a dictionary
        """
        db = postgres_ref_db_connection()

        ref_list = []
        cur = db.cursor()

        cur.execute(query)
        urls = cur.fetchall()

        for i in urls:
            data = list(i)
            ref_zip_list = zip(columns, data)
            ref_dict = dict(ref_zip_list)
            ref_list.append(ref_dict)

        db.close()
        return ref_list
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

    def create_firefox_driver(path_to_profile):
        """
        Creates a firefox driver using a specified profile

        param path_to_profile: The filepath of the profile
        type path_to_profile: String representing a filepath
        """
        profile = webdriver.FirefoxProfile(path_to_profile)
        driver = webdriver.Firefox(profile)
        return driver

    def make_pdf_from_xlsx(filename, path_to_edit, path_to_completed, pdf_ready):
        """
        Converts XLSX to PDF

        param filename: The name of the xlsx file to edit
        type filename: String representing a file name
        param path_to_edit: The location of the folder containing a file to edit
        type path_to_edit: String representing a filepath
        param path_to_edit: The location of the folder to place a completed file
        type path_to_completed: String representing a filepath
        param pdf_ready: The location of the folder containing a file to edit
        type pdf_ready: String representing a filepath
        """
        try:
            for i in range(5):
                pdf_name = filename.replace('xlsx', 'pdf')
                try:
                    with timeout(45, exception=RuntimeError):
                        pdf_command = 'cd /Applications/LibreOffice.app/Contents/MacOS && ./soffice --headless --convert-to pdf --outdir ' + pdf_ready + ' ' + filename 
                        subprocess.check_output(['bash', '-c', pdf_command])
                        break
                except RuntimeError:
                    kill_command = 'killall soffice && killall libreoffice && killall libre'
                    process = subprocess.Popen(kill_command.split(), stdout=subprocess.PIPE)
                    time.sleep(5)
                    output, error = process.communicate()
                    continue
        except Exception as e:
            print(e)
            print('Fucked up converting to pdf')
            return None

        try:
            to_edit = path_to_edit + pdf_name
            edited = path_to_completed + pdf_name
            edit_pdf(to_edit)
            crop_pdf(to_edit, edited)

            return edited
        except Exception as e:
            print(e)
            print('Fucked up editing the PDF')
            return None


    def send_gmail(attachment, recipient, message_text, subject, your_email, password):
        """
        Sends an email from gmail with an attachment

        param attachment: The first attachment to the email
        type attachment: String representing a file path
        param attachment2: The second attachment to the email
        type attachment2: String representing a file path
        param recipient: The recipient's email address
        type recipient: String representing an email address
        param message_text: The body text of the email
        type message_text: String representing a message
        param subject: The subject of the email
        type subject: String representing a subject line
        param your_email: Your gmail login
        type your_email: String representing an email address
        param password: Your gmail password
        type password: String representing a password
        """
        recipients = [recipient] 
        emaillist = [elem.strip().split(',') for elem in recipients]
        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = your_email
        msg['Reply-to'] = your_email
         
        msg.preamble = 'Multipart massage.\n'
        part = MIMEText(message_text)
        msg.attach(part)
         
        part = MIMEApplication(open(str(attachment),"rb").read())
        part.add_header('Content-Disposition', 'attachment', filename=attachment.split('/')[-1])
        msg.attach(part)

        server = smtplib.SMTP("smtp.gmail.com:587")
        server.ehlo()
        server.starttls()
        server.login(your_email, password)
         
        server.sendmail(msg['From'], emaillist , msg.as_string())

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

    def get_2fa_from_pushbullet(api_key, text_to_strip=''):
        """
        Receives a 2fa code from Pushbullet that was sent there from your phone using something like IFTTT or AutoMagic

        param api_key: Your pushbullet api key
        type api_key: String representing an api key
        param text_to_strip: The extraneous text you want to strip from the 2fa message
        type text_to_strip: String
        """
        pb = Pushbullet(api_key)
        for i in range(100):
            pushes = pb.get_pushes()
            latest = pushes[0]['body']
            check = open('2fa.txt', 'r').read()
            if latest == check:
                time.sleep(10)
            else:
                open('2fa.txt', 'w').close()
                with open("2fa.txt", "w") as text_file:
                    text_file.write(latest)
                break
        pb.delete_push(pushes[0].get("iden"))
        code = latest.replace(text_to_strip, '')
        return code
