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
from ntlk.corpus import stopwords
from collections import Counter
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
stop_spanish = set(stopwords.words('spanish'))

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
  metricsVsValues = {}
  text = request.args.get('enteredText')
  metrics_to_compute = json.loads(request.args.get('metricsToCompute'))
  print(f"text is {text} and metrics are {metrics_to_compute}")
  text = text.strip('\n\s+')
  print(f"text is {text}")
  computed_staza = pipe_stanza(text)
  metricsVsValues = compute_descriptive_metrics(text,computed_staza,metricsVsValues)
  metricsVsValues = compute_referential_cohesion(text,computed_staza,metricsVsValues)
  metricsVsValues = latent_semantic_analysis(text,computed_staza,metricsVsValues)
  metricsVsValues = lexical_diversity(text,computed_staza,metricsVsValues)
  metricsVsValues = syntactic_complexity(text,computed_staza,metricsVsValues)
  metricsVsValues = word_information(text,computed_staza,metricsVsValues)
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

def compute_referential_cohesion(text,stanza_output,dict_to_put):
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
  prev_nouns = set()
  all_nouns = dict()
  arguments_prev = set()
  all_args = dict()
  prev_stems = set()
  all_stems = dict()
  prev_cwr = set()
  all_cwr = dict()
  for token in sents_0.words:
    if token.upos == 'NOUN':
      prev_nouns.add(token.text)
      if token.text in all_nouns:
        all_nouns[token.text] = all_nouns[token.text]+1
      else:
        all_nouns[token.text] = 1
    if token.upos == 'NOUN' or token.upos == 'PRON':
      arguments_prev.add(token.lemma)
      if token.lemma in all_args:
        all_args[token.lemma] = all_args[token.lemma] + 1
      else:
        all_args[token.lemma] = 1
    if token.upos == 'NOUN' or token.upos == 'VERB' or token.upos == 'ADV' or token.upos == 'ADJ':
      prev_stems.add(token.lemma)
      prev_cwr.add(token.text)
      if token.lemma in all_stems:
        all_stems[token.lemma] = all_stems[token.lemma] + 1
      else:
        all_stems[token.lemma] = 1
      if token.text in all_cwr:
        all_cwr[token.text] = all_cwr[token.text] + 1
      else:
        all_cwr[token.text] = 1
  if num_sents > 1:
    for i in range(1,num_sents):
      curr_sent = stanza_output.sentences[i]
      curr_nouns = set()
      curr_args = set()
      curr_noun_lemmas = set()
      curr_stems_lemmas = set()
      curr_cwr = []
      curr_cwr_set = set()
      curr_cwr_overlap = 0
      for word in curr_sent.words:
        if word.upos == 'NOUN':
          curr_nouns.add(word.text)
          curr_noun_lemmas.add(word.lemma)
          if word.text in all_nouns:
            all_nouns[word.text] = all_nouns[word.text]+1
          else:
            all_nouns[word.text] = 1
        if word.upos == 'NOUN' or word.upos == 'PRON':
          curr_args.add(word.lemma)
          if word.lemma in all_args:
            all_args[word.lemma] = all_args[word.lemma] + 1
          else:
            all_args[word.lemma] = 1
        if word.upos == 'NOUN' or word.upos == 'VERB' or word.upos == 'ADV' or word.upos == 'ADJ':
          curr_stems_lemmas.add(word.lemma)
          curr_cwr.append(word.text)
          curr_cwr_set.add(word.text)
          if word.lemma in all_stems:
            all_stems[word.lemma] = all_stems[word.lemma] + 1
          else:
            all_stems[word.lemma] = 1
          if word.text in all_cwr:
            all_cwr[token.text] = all_cwr[token.text] + 1
          else:
            all_cwr[token.text] = 1
      if len(curr_nouns.intersection(prev_nouns)) > 0:
        noun_overlap_adj+=1
      if len(curr_args.intersection(arguments_prev)) > 0:
        arg_overlap_local+=1
      if len(curr_noun_lemmas.intersection(prev_stems)) > 0:
        stem_overlap_local+=1
      for x in curr_cwr:
        if x in prev_cwr:
          curr_cwr_overlap = curr_cwr_overlap + 1
      curr_cwr_overlap/=len(curr_cwr)
      cwr_overlap_local = cwr_overlap_local + curr_cwr_overlap
      prev_nouns = curr_nouns
      arguments_prev = curr_args
      prev_stems = curr_stems_lemmas
      prev_cwr = curr_cwr
  noun_overlap_adj/=num_sents
  arg_overlap_local/=num_sents
  stem_overlap_local/=num_sents
  dict_to_put['Noun overlap adjacent'] = noun_overlap_adj
  dict_to_put['Argument overlap adjacent'] = arg_overlap_local
  dict_to_put['Stem overlap adjacent'] = stem_overlap_local
  dict_to_put['Content word overlap local'] = cwr_overlap_local
  for i in range(num_sents):
    curr_sent = stanza_output.sentences[i]
    curr_nouns = dict()
    curr_args = dict()
    curr_nouns_lemmas = dict()
    curr_cwr_dict = dict()
    curr_cwr_list = []
    for word in curr_sent.words:
      if word.upos == 'NOUN':
        if word.text in curr_nouns:
          curr_nouns[word.text] = curr_nouns[word.text] + 1
        else:
          curr_nouns[word.text] = 1
        if word.lemma in curr_nouns_lemmas:
          curr_noun_lemmas[word.lemma] = curr_noun_lemmas[word.lemma] + 1
        else:
          curr_noun_lemmas[word.lemma] = 1
      if word.upos == 'NOUN' or word.upos == 'PRON':
        if word.lemma in curr_args:
          curr_args[word.lemma] = curr_args[word.lemma] +1
        else:
          curr_args[word.lemma] = 1
      if word.upos == 'NOUN' or word.upos == 'VERB' or word.upos == 'ADV' or word.upos == 'ADJ':
        if word.text in curr_cwr_dict:
          curr_cwr_dict[word.text] = curr_cwr_dict[word.text] + 1
        else:
          curr_cwr_dict[word.text] = 1
        curr_cwr_list.append(word.text)
    for x in curr_nouns:
      if x in all_nouns:
        all_nouns[x] = all_nouns[x] - curr_nouns[x]
        if all_nouns[x] <= 0:
          del all_nouns[x]
    for x in curr_args:
      if x in all_args:
        all_args[x] = all_args[x] - curr_args[x]
        if all_args[x] <= 0:
          del all_args[x]
    for x in curr_noun_lemmas:
      if x in all_stems:
        all_stems[x] = all_stems[x] - curr_noun_lemmas[x]
        if all_stems[x] <= 0:
          del all_stems[x]
    for x in curr_cwr_dict:
      if x in all_cwr:
        all_cwr[x] = all_cwr[x] - curr_cwr_dict[x]
        if all_cwr[x]<=0:
          del all_cwr[x]
    found_overlap = False
    found_overlap_arg = False
    found_stem_overlap_global = False
    curr_cwr_overlap = 0
    for x in curr_cwr_list:
      if x in all_cwr:
        curr_cwr_overlap+=1
    cwr_overlap_global+=(curr_cwr_overlap/len(curr_cwr_list))
    for x in curr_cwr_dict:
      if x in all_cwr:
        all_cwr[x] = all_cwr[x] + curr_cwr_dict[x]
      else:
        all_cwr[x] = curr_cwr_dict[x]
    for x in curr_nouns:
      if x in all_nouns:
        found_overlap = True
        all_nouns[x] = all_nouns[x] + curr_nouns[x]
      else:
        all_nouns[x] = curr_nouns[x]
    for x in curr_noun_lemmas:
      if x in all_stems:
        found_stem_overlap_global = True
        all_stems[x] = all_stems[x] + curr_noun_lemmas[x]
      else:
         all_stems[x] = curr_noun_lemmas[x]
    if found_overlap:
      noun_overlap_global+=1
    for x in curr_args:
      if x in all_args:
        found_overlap_arg = True
        all_args[x] = all_args[x] + curr_args[x]
      else:
        all_args[x] = curr_args[x]
    if found_overlap_arg:
      arg_overlap_global+=1
    if found_stem_overlap_global:
      stem_overlap_global+=1
  noun_overlap_global/=num_sents
  dict_to_put['Noun overlap global'] = noun_overlap_global
  arg_overlap_global/=num_sents
  dict_to_put['Argument overlap global'] = arg_overlap_global
  stem_overlap_global/=num_sents
  dict_to_put['Global stem overlap'] = stem_overlap_global
  dict_to_put['Global content word overlap'] = cwr_overlap_global
  return dict_to_put

def latent_semantic_analysis(text,stanza_output,dict_to_put):
  #to-do
  return dict_to_put

def lexical_diversity(text,stanza_output,dict_to_put):
  content_words = set()
  content_words_count = 0
  all_words = set()
  all_words_count = 0
  for sent in stanza_output.sentences:
    for token in sent.words:
      if token.text not in stop_spanish:
        if token.upos == 'NOUN' or token.upos == 'VERB' or token.upos == 'ADV' or token.upos == 'ADJ':
          content_words.add(token.text)
          content_words_count+=1
        all_words.add(token.text)
        all_words_count+=1
  dict_to_put['Lexical Diversity for all words'] = len(all_words)/all_words_count
  dict_to_put['Lexical Diversity for content words'] = len(content_words)/content_words_count
  return dict_to_put

def syntactic_complexity(text,stanza_output,dict_to_put):
  return dict_to_put

def word_information(text,stanza_output,dict_to_put):
  avg_freq_all_words = 0
  avg_freq_content_words = 0
  all_poses = []
  words_dict = dict()
  word_cwr_dict = dict()
  curr_sent_tokens = []
  min_freqs = []
  polysemies = []
  for sent in stanza_output.sentences:
    curr_sent_tokens = []
    for token in sent.words:
      all_poses.append(token.upos)
    if token.text not in stop_spanish:
      curr_sent_tokens.append(token.text)
      if token.upos == 'NOUN' or token.upos == 'VERB' or token.upos == 'ADV' or token.upos == 'ADJ':
        polysemies.append(len(wn.synsets(token.text,"spa")))
        if token.text in word_cwr_dict:
          word_cwr_dict[token.text] = word_cwr_dict[token.text]+1
        else:
          word_cwr_dict[token.text] = 1
      if token.text in words_dict:
        words_dict[token.text] = words_dict[token.text] + 1
      else:
        words_dict[token.text] = 1
    counter_words = Counter(curr_sent_tokens)
    min_freqs.append(counter_words.most_common()[-1][1])
  dict_to_put['Minimum average frequency of words in all sentences'] = sum(min_freqs)/len(min_freqs)
  for word in words_dict:
    avg_freq_all_words+=words_dict[word]
  avg_freq_all_words/=len(words_dict)
  dict_to_put['Average frequency of all words'] = avg_freq_all_words
  for word in word_cwr_dict:
    avg_freq_content_words+=word_cwr_dict[word]
  avg_freq_content_words/=len(word_cwr_dict)
  dict_to_put['Average frequency of content words'] = avg_freq_content_words
  dict_to_put['Average polysemy of content words'] = sum(polysemies)/len(polysemies)
  len_poses = len(all_poses)
  inc_nouns = []
  inc_adjs = []
  inc_advs = []
  inc_verbs = []
  inc_nouns_win_1 = 0
  inc_verbs_win_1 = 0
  inc_adv_win_1 = 0
  inc_adj_win_1 = 0
  for i in range(0,min(1000,len_poses)):
    if all_poses[i] == 'NOUN':
      inc_nouns_win_1+=1
    elif all_poses[i] == 'VERB':
      inc_verbs_win_1+=1
    elif all_poses[i] == 'ADV':
      inc_adv_win_1+=1
    elif all_poses[i] == 'ADJ':
      inc_adj_win_1+=1
  inc_nouns.append(inc_nouns_win_1/1000)
  inc_adjs.append(inc_adj_win_1/1000)
  inc_advs.append(inc_adv_win_1/1000)
  inc_verbs.append(inc_verbs_win_1/1000)
  if len_poses>1000:
    for i in range(1,len_poses):
      j = min(i+999,len_poses)
      if j-i+1==1000:
        inc_noun_prev = inc_nouns[i-1]
        inc_verb_prev = inc_verbs[i-1]
        inc_adv_prev = inc_advs[i-1]
        inc_adj_prev = inc_adjs[i-1]
        if all_poses[i-1]=='NOUN':
          inc_noun_prev-=1
        elif all_poses[i-1] == 'VERB':
          inc_verb_prev-=1
        elif all_poses[i-1] == 'ADV':
          inc_adv_prev-=1
        elif all_poses[i-1] == 'ADJ':
          inc_adj_prev-=1
        if all_poses[j] == 'NOUN':
          inc_noun_prev+=1
        elif all_poses[j] == 'VERB':
          inc_verb_prev+=1
        elif all_poses[j] == 'ADV':
          inc_adv_prev+=1
        elif all_poses[j] == 'ADJ':
          inc_adj_prev+=1
        inc_nouns.append(inc_noun_prev/1000)
        inc_adjs.append(inc_adj_prev/1000)
        inc_advs.append(inc_adv_prev/1000)
        inc_verbs.append(inc_verb_prev/1000)
  dict_to_put['Noun incidence average'] = sum(inc_nouns)/len(inc_nouns)
  dict_to_put['Verb incidence average'] = sum(inc_verbs)/len(inc_verbs)
  dict_to_put['Adverb incidence average'] = sum(inc_advs)/len(inc_advs)
  dict_to_put['Adjective incidence average'] = sum(inc_adjs)/len(inc_adjs)
  dict_to_put['Flesch reading ease'] = textstat.flesch_reading_ease(text)
  dict_to_put['Flesch kincaid grade level'] = textstat.flesch_kincaid_grade(text)
  return dict_to_put

if __name__ == "__main__":
  app.run(debug=True)
