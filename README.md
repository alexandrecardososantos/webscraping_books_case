# Webscraping a book marketplace case

The goal of this case is to web scrap a website that was built to be web scraped and then load the data into a database. This must be a daily task, so the data can be analyzed time by time.

In the end of the project will be possible to answer those two questions below:
> What is the average price of books by rating (in stars)?
> 
> How many books have 2 or less copies on a specific day?

## Steps
- Understand the website structure through HTML
- Web scrap using Python libraries
- Setup Docker
- Create a PostgreSQL data base
- Schedule DAG in Apache Airflow

## Understand the website structure through HTML

The first thing to do is to visit the website that is going to be scrapped https://books.toscrape.com/ to locate the needed information and get a clue about where to start.

Right at the home page it is possible to get some leads. There's a list of book categories and there are at least one thousand books.
<div align=left>
<img src="https://github.com/alexandrecardososantos/imagens/blob/main/case_wb_01.JPG?raw=tru" width="1000" height="500">
</div>

<br>

Travel category's page as an example. Seems to have the number of books by catergory.
<div align=left>
<img src="https://github.com/alexandrecardososantos/imagens/blob/main/case_wb_02.JPG?raw=tru" width="1000" height="500">
</div>

<br>

And finnaly a books's page example, where the data is located:
<div align=left>
<img src="https://github.com/alexandrecardososantos/imagens/blob/main/case_wb_03.JPG?raw=tru">
<img src="https://github.com/alexandrecardososantos/imagens/blob/main/case_wb_04.JPG?raw=tru">
</div>

<br>

So the logic will be:
-  web scrap the home page to create a list of all categories
-  go through category list and get the list of books
-  go through every book to get the data and createalexandrecardososantos/imagens a dataframe

There are probably plenty of other ways to web scrap this site, but this logic seems fine to this project.

## Web scrap using Python libraries

Python's libraries requirements for this project:
- pandas version 1.2.5
  - manipulate data with Python
- numpy version 1.19.5
  - mathematical functions
- re (regular expression) version 2.2.1
  - manipulate strings
- requests version 2.25.1
  - easy way to send HTTP requests (reference: https://docs.python-requests.org/en/latest/)  
- beautifulsoup4 version 4.9.3
  - makes the web scrap possible and very easy (reference: https://beautiful-soup-4.readthedocs.io/en/latest/)
- psycopg2 version 2.9.3
  - connect to PostgreSQL database (reference:https://www.geeksforgeeks.org/how-to-insert-a-pandas-dataframe-to-an-existing-postgresql-table/)

The code can be found [here](https://github.com/alexandrecardososantos/webscraping_books_case/blob/main/dags/books_webscraping.py) (already inside the PythonOperator DAG).

## Setup Docker

This project was developed with Windows operational system, so in order to schedule the task in Apache Airflow, Docker must be installed.

- [Docker installer](https://runnable.com/docker/install-docker-on-windows-10)

After Docker is already installed, the app enviroment must be setted up in order to run Airflow and PostgreSQL. The project folder must have:

- [docker-compose.yaml](https://github.com/alexandrecardososantos/webscraping_books_case/blob/main/docker-compose.yaml) file
- dags folder
- logs folder
- plugins folder

The [books_webscraping.py](https://github.com/alexandrecardososantos/webscraping_books_case/blob/main/dags/books_webscraping.py) file must be placed inside the dag folder.

Example:
<br>
![alexandrecardososantos](https://github.com/alexandrecardososantos/imagens/blob/main/case_wb_05.JPG?raw=true)

Yet inside the project folder, run the commands below on terminal. The first two commands below download the images from Docker hub. The images that should be download are setted already inside the docker-compose.yaml file. 

```sh
docker-compose up airflow-init
```

When it's finished a message like this will be shown:
<br>
![alexandrecardososantos](https://github.com/alexandrecardososantos/imagens/blob/main/case_wb_06.JPG?raw=true)

Then run this command:
```sh
docker-compose up -d
```

And after finished, should look like this:
<br>
![alexandrecardososantos](https://github.com/alexandrecardososantos/imagens/blob/main/case_wb_07.JPG?raw=true)

Still on terminal, run the command
```sh
docker ps
```

This will show all the running containers. Some will take a few tries to get from "unhealthy" to "healthy".

Example:
<br>
![alexandrecardososantos](https://github.com/alexandrecardososantos/imagens/blob/main/case_wb_08.JPG?raw=true)

Now Airflow and PostgreSQL are ready to be used:
- Airflow http://localhost:8080/
- PostgreSQL http://localhost:15432/

(reference: https://www.youtube.com/watch?v=aTaytcxy2Ck)

## Create a PostgreSQL data base

The pgAdmin 4 login and password are setted at the docker-compose.yaml file. 

```sh
login: postgres@postgres.com
password: postgres
```

After login, the steps below should be followed:
<br>
![alexandrecardososantos](https://github.com/alexandrecardososantos/imagens/blob/main/case_wb_09.JPG?raw=true)
<br>

Fill Name with <b>localhost</b> and then click in <b>Connection</b>.
<br>
![alexandrecardososantos](https://github.com/alexandrecardososantos/imagens/blob/main/case_wb_10.JPG?raw=true)
<br>

On the terminal, run docker ps command to identify the host name.
<br>
![alexandrecardososantos](https://github.com/alexandrecardososantos/imagens/blob/main/case_wb_11.JPG?raw=true)
<br>

Then back to Connection window fill the:
- Host name (image above)
- Port <b>5432</b>
- Maintence database <b>airflow</b>
- Username <b>airflow</b>
- Password <b>airflow</b>

And then save.
<br>
![alexandrecardososantos](https://github.com/alexandrecardososantos/imagens/blob/main/case_wb_12.JPG?raw=true)
<br>

The databese is created. Open the SQL editor to run the query below and create the table.
<br>
![alexandrecardososantos](https://github.com/alexandrecardososantos/imagens/blob/main/case_wb_13.JPG?raw=true)
<br>

The data will be arised from web scrapping as a pandas dataframe and then inserted in the PostgreSQL table, so a table must be created with the same variables that exists in the dataframe

```sh
CREATE TABLE IF NOT EXISTS public.book_data
(
    product_type character(20) COLLATE pg_catalog."default",
    category character(20) COLLATE pg_catalog."default",
    product_name text COLLATE pg_catalog."default",
    product_description text COLLATE pg_catalog."default",
    rating integer,
    upc character(16) COLLATE pg_catalog."default",
    price double precision,
    price_with_tax double precision,
    tax double precision,
    available_in_stock integer,
    number_of_reviews integer,
    reference date
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.book_data
    OWNER to airflow;
```

<br>

![alexandrecardososantos](https://github.com/alexandrecardososantos/imagens/blob/main/case_wb_14.JPG?raw=true)
<br>

After run the command, refresh the database it is possible to check that the table was created.
<br>

![alexandrecardososantos](https://github.com/alexandrecardososantos/imagens/blob/main/case_wb_15.JPG?raw=true)
<br>

## Schedule DAG in Apache Airflow

The Airflow login and password are setted at the docker-compose.yaml file. 

```sh
login: airflow
password: airflow
```

Since the [DAG](https://github.com/alexandrecardososantos/webscraping_books_case/blob/main/dags/books_webscraping.py) is already inside the project folder, airflow should look like this:
<br>

![alexandrecardososantos](https://github.com/alexandrecardososantos/imagens/blob/main/case_wb_16.JPG?raw=true)
<br>

Unpause the DAG.
<br>

![alexandrecardososantos](https://github.com/alexandrecardososantos/imagens/blob/main/case_wb_17.JPG?raw=true)
<br>

Run the DAG.
<br>
![alexandrecardososantos](https://github.com/alexandrecardososantos/imagens/blob/main/case_wb_18.JPG?raw=true)
<br>

The DAG will be running for a while.
<br>

![alexandrecardososantos](https://github.com/alexandrecardososantos/imagens/blob/main/case_wb_19.JPG?raw=true)
<br>

And then finish. Success means that ran with no issues.
<br>

![alexandrecardososantos](https://github.com/alexandrecardososantos/imagens/blob/main/case_wb_20.JPG?raw=true)
<br>

Now it's possible to run a query and check if the data was inserted to the table. Looks like worked fine.
<br>

![alexandrecardososantos](https://github.com/alexandrecardososantos/imagens/blob/main/case_wb_21.JPG?raw=true)
<br>

The DAG is schedule to run everyday.
<br>

![alexandrecardososantos](https://github.com/alexandrecardososantos/imagens/blob/main/case_wb_22.JPG?raw=true)
<br>

It's possible to check when will be the next run:
<br>

![alexandrecardososantos](https://github.com/alexandrecardososantos/imagens/blob/main/case_wb_23.JPG?raw=true)
<br>

(reference: https://www.linkedin.com/pulse/building-server-postgres-airflow-simple-way-docker-rabelo-saraiva/)

## Answers

The price by star rating can be found in the image bellow. Looks not linear, so it means that a good classified book is not necessarily more expansive than a bad classified book.

<br>

![alexandrecardososantos](https://github.com/alexandrecardososantos/imagens/blob/main/case_wb_24.JPG?raw=true)

Looks like 112 books have 2 or less copies in that day. There's no filter of day in the query below, because the data is from only one day reference.
<br>

![alexandrecardososantos](https://github.com/alexandrecardososantos/imagens/blob/main/case_wb_25.JPG?raw=true)

## Conclusion

Any <b>data analysts users</b> that have enough SQL skills and get access to this database would be able to answer those questions. They wouldn't have to worry about how the data was loaded in the table, but just consume.
