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
show_search = True
show_readability = False
show_vocab = False
show_more_results = False
metrics_criteria = False
text_info_search = False
lang_info_search = False
title_keyword_search = False
form_errors = ''
has_errors = False
numparas = ""
author = ""
book_title = ""
text_keywords = ""
num_sents = ""
num_words = ""
mean_len_paras = ""
std_mlp = ""
mean_num_words_in_sents = ""
std_mls = ""
mean_num_sylls = ""
std_mean_sylls = ""
mean_num_letters = ""
std_mean_letters_in_words = ""
noun_overlap_adj = ""
noun_overlap_global = ""
cwr_overlap_adj = ""
cwr_overlap_global = ""
arg_overlap_adj = None
arg_overlap_global = ""
local_stem_overlap = ""
genre = ""
text_type = ""
text_len = None
authentic_or_simplified = []
authentic = False
simplified = False
top_frequent_words_1000 = ""
top_frequent_words_2000 = ""
top_frequent_words_3000 = ""
top_frequent_words_4000 = ""
top_frequent_words_5000 = ""
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
  return render_template('index.html',results = [],search = show_search,readability = show_readability,vocab = show_vocab, moreresults = show_more_results,show_metrics_criteria = metrics_criteria,
                         show_text_info=text_info_search,show_lang_info=lang_info_search,
                         show_title_keyword = title_keyword_search, error=form_errors,form_error=has_errors,
                         numparas=numparas
                         ,text_keywords=text_keywords,num_sents=num_sents,num_words=num_words,author=author,
                         book_title = book_title, mean_len_paras = mean_len_paras,std_mlp=std_mlp,mean_num_words_in_sents=mean_num_words_in_sents,
                         std_mls = std_mls,mean_num_sylls = mean_num_sylls,std_mean_sylls = std_mean_sylls,mean_num_letters = mean_num_letters,
                         std_mean_letters_in_words = std_mean_letters_in_words,noun_overlap_adj=noun_overlap_adj,noun_overlap_global = noun_overlap_global,
                         cwr_overlap_adj = cwr_overlap_adj, cwr_overlap_global = cwr_overlap_global,arg_overlap_adj=arg_overlap_adj,local_stem_overlap=local_stem_overlap,
                         genre=genre,text_type=text_type,text_len=text_len,authentic=authentic,simplified=simplified,
                         top_frequent_words_1000=top_frequent_words_1000,top_frequent_words_2000=top_frequent_words_2000,top_frequent_words_3000=top_frequent_words_3000,
                         top_frequent_words_4000=top_frequent_words_4000,top_frequent_words_5000=top_frequent_words_5000
                         )

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
      print(request.form)
      global show_search
      global show_readability
      global show_vocab
      global show_more_results
      global metrics_criteria
      global text_info_search
      global lang_info_search
      global title_keyword_search
      global form_errors
      global has_errors
      global numparas
      global author
      global book_title
      global text_keywords
      global num_sents
      global num_words
      global mean_len_paras
      global std_mlp
      global mean_num_words_in_sents
      global std_mls
      global mean_num_sylls
      global std_mean_sylls
      global mean_num_letters
      global std_mean_letters_in_words
      global noun_overlap_adj
      global noun_overlap_global
      global cwr_overlap_adj
      global cwr_overlap_global
      global arg_overlap_adj
      global arg_overlap_global
      global local_stem_overlap
      global genre
      global text_type
      global text_len
      global authentic
      global simplified
      global top_frequent_words_1000
      global top_frequent_words_2000
      global top_frequent_words_3000
      global top_frequent_words_4000
      global top_frequent_words_5000
      if 'num_paras' in request.form:
        numparas = request.form['num_paras']
      if 'author' in request.form:
        author = request.form['author']
      if 'text_keywords' in request.form:
        text_keywords = request.form['text_keywords']
      if 'num_sents' in request.form:
        num_sents = request.form['num_sents']
      if 'num_words' in request.form:
        num_words = request.form['num_words']
      if 'mean_len_paras' in request.form:
        mean_len_paras = request.form['mean_len_paras']
      if 'std_mlp' in request.form:
        std_mlp = request.form['std_mlp']
      if 'mean_num_words_in_sents' in request.form:
        mean_num_words_in_sents = request.form['mean_num_words_in_sents']
      if 'std_mls' in request.form:
        std_mls = request.form['std_mls']
      if 'mean_num_sylls' in request.form:
        mean_num_sylls = request.form['mean_num_sylls']
      if 'std_mean_sylls' in request.form:
        std_mean_sylls = request.form['std_mean_sylls']
      if 'mean_num_letters' in request.form:
        mean_num_letters = request.form['mean_num_letters']
      if 'std_mean_letters_in_words' in request.form:
        std_mean_letters_in_words = request.form['std_mean_letters_in_words']
      if 'noun_overlap_adj' in request.form:
        noun_overlap_adj = request.form['noun_overlap_adj']
      if 'noun_overlap_global' in request.form:
        noun_overlap_global = request.form['noun_overlap_global']
      if 'cwr_overlap_adj' in request.form:
        cwr_overlap_adj = request.form['cwr_overlap_adj']
      if 'cwr_overlap_global' in request.form:
        cwr_overlap_global = request.form['cwr_overlap_global']
      if 'arg_overlap_adj' in request.form:
        arg_overlap_adj = request.form['arg_overlap_adj']
      if 'arg_overlap_global' in request.form:
        arg_overlap_global = request.form['arg_overlap_global']
      if 'local_stem_overlap' in request.form:
        local_stem_overlap = request.form['local_stem_overlap']
      if 'genre' in request.form:
        genre = request.form['genre']
      if 'text_type' in request.form:
        text_type = request.form['text_type']
      if 'text_len' in request.form:
        text_len = request.form['text_len']
      if 'authentic_or_simplified' in request.form:
        checked_values = request.form.getlist('authentic_or_simplified')
        if 'authentic' in checked_values:
          authentic = True
        if 'simplified' in checked_values:
          simplified = True 
      if 'top_frequent_words_1000' in request.form:
        top_frequent_words_1000 = request.form['top_frequent_words_1000']
      if 'top_frequent_words_2000' in request.form:
        top_frequent_words_2000 = request.form['top_frequent_words_2000']
      if 'top_frequent_words_3000' in request.form:
        top_frequent_words_3000 = request.form['top_frequent_words_3000']
      if 'top_frequent_words_4000' in request.form:
        top_frequent_words_4000 = request.form['top_frequent_words_4000']
      if 'top_frequent_words_5000' in request.form:
        top_frequent_words_5000 = request.form['top_frequent_words_5000']
      if 'select_button' in request.form:
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
      elif 'show_title_keyword_button' in request.form and request.form['show_title_keyword_button']!=None and request.form['show_title_keyword_button']=='title_keyword_button':
        title_keyword_search = not(title_keyword_search)
      elif 'search_texts' in request.form and request.form['search_texts']!=None and request.form['search_texts']=='search_texts_button':
        msg = validate(request)
        if len(msg)>0:
          form_errors = msg
          has_errors = True
          print(form_errors)
        else:
          has_errors = True
          form_errors = ''
  return render_template('index.html',results = [],search=show_search,readability =show_readability,vocab =show_vocab, moreresults =show_more_results, show_metrics_criteria = metrics_criteria,show_text_info=text_info_search,show_lang_info=lang_info_search,show_title_keyword=title_keyword_search,error=form_errors,form_error=has_errors,
                         numparas=numparas
                         ,text_keywords=text_keywords,num_sents=num_sents,num_words=num_words,author=author,
                         book_title = book_title, mean_len_paras = mean_len_paras,std_mlp=std_mlp,mean_num_words_in_sents=mean_num_words_in_sents,
                         std_mls = std_mls,mean_num_sylls = mean_num_sylls,std_mean_sylls = std_mean_sylls,mean_num_letters = mean_num_letters,
                         std_mean_letters_in_words = std_mean_letters_in_words,noun_overlap_adj=noun_overlap_adj,noun_overlap_global = noun_overlap_global,
                         cwr_overlap_adj = cwr_overlap_adj, cwr_overlap_global = cwr_overlap_global,arg_overlap_adj=arg_overlap_adj,local_stem_overlap=local_stem_overlap,
                         genre=genre,text_type=text_type,text_len=text_len,authentic=authentic,simplified=simplified,
                         top_frequent_words_1000=top_frequent_words_1000,top_frequent_words_2000=top_frequent_words_2000,top_frequent_words_3000=top_frequent_words_3000,
                         top_frequent_words_4000=top_frequent_words_4000,top_frequent_words_5000=top_frequent_words_5000
                         )

def validate(request):
  print('entered validate method')
  print(request.form)
  error_msg = ''
  if 'author' in request.form and request.form['author']!=None and '@' in request.form['author']:
    print('entered this')
    error_msg = 'loll!!!'
  return error_msg

         

         
         

if __name__ == "__main__":
  app.run(debug=True)
