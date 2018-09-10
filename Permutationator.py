from itertools import combinations
from multiprocessing.dummy import Pool as ThreadPool
import threading 
import datetime
import psycopg2
import pdb
import simplejson
from psycopg2.pool import ThreadedConnectionPool
import random, string
import time


class word_permutationator(object):

    def __init__(self, filename, short_length, max_length, process_count, past_results=False):
        """
        gets every possible combination of words in any language between x and n chars long using a txt document seperated by new lines

        param words: List of all unique words in a language (or whatever)
        type words: list
        param short_length: the minimum length of a string representing a combination of words
        type short_length: int
        param max_length: the minimum length of a string representing a combination of words
        type max_length: int
        param process_count: the number of processesors to use when multiprocessing
        type process_count: int
        """

        self.short_length = short_length
        self.max_length = max_length
        self.process_count = process_count
        if past_results:
            self.words = self.read_local_data(filename=filename)
        else:
            self.words = self.get_words_from_doc(filename, max_length)
        self.db = self.postgres_db_connection()
        # self.db.set_isolation_level(0)
        self.lock = threading.Lock()
        self.pool_permutationator()

    # def postgres_db_connection(self):
    #     """
    #     Set up the postgres connection for a threaded connection pool (DB might lock up... but way faster)
    #     """
    #     DSN = "host='cryptocache.c9rveqedlpj3.us-east-1.rds.amazonaws.com' user='northatlantic' password='BigRidiculousPassword1!' dbname='CryptoCache' port=5432"
    #     return ThreadedConnectionPool(minconn=1, maxconn=10, DSN)

    def postgres_db_connection(self):
        """
        Set up the postgres connection for a single connection (more stable on the DB end)
        """
        return psycopg2.connect(host='HOST',
                              user='USERNAME',
                              password='PASSWORD',
                              database='DB_NAME',
                              port=5432)

    def insert_records(self, insert_statement, values):
        """
        Inserts a list of values into a database

        param insert_statement: The SQL query used to insert a row of data
        type insert_statement: string representing a SQL query
        param values: the list of tuples to insert into the database
        type values: list containing a tuple
        """
    
        conn = self.db
        if len(values) > 0:
            cur = conn.cursor()
            try:
                if len(values) >= 1:
                    for value in values:
                        cur.execute(insert_statement, value)
                    self.db.commit()
                        
            except Exception as err:
                self.db.rollback()
                pass
            finally:
                cur.close() 
                # self.db.putconn(conn)


    def get_words_from_doc(self, doc_name, max_length):
        """
        gets every word in the english language as a list from a txt file seperated by new lines

        param doc_name: the name of the document
        type doc_name: string
        param max_length: the minimum length of a string representing a combination of words
        type max_length: int
        """
        print('Getting words from doc')
        doc = open(doc_name, 'r')
        listed_words = doc.read().split('\n')
        for count, word in enumerate(listed_words):
            try:
                #if word is just a repeated letter (like aaaaaa)
                if word == len(word) * word[0]:
                    listed_words.remove(word)
                #if the word is 1 letter long or longer than the max possible length of the combination (two letter word + one space + word)
                elif len(word) < 2 or len(word) > (max_length-3):
                    listed_words.remove(word)
                #check if word has any bullshit like numbers or special chars
                elif set('[~!@#$%=^&*()_+-{}":;\']+$0987654321').intersection(word) and not word.isalpha():
                    listed_words.remove(word)
                else:
                    continue
            except Exception as e:
                print(e)
                listed_words.remove(word)
                continue

        self.write_local_data(listed_words, 'listed_words.txt')
        return listed_words

    def write_local_data(self, data, filename):
        """
        Write all results to a local file, to be mathced up against on future runs

        param data: a list to write to a local file
        type data: list
        param filename: name and extension of the file to write to
        type filename: string
        """

        f = open(filename, 'w')
        simplejson.dump(data, f)
        f.close()

    def read_local_data(self, filename=None):
        """
        read results from a local file to be used for combinations

        param filename: name of the file to read words from
        type filename: string
        """
        try:
            f = open(filename, 'r')
            results = simplejson.load(f)
            f.close()
        except Exception as e:
            results = []
        return results

    def get_threadkey(self):

       return ''.join(random.choice(string.ascii_lowercase) for i in range(5))

    def pool_permutationator(self):
        """
        Pools the work of finding every combination of words
        """
        print('''Getting all possible permuations of {} words between {} and {} chars 
            long using {} processes'''.format(str(len(self.words)), self.short_length, self.max_length, self.process_count))

        top_range = int(round((self.max_length/2)*.8125))
        ranges = list(range(2, top_range))
        # pool = ThreadPool(2) 
        pool.map(self.get_and_write_permutations, ranges)

    def get_and_write_permutations(self, len_range):
        global threadlock
        global lock_count
        global insert_data
        """
        finds every possible combination of words up to the amount specified in the len_range

        param len_range: the number of words to be used in a combination
        type len_range: int
        """
        thread_key = self.get_threadkey()
        add_count = 0
        values_list = []
        for combo in combinations(self.words, len_range):
            item = " ".join(combo).lower()
            char_count = len(item)
            if char_count < self.short_length or char_count > self.max_length:
                continue
            if item in values_list:
                continue
            else:
                add_count += 1
                time_added = datetime.datetime.utcnow()
                values_tuple = (item,
                        len_range,
                        char_count,
                        time_added)
                values_list.append(values_tuple)
                if add_count > 9999:
                    
                    query = "INSERT INTO SCHEMA.TABLE (permutation, word_count, char_count, time_added) VALUES (%s, %s, %s, %s)"
                    if threadlock and lock_count < 4:
                        lock_count += 1
                        insert_data.extend(values_list)
                        while threadlock:
                            time.sleep(2)
                            if not threadlock:
                                break
                    elif threadlock == 3:
                        print('Inserting Batch')
                        insert_data.extend(values_list)
                        self.insert_records(query, insert_data)
                        insert_data = []
                        threadlock = False

                    add_count = 0
                    values_list = []
        return None
            


if __name__ == "__main__":
    permutationiator = word_permutationator('listed_words.txt', 9, 34, 4, past_results=True)
    print('Complete')
