import flask
from flask import *
from fileinput import filename
import requests
import pymongo
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import re
import json
import math
app = Flask(__name__)
uri = "mongodb+srv://deekshitha1425:KQhXiEZaNhoiW606@cluster0.kzjipbi.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client['CALI']
results_global = []
results= {}
curr_page_num = 1
offset = 0
per_page = 20
default_ret = 10
total_num_books = 0
show_next = True
total_num_pages = 0

#default app routing
@app.route('/')
def homepage():
  global total_num_books
  global show_next
  global per_page
  global results_global
  global results
  global total_num_pages
  try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
    col = db['Books_with_metrics']
    total_num_books = col.count_documents({})
    print(f"total_num_books : {total_num_books}")
    all_books = col.find()
    #print(f"all_books : {all_books}")
    results_global = []
    numResults = 0
    if per_page < total_num_books:
      numResults = per_page
    else:
      numResults = total_num_books
    for x in all_books:
       del x['_id']
       results_global.append(x)
       key = x['Book_name']
       values = {}
       for z in x:
         if z!='Book_name':
           values[z] = x[z]
       results[key] = values
    if total_num_books > per_page:
      show_next = True
    total_num_pages = math.ceil(len(results_global)/per_page)
  except Exception as e:
    print(e)
  return render_template('index.html',results=results_global[0:20],showNext = show_next,curr_page_number = 1,numResults=numResults,offset=0,resultsStr=jsonify(results_global))

@app.route('/fetchAll',methods=['GET'])
def fetchAll():
  return db['Books_with_metrics'].find()

@app.route('/collect_file_data',methods=['POST','GET'])
def collect_file_data():
    if request.method=='POST':
      file_input = request.files['file_upload']
      with open(file_input) as opened_file:
        for line in opened_file:
            print(line)
    return render_template('index.html')

@app.route('/changeTab',methods=['POST','GET'])
def changeTab():
  return render_template('index.html')
  


@app.route('/validate_form',methods=['POST','GET'])
def validate():
  global results
  print("entered validation")
  return results

@app.route('/getNextResults',methods=['GET','POST'])
def getNextResults():
  global results_global
  global per_page
  pageNum = int(request.args.get('pageNum'))
  print(f"pagenum is {pageNum}")
  request_res = {}
  isLastPage = False
  if pageNum>=total_num_pages:
    isLastPage = True
  request_res['isLastPage'] = isLastPage
  temp_res = results_global[(pageNum-1)*per_page:(pageNum-1)*per_page+per_page]
  request_res['books'] = temp_res
  return request_res
  

if __name__ == "__main__":
  app.run(debug=True)
