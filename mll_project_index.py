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
from nltk.corpus import wordnet as wn
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
textstat.set_lang('es')
funs_to_call = []
values_coh_metrics = ['number_of_words','number_of_sentences','number_of_paras','mean_len_paras',
                      'std_mean_len_paras','mean_len_sents','std_mean_len_sents','mean_num_sylls',
                      'mean_num_letters','std_mean_num_letters','noun_overlap_local','noun_overlap_global',
                      'arg_overlap_local','arg_overlap_global','stem_overlap_local','stem_overlap_global','cwr_overlap_global',
                      'cwr_overlap_local',
                      'lsa_adj','ttr_cwr','mod_per_np','syn_med_pos','syn_med_wrd','syn_med_lemmas','syn_sim_adj',
                      'noun_incidence','verb_incidence','adj_incidence','adv_incidence','avg_freq_cwr','avg_freq_all','avg_freq_min',
                      'polysemy','hypernymy','flesch_reading_ease','flesch_kincaid']
dict_coh_metrics = {}
mapping_values_text = {}
start = 0
for x in values_coh_metrics:
  dict_coh_metrics[x] = start
  start = start + 1
print(f"dict_coh_metrics : {dict_coh_metrics}")
def number_of_words(text,stanza_output):
  return len(text.split())

funs_to_call.append(number_of_words)

def number_of_sentences(text,stanza_output):
  return len(stanza_output.sentences)

funs_to_call.append(number_of_sentences)

def number_of_paras(text,stanza_output):
  return len(re.split(r"\n\n",text))

funs_to_call.append(number_of_paras)

def mean_len_paras(text,stanza_output):
  paras = re.split(r"\n\n",text)
  mean_len = 0
  for para in paras:
    para = para.strip("\n")
    mean_len += len(pipe_stanza(para).sentences)
  mean_len = mean_len/len(paras)
  return mean_len

funs_to_call.append(mean_len_paras)

def std_mean_len_paras(text,stanza_output):
  paras = re.split(r"\n\n",text)
  len_paras = []
  for para in paras:
    len_paras.append(len(para.sentences))
  num_paras = len(len_paras)
  mean_len = sum(len_paras)/num_paras
  std = 0
  if num_paras > 1:
    for x in len_paras:
      std+=(x-mean_len)**2
    std/=(num_paras-1)
    std**=0.5
  return std

funs_to_call.append(std_mean_len_paras)

def mean_len_sents(text,stanza_output):
  len_sents = []
  for sent in stanza_output.sentences:
    len_sents.append(len(sent.trim().split()))
  mean_len_sent = sum(len_sents)/len(len_sents)
  return mean_len_sent

funs_to_call.append(mean_len_sents)

def std_mean_len_sents(text,stanza_output):
  len_sents = []
  for sent in stanza_output.sentences:
    len_sents.append(len(sent.trim().split()))
  mean_len_sent = sum(len_sents)/len(len_sents)
  std = 0
  if len(len_sents)>1:
    for x in len_sents:
      std+=(x-mean_len_sent)**2
    std/=(len(len_sents)-1)
    std**=0.5
  return std

funs_to_call.append(std_mean_len_sents)

def mean_num_sylls(text,stanza_output):
  return textstat.syllable_count(text)

funs_to_call.append(mean_num_sylls)

def mean_num_letters(text,stanza_output):
  words = text.split()
  num_letters = 0
  for word in words:
    num_letters+=len(word)
  return num_letters/len(words)

funs_to_call.append(mean_num_letters)

def std_mean_num_letters(text,stanza_output):
  words = text.split()
  words_len = []
  for word in words:
    words_len.append(len(word))
  std = 0
  if len(words_len)>1:
    mean = sum(words_len)/len(words_len)
    for x in words_len:
      std+=(x-mean)**2
    std/=(len(words_len)-1)
    std = std**0.5
  return std

funs_to_call.append(std_mean_num_letters)

def noun_overlap_local(text,stanza_output):
  prev_sent = stanza_output.sentences[0]
  num_sents = len(stanza_output.sentences)
  overlap = 0
  prev_nouns = set()
  for token in prev_sent.words:
    if token.upos == 'NOUN':
      prev_nouns.add(token.text)
  if num_sents > 1:
    for i in range(1,num_sents):
      curr_sent = stanza_output.sentences[i]
      curr_nouns = set()
      for token in curr_sent.words:
        if token.upos=='NOUN':
          curr_nouns.add(token.text)
      if len(curr_nouns.intersection(prev_nouns))>0:
        overlap+=1
      prev_nouns = curr_nouns
  return overlap/num_sents

funs_to_call.append(noun_overlap_local)

def noun_overlap_global(text,stanza_output):
  global_nouns_dict = dict()
  for sent in stanza_output.sentences:
    for token in sent.words:
      if token.upos=='NOUN':
        if token.text in global_nouns_dict:
          global_nouns_dict[token.text] = global_nouns_dict[token.text]+1
        else:
          global_nouns_dict[token.text] = 1
  overlap = 0
  for sent in stanza_output.sentences:
    curr_nouns = dict()
    found_overlap = False
    for token in sent.words:
      if token.upos == 'NOUN':
        if token.text in curr_nouns:
          curr_nouns[token.text] = curr_nouns[token.text]+1
        else:
          curr_nouns[token.text] = 1
    for x in curr_nouns:
      global_nouns_dict[x] = global_nouns_dict[x]-curr_nouns[x]
      if global_nouns_dict[x] <= 0:
        del global_nouns_dict[x]
    for x in curr_nouns:
      if x in global_nouns_dict:
        found_overlap = True
        global_nouns_dict[x] = global_nouns_dict[x] + curr_nouns[x]
      else:
        global_nouns_dict[x] = curr_nouns[x]
    if found_overlap:
      overlap+=1
  return overlap/len(stanza_output.sentences)

funs_to_call.append(noun_overlap_global)

def arg_overlap_local(text,stanza_output):
  overlap = 0
  prev_args = set()
  sent_1 = stanza_output.sentences[0]
  num_sents = len(stanza_output.sentences)
  if num_sents > 1:
    for token in sent_1.words:
      if token.upos == 'NOUN' or token.upos =='PRON':
        prev_args.add(token.lemma)
    for i in range(1,num_sents):
      curr_sent = stanza_output.sentences[i]
      curr_args = set()
      for token in curr_sent.words:
        if token.upos == 'NOUN' or token.upos == 'PRON':
          curr_args.add(token.lemma)
      if len(prev_args.intersection(curr_args)) > 0:
        overlap = overlap + 1
      prev_args = curr_args
  return overlap/num_sents

funs_to_call.append(arg_overlap_local)

def arg_overlap_global(text,stanza_output):
  overlap = 0
  all_args = dict()
  for sent in stanza_output.sentences:
    for token in sent.words:
      if token.upos == 'NOUN' or token.upos == 'PRON':
        if token.lemma in all_args:
          all_args[token.lemma] = all_args[token.lemma] + 1
        else:
          all_args[token.lemma] = 1
  num_sents = len(stanza_output.sentences)
  if num_sents > 1:
    for sent in stanza_output.sentences:
      curr_args = dict()
      found_overlap = False
      for token in sent.words:
        if token.upos=='NOUN' or token.upos=='PRON':
          if token.lemma in curr_args:
            curr_args[token.lemma] = curr_args[token.lemma] + 1
          else:
            curr_args[token.lemma] = 1
      for x in curr_args:
        all_args[x] = all_args[x] - curr_args[x]
        if all_args[x]<=0:
          del all_args[x]
      for x in curr_args:
        if x in all_args:
          found_overlap = True
          all_args[x] = all_args[x] + curr_args[x]
        else:
          all_args[x] = curr_args[x]
      if found_overlap:
        overlap = overlap + 1
  return overlap/num_sents

funs_to_call.append(arg_overlap_global)

def stem_overlap_local(text,stanza_output):
  overlap = 0
  sent_0 = stanza_output.sentences[0]
  prev_stem = set()
  num_sentences = len(stanza_output.sentences)
  if num_sentences > 1:
    for token in sent_0.words:
      if token.upos == 'NOUN' or token.upos == 'VERB' or token.upos =='ADV' or token.upos=='ADJ':
        prev_stem.add(token.lemma)
    for i in range(1,num_sentences):
      curr_sent = stanza_output.sentences[i]
      curr_stems = set()
      for token in curr_sent:
        if token.upos == 'NOUN':
          curr_stems.add(token.lemma)
      if len(curr_stems.intersection(prev_stem))>0:
        overlap+=1
      prev_stem = set()
      for token in curr_sent:
        if token.upos == 'NOUN' or token.upos == 'VERB' or token.upos == 'ADV' or token.upos == 'ADJ':
          prev_stem.add(token.lemma)
    overlap/=num_sentences
  return overlap

funs_to_call.append(stem_overlap_local)

def stem_overlap_global(text,stanza_output):
  overlap = 0
  all_stems = dict()
  num_sentences = len(stanza_output.sentences)
  if num_sentences > 1:
    for sent in stanza_output.sentences:
      for token in sent.words:
        if token.upos == 'NOUN' or token.upos == 'ADV' or token.upos == 'ADJ' or token.upos=='VERB':
          if token.lemma in all_stems:
            all_stems[token.lemma] = all_stems[token.lemma] + 1
          else:
            all_stems[token.lemma] = 1
    for sent in stanza_output.sentences:
      found_overlap = False
      curr_stems_dict = dict()
      for token in sent.words:
        if token.upos == 'NOUN':
          if token.lemma in curr_stems_dict:
            curr_stems_dict[token.lemma] = curr_stems_dict[token.lemma] + 1
          else:
            curr_stems_dict[token.lemma] = 1
      for x in curr_stems_dict:
        all_stems[x] = all_stems[x] - curr_stems_dict[x]
        if all_stems[x] <=0:
          del all_stems[x]
      for x in curr_stems_dict:
        if x in all_stems:
          found_overlap = True
          all_stems[x] = all_stems[x]+curr_stems_dict[x]
        else:
          all_stems[x] = all_stems[x]+curr_stems_dict[x]
      if found_overlap:
        overlap+=1
    return overlap/num_sentences


funs_to_call.append(stem_overlap_global)

def cwr_overlap_global(text,stanza_output):
  overlap = 0
  all_cwrs = dict()
  num_sents = len(stanza_output.sentences)
  if num_sents > 1:
    for sent in stanza_output.sentences:
      for token in sent.words:
        if token.upos == 'NOUN' or token.upos == 'VERB' or token.upos =='ADV' or token.upos=='ADJ':
          if token.text in all_cwrs:
            all_cwrs[token.text] = all_cwrs[token.text]+1
          else:
            all_cwrs[token.text] = 1
    for sent in stanza_output.sentences:
      curr_cwr = []
      for token in sent.words:
        if token.upos == 'NOUN' or token.upos == 'VERB' or token.upos == 'ADV' or token.upos=='ADJ':
          curr_cwr.append(token.text)
          if token.text in all_cwrs:
            all_cwrs[token.text] = all_cwrs[token.text] - 1
            if all_cwrs[token.text] <= 0:
              del all_cwrs[token.text]
      overlap_curr = 0
      for x in curr_cwr:
        if x in all_cwrs:
          overlap_curr+=1
      overlap+=(overlap_curr/len(curr_cwr))
      for x in curr_cwr:
        if x in all_cwrs:
          all_cwrs[x] = all_cwrs[x]+1
        else:
          all_cwrs[x] = 1
  return overlap/num_sents

funs_to_call.append(cwr_overlap_global)

def cwr_overlap_local(text,stanza_output):
  overlap = 0
  num_sents = len(stanza_output.sentences)
  if num_sents > 1:
    sent_0 = stanza_output.sentences[0]
    prev_cwr = set()
    for token in sent_0.words:
      if token.upos == 'NOUN' or token.upos == 'VERB' or token.upos == 'ADV' or token.upos == 'ADJ':
        prev_cwr.add(token.text)
    for i in range(1,num_sents):
      sent_i = stanza_output.sentences[i]
      curr_cwr = []
      curr_cwr_set = set()
      for token in sent_i.words:
        if token.upos == 'NOUN' or token.upos == 'VERB' or token.upos == 'ADV' or token.upos == 'ADJ':
          curr_cwr.append(token.text)
          curr_cwr_set.add(token.text)
      curr_overlap = 0
      for x in curr_cwr:
        if x in prev_cwr:
          curr_overlap+=1
      curr_overlap/=len(curr_cwr)
      overlap+=curr_overlap
      prev_cwr = curr_cwr_set
  return overlap

funs_to_call.append(cwr_overlap_local)

def lsa_adj(text,stanza_output):
  #to-do
  return 0

funs_to_call.append(lsa_adj)

def ttr_cwr(text,stanza_output):
  types_cwr = set()
  num_tokens_cwr = 0
  for sent in stanza_output.sentences:
    for token in sent.words:
      if token.upos == 'NOUN' or token.upos == 'VERB' or token.upos == 'ADV' or token.upos == 'ADJ':
        types_cwr.add(token.text)
        num_tokens_cwr+=1
  return len(types_cwr)/num_tokens_cwr

funs_to_call.append(ttr_cwr)

def mod_per_np(text,stanza_output):
  #to-do
  return 0

funs_to_call.append(mod_per_np)

def syn_med_pos(text,stanza_output):
  #to-do
  return 0

funs_to_call.append(syn_med_pos)

def syn_med_wrd(text,stanza_output):
  #to-do
  return 0

funs_to_call.append(syn_med_wrd)

def syn_med_lemmas(text,stanza_output):
  #to-do
  return 0

funs_to_call.append(syn_med_lemmas)

def syn_sim_adj(text,stanza_output):
  #to-do
  return 0

funs_to_call.append(syn_sim_adj)

def noun_incidence(text,stanza_output):
  all_poses = []
  for sent in stanza_output.sentences:
    for token in sent.words:
      all_poses.append(token.upos)
  prev_count = 0
  for i in range(0,min(1000,len(all_poses))):
    if all_poses[i] == 'NOUN':
      prev_count+=1
  incidences_until_i = []
  if all_poses[0]=='NOUN':
    incidences_until_i.append(1)
  else:
    incidences_until_i.append(0)
  for i in range(1,len(all_poses)):
    if all_poses[i] == 'NOUN':
      incidences_until_i.append(incidences_until_i[i-1]+1)
    else:
      incidences_until_i.append(incidences_until_i[i-1])
  incidences = []
  incidences.append(prev_count)
  for i in range(1,len(all_poses)):
    j = min(i+1000,len(all_poses))
    incidences.append(incidences_until_i[j]-incidences_until_i[i-1])
  return sum(incidences)/len(incidences)

funs_to_call.append(noun_incidence)

def verb_incidence(text,stanza_output):
  all_poses = []
  for sent in stanza_output.sentences:
    for token in sent.words:
      all_poses.append(token.upos)
  prev_count = 0
  for i in range(0,min(1000,len(all_poses))):
    if all_poses[i] == 'VERB':
      prev_count+=1
  incidences_until_i = []
  if all_poses[0]=='VERB':
    incidences_until_i.append(1)
  else:
    incidences_until_i.append(0)
  for i in range(1,len(all_poses)):
    if all_poses[i] == 'VERB':
      incidences_until_i.append(incidences_until_i[i-1]+1)
    else:
      incidences_until_i.append(incidences_until_i[i-1])
  incidences = []
  incidences.append(prev_count)
  for i in range(1,len(all_poses)):
    j = min(i+1000,len(all_poses))
    incidences.append(incidences_until_i[j]-incidences_until_i[i-1])
  return sum(incidences)/len(incidences)

funs_to_call.append(verb_incidence)

def adj_incidence(text,stanza_output):
  all_poses = []
  for sent in stanza_output.sentences:
    for token in sent.words:
      all_poses.append(token.upos)
  prev_count = 0
  for i in range(0,min(1000,len(all_poses))):
    if all_poses[i] == 'ADJ':
      prev_count+=1
  incidences_until_i = []
  if all_poses[0]=='ADJ':
    incidences_until_i.append(1)
  else:
    incidences_until_i.append(0)
  for i in range(1,len(all_poses)):
    if all_poses[i] == 'ADJ':
      incidences_until_i.append(incidences_until_i[i-1]+1)
    else:
      incidences_until_i.append(incidences_until_i[i-1])
  incidences = []
  incidences.append(prev_count)
  for i in range(1,len(all_poses)):
    j = min(i+1000,len(all_poses))
    incidences.append(incidences_until_i[j]-incidences_until_i[i-1])
  return sum(incidences)/len(incidences)

funs_to_call.append(adj_incidence)

def adv_incidence(text,stanza_output):
  all_poses = []
  for sent in stanza_output.sentences:
    for token in sent.words:
      all_poses.append(token.upos)
  prev_count = 0
  for i in range(0,min(1000,len(all_poses))):
    if all_poses[i] == 'ADV':
      prev_count+=1
  incidences_until_i = []
  if all_poses[0]=='ADV':
    incidences_until_i.append(1)
  else:
    incidences_until_i.append(0)
  for i in range(1,len(all_poses)):
    if all_poses[i] == 'ADV':
      incidences_until_i.append(incidences_until_i[i-1]+1)
    else:
      incidences_until_i.append(incidences_until_i[i-1])
  incidences = []
  incidences.append(prev_count)
  for i in range(1,len(all_poses)):
    j = min(i+1000,len(all_poses))
    incidences.append(incidences_until_i[j]-incidences_until_i[i-1])
  return sum(incidences)/len(incidences)

funs_to_call.append(adv_incidence)

def avg_freq_cwr(text,stanza_output):
  #to-do
  return 0

funs_to_call.append(avg_freq_cwr)

def avg_freq_all(text,stanza_output):
  #to-do
  return 0

funs_to_call.append(avg_freq_all)

def avg_freq_min(text,stanza_output):
  #to-do
  return 0

funs_to_call.append(avg_freq_min)

def polysemy(text,stanza_output):
  total_cwr = 0
  total_freq = 0
  for sent in stanza_output.sentences:
    for token in sent.words:
      if token.upos == 'NOUN' or token.upos == 'VERB' or token.upos == 'ADV' or token.upos == 'ADJ':
        total_cwr+=1
        total_freq+=len(wn.synsets(token.text,lang="spa"))
  return total_freq/total_cwr

funs_to_call.append(polysemy)

def hypernymy(text,stanza_output):
  #to-do
  return 0

funs_to_call.append(hypernymy)

def flesch_reading_ease(text,stanza_output):
  return textstat.flesch_reading_ease(text)

funs_to_call.append(flesch_reading_ease)

def flesch_kincaid(text,stanza_output):
  return textstat.flesch_kincaid_grade(text)

funs_to_call.append(flesch_kincaid)


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
  global funs_to_call
  metricsVsValues = {}
  text = request.args.get('enteredText')
  metrics_to_compute = json.loads(request.args.get('metricsToCompute'))
  print(f"text is {text} and metrics are {metrics_to_compute}")
  text = text.strip('\n\s+')
  print(f"text is {text}")
  computed_staza = pipe_stanza(text)
  for x in metrics_to_compute:
    print(f"isis : {x}")
    metricsVsValues[x] = funs_to_call[dict_coh_metrics[x]](text,computed_staza)
    print(f"{metricsVsValues[x]}")
  return metricsVsValues

@app.route('/landing_page')
def landing_page():
  return render_template('landing_page.html')

@app.route('/analyze_text')
def analyze_text():
  return render_template('analyze_text.html')

def compute_descriptive_metrics(text,stanza_output,dict_to_put):
  words = text.split()
  num_words = len(words)
  dict_to_put['Number of words'] = num_words
  num_sents = len(stanza_output.sentences)
  dict_to_put['Number of sentences'] = num_sents
  paras = re.split(r"\n\n",text)
  len_paras = len(paras)
  dict_to_put['Number of Paragraphs'] = len_paras
  paras_lens = []
  for para in paras:
    paras_lens.append(len(pipe_stanza(para).sentences))
  mean_len_paras = sum(paras_lens)/len(paras_lens)
  dict_to_put['Mean length of paragraphs'] = mean_len_paras
  std_mean_len_paras = 0
  if len_paras > 1:
     for x in paras_lens:
       std_mean_len_paras = std_mean_len_paras + (x-mean_len_paras)**2
     std_mean_len_paras /=(len_paras-1)
     std_mean_len_paras = std_mean_len_paras ** 0.5
  dict_to_put['Standard deviation of mean length of paras'] = std_mean_len_paras
  words_in_sents = []
  for sent in stanza_output.sentences:
    words_in_sents.append(len(sent.split()))
  mean_len_sents = sum(words_in_sents)/len(words_in_sents)
  dict_to_put['Mean length of sentences'] = mean_len_sents
  std_mean_len_sents = 0
  if num_sents > 1:
    for x in words_in_sents:
      std_mean_len_sents = std_mean_len_sents + (x-mean_len_sents)**2
    std_mean_len_sents/=(num_sents - 1)
    std_mean_len_sents = std_mean_len_sents ** 0.5
  dict_to_put['Standard deviation of mean length of sentences'] = std_mean_len_sents
  sylls_lens = []
  for word in words:
    sylls_lens.append(textstat.syllable_count(word))
  mean_num_sylls = sum(sylls_lens)/len(sylls_lens)
  dict_to_put['Mean number of syllables'] = mean_num_sylls
  std_mean_num_sylls = 0
  if len(sylls_lens) > 1:
    for x in sylls_lens:
      std_mean_num_sylls = std_mean_num_sylls + (x-mean_num_sylls)**2
    std_mean_num_sylls/=(len(sylls_lens)-1)
    std_mean_num_sylls**=0.5
  dict_to_put['Standard deviation of mean number of syllables'] = std_mean_num_sylls
  words_lens = []
  for word in words:
    words_lens.append(len(word))
  mean_num_letters = sum(words_lens)/len(words_lens)
  dict_to_put['Mean number of letters in words'] = mean_num_letters
  std_mean_num_letters = 0
  if len(words_lens) > 1:
    for x in words_lens:
      std_mean_num_letters = std_mean_num_letters + (x-mean_num_letters)**2
    std_mean_num_letters/=(len(words_lens)-1)
    std_mean_num_letters **=0.5
  dict_to_put['Standard deviation of mean number of letters in words'] = std_mean_num_letters
  return dict_to_put

def compute_word_information(text,stanza_output,dict_to_put):
  noun_overlap_adj = 0
  noun_overlap_global = 0
  arg_overlap_local = 0
  arg_overlap_global = 0
  stem_overlap_global = 0
  stem_overlap_local = 0
  cwr_overlap_local = 0
  cwr_overlap_global = 0
  num_sents = len(stanza_output.sentences)
  sents_0 = stanza_output.sentences[0]
  sents_0_nouns = set()
  for token in sents_0.words:
    if token.upos == 'NOUN':
      sents_0_nouns.add(token.text)
  noun_overlap_adj = 0
  if num_sents > 1:
    for i in range(1,num_sents):
      curr_sent = stanza_output.sentences[i]
      curr_nouns = set()
      for word in curr_sent.words:


    

  return dict_to_put

if __name__ == "__main__":
  app.run(debug=True)
