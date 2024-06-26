var selected_book;
var all_results;
var all_results_list;
var curr_book_data;
const descriptive_coh_metrics = ["mean_len_of_paras", "mean_num_of_letters_in_words", "mean_num_words_per_sent", "num_of_paras", "num_of_sentences", "num_words"];
const referential_cohesion_metrics = ["local_argument_overlap", "local_content_word_overlap", "local_noun_overlap", "local_stem_overlap"];
const word_information = ["adj_incidence", "adverb_incidence", "content_word_incidence", "noun_incidence", "verb_incidence"];
const lexical_diversity = ["content_ttr", "ttr"];
const syn_complexity_feats = ["min_edit_dist_lemma", "min_edit_dist_pos", "min_edit_dist_sent"];
const other_feats = ["gradelevel"];
var search_results = [];
var search_results_len = 0;
var is_context_search = false;
var field_name_mappings = {
  "mean_len_of_paras": "Mean length of Paragraphs",
  "mean_num_of_letters_in_words": "Mean number of letters in words",
  "mean_num_words_per_sent": "Mean number of words per sentence",
  "num_of_paras": "Number of paragraphs",
  "num_of_sentences": "Number of sentences",
  "num_words": "Number of words",
  "local_argument_overlap": "Local argument overlap",
  "local_content_word_overlap": "Local content word overlap",
  "local_noun_overlap": "Local noun overlap",
  "local_stem_overlap": "Local stem overlap",
  "adj_incidence": "Adjective Incidence",
  "adverb_incidence": "Adverb Incidence",
  "content_word_incidence": "Content word Incidence",
  "noun_incidence": "Noun incidence",
  "verb_incidence": "Verb Incidence",
  "content_ttr": "Content word Type token ratio",
  "ttr": "Type token ratio",
  "min_edit_dist_lemma": "Min edit distance lemma",
  "min_edit_dist_pos": "Min edit distance POS",
  "min_edit_dist_sent": "Min edit distance sentences",
  "gradelevel": "Flesch Kincaid grade level"
};
var total_len;
var last_page_num;
var results_desc = ["Number of words","Number of sentences","Number of Paragraphs",
"Mean length of paragraphs","Standard deviation of mean length of paras","Mean length of sentences",
"Standard deviation of mean length of sentences","Mean number of syllables","Standard deviation of mean number of syllables",
"Mean number of letters in words","Standard deviation of mean number of letters in words"];
var results_ref = ["Noun overlap adjacent","Argument overlap adjacent",
"Stem overlap adjacent","Content word overlap adjacent",
"Content word overlap global",
"Global noun overlap","Global stem overlap",
"Global argument overlap"];
var lsa_feats = ["Latent semantic analysis adjacent"];
var lexical_diversity_feats = ["Type token ratio for all words","Type token ratio for content words"];
var syntactic_complexity = ["Average minimum edit distance of POSes between adjacent sentences",
"Average minimum edit distance of lemmas between adjacent sentences","Average minimum edit distance of words between adjacent sentences",
"Average proportion of intersection of tree nodes between adjacent sentences"];
var word_info_feats = ["Minimum average frequency of words in all sentences",
"Average frequency of all words","Average frequency of content words","Average polysemy of content words",
"Noun incidence average","Verb incidence average","Adverb incidence average","Adjective incidence average",
"Flesch reading ease","Flesch kincaid grade level"];
var fileContent = "";
var text_to_send="";
function handleFileChange(){
  input = document.getElementById('file_to_analyze');
  file = input.files[0];
  file_name_regex = /.*[.pdf|.txt]$/;
  console.log("file name matches regex : "+file_name_regex.test(file.name));
  console.log("file name is "+file.name);
  if(file_name_regex.test(file.name)==false)
    alert("Only .pdf,.txt files are accepted");
  if(file.name.includes(".pdf"))
  {
    var form_data = new FormData();
    console.log("is file undefined here : "+file);
    form_data.append('file', file);
    $.ajax(
      {
        url:'/extractPDFContents',
        method : 'POST',
        cache : false,
        processData : false,
        data : form_data,
        contentType : false,
        success:function(res){
          fileContent = res;
          console.log("fileContent is : "+fileContent);
          if(fileContent.length == 0 || undefined==fileContent)
            alert("File is in unreadable format. Try uploading in a readable format.");
        }
      }
    )
  }
  else{
  const reader = new FileReader();
  
  reader.onload = function() {

    const contents = reader.result;
    fileContent = contents;
    console.log("fileContents are : "+fileContent);
  };
  //reader.readAsDataURL(file);
  reader.readAsText(file);
}
}

function handleChange(event, value) {
  event.target.value = value;
}
function handleChange_checkbox(event) {
  event.target.checked = event.target.checked;
}
function toggle_block(event, id_str) {
  display_curr = document.getElementsByClassName(id_str)[0].style.display;
  if (undefined == display_curr || display_curr == "none" || display_curr == "")
    document.getElementsByClassName(id_str + "")[0].style.display = "block";
  else
    document.getElementsByClassName(id_str + "")[0].style.display = "none";
}
function validateAndSubmit(event) {
  keyValuePairs = {};
  event.preventDefault();
  errors_present = false;
  error_msg = "";
  var num_fields_entered = 0;
  const positive_integer_regex = /^[0-9]+$/u;
  const author_regex = /\b\p{Letter}\p{Letter}*.*/u;
  table_1 = document.getElementById('criteria_block_metrics');
  table_1_rows = table_1.querySelectorAll('tr');
  table_1_rows.forEach((input) => {
    columns = input.childNodes;
    var fieldname = "";
    for (var i = 0; i < columns.length; i++) {
      element = columns[i];
      if (undefined != element.childNodes && element.childNodes.length > 0) {
        if (undefined == element.childNodes[0].tagName) {
          fieldname = element.childNodes[0].textContent;
        }
        else {
          value_curr = element.childNodes[0].value;
          if (undefined != value_curr && value_curr != "") {
            keyValuePairs[element.childNodes[0].id + ""] = { $gt: Number(value_curr) };
            num_fields_entered = num_fields_entered + 1;
          }
          if (undefined != value_curr) {
            if (fieldname == 'Number of Paragraphs' || fieldname == 'Number of sentences' || fieldname == 'Number of words') {
              if (value_curr < 0 || (value_curr != "" && positive_integer_regex.test(value_curr) == false)) {
                error_string = fieldname + " " + " has to be >=0";
                error_msg = error_msg.concat(" ", error_string);
              }
            }
            else {
              if (value_curr < 0) {
                error_string = fieldname + " " + " has to be a positive value";
                error_msg = error_msg.concat(" ", error_string);
              }
            }
          }
        }
      }
    }
  });
  table_2 = document.getElementById('criteria_block_metrics_referntial');
  table_2_rows = table_2.querySelectorAll('tr');
  table_2_rows.forEach((input) => {
    columns = input.childNodes;
    var fieldname = "";
    for (var i = 0; i < columns.length; i++) {
      element = columns[i];
      if (undefined != element.childNodes && element.childNodes.length > 0) {
        if (undefined == element.childNodes[0].tagName) {
          fieldname = element.childNodes[0].textContent;
        }
        else {
          value_curr = element.childNodes[0].value;
          if (undefined != value_curr && value_curr != "") {
            keyValuePairs[element.childNodes[0].id + ""] = { $gt: Number(value_curr) };
            num_fields_entered = num_fields_entered + 1;
          }
          if (undefined != value_curr) {
            if (value_curr < 0) {
              error_string = fieldname + " " + " has to be >=0";
              error_msg = error_msg.concat(" ", error_string);
            }
          }
        }
      }
    }
  });
  table_3 = document.getElementById('criteria_block_metrics_diversity');
  table_3_rows = table_3.querySelectorAll('tr');
  table_3_rows.forEach((input) => {
    columns = input.childNodes;
    var fieldname = "";
    for (var i = 0; i < columns.length; i++) {
      element = columns[i];
      if (undefined != element.childNodes && element.childNodes.length > 0) {
        if (undefined == element.childNodes[0].tagName) {
          fieldname = element.childNodes[0].textContent;
        }
        else {
          value_curr = element.childNodes[0].value;
          if (undefined != value_curr && value_curr != "") {
            keyValuePairs[element.childNodes[0].id + ""] = { $gt: Number(value_curr) };
            num_fields_entered = num_fields_entered + 1;
          }
          if (undefined != value_curr) {
            if (fieldname == 'Type token ratio') {
              if (value_curr < 0 || value_curr > 1) {
                error_msg = error_msg.concat(" ", "Type token ratio has to be between 0 and 1");
              }
            }
            else if (fieldname == 'Average Minimium Word frequency') {
              if (value_curr < 0 || (value_curr != "" && positive_integer_regex.test(value_curr) == false)) {
                error_msg = error_msg.concat(" ", "Average minimum word frequency has to be an integer >=0");
              }
            }
            else {
              if (value_curr < 0) {
                error_msg = error_msg.concat(" ", fieldname + " has to be >=0");
              }
            }
          }
        }
      }
    }
  });
  table_4 = document.getElementById('criteria_block_metrics_syn_complexity');
  table_4_rows = table_4.querySelectorAll('tr');
  table_4_rows.forEach((input) => {
    columns = input.childNodes;
    var fieldname = "";
    for (var i = 0; i < columns.length; i++) {
      element = columns[i];
      if (undefined != element.childNodes && element.childNodes.length > 0) {
        if (undefined == element.childNodes[0].tagName) {
          fieldname = element.childNodes[0].textContent;
        }
        else {
          value_curr = element.childNodes[0].value;
          if (undefined != value_curr && value_curr != "") {
            keyValuePairs[element.childNodes[0].id + ""] = { $gt: Number(value_curr) };
            num_fields_entered = num_fields_entered + 1;
          }
          if (undefined != value_curr) {
            if (fieldname != 'Flesch Reading Ease' && fieldname != 'Flesch Kincaid Reading Level') {
              if (value_curr < 0) {
                error_msg = error_msg.concat(" ", fieldname + " has to be >0");
              }
            }
            else {
              if (fieldname == 'Flesch Reading Ease') {
                if (value_curr < 0 || value_curr > 100)
                  error_msg = error_msg.concat(" ", "Flesch Reading ease has to be between 0 and 100 (inclusive)");
              }
              else if (fieldname == 'Flesch Kincaid Reading Level') {
                if (value_curr < 0 || value_curr > 18)
                  error_msg = error_msg.concat(" ", "Flesch Kincaid Reading Level has to be between 0 and 18 (inclusive)");
              }
            }
          }
        }
      }
    }
  });
  table_5 = document.getElementById('criteria_block_lang');
  table_5_rows = table_5.querySelectorAll('tr');
  table_5_rows.forEach((input) => {
    columns = input.childNodes;
    var fieldname = "";
    for (var i = 0; i < columns.length; i++) {
      element = columns[i];
      if (undefined != element.childNodes && element.childNodes.length > 0) {
        if (undefined == element.childNodes[0].tagName) {
          fieldname = element.childNodes[0].textContent;
        }
        else {
          value_curr = element.childNodes[0].value;
          if (undefined != value_curr && value_curr != "") {
            keyValuePairs[element.childNodes[0].id + ""] = { $gt: Number(value_curr) };
            num_fields_entered = num_fields_entered + 1;
          }
          if (undefined != value_curr) {
            if (value_curr < 0 || value_curr > 0) {
              error_msg = error_msg.concat(" ", fieldname + " has to be between 0 and 100 (inclusive)");
            }
          }
        }
      }
    }
  });
  table_6 = document.getElementById('table1');
  table_6_rows = table_6.querySelectorAll('tr');
  table_6_rows.forEach((input) => {
    columns = input.childNodes;
    var fieldname = "";
    for (var i = 0; i < columns.length; i++) {
      element = columns[i];
      if (undefined != element.childNodes && element.childNodes.length > 0) {
        if (undefined == element.childNodes[0].tagName) {
          fieldname = element.childNodes[0].textContent;
        }
        else {
          value_curr = element.childNodes[0].value;
          if (undefined != value_curr && value_curr != "") {
            keyValuePairs[element.childNodes[0].id + ""] = { $regex: value_curr, $options: 'i' };
            num_fields_entered = num_fields_entered + 1;
          }
          if (undefined != value_curr) {
            if ((fieldname == "Author" || fieldname == "Title") && value_curr != "" && author_regex.test(value_curr) == false) {
              error_msg = error_msg.concat(" ", fieldname + " should contain at least one letter and should start with a letter");
            }
          }
        }
      }
    }
  });
  table_7 = document.getElementById('criteria_block_text_info');
  table_7_rows = table_7.querySelectorAll('tr');
  table_7_rows.forEach((input) => {
    columns = input.childNodes;
    var fieldname = "";
    for (var i = 0; i < columns.length; i++) {
      element = columns[i];
      if (undefined != element.childNodes && element.childNodes.length > 0) {
        if (undefined == element.childNodes[0].tagName) {
          fieldname = element.childNodes[0].textContent;
        }
        else {
          value_curr = element.childNodes[0].value;
          if ((undefined != value_curr) && value_curr != "") {
            if (fieldname != "Authentic" && fieldname != "Simplified") {
              num_fields_entered = num_fields_entered + 1;
              keyValuePairs[element.childNodes[0].id + ""] = { $regex: value_curr, $options: 'i' };
            }
            else {
              if (element.childNodes[0].checked)
                num_fields_entered = num_fields_entered + 1;
            }
          }
          if (undefined != value_curr) {
            if ((fieldname == "Genre" || fieldname == "Type") && value_curr != "" && author_regex.test(value_curr) == false) {
              error_msg = error_msg.concat(" ", fieldname + " should contain at least one letter and should start with a letter");
            }
            else if (fieldname == "Length" && value_curr != "" && (positive_integer_regex.test(value_curr) == false || value_curr < 0)) {
              error_msg = error_msg.concat(" ", fieldname + " should be an integer >=0");
            }
          }
        }
      }
    }
  });
  if (error_msg != "")
    alert(error_msg);
  if (num_fields_entered == 0)
    alert("Enter atleast one field to proceed to search");
  if (error_msg == "" && num_fields_entered > 0) {
    $.ajax(
      {
        url: "/searchWithCriteria",
        data: {
          "keyValuePairs": JSON.stringify(keyValuePairs)
        },
        type: "GET",
        contentType: "application/json",
        success: function (res) {
          search_results = res;
          if (search_results.length > 0) {
            var books_str = "<table>";
            for (var i = 0; i < Math.min(20, res.length); i++) {
              books_str += '<tr>';
              books_str += '<td>';
              books_str += '<input type="radio" name="books"'
              books_str += 'value=\"';
              books_str += (res[i]['Book_name'])
              books_str += '\"';
              if (res[i]['Book_name'] == selected_book)
                books_str += 'checked = true';
              books_str += 'onchange="handleBookSelection(event)">';
              books_str += '<a href=\"';
              books_str += res[i]['url'];
              books_str += '\"';
              books_str += 'target="_blank">';
              books_str += res[i]['Book_name'];
              books_str += '</td></tr>';

            }
            books_str += "</table>";
            document.getElementById('all_books_block').innerHTML = books_str;
          }
          else {
            document.getElementById('all_books_block').innerHTML = "No books match the provided criteria";

          }
          is_context_search = true;
          search_results_len = search_results.length;
          if (search_results_len <= 20) {
            document.getElementById('previous_button').disabled = true;
            document.getElementById('next_button').disabled = true;
          }
          document.getElementById('previous_button').value = 0;
          document.getElementById('next_button').value = 1;
          total_len = search_results_len;
          last_page_num = Math.ceil(total_len / 20);

        }
      }
    )
  }

}
function displaySingleTab(event) {
  if (event.target.name == "Search") {
    document.getElementsByClassName('search_tab')[0].style.display = "block";
    document.getElementsByClassName('readability_tab')[0].style.display = "none";
    document.getElementsByClassName('vocab_tab')[0].style.display = "none";
    document.getElementsByClassName('analyze_text_box')[0].style.display = "none";
    document.getElementsByClassName('analyze_text_file')[0].style.display = "none";
  }
  else if (event.target.name == "Readability") {
    document.getElementsByClassName('search_tab')[0].style.display = "none";
    document.getElementsByClassName('readability_tab')[0].style.display = "block";
    document.getElementsByClassName('vocab_tab')[0].style.display = "none";
    document.getElementsByClassName('analyze_text_box')[0].style.display = "none";
    document.getElementsByClassName('analyze_text_file')[0].style.display = "none";
  }
  else if (event.target.name == "Vocabulary") {
    document.getElementsByClassName('search_tab')[0].style.display = "none";
    document.getElementsByClassName('readability_tab')[0].style.display = "none";
    document.getElementsByClassName('vocab_tab')[0].style.display = "block";
    document.getElementsByClassName('analyze_text_box')[0].style.display = "none";
    document.getElementsByClassName('analyze_text_file')[0].style.display = "none";
  }
  else if (event.target.name == "text_box_analyze") {
    document.getElementsByClassName('search_tab')[0].style.display = "none";
    document.getElementsByClassName('readability_tab')[0].style.display = "none";
    document.getElementsByClassName('vocab_tab')[0].style.display = "none";
    document.getElementsByClassName('analyze_text_box')[0].style.display = "block";
    document.getElementsByClassName('analyze_text_file')[0].style.display = "none";
  }
  else if(event.target.name == "upload_a_file"){
    document.getElementsByClassName('search_tab')[0].style.display = "none";
    document.getElementsByClassName('readability_tab')[0].style.display = "none";
    document.getElementsByClassName('vocab_tab')[0].style.display = "none";
    document.getElementsByClassName('analyze_text_box')[0].style.display = "none";
    document.getElementsByClassName('analyze_text_file')[0].style.display = "block";
  }
}
function handleLoad() {
  $.ajax(
    {
      url: '/fetchAll',
      method: "GET"
    }
  ).then((response) => {
    all_results = JSON.parse(JSON.stringify(response));

  })
  $.ajax(
    {
      url: '/fetchAllList',
      method: "GET"
    }
  ).then(
    (response) => {
      all_results_list = response;
      console.log(all_results_list);
      total_len = all_results_list.length;
      last_page_num = Math.ceil(total_len / 20);
    }
  )

}
function getVocabData(dictOfValues) {
  var vocab_str = "";
  nouns_list = dictOfValues['NOUNS'];
  if (nouns_list != undefined && nouns_list.length > 0) {
    vocab_str += "<b>Top 25 Nouns</b>";
    vocab_str += "<br/>";
    for (var i = 0; i < nouns_list.length; i++) {
      vocab_str += nouns_list[i];
      vocab_str += "<br/>";
    }
  }
  verbs_list = dictOfValues['VERB'];
  if (undefined != verbs_list && verbs_list.length > 0) {
    vocab_str += "<b> Top 25 Verbs</b>";
    vocab_str += "<br/>";
    for (var i = 0; i < verbs_list.length; i++) {
      vocab_str += verbs_list[i];
      vocab_str += "<br/>";
    }
  }
  adj_list = dictOfValues['ADJ'];
  if (undefined != adj_list && adj_list.length > 0) {
    vocab_str += "<b> Top 25 Adjectives</b>";
    vocab_str += "<br/>";
    for (var i = 0; i < adj_list.length; i++) {
      vocab_str += adj_list[i];
      vocab_str += "<br/>";
    }
  }
  return vocab_str;
}
function getCollocationsData(dictOfValues) {
  collocation_str = "";
  bigrams = dictOfValues['bigrams'];
  if (undefined != bigrams && bigrams.length>0) {
    collocation_str += "Top 25 bigrams : ";
    collocation_str += "<br/>";
    for (var i = 0; i < bigrams.length; i++) {
      collocation_str += bigrams[i];
      collocation_str += "<br/>";
    }
  }
  trigrams = dictOfValues['trigrams'];
  if (undefined != trigrams && trigrams.length > 0) {
    collocation_str += "Top 25 trigrams : ";
    collocation_str += "<br/>";
    for (var i = 0; i < trigrams.length; i++) {
      collocation_str += trigrams[i];
      collocation_str += "<br/>";
    }
  }
  quadrgrams = dictOfValues['quadrgrams'];
  console.log("length of quadrgrams : "+quadrgrams.length);
  if (undefined != quadrgrams && quadrgrams.length > 0) {
    collocation_str += "Top 25 quadrgrams : ";
    collocation_str += "<br/>";
    for (var i = 0; i < quadrgrams.length; i++) {
      collocation_str += quadrgrams[i];
      collocation_str += "<br/>";
    }
  }
  return collocation_str;
}
function handleBookSelection(event) {
  selected_book = event.target.value;
  document.getElementById('selected_book_name').innerHTML = event.target.value;
  let vocab_data = "";

  if (undefined == all_results) {
    $.ajax(
      {
        url: '/fetchAll',
        method: "GET"
      }
    ).then((response) => {
      all_results = JSON.parse(JSON.stringify(response));

    }).then(
      () => {
        curr_book_data = JSON.stringify(all_results[selected_book]);
        console.log("curr_book_data : in ajax fectch" + curr_book_data);
        desc_print_str = printSubCategoryMetrics(descriptive_coh_metrics, curr_book_data);
        ref_print_str = printSubCategoryMetrics(referential_cohesion_metrics, curr_book_data);
        word_info_str = printSubCategoryMetrics(word_information, curr_book_data);
        lexical_diversity_str = printSubCategoryMetrics(lexical_diversity, curr_book_data);
        syn_complexity_str = printSubCategoryMetrics(syn_complexity_feats, curr_book_data);
        other_feats_str = printSubCategoryMetrics(other_feats, curr_book_data);
        document.getElementById('readability_tab').innerHTML =
          "<b> Descriptive Metrics </b>" + "</br>" + desc_print_str + "</br>" +
          "<b> Referential Cohesion Metrics </b>" + "</br>" + ref_print_str + "</br>" +
          "<b> Word Information Metrics </b>" + "</br>" + word_info_str + "</br>" +
          "<b> Lexical Diversity Metrics </b>" + "</br>" + lexical_diversity_str + "</br>" +
          "<b> Syntactic Complexity Metrics </b>" + "</br>" + syn_complexity_str + "</br>" +
          "<b> Traditional Readability Metrics </b>" + "</br>" + other_feats_str + "</br>";
        vocab_data = getVocabData(curr_book_data);
        document.getElementById('vocab_results_pos').innerHTML = vocab_data;
        collocations_data = getCollocationsData(curr_book_data);
        document.getElementById('vocab_results_collocations').innerHTML = collocations_data;


      }
    )
  }
  else {
    console.log("entered else :");
    curr_book_data = JSON.parse(JSON.stringify(all_results[selected_book]));
    console.log("curr_book_data : in else" + curr_book_data);
    desc_print_str = printSubCategoryMetrics(descriptive_coh_metrics, curr_book_data);
    ref_print_str = printSubCategoryMetrics(referential_cohesion_metrics, curr_book_data);
    word_info_str = printSubCategoryMetrics(word_information, curr_book_data);
    lexical_diversity_str = printSubCategoryMetrics(lexical_diversity, curr_book_data);
    syn_complexity_str = printSubCategoryMetrics(syn_complexity_feats, curr_book_data);
    other_feats_str = printSubCategoryMetrics(other_feats, curr_book_data);
    document.getElementById('readability_tab').innerHTML =
      "<b> Descriptive Metrics </b>" + "</br>" + desc_print_str + "</br>" +
      "<b> Referential Cohesion Metrics </b>" + "</br>" + ref_print_str + "</br>" +
      "<b> Word Information Metrics </b>" + "</br>" + word_info_str + "</br>" +
      "<b> Lexical Diversity Metrics </b>" + "</br>" + lexical_diversity_str + "</br>" +
      "<b> Syntactic Complexity Metrics </b>" + "</br>" + syn_complexity_str + "</br>" +
      "<b> Traditional Readability Metrics </b>" + "</br>" + other_feats_str + "</br>";
    vocab_data = getVocabData(curr_book_data);
    console.log("vocab_data is : " + vocab_data);
    document.getElementById('vocab_results_pos').innerHTML = vocab_data;
    collocations_data = getCollocationsData(curr_book_data);
    document.getElementById('vocab_results_collocations').innerHTML = collocations_data;
  }


}
function printSubCategoryMetrics(listofmetricNames, dictOfValues) {
  var ret_str = "";
  console.log("in printSubCategoryMetrics : " + dictOfValues);
  for (var i = 0; i < listofmetricNames.length; i++) {
    ret_str += field_name_mappings[listofmetricNames[i]];
    ret_str += " : ";
    ret_str += dictOfValues[listofmetricNames[i]];
    ret_str += "<br/>";
  }
  return ret_str;
}
function handleNextClick(event) {
  event.preventDefault();
  iterate_list = []
  if (is_context_search)
    iterate_list = search_results;
  else
    iterate_list = all_results_list;
  var curr_page_number = Number(event.target.value);
  var start_index = curr_page_number * 20;
  var end_index = start_index + 20;
  if (end_index > total_len)
    end_index = total_len;
  console.log("start_index is : " + start_index + " end_index : " + end_index);
  if (curr_page_number + 1 == last_page_num)
    document.getElementById('next_button').disabled = true;
  books_str = "<table>";
  for (var i = start_index; i < end_index; i++) {
    books_str += '<tr>';
    books_str += '<td>';
    books_str += '<input type="radio" name="books"'
    books_str += 'value=\"';
    books_str += (iterate_list[i]['Book_name'])
    books_str += '\"';
    books_str += 'onchange="handleBookSelection(event)">';
    books_str += '<a href=\"';
    books_str += iterate_list[i]['url'];
    books_str += '\"';
    books_str += 'target="_blank">';
    books_str += iterate_list[i]['Book_name'];
    books_str += '</td></tr>';
  }
  books_str += '</table>';
  document.getElementById('all_books_block').innerHTML = books_str;
  document.getElementById('next_button').value = curr_page_number + 1;
  if (curr_page_number + 1 > 1) {
    document.getElementById('previous_button').disabled = false;
  }
  else {
    document.getElementById('previous_button').disabled = true;
  }
  document.getElementById('previous_button').value = curr_page_number;
}
function handlePreviousButton(event) {
  var pageNum = Number(event.target.value);
  var start_index = (pageNum - 1) * 20;
  var end_index = start_index + 20;
  iterate_list = [];
  if (is_context_search)
    iterate_list = search_results;
  else
    iterate_list = all_results_list;
  books_str = "<table>";
  for (var i = start_index; i < end_index; i++) {
    books_str += '<tr>';
    books_str += '<td>';
    books_str += '<input type="radio" name="books"'
    books_str += 'value=\"';
    books_str += (iterate_list[i]['Book_name'])
    books_str += '\"';
    if (iterate_list[i]['Book_name'] == selected_book)
      books_str += 'checked = true';
    books_str += 'onchange="handleBookSelection(event)">';
    books_str += '<a href=\"';
    books_str += iterate_list[i]['url'];
    books_str += '\"';
    books_str += 'target="_blank">';
    books_str += iterate_list[i]['Book_name'];
    books_str += '</td></tr>';
  }
  books_str += '</table>';
  document.getElementById('all_books_block').innerHTML = books_str;
  console.log(document.getElementById('all_books_block').innerHTML);
  document.getElementById('previous_button').value = pageNum - 1;
  if (pageNum == 1) {
    event.target.disabled = true;
  }
  document.getElementById('next_button').value = pageNum;
  document.getElementById('next_button').disabled = false;

}
function clear_all()
{
  clear_all_block('table1');
  clear_all_block('criteria_block_metrics');
  clear_all_block('criteria_block_text_info');
  clear_all_block('criteria_block_lang');
  clear_all_block('criteria_block_metrics_referntial');
  clear_all_block('criteria_block_metrics_diversity');
  clear_all_block('criteria_block_metrics_syn_complexity');
  document.getElementById('selected_book_name').innerHTML = "";
  setToDefaultBooksList();



}
function clear_all_block(id_str)
{
  table_id_str = document.getElementById(id_str);
  table_rows = table_id_str.querySelectorAll('tr');
  table_rows.forEach(
    (row)=>{
      childNodes_curr = row.childNodes;
      if(undefined!=childNodes_curr)
      {
        for(var i = 0; i < childNodes_curr.length;i++)
        {
          if(undefined!=childNodes_curr[i].tagName){
          second_level_ch_nodes = childNodes_curr[i].childNodes;
          for(var j = 0; j < second_level_ch_nodes.length; j++){
            if(undefined!=second_level_ch_nodes[j].tagName){
              second_level_ch_nodes[j].value = "";
            if(undefined!=second_level_ch_nodes[j].tagName && second_level_ch_nodes[j].type=="checkbox")
            second_level_ch_nodes[j].checked = false;
            }
          }
          }
        }
      }
    }
  )
}
function setToDefaultBooksList()
{
    books_str = "";
    books_str+="<table>";
    for(var i = 0; i < 20; i++)
    {
      books_str+='<tr><td>';
      books_str+='<input type="radio" name="books" value =\"';
      books_str+=all_results_list[i]['Book_name'];
      books_str+="\"";
      books_str += 'onchange="handleBookSelection(event)">';
      books_str += '<a href=\"';
      books_str += all_results_list[i]['url'];
      books_str += '\"';
      books_str += 'target="_blank">';
      books_str += all_results_list[i]['Book_name'];
      books_str += '</td></tr>';
    }
    books_str+="</table>";
    document.getElementById('all_books_block').innerHTML = books_str;
    document.getElementById('previous_button').disabled = true;
    document.getElementById('next_button').disabled = false;
    document.getElementById('previous_button').value = 0;
    document.getElementById('next_button').value = 1;
    total_len = all_results_list.length;
    last_page_num = Math.ceil(total_len / 20);
    is_context_search = false;
    document.getElementById('readability_tab').innerHTML = "";
    document.getElementById('vocab_results_pos').innerHTML = "";
    document.getElementById('vocab_results_collocations').innerHTML = "";
}
function analyzeEnteredText()
{
  document.getElementById('results_metrics').innerHTML = "";
  text_entered = document.getElementById('entered_text').value;
  console.log("in analyze entered text : "+fileContent);
  if((undefined==text_entered && undefined==fileContent) || (text_entered == "" && fileContent=="") || (text_entered.length==0 && fileContent.length==0))
  {
    alert("Enter a non empty text in the text area or a non empty file that needs to be analyzed");
  }
  else if(undefined!=text_entered && undefined!=fileContent && text_entered.length>0 && fileContent.length>0)
  {
    alert("Enter either text or upload a file to be analyzed. Not both!");
  }
  else{
    document.getElementsByClassName('loader')[0].style.display = "block";
    if(undefined!=text_entered && text_entered!="" && text_entered.length>0)
    text_to_send = text_entered;
    else
    text_to_send = fileContent;
    console.log("in sending : "+text_to_send);
    $.ajax(
      {
        url:"/computeMetrics",
        method : "GET",
        data :{
          "enteredText":text_to_send
        },
        contentType:"application/json",
        success:function(res){
          dict_metrics = res;
          results_str = "<br/>"
          results_str+="<b>Results : </b>";
          results_str+="<br/>";
          results_str+="<b>Descriptive metrics : </b>";
          results_str+="<br/>";
          for(var i=0; i<results_desc.length;i++)
          {
            results_str+=results_desc[i];
            results_str+=" : ";
            results_str+=dict_metrics[results_desc[i]];
            results_str+="<br/>";
          }
          results_str+="<b>Referential cohesion metrics</b>";
          results_str+="<br/>";
          for(var i=0; i<results_ref.length;i++)
          {
            results_str+=results_ref[i];
            results_str+=" : ";
            results_str+=dict_metrics[results_ref[i]];
            results_str+="<br/>";
          }
          results_str+="<b>Latent semantic analysis metrics</b>";
          results_str+="<br/>";
          for(var i=0;i<lsa_feats.length;i++)
          {
            results_str+=lsa_feats[i];
            results_str+=" : ";
            results_str+=dict_metrics[lsa_feats[i]];
            results_str+="<br/>";
          }
          results_str+="<b>Lexical diversity metrics</b>";
          results_str+="<br/>";
          for(var i=0; i<lexical_diversity_feats.length;i++)
          {
            results_str+=lexical_diversity_feats[i];
            results_str+=" : ";
            results_str+=dict_metrics[lexical_diversity_feats[i]];
            results_str+="<br/>";
          }
          results_str+="<b>Syntactic complexity metrics</b>";
          results_str+="<br/>";
          for(var i=0; i<syntactic_complexity.length;i++)
          {
            results_str+=syntactic_complexity[i];
            results_str+=" : ";
            results_str+=dict_metrics[syntactic_complexity[i]];
            results_str+="<br/>";
          }
          results_str+="<b>Word Information</b>";
          results_str+="<br/>";
          for(var i=0; i<word_info_feats.length;i++)
          {
            results_str+=word_info_feats[i];
            results_str+=" : ";
            results_str+=dict_metrics[word_info_feats[i]];
            results_str+="<br/>";
          }
          results_str+="<br/>";
          var top_nouns = dict_metrics['Most common nouns'];
          if(undefined!=top_nouns && top_nouns.length>0){
          results_str+="<b>Top Nouns</b>";
          for(var i = 0; i < top_nouns.length; i++)
          {
            results_str+=top_nouns[i];
            results_str+="<br/>";
          }
          }
          var top_verbs = dict_metrics['Most common verbs'];
          if(undefined!=top_verbs && top_verbs.length > 0){
          results_str+="<b>Top Verbs</b>";
          results_str+="<br/>";
          for(var i = 0; i < top_verbs.length; i++)
          {
            results_str+=top_verbs[i];
            results_str+="<br/>";
          }
          }
          var top_adjectives = dict_metrics['Most common adjectives'];
          if(undefined!=top_adjectives && top_adjectives.length > 0){
          results_str+="<b>Top Adjectives</b>";
          results_str+="<br/>";
          console.log("top_adjectives : "+top_adjectives.length);
          for(var i = 0; i < top_adjectives.length;i++)
          {
            results_str+=top_adjectives[i];
            results_str+="<br/>";
          }
          }
          var top_bigrams = dict_metrics['Top bigrams'];
          if(undefined!=top_bigrams && top_bigrams.length>0){
          results_str+="<br/>";
          results_str+="<b>Top bigrams</b>";
          results_str+="<br/>";
          for(var i = 0; i < top_bigrams.length;i++)
          {
            results_str+=top_bigrams[i];
            results_str+="<br/>";
          }
        }
          var top_trigrams = dict_metrics['Top trigrams'];
          if(undefined!=top_trigrams && top_trigrams.length>0){
          results_str+="<b>Top trigrams</b>";
          results_str+="<br/>";
          for(var i = 0; i < top_trigrams.length; i++)
          {
            results_str+=top_trigrams[i];
            results_str+="<br/>";
          }
        }
          var top_quadrgrams = dict_metrics['Top quadrgrams'];
          if(undefined!=top_quadrgrams && top_quadrgrams.length>0){
          results_str+="<b>Top Quadrgrams</b>";
          results_str+="<br/>";
          for(var i = 0; i <top_quadrgrams.length; i++)
          {
            results_str+=top_quadrgrams[i];
            results_str+="<br/>";
          }
        }
          document.getElementsByClassName('loader')[0].style.display = "none";
          document.getElementById('results_metrics').innerHTML = results_str;
        }
      }
    )
  }
}
