import flask
from flask import *
from fileinput import filename
import requests
import pymongo
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
app = Flask(__name__)
uri = "mongodb+srv://deekshitha1425:KQhXiEZaNhoiW606@cluster0.kzjipbi.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client['sample_airbnb']
show_search = True
show_readability = False
show_vocab = False
show_more_results = False
metrics_criteria = False
text_info_search = False
lang_info_search = False
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
  return render_template('index.html',results = [],search = show_search,readability = show_readability,vocab = show_vocab, moreresults = show_more_results,show_metrics_criteria = metrics_criteria,show_text_info=text_info_search,show_lang_info=lang_info_search)

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
  print('entered changetab')
  if request.method == 'POST':
      global show_search
      global show_readability
      global show_vocab
      global show_more_results
      global metrics_criteria
      global text_info_search
      global lang_info_search
      if 'select_button' in request.form and request.form['select_button']!=None:
        if request.form['select_button'] == 'Search':
          print('entered search')
          show_search = True
          show_readability = False
          show_vocab = False
          show_more_results = False
        elif request.form['select_button'] == 'Readability':
          print('entered readability')
          show_search = False
          show_readability = True
          show_vocab = False
          show_more_results = False
        elif request.form['select_button'] == 'Vocabulary':
          print('entered vocab')
          show_search = False
          show_readability = False
          show_vocab = True
          show_more_results = False
        elif request.form['select_button'] == 'More_Results':
          print('entered more')
          show_search = False
          show_readability = False
          show_vocab = False
          show_more_results = True
      elif 'show_table_metrics' in request.form and request.form['show_table_metrics']!=None and request.form['show_table_metrics']=='readability_metrics_button':
        metrics_criteria = not(metrics_criteria)
      elif 'show_table_text_info' in request.form and request.form['show_table_text_info']!=None and request.form['show_table_text_info']=='text_info_button':
        text_info_search = not(text_info_search)
      elif 'show_table_lang_criteria' in request.form and request.form['show_table_lang_criteria']!=None and request.form['show_table_lang_criteria']=='lang_criteria_button':
        lang_info_search = not(lang_info_search)
  return render_template('index.html',results = [],search=show_search,readability =show_readability,vocab =show_vocab, moreresults =show_more_results, show_metrics_criteria = metrics_criteria,show_text_info=text_info_search,show_lang_info=lang_info_search)

         

         
         

if __name__ == "__main__":
  app.run(debug=True)
