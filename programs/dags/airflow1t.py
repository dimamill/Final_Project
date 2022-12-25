import time
import requests
from airflow.models import Variable
import os
import pathlib
from datetime import datetime
import psycopg2
import pandas as pd
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python_operator import PythonOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.postgres_operator import PostgresOperator
from airflow.hooks.base import BaseHook
import psycopg2.extras as extras






def extract_data(**kwargs):
    ti = kwargs['ti']
    import feedparser
    import csv
    import pandas as pd
    import re

    newsurls = {'Vedomosti': 'https://www.vedomosti.ru/rss/news',
                'Lenta.ru': 'https://lenta.ru/rss/',
                'Tass': 'https://tass.ru/rss/v2.xml'}

    f_all_news = 'allnews.csv' #файл со всеми новостями
    f_certain_news = 'certainnews.csv' #файл с новостями по ключевым словам
    vector1 = 'ДолЛАР|РубЛ|ЕвРО'  # пример таргетов
    vector2 = 'ЦБ|СбЕРбАНК|курс'

    def parseRSS(rss_url):  # функция получает линк на рсс ленту, возвращает распаршенную ленту с помощью feedpaeser
        return feedparser.parse(rss_url)

    def getHeadlines(rss_url):  # функция для получения заголовков новости
        headlines = []
        feed = parseRSS(rss_url)
        for newsitem in feed['items']:
            headlines.append(newsitem['title'])
        return headlines

    def getCategories(rss_url):  # функция для получения описания новости
        categories = []
        feed = parseRSS(rss_url)
        for newsitem in feed['items']:
            categories.append(newsitem['category'])
        return categories

    def getLinks(rss_url):  # функция для получения ссылки на источник новости
        links = []
        feed = parseRSS(rss_url)
        for newsitem in feed['items']:
            links.append(newsitem['link'])
        return links

    def getDates(rss_url):  # функция для получения даты публикации новости
        dates = []
        feed = parseRSS(rss_url)
        for newsitem in feed['items']:
            dates.append(newsitem['published'])
        return dates

    allheadlines = []
    allcategories = []
    alllinks = []
    alldates = []
    # Прогоняем наши URL и добавляем их в наши пустые списки

    for key, url in newsurls.items():
        allheadlines.extend(getHeadlines(url))

    for key, url in newsurls.items():
        allcategories.extend(getCategories(url))

    for key, url in newsurls.items():
        alllinks.extend(getLinks(url))

    for key, url in newsurls.items():
        alldates.extend(getDates(url))

    def write_all_news(all_news_filepath):  # функция для записи всех новостей в .csv, возвращает нам этот датасет
        header = ['Title', 'Category', 'Links', 'Publication_Date']

        with open(all_news_filepath, 'w', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')

            writer.writerow(i for i in header)

            for a, b, c, d in zip(allheadlines, allcategories,
                                  alllinks, alldates):
                writer.writerow((a, b, c, d))

            df = pd.read_csv(all_news_filepath)

        return df

    def looking_for_certain_news(all_news_filepath, certain_news_filepath, target1,
                                 target2):  # функция для поиска, а затем записи
        # определенных новостей по таргета,
        # затем возвращает этот датасет
        df = pd.read_csv(all_news_filepath)

        result = df.apply(lambda x: x.str.contains(target1, na=False,
                                                   flags=re.IGNORECASE, regex=True)).any(axis=1)
        result2 = df.apply(lambda x: x.str.contains(target2, na=False,
                                                    flags=re.IGNORECASE, regex=True)).any(axis=1)
        new_df = df[result & result2]

        new_df.to_csv(certain_news_filepath
                      , sep='\t', encoding='utf-8-sig')

        return new_df

    print(write_all_news(f_all_news))
    print("All_news")
    all_news_json = write_all_news(f_all_news).to_json()
    ti.xcom_push(key='allnews_csv', value=all_news_json)

def transform_data(**kwargs):
    ti = kwargs['ti']
    df = ti.xcom_pull(key='allnews_csv', task_ids=['extract_data'])[0]
    print(df)
    ti.xcom_push(key='alnews_csv', value=df)


def get_conn_credentails(conn_id) -> BaseHook.get_connection:
    conn = BaseHook.get_connection(conn_id)
    return conn
def load_data():
    conn_id = Variable.get("conn_id")
    pg_conn=get_conn_credentails(conn_id)
    pg_hostname,pg_port,pg_username,pg_pass,pg_db=pg_conn.host,pg_conn.port,pg_conn.login,pg_conn.password,pg_conn.schema

    def execute_values(conn, df, table):

        tuples = [tuple(x) for x in df.to_numpy()]

        cols = ','.join(list(df.columns))

        #создание пустой таблицы
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
        print("execute_values() done")
        cursor.close()
    conn = psycopg2.connect(host=pg_hostname, port=pg_port, user=pg_username, password=pg_pass, database=pg_db)
    cursor = conn.cursor()
    #добавление данных с датасета в созданную таблицу
    cursor.execute("DROP TABLE IF EXISTS allnews; CREATE TABLE IF NOT EXISTS allnews (Title text ,Category text, Links text, Publication_Date date); SELECT category, COUNT(*) AS count FROM allnews GROUP BY category;")
    data = pd.read_csv("allnews.csv")

    # Создаем DataFrame
    data = data[["Title", "Category", "Links", "Publication_Date"]]
    # Create DataFrame
    # Конвертируем data в sql

    execute_values(conn, data, 'allnews')


    conn.commit()
    cursor.close()
    conn.close()



with DAG(dag_id="analysis_of_published_news", start_date=datetime(2022, 12, 12), schedule="0 0 * * *") as dag:
    # Tasks are represented as operators
    extract_data = PythonOperator(task_id="extract_data", python_callable=extract_data)
    transform_data = PythonOperator(task_id='transform_data', python_callable=transform_data)
    load_data = PythonOperator(task_id="load_data", python_callable=load_data)




    extract_data >>transform_data>>load_data
