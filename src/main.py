from fastapi import FastAPI
import json
from utils import dbPostgresGetEngine
from model import Author, Article
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from psycopg2 import IntegrityError, errors
import uvicorn
from pydantic import BaseModel
from datetime import datetime

app = FastAPI(title="NyTimesAPI", version="1.0.0", description="Use this set of API to get the latest Articles, Author in the NYTIMES news")


@app.get('/')
def get_index():
    ''' This set of API provides you the capability to query among Articles and Author of NYTimes
    '''
    return {'Description': 'This API provide you the NyTimes articles'}

@app.get('/author/{fullname}')
def get_item(fullname):
    ''' Invoke this API with GET method and passing a Author full name, to get all theirs articles
    '''
    engine = dbPostgresGetEngine()
    session_maker = sessionmaker(bind=engine)
    session = session_maker()
    query = session.query(Article).join(Author, Author.slug_id==Article.slug_id).filter(Author.fullname == fullname)
    data='{"author":"", "articles":[]}'
    jsonData=json.loads(data)
    jsonData["author"]=fullname
    for element in query.all():
        item_dict = {}
        item_dict["slug_id"]=element.slug_id
        item_dict["url"]=element.url
        item_dict["title"]=element.title
        item_dict["section"]=element.section
        item_dict["subsection"]=element.subsection
        item_dict["created_date"]=element.article_date
        jsonData["articles"].append(item_dict)
    session.close()
    return jsonData

@app.get('/author/{fullname}/{section}')
def get_item(fullname, section):
    ''' Invoke this API with GET method and passing an Author full name and a Section, to get all theirs articles
    for a specific section. Example of sections are "World, Arts, Climate, Books, Real Estate, Sports, Food"
    '''
    engine = dbPostgresGetEngine()
    session_maker = sessionmaker(bind=engine)
    session = session_maker()
    query = session.query(Article).join(Author, Author.slug_id==Article.slug_id).filter(Author.fullname == fullname).filter(Article.section == section)
    data='{"author":"", "section":"", "articles":[]}'
    jsonData=json.loads(data)
    jsonData["author"]=fullname
    jsonData["section"]=section
    for element in query.all():
        item_dict = {}
        item_dict["slug_id"]=element.slug_id
        item_dict["url"]=element.url
        item_dict["title"]=element.title
        item_dict["section"]=element.section
        item_dict["subsection"]=element.subsection
        item_dict["created_date"]=element.article_date
        jsonData["articles"].append(item_dict)
    session.close()
    return jsonData


@app.get('/article/{dateFrom}/{dateTo}')
def get_item(dateFrom, dateTo):
    ''' Invoke this API with GET method and passing two dates, to get all the articles published
    in that timespan
    '''
    engine = dbPostgresGetEngine()
    session_maker = sessionmaker(bind=engine)
    session = session_maker()
    query = session.query(Article).join(Author, Author.slug_id==Article.slug_id).filter(Article.article_date > dateFrom).filter(Article.article_date < dateTo)
    data='{"author":"", "articles":[]}'
    jsonData=json.loads(data)
    for element in query.all():
        item_dict = {}
        item_dict["slug_id"]=element.slug_id
        item_dict["url"]=element.url
        item_dict["title"]=element.title
        item_dict["section"]=element.section
        item_dict["subsection"]=element.subsection
        item_dict["created_date"]=element.article_date
        jsonData["articles"].append(item_dict)
    session.close()
    return jsonData


class article(BaseModel):
    slug_id: str
    article_date: datetime
    title: str
    section: str
    subsection: str
    url: str
    webPageAvailability: str
    apiInvokeDate: datetime

#@api.put("/article/")


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)