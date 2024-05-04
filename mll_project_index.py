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
import stanza
import textstat
import stanza.models
import re
from stanza.pipeline.core import DownloadMethod
from nltk.corpus import wordnet as wn
from nltk.corpus import stopwords
from collections import Counter
from Levenshtein import distance
from pypdf import PdfReader
from nltk.collocations import *
import nltk
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
  print(f"text is {text}")
  text = text.strip('\n\s+')
  print(f"text is {text}")
  computed_staza = pipe_stanza(text)
  metricsVsValues = compute_descriptive_metrics(text,computed_staza,metricsVsValues)
  metricsVsValues = compute_ref_adj(text,computed_staza,metricsVsValues)
  metricsVsValues = compute_ref_global(text,computed_staza,metricsVsValues)
  metricsVsValues = latent_semantic_analysis(text,computed_staza,metricsVsValues)
  metricsVsValues = lexical_diversity(text,computed_staza,metricsVsValues)
  metricsVsValues = syntactic_complexity(text,computed_staza,metricsVsValues)
  metricsVsValues = word_information(text,computed_staza,metricsVsValues)
  metricsVsValues = returnTopNouns(text,computed_staza,metricsVsValues)
  metricsVsValues = returnTopVerbs(text,computed_staza,metricsVsValues)
  metricsVsValues = returnTopAdjectives(text,computed_staza,metricsVsValues)
  metricsVsValues = returnTopCollocations(text,computed_staza,metricsVsValues)
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
    words_in_sents.append(len(sent.words))
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


def compute_ref_adj(text,stanza_output,dict_to_put):
  num_sents = len(stanza_output.sentences)
  if num_sents > 1:
    sent_0 = stanza_output.sentences[0]
    noun_overlap_adj = 0
    arg_overlap_adj = 0
    stem_overlap_adj = 0
    cwr_overlap_adj = 0
    prev_nouns = set()
    prev_args = set()
    prev_stems = set()
    prev_cwrs = []
    for word in sent_0.words:
      if word.upos == 'NOUN':
        prev_nouns.add(word.text)
      if word.upos == 'NOUN' or word.upos == 'PRON':
        prev_args.add(word.text)
      if word.upos == 'NOUN' or word.upos == 'VERB' or word.upos == 'ADV' or word.upos == 'ADJ':
        prev_stems.add(word.lemma)
        prev_cwrs.append(word.text)
    for i in range(1,num_sents):
      curr_sent = stanza_output.sentences[i]
      curr_nouns = set()
      curr_args = set()
      curr_nouns_stems = set()
      curr_cwr_stems = set()
      curr_cwrs = []
      for word in curr_sent.words:
        if word.upos == 'NOUN':
          curr_nouns.add(word.text)
          curr_nouns_stems.add(word.lemma)
        if word.upos == 'NOUN' or word.upos=='PRON':
          curr_args.add(word.text)
        if word.upos == 'NOUN' or word.upos == 'VERB' or word.upos == 'ADV' or word.upos == 'ADJ':
          curr_cwr_stems.add(word.lemma)
          curr_cwrs.append(word.text)
      if len(curr_nouns.intersection(prev_nouns)) > 0:
        noun_overlap_adj+=1
      if len(curr_args.intersection(prev_args)) > 0:
        arg_overlap_adj+=1
      if len(curr_nouns_stems.intersection(prev_stems)) > 0:
        stem_overlap_adj+=1
      curr_cwr_overlap = 0
      for x in curr_cwrs:
        if x in prev_cwrs:
          curr_cwr_overlap+=1
      if len(curr_cwrs)>0:
        curr_cwr_overlap/=len(curr_cwrs)
        cwr_overlap_adj+=curr_cwr_overlap
    prev_nouns = curr_nouns
    prev_args = curr_args
    prev_stems = curr_cwr_stems
    prev_cwrs = curr_cwrs
    noun_overlap_adj/=num_sents
    arg_overlap_adj/=num_sents
    stem_overlap_adj/=num_sents
    cwr_overlap_adj/=num_sents
  dict_to_put['Noun overlap adjacent'] = noun_overlap_adj
  dict_to_put['Argument overlap adjacent'] = arg_overlap_adj
  dict_to_put['Stem overlap adjacent'] = stem_overlap_adj
  dict_to_put['Content word overlap adjacent'] = cwr_overlap_adj
  return dict_to_put


def compute_ref_global(text,stanza_output,dict_to_put):
  noun_overlap_global = 0
  cwr_overlap_global = 0
  stem_overlap_global = 0
  arg_overlap_global = 0
  all_nouns = dict()
  all_stems = dict()
  all_cwrs = dict()
  all_args = dict()
  num_sents = len(stanza_output.sentences)
  if num_sents > 1:
    for sent in stanza_output.sentences:
      for word in sent.words:
        if word.upos == 'NOUN':
          if word.text in all_nouns:
            all_nouns[word.text] = all_nouns[word.text] + 1
          else:
            all_nouns[word.text] = 1
        if word.upos == 'NOUN' or word.upos == 'PRON':
          if word.text in all_args:
            all_args[word.text] = all_args[word.text] + 1
          else:
            all_args[word.text] = 1
        if word.upos == 'NOUN' or word.upos == 'VERB' or word.upos == 'ADV' or word.upos == 'ADJ':
          if word.text in all_cwrs:
            all_cwrs[word.text] = all_cwrs[word.text] + 1
          else:
            all_cwrs[word.text] = 1
          if word.lemma in all_stems:
            all_stems[word.lemma] = all_stems[word.lemma] + 1
          else:
            all_stems[word.lemma] = 1
    for sent in stanza_output.sentences:
      curr_nouns = dict()
      curr_noun_stems = dict()
      curr_args = dict()
      curr_cwrs = dict()
      for word in sent.words:
        if word.upos == 'NOUN':
          if word.text in curr_nouns:
            curr_nouns[word.text] = curr_nouns[word.text] + 1
          else:
            curr_nouns[word.text] = 1
          if word.lemma in curr_noun_stems:
            curr_noun_stems[word.lemma] = curr_noun_stems[word.lemma] + 1
          else:
            curr_noun_stems[word.lemma] = 1
        if word.upos == 'NOUN' or word.upos == 'PRON':
          if word.text in curr_args:
            curr_args[word.text] = curr_args[word.text] + 1
          else:
            curr_args[word.text] = 1
        if word.upos == 'NOUN' or word.upos =='VERB' or word.upos == 'ADV' or word.upos == 'ADJ':
          if word.text in curr_cwrs:
            curr_cwrs[word.text] = curr_cwrs[word.text]+1
          else:
            curr_cwrs[word.text] = 1
      #removing current sent nouns to check global overlap with other sentences' nouns
      for x in curr_nouns:
        if x in all_nouns:
          all_nouns[x] = all_nouns[x] - curr_nouns[x]
          if all_nouns[x] <= 0:
            del all_nouns[x]
      found_overlap_noun = False
      #putting back nouns and checking if any noun from current sent overlapped with other sentences
      for x in curr_nouns:
        if x in all_nouns:
          found_overlap_noun = True
          all_nouns[x] = all_nouns[x] + curr_nouns[x]
        else:
          all_nouns[x] = curr_nouns[x]
      if found_overlap_noun:
        noun_overlap_global+=1
      #removing curr noun stems from all stems before checking for overlap
      for x in curr_noun_stems:
        if x in all_stems:
          all_stems[x] = all_stems[x] - curr_noun_stems[x]
        if all_stems[x] <= 0:
          del all_stems[x]
      found_stem_overlap = False
      for x in curr_noun_stems:
        if x in all_stems:
          found_stem_overlap = True
          all_stems[x] = all_stems[x] + curr_noun_stems[x]
        else:
          all_stems[x] = curr_noun_stems[x]
      if found_stem_overlap:
        stem_overlap_global+=1
      #arguments
      for x in curr_args:
        if x in all_args:
          all_args[x] = all_args[x] - curr_args[x]
          if all_args[x]<=0:
            del all_args[x]
      found_arg_overlap = False
      for x in curr_args:
        if x in all_args:
          found_arg_overlap = True
          all_args[x] = all_args[x] + curr_args[x]
        else:
          all_args[x] = curr_args[x]
      if found_arg_overlap:
        arg_overlap_global+=1
      #content words
      for x in curr_cwrs:
        if x in all_cwrs:
          all_cwrs[x] = all_cwrs[x] - curr_cwrs[x]
          if all_cwrs[x]<=0:
            del all_cwrs[x]
      cwr_overlap_curr = 0
      curr_num_cwrs = 0
      for x in curr_cwrs:
        curr_num_cwrs+=curr_cwrs[x]
        if x in all_cwrs:
          cwr_overlap_curr+=min(all_cwrs[x],curr_cwrs[x])
          all_cwrs[x] = all_cwrs[x] + curr_cwrs[x]
        else:
          all_cwrs[x] = curr_cwrs[x]
      if curr_num_cwrs>0:
        cwr_overlap_global+=(cwr_overlap_curr/curr_num_cwrs)  
    dict_to_put['Content word overlap global'] = cwr_overlap_global
    dict_to_put['Global noun overlap'] = noun_overlap_global/num_sents
    dict_to_put['Global stem overlap'] = stem_overlap_global/num_sents
    dict_to_put['Global argument overlap'] = arg_overlap_global/num_sents
  return dict_to_put

def latent_semantic_analysis(text,stanza_output,dict_to_put):
  num_sentences = len(stanza_output.sentences)
  sent_0 = stanza_output.sentences[0]
  prev_words = set()
  lsa_adj = 0
  for word in sent_0.words:
    if word.text not in stop_spanish:
      prev_words.add(word.text)
  if num_sentences > 1:
    for i in range(1,num_sentences):
      curr_sent = stanza_output.sentences[i]
      curr_words = set()
      for token in curr_sent.words:
        if token.text not in stop_spanish:
          curr_words.add(token.text)
      if len(curr_words)>0:
        lsa_adj+=len(curr_words.intersection(prev_words))/(len(curr_words))
      prev_words = curr_words
  dict_to_put['Latent semantic analysis adjacent'] = lsa_adj/num_sentences
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
  dict_to_put['Type token ratio for all words'] = len(all_words)/all_words_count
  dict_to_put['Type token ratio for content words'] = len(content_words)/content_words_count
  return dict_to_put

def syntactic_complexity(text,stanza_output,dict_to_put):
  min_edit_pos = 0
  min_edit_word = 0
  min_edit_lemma = 0
  num_sents = len(stanza_output.sentences)
  if num_sents>1:
    sent_0 = stanza_output.sentences[0]
    prev_words = []
    prev_lemmas = []
    prev_poses = []
    for word in sent_0.words:
      prev_words.append(word.text)
      prev_lemmas.append(word.lemma)
      prev_poses.append(word.upos)
    for i in range(1,num_sents):
      sent_i = stanza_output.sentences[i]
      curr_words = []
      curr_lemmas = []
      curr_poses = []
      for word in sent_i.words:
        curr_words.append(word.text)
        curr_lemmas.append(word.lemma)
        curr_poses.append(word.upos)
      min_edit_pos+=distance(prev_poses,curr_poses)
      min_edit_word+=distance(prev_words,curr_words)
      min_edit_lemma+=distance(prev_lemmas,curr_lemmas)
      prev_words = curr_words
      prev_lemmas = curr_lemmas
      prev_poses = curr_poses
    min_edit_pos/=num_sents
    min_edit_word/=num_sents
    min_edit_lemma/=num_sents
    dict_to_put['Average minimum edit distance of POSes between adjacent sentences'] = min_edit_pos
    dict_to_put['Average minimum edit distance of lemmas between adjacent sentences'] = min_edit_lemma
    dict_to_put['Average minimum edit distance of words between adjacent sentences'] = min_edit_word
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
        polysemies.append(len(wn.synsets(token.text,lang='spa')))
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
  if len(word_cwr_dict)>0:
    avg_freq_content_words/=len(word_cwr_dict)
  dict_to_put['Average frequency of content words'] = avg_freq_content_words
  if len(polysemies) > 0:
    dict_to_put['Average polysemy of content words'] = sum(polysemies)/len(polysemies)
  else:
    dict_to_put['Average polysemy of content words'] = 0
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

@app.route('/extractPDFContents',methods=['POST'])
def extractPDFContents():
  file = request.files.get('file')
  reader = PdfReader(file)
  extracted_text = ''
  for page in reader.pages:
    extracted_text+=page.extract_text()
  print(f"extracted text is : {extracted_text}")
  return extracted_text

def returnTopNouns(text,stanza_output,dict_to_put):
  if len(stanza_output.sentences)>0:
    all_nouns = []
    for sent in stanza_output.sentences:
      for token in sent.words:
        if token.upos == 'NOUN':
          all_nouns.append(token.text)
    counter = Counter(all_nouns).most_common(25)
    ret_nouns = []
    for x in counter:
      ret_nouns.append(x[0])
    dict_to_put['Most common nouns'] = ret_nouns
  return dict_to_put

def returnTopVerbs(text,stanza_output,dict_to_put):
  if len(stanza_output.sentences)>0:
    all_verbs = []
    for sent in stanza_output.sentences:
      for word in sent.words:
        if word.upos=='VERB':
          all_verbs.append(word.text)
    counter_verbs = Counter(all_verbs).most_common(25)
    verbs_top_25 = []
    for x in counter_verbs:
      verbs_top_25.append(x[0])
    dict_to_put['Most common verbs'] = verbs_top_25
  return dict_to_put

def returnTopAdjectives(text,stanza_output,dict_to_put):
  if len(stanza_output.sentences)>0:
    all_adjs = []
    for sent in stanza_output.sentences:
      for word in sent.words:
        if word.upos == 'ADJ':
          all_adjs.append(word.text)
    counter_adjs = Counter(all_adjs).most_common(25)
    adj_top_25 = []
    for x in counter_adjs:
      adj_top_25.append(x[0])
    dict_to_put['Most common adjectives'] = adj_top_25
  return dict_to_put

def returnTopCollocations(text,stanza_output,dict_to_put):
  '''ref : https://www.nltk.org/howto/collocations.html'''
  bigram_measures = nltk.collocations.BigramAssocMeasures()
  trigram_measures = nltk.collocations.TrigramAssocMeasures()
  quadrgrams_measures = nltk.collocations.QuadgramAssocMeasures()
  tokens = nltk.wordpunct_tokenize(text)
  finder_bigrams = BigramCollocationFinder.from_words(tokens)
  ignored_words = stop_spanish
  finder_bigrams.apply_word_filter(lambda w:w in ignored_words or not(w.isalnum()))
  scored_bigrams = finder_bigrams.score_ngrams(bigram_measures.raw_freq)
  dict_to_put['Top bigrams'] = scored_bigrams
  finder_trigrams = TrigramCollocationFinder.from_words(tokens)
  finder_trigrams.apply_word_filter(lambda w:w in ignored_words or not(w.isalnum()))
  scored_trigrams = finder_trigrams.score_ngrams(trigram_measures.raw_freq)
  dict_to_put['Top trigrams'] = scored_trigrams
  finder_quadrgrams = QuadgramCollocationFinder.from_words(tokens)
  finder_quadrgrams.apply_word_filter(lambda w:w in ignored_words or not(w.isalnum()))
  scored_quadrgrams = finder_quadrgrams.score_ngrams(quadrgrams_measures.raw_freq)
  dict_to_put['Top quadrgrams'] = scored_quadrgrams
  return dict_to_put


if __name__ == "__main__":
  app.run(debug=True)
