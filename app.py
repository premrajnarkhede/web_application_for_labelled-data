#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from flask import Flask, render_template, request,session
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_cors import CORS
from forms import *
import os
import sqlite3
from flask import g,jsonify
from flask_kvsession import KVSessionExtension
from simplekv.fs import FilesystemStore
import json
import random

#Optional 
# from stemming.porter2 import stem
# import requests
# import nltk.data
# 
# sent_detector = nltk.data.load('tokenizers/punkt/english.pickle')

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
CORS(app)
app.config.from_object('config')
store = FilesystemStore('sessiondata')
KVSessionExtension(store, app)


DATABASE = 'training_data.db'





def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db





@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()



@app.route('/getSummary')
def getSummary():
    sql = "select category,count(*) from training_set group by category"
    db = get_db()
    results = db.execute(sql)
    array = []
    for r in results:
        array.append(r)
    return jsonify(array)
@app.route('/')
def home():
    db = get_db()
    sql = '''CREATE TABLE IF NOT EXISTS training_set (
        text BLOB,
        category VARCHAR(128),
        idd TEXT,
        Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
       )'''
    db.execute(sql)
    sql2 = '''CREATE INDEX category_idx ON training_set (category);'''
    try:
        db.execute(sql2)
    except Exception as e:
        print(e)
    sql2 = '''CREATE INDEX text_idx ON training_set (text);'''
    try:
        db.execute(sql2)
    except Exception as e:
        print(e)
    return render_template('pages/placeholder.home.html')

@app.route("/deleteLastEntry")
def deleteEntry():
    sql = "DELETE FROM training_set WHERE rowid = (SELECT MAX(rowid) FROM training_set);"
    db = get_db()
    cursor = db.cursor()
    cursor.execute(sql)
    db.commit()
    return "1"

@app.route("/showLast/<number>")
def showLast(number):
    sql = "SELECT * FROM training_set order by rowid desc limit "+number
    db = get_db()
    cursor = db.cursor()
    cursor.execute(sql)
    array = []
    for res in cursor:
        array.append(res)
    return jsonify(array)

@app.route("/generateData",methods=['POST'])
def generateData():
    data=json.loads(request.data)
    # print data
    tags1 = data["tags1"]
    tags2 = data["tags2"]
    totalsens = [["This is a test document 1. You really need to modify generateData function in app.py to get your data points up here","id1"],
        ["This is a test document 2. You really need to modify generateData function in app.py to get your data points up here","id2"],
        ["This is a test document 3. You really need to modify generateData function in app.py to get your data points up here","id3"],
        ["This is a test document 4. You really need to modify generateData function in app.py to get your data points up here","id4"],
        ["This is a test document 5. You really need to modify generateData function in app.py to get your data points up here","id5"],
        ["This is a test document 6. You really need to modify generateData function in app.py to get your data points up here","id6"]]
    
    random.shuffle(totalsens)
    session["sentences"] = totalsens
    session["counter"] = 0
    return "1"
    #print searchquery    

def shuffleTexts():
    #for i in range(len(session["sentences"])):
    counter = session["counter"]
    try:
        sen = session["sentences"][counter]
        #print sen,"<---"
    except:
        return None
    session["counter"] = session["counter"]+1
    return sen


@app.route("/updateData",methods=['POST'])
def updateResults():
    data=json.loads(request.data)
    print(data)
    db = get_db()
    cursor = db.cursor()
    error_flag = 200
    if "sentence" in data and data["sentence"]!="":
        
        try:
            cursor.execute("insert into training_set(text,category,idd) values(?,?,?)",[data["sentence"],data["cat"],data["idd"]])
            
            db.commit()
        except:
            error_flag = 500
            pass
    while 1:
        text = shuffleTexts()
        if not text:
            break
        #print text,"TEXT--------------------"
        sql = "select * from training_set where text=?"
        results = []
        try:
            results = cursor.execute(sql,[text[0]])
        except:
            pass
        break_flag = 1
        for r in results:
            break_flag = 0
        if break_flag==1:
            return jsonify({"text":text[0],"id":text[1]}),error_flag
            
    return jsonify({"text":"Choose new seed keywords. All texts are exhausted or zero results","id":"Delete"}),error_flag
        
@app.route("/getCategories")
def getCategories():
    dicta = json.loads(open("categories.json","r").read())
    return jsonify(dicta)

@app.route("/updateCategories",methods=['POST'])
def updateCategories():
    data=json.loads(request.data)
    categories = data["categories"]
    thefile = open("categories.json","w")
    thefile.write(json.dumps(categories))
    thefile.close()
    return "1"
    
# Error handlers.



@app.errorhandler(500)
def internal_error(error):
    #db_session.rollback()
    return render_template('errors/500.html'), 500


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

# Or specify port manually:

