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
import spacy
import stanza
import textstat
import stanza.models
import re
from stanza.pipeline.core import DownloadMethod
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
all_books = []
nlp = None
pipe_stanza = stanza.Pipeline(lang='es', processors='tokenize,pos,lemma,constituency',download_method=DownloadMethod.REUSE_RESOURCES)

@app.route('/')
def homepage():
  return render_template('landing_page.html')

@app.route('/teachers_and_learners')
def teachers_and_learners():
  global total_num_books
  global show_next
  global per_page
  global results_global
  global results
  global total_num_pages
  global all_books
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
  global results
  print(f"entered fetchAll :")
  return results

@app.route('/fetchAllList',methods=['GET'])
def fetchAllList():
  global results_global
  return results_global

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
  
@app.route('/searchWithCriteria',methods=['GET'])
def searchWithCriteria():
  res_list = []
  col = db['Books_with_metrics']
  keyValuePairs = json.loads(request.args.get('keyValuePairs'))
  print(f'keyValue : {keyValuePairs}')
  if len(keyValuePairs)==1:
    for rec in col.find(keyValuePairs):
      del rec['_id']
      res_list.append(rec)
  else:
    all_condtions = []
    for x in keyValuePairs:
      all_condtions.append({x:keyValuePairs[x]})
    for rec in col.find({'$and':all_condtions}):
      del rec['_id']
      res_list.append(rec)
  print(f"total num of results : {len(res_list)}")
  return res_list

@app.route('/computeMetrics',methods=['GET'])
def computeMetrics():
  global pipe_stanza
  metricsVsValues = {}
  text = request.args.get('enteredText')
  text = text.strip('\n\s+')
  metricsVsValues = computeDescriptiveMetrics(text,pipe_stanza)
  return metricsVsValues

def computeDescriptiveMetrics(text,pipe_stanza):
  #print(f"in compute text is {text}")
  return_dict = {}
  words = text.split() #just splitted the text by spaces
  num_words = len(words)
  return_dict['Number of words'] = num_words
  sents = pipe_stanza(text)
  num_sents = len(sents.sentences)#same as number of sentences returned by stanza paraser
  return_dict['Number of sentences'] = num_sents
  paras = re.split(r"\n\n", text)#splitted by double new line for num paras
  #print(f"paragraphs are : {paras}")
  num_paras = len(paras)
  return_dict['Number of Paragraphs'] = num_paras
  mean_len_paras = 0
  paras_lens = []
  for para in paras:
    para = para.strip('\n')
    sents_in_para = len(pipe_stanza(para).sentences)
    paras_lens.append(sents_in_para)
  mean_len_paras = num_sents/num_paras #total num sentences /total num of paragraphs
  return_dict['Mean length of Paragraphs'] = mean_len_paras
  std_mean_len_paras = 0
  if len(paras_lens)>1:
    for x in paras_lens:
      std_mean_len_paras = std_mean_len_paras + (x-mean_len_paras)**2
    std_mean_len_paras/=(len(paras_lens)-1)
    std_mean_len_paras = std_mean_len_paras**0.5
  return_dict['Standard deviation of Mean length of Paragraphs'] = std_mean_len_paras
  textstat.set_lang('es')
  num_sylls = 0
  syllables_nums = []
  letters_in_words = []
  for word in words:
    curr_word_sylls = textstat.syllable_count(word)
    syllables_nums.append(curr_word_sylls)
    num_sylls+=curr_word_sylls
    letters_in_words.append(len(word))
  mean_num_sylls = num_sylls/num_words
  mean_num_letters = sum(letters_in_words)/num_words
  std_mean_num_letters = 0
  return_dict['Mean number of letters in words'] = mean_num_letters
  if num_words>1:
    for x in letters_in_words:
      std_mean_num_letters = std_mean_num_letters + (x-mean_num_letters)**2
  std_mean_num_letters = std_mean_num_letters/(num_words-1)
  std_mean_num_letters = std_mean_num_letters ** 0.5
  return_dict['Standard deviation of mean number of letters in words'] = std_mean_num_letters
  return_dict['Mean number of syllables per word'] = mean_num_sylls
  std_mean_sylls = 0
  if num_words > 1:
    for x in syllables_nums:
      std_mean_sylls = std_mean_sylls + (x-mean_num_sylls)**2
    std_mean_sylls = std_mean_sylls/(num_words-1)
    std_mean_sylls = std_mean_sylls ** 0.5
  return_dict['Standard deviation of mean number of syllables in words'] = std_mean_sylls
  computeReferentialCohesion(sents,return_dict)
  return return_dict

def computeReferentialCohesion(stanza_op,dict_to_place):
  noun_overlap_global = 0
  noun_overlap_local = 0
  prev_sent = stanza_op.sentences[0]
  nouns_prev = set()
  for token in prev_sent.words:
    if token.pos=='NOUN':
      nouns_prev.add(token.text)
  num_sentences = len(stanza_op.sentences)
  for i in range(1,num_sentences):
    print(f"prev nouns : {nouns_prev}")
    curr_sent = stanza_op.sentences[i]
    nouns_curr = set()
    for token in curr_sent.words:
      if token.pos=='NOUN':
        nouns_curr.add(token.text)
    print(f"current nouns : {nouns_curr}")
    intersection = nouns_prev.intersection(nouns_curr)
    if len(intersection)>0:
      noun_overlap_local+=1
    nouns_prev = nouns_curr
  noun_overlap_local = noun_overlap_local/num_sentences
  dict_to_place['Noun overlap local'] = noun_overlap_local


@app.route('/landing_page')
def landing_page():
  return render_template('landing_page.html')

@app.route('/analyze_text')
def analyze_text():
  return render_template('analyze_text.html')


if __name__ == "__main__":
  app.run(debug=True)
