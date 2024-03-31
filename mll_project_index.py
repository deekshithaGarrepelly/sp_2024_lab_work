import flask
from flask import *
from fileinput import filename
import requests
import pymongo
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import re
app = Flask(__name__)
uri = "mongodb+srv://deekshitha1425:KQhXiEZaNhoiW606@cluster0.kzjipbi.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client['sample_airbnb']
#default app routing
@app.route('/')
def homepage():
  results = []
  try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
    '''col = db['listingsAndReviews']
    all_reviews = col.find()
    print(all_reviews)
    for x in all_reviews:
       results.append(x['name'])'''
  except Exception as e:
    print(e)
  return render_template('index.html')

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
  


@app.route('/validate_form',methods=['POST'])
def validate(request):
  return render_template('index.html')
  

         

         
         

if __name__ == "__main__":
  app.run(debug=True)
