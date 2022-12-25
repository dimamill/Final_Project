***Анализ публикуемых новостей***
==================================
**Общая задача:** создать ETL-процесс формирования витрин данных для анализа публика-ций новостей.
--------------------------------
**Подробное описание задачи:**
------------------------------
•	Разработать скрипты загрузки данных в 2-х режимах:
1. Инициализирующий – загрузка полного слепка данных источника
2. Инкрементальный – загрузка дельты данных за прошедшие сутки

•	Организовать правильную структуру хранения данных
1. Сырой слой данных
2. Промежуточный слой
3. Слой витрин
В качестве результата работы программного продукта необходимо написать скрипт, который формирует витрину данных следующего содержания:
1. Суррогатный ключ категории;
2. Название категории;
3. Общее количество новостей из всех источников по данной категории за все время;
4. Количество новостей данной категории для каждого из источников за все время;
5. Общее количество новостей из всех источников по данной категории за последние сутки;
6. Количество новостей данной категории для каждого из источников за последние сутки;
7. Среднее количество публикаций по данной категории в сутки;
8. День, в который было сделано максимальное количество публикаций по данной категории;
9. Количество публикаций новостей данной категории по дням недели.
**Источники:**
----------------
•	https://lenta.ru/rss/

•	https://www.vedomosti.ru/rss/news

•	https://tass.ru/rss/v2.xml


**Реализация скрипта обработки логов**
-------------------------------------
Алгоритм работы
1.	Спарсить данные из источников
2.	Выполнить разбор данных по определенным тегам
3.	Выполнить разбор полей
4.	Выполнить обработку разобранной строки
5.	Выполнить обобщение обработанных строк
6.	Записать результат в файл

**Порядок работы**
----------------------
1.	Поднять докер-контейнеры: все данные для этого представлены в файле: docker-compose.yaml
2.	Подключить необходимые библиотеки: данные в файле dockerfile, библиотеки в requirements.txt
3.	Создать DAG: `airflow1t.py (analysis_of_published_news)`

**Парсинг данных выполняется с использованием библиотеки feedparser.**
-----------------------------------

Создаем следующие библиотеки:
`parseRSS` # функция получает линк на рсс ленту, возвращает распаршенную ленту с помощью feedpaeser
`getHeadlines` # функция для получения заголовков новости
`getCategories` # функция для получения описания новости
`getLinks` # функция для получения ссылки на источник новости
getDates # функция для получения даты публикации новости

Далее создаем списки для записи данных:
`allheadlines = []` #заголовки
`allcategories = []` #категории
`alllinks = []` #ссылки
`alldates = []` #даты публикации

**Функция для записи данных в csv файл:**
------------------------------------

`write_all_news`

**Все новости записываются в csv файл:**
----------------------------------

`f_all_news = 'allnews.csv'`

**Также реализована возможность записи новостей по нужным нам тегам. Они за-писываются в csv файл:**
--------------------------------------

`f_certain_news = 'certainnews.csv' #файл с новостями по ключевым словам
vector1 = 'ДолЛАР|РубЛ|ЕвРО'  # пример таргетов
vector2 = 'ЦБ|СбЕРбАНК|курс'`

**Все данные функции реализуются в таске:**
------------------------------------------
`extract_data`

В Airflow в XCom передаются все данные файла `f_all_news = 'allnews.csv’`. Они записываются в датафрейм df.

**Далее в таске transform_data выводятся строки данного датафрейма.**
--------------------------------------------------------

В таске load_data происходит процесс загрузки данных в Posrgresql. В БД создает-ся таблица под названием allnews со столбцами Title (Заголовки новостей), Cate-gory (Название категории), Links (Ссылка новости), Publication_date (Время публи-кации новости).


**Формирование витрины данных**
---------------------------------

Получение данных из БД возможно с помощью запросов

**Слой данных:**
--------------------

![image](https://user-images.githubusercontent.com/114313955/209476769-651f7557-2c99-4d1a-953e-8fa5a4d1287d.png)


**Схема проекта:**
-----------------------

![image](https://user-images.githubusercontent.com/114313955/209476717-11e08bf4-0db5-4be6-9960-f43436f60ad0.png)


**Структура DAGa:**
----------------------

![image](https://user-images.githubusercontent.com/114313955/209475876-8183ada0-6ead-4c9f-8155-f24532cac2d1.png)

**Установка и запуск:**
===========================

**Запуск проекта:**
------------------------

`docker-compose up -d` 

**Настройка Airflow:**
------------------------

Графический интерфейс Airflow:

`http://localhost:8082/` 

Логин  | Пароль
------------- | -------------
airflow       | airflow

Подключение к PosrgreSQL:

user  | password | db
------------- | ------------- | ------------
postgres       | password | test

В графическом интерфейсе Airflow в разделе Connections необходимо добавить соединение:

Conn Id  | Conn Type | host | Port 
------------- | ------------- | ------------ | ----------------
database_PG | postgres | host.docker.internal | 5425

В разделе Variables необходимо добавить переменную:

Key  | Val
------------- | -------------
conn_id       | database_PG


В папке docs расположены описание проекта, презентация и CSV файлы (как пример выгрузки данных)

В папке programs расположены скрипты, данные со всеми настройками для правильной работы скрипта
