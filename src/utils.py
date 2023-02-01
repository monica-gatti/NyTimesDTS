import psycopg2
from sqlalchemy import create_engine
import yaml
import os
from typing import Literal
from datetime import datetime
from elasticsearch import Elasticsearch
import logging
from AESCyper import sym_decrypt
from sqlalchemy.engine import Engine
from sqlalchemy_utils import database_exists, create_database

env = os.environ.get('NYTIMES_ENV')
dirname = os.path.dirname(__file__)
appFileName, credFileName = "", ""
if env == "local":
    appFileName = os.path.join(dirname, env+'_app.yaml')
    credFileName = os.path.join(dirname, env+'_nycred.yaml')
elif env == "dev":
    appFileName = os.path.join(dirname, env+'_app.yaml')
    credFileName = os.path.join(dirname, env+'_nycred.yaml')

contexts = Literal["TIME_WIRES_CONTEXT", "BOOKS_CONTEXT", "ARTICLES_CONTEXT", "TIME_WIRES_SECTIONS_LIST", "TIME_WIRES_CONTEXT_ALL", "DB_HOST", "DB_PORT", "DB_NAME" ]
user_agents = Literal["CROME_USER_AGENT","MOZILLA_USER_AGENT"]

def getUserAgent(user_agent_: user_agents) -> str:
    '''
    Return the valid user agent to simulate a browser to get a web page
    @user_agent_: choose a User agent in the list to get the web page
    '''
    return getConfKey(appFileName,'SCRAPING', user_agent_)
    
def getNYTkey() -> str:
    nytimekey = getConfKey(credFileName,'API', "api_key" )
    if env == "local":
        return sym_decrypt(getConfKey(credFileName,'API', "api_key" ))
    elif env == "dev":
        return nytimekey    

def getNYTUrl(context_:contexts) -> str:
    '''
    Return the valid Url to invoke NYTimes API
    @context_: choose a Url in the list
    '''
    baseUrl = getConfKey(appFileName, 'API','BASE_URL')
    context = getConfKey(appFileName, 'API', context_)
    key = str(getNYTkey())
    return str(baseUrl) + str(context) + key

def ingestArticlesEs(slugname:str, created_date, body: str,) -> None:
    es_url = getConfKey(appFileName,'ELASTIC_SEARCH','API_URL')
    es_index = getConfKey(appFileName,'ELASTIC_SEARCH','ARTICLE_INDEX') 
    es_usr = getConfKey(credFileName, 'ELASTIC_SEARCH', 'usr')
    es_pwd = ""
    if env == "local":
        es_pwd = sym_decrypt(getConfKey(credFileName, "ELASTIC_SEARCH", "pwd"))
    elif env == "dev":
        es_pwd = getConfKey(credFileName, "ELASTIC_SEARCH", "pwd")

    try:
        es = Elasticsearch(es_url,basic_auth=(es_usr, es_pwd), verify_certs=False)  
        doc = {
            'slug_name': slugname,
            'body':  body,
            'created_date': created_date,
            'word_count': len(body)
        }
        resp = es.index(index=es_index, id=slugname, document=doc)
        print(resp['result'])
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")

def ingestBooksEs(title: str, author: str,rank: int,description) -> None:                 
    stream = open(appFileName, 'r')
    data = yaml.load(stream, Loader=yaml.BaseLoader)
    es_url = data.get('ELASTIC_SEARCH').get("API_URL")
    es_index = data.get('ELASTIC_SEARCH').get("INDEX") 
    stream.close()
    stream = open(credFileName, 'r')
    data = yaml.load(stream, Loader=yaml.BaseLoader)
    es_pwd =  sym_decrypt(data.get('ELASTIC_SEARCH').get('pwd'))
    es = Elasticsearch(es_url,basic_auth=("elastic", es_pwd), verify_certs=False)  
    doc = {
        'title': title,
        'author':  author,
        'rank': rank,
        'description': description,
    }
    resp = es.index(index=es_index, document=doc)
    print(resp)

def getStringCurrentDate() -> str:
    now = datetime.now()
    return now.strftime("%d-%m-%Y_%H%M%S")

def logActivity(filename: str) -> None:
    print(dirname)
    loggingFileName = os.path.join(dirname, filename)
    logging.basicConfig(filename=loggingFileName, level=logging.INFO)


def dbPostgresGetEngine() -> Engine:
    db_host, db_port, db_name, db_usr = "","","",""
    db_pwd,db_connstr="", ""
    db_host = getConfKey(appFileName, 'DB', 'DB_HOST')
    db_port = getConfKey(appFileName, 'DB', 'DB_PORT')
    db_name = getConfKey(appFileName, 'DB', 'DB_NAME')
    db_usr = getConfKey(credFileName, 'DB', 'usr')
    
    if env == "local":
        db_pwd =  sym_decrypt(getConfKey(credFileName, 'DB', 'pwd'))
    elif env=="dev":
        db_pwd =  getConfKey(credFileName, 'DB', 'pwd')
    db_connstr = "postgresql://" + db_usr +":" + db_pwd + "@"+db_host+ ":" + db_port + "/"+db_name
    engine = create_engine(db_connstr)
    if not database_exists(engine.url):
        engine = create_database(engine.url)
    return engine

def dbPostgresOpenConnection():
    stream = open(credFileName, 'r')
    data = yaml.load(stream, Loader=yaml.BaseLoader)
    pwd =  sym_decrypt(data.get('DB').get('pwd'))
    
    return psycopg2.connect(
        host="localhost",
        database="NyTimes",
        user="postgres",
        password=sym_decrypt(pwd),
        port=5432)


def getConfKey(filename: str, section: str, key: str) -> str:
    stream = open(filename, 'r')
    data = yaml.load(stream, Loader=yaml.BaseLoader)
    value = data.get(section).get(key)
    stream.close()
    return value
