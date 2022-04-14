
# Módulos do Airflow
from datetime import datetime, timedelta  
from airflow import DAG
from airflow.operators.python_operator import PythonOperator

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2022, 4, 13),
    'email': ['airflow@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(seconds=30),
    'schedule_interval': '@daily'
}

with DAG(    
    dag_id='book_webscraping',
    default_args=default_args,
    schedule_interval='@daily',
    tags=['book_webscraping'],
) as dag:    

    def update_books_data():
        
        import requests
        from bs4 import BeautifulSoup
        import pandas as pd
        import re

        url_home = 'https://books.toscrape.com/'
        request = requests.get(url_home)

        def _soup(reques_content):
            return BeautifulSoup(reques_content, 'html.parser')

        def get_category_list():
            soup = _soup(request.content)
            category_list = soup.find('ul', {"class": "nav nav-list"})
            return category_list

        def update_url_category_list():
            url_category_list = []
            for category_link in get_category_list().find_all('a'):
                category_link = category_link.get('href')
                
                if category_link != 'catalogue/category/books_1/index.html':
                    url_category_list.append(category_link.rsplit('catalogue/category/books')[1].rsplit('/')[1])
            return url_category_list

        books_url_list = []

        def get_books_url(soup):
            book_list = soup.find('section')

            for books_list in book_list.find_all('a'):
                books_list = books_list.get('href')

                if books_list not in books_url_list:
                    if "page" not in books_list:
                        books_url_list.append(books_list)

        def update_books_list(category):
            
            url = f'{url_home}catalogue/category/books/{category}/index.html'
            soup = _soup(requests.get(url).content)
            get_books_url(soup)                                 
            page = 2
            while soup.find('li', {'class':'next'}) is not None:

                url = f'{url_home}catalogue/category/books/{category}/page-{page}.html'
                soup = _soup(requests.get(url).content)
                get_books_url(soup)
                page += 1


        for url_category in update_url_category_list():
            update_books_list(url_category)
            
        book_data_base = []

        def string_rating(star_rating):
            star_number = {
                'One': 1,
                'Two': 2,
                'Three': 3,
                'Four': 4,
                'Five': 5
            }
            return star_number.get(star_rating)

        def get_book_description(soup_book):
                if soup_book.find('article', {'class':'product_page'}).find('p', attrs={'class': None}) is not None:
                    book_description = soup_book.find('article', {'class':'product_page'}).find('p', attrs={'class': None}).get_text()
                else:
                    book_description ='INFORMATION NOT AVAILABLE'
                return book_description

        def update_book_data_base(books):
            url_book = f'{url_home}catalogue/{books[9:]}'
            soup_book = _soup(requests.get(url_book).content)
            book_category = soup_book.find('ul', {'class':'breadcrumb'}).select('a', href = '../category/books/')[2].get_text()
            book_name = soup_book.find('div', {'class':'col-sm-6 product_main'}).find('h1').get_text()
            book_description = get_book_description(soup_book)
            book_data_table = soup_book.find('table', {'class':'table table-striped'})
            book_star_rating = soup_book.find('div', {'class':'col-sm-6 product_main'}).find('p', {"class" : 'star-rating'})
            star_rating = book_star_rating['class'][1]
            rating = string_rating(star_rating)

            book_data = [book_category, book_name, book_description, rating]

            for book_items in book_data_table.find_all('td'):
                if 'available' in book_items.get_text():
                    book_items = re.findall('[0-9]+',book_items.get_text())[0]
                else:
                    book_items = book_items.get_text()
                book_data.append(book_items)

            book_data_base.append(book_data)

        for books_url in books_url_list:
            update_book_data_base(books_url)
            
        book_data = pd.DataFrame(book_data_base,columns=['CATEGORY','PRODUCT_NAME', 'PRODUCT_DESCRIPTION','RATING','UPC','PRODUCT_TYPE', 'PRICE', 'PRICE_WITH_TAX', 'TAX','AVAILABLE_IN_STOCK', 'NUMBER_OF_REVIEWS'])

        import datetime

        reference = datetime.datetime.now()

        book_data['REFERENCE'] = reference

        book_data['RATING'] = book_data['RATING'].astype('int')
        book_data['PRICE'] = book_data['PRICE'].replace('[\£,]', '', regex=True).astype(float)
        book_data['PRICE_WITH_TAX'] = book_data['PRICE_WITH_TAX'].replace('[\£,]', '', regex=True).astype(float)
        book_data['TAX'] = book_data['TAX'].replace('[\£,]', '', regex=True).astype(float)
        book_data['AVAILABLE_IN_STOCK'] = book_data['AVAILABLE_IN_STOCK'].astype('int')
        book_data['NUMBER_OF_REVIEWS'] = book_data['NUMBER_OF_REVIEWS'].astype('int')

        import psycopg2
        import numpy as np
        import psycopg2.extras as extras

        def execute_values(conn, df, table):
        
            tuples = [tuple(x) for x in df.to_numpy()]
        
            cols = ','.join(list(df.columns))
            
            query = "INSERT INTO %s(%s) VALUES %%s" % (table, cols)
            cursor = conn.cursor()
            try:
                extras.execute_values(cursor, query, tuples)
                conn.commit()
            except (Exception, psycopg2.DatabaseError) as error:
                print("Error: %s" % error)
                conn.rollback()
                cursor.close()
                return 1
            print("the dataframe is inserted")
            cursor.close()
        
        
        conn = psycopg2.connect(
            database="airflow", user='airflow', password='airflow', host='case-books_postgres_1', port='5432'
        )
        

        execute_values(conn, book_data, 'book_data')

        return print('Updated book data')


    task_1 = PythonOperator(task_id='webscraping_save_pg', python_callable=update_books_data)

    task_1