import streamlit as st
st. set_page_config(layout="wide")
from pathlib import Path
import requests
from requests.sessions import DEFAULT_REDIRECT_LIMIT
import base64
import verovio
import os
import requests
import re
import intervals
from intervals import * 
from intervals import main_objs
import intervals.visualizations as viz
import pandas as pd
import altair as alt 
from ipywidgets import interact
from pyvis.network import Network
import glob as glob
from IPython.display import SVG
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.figure_factory as ff
import streamlit.components.v1 as components
from os import listdir 
import os.path 
import json

import xml.etree.ElementTree as ET
from xml.etree import ElementTree
from io import StringIO


from pandas.api.types import (
    is_categorical_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
)

#
    
uploaded_file = st.file_uploader("Choose a file",  
                                    label_visibility = 'visible',
                                    type = ['.mei', '.xml', '.mid'])
# st.write(uploaded_file)
# file = 'https://raw.githubusercontent.com/CRIM-Project/CRIM-online/master/crim/static/mei/MEI_4.0/CRIM_Model_0001.mei'
# st.write(file)

# import urllib.request
# import xml.etree.ElementTree as ET

# # URL of the GitHub raw XML file
# url = "https://raw.githubusercontent.com/CRIM-Project/CRIM-online/master/crim/static/mei/MEI_4.0/CRIM_Model_0001.mei"

# # Download the raw XML file
# response = urllib.request.urlopen(url)
# xml_data = response.read()

# xml_bytes = b'<root>Hello, World!</root>'
# xml_string = uploaded_file.decode('utf-8')
# st.write(type(str(uploaded_file)))

# Parse the XML data
root = ET.fromstring(uploaded_file)

# Access and manipulate the XML data
# Example: Get the value of a specific element
# value = root.find("element_name").text

st.write(root)

# insert html within Streamlit, using components()
components.html(   
    """
    <div class="panel-body">
    <div id="app" class="panel" style="border: 1px solid lightgray; min-height: 800px;"></div>
</div>

<script type="module">
    import 'https://editor.verovio.org/javascript/app/verovio-app.js';

    // Create the app - here with an empty option object
    const app = new Verovio.App(document.getElementById("app"), {});

    // Load a file (MEI or MusicXML)

    fetch('"""+uploaded_file+"""')
        .then(function(response) {
            return response.text();
        })
        .then(function(text) {
            app.loadData(text);
        });
</script>
    """,
    height=800,
    # width=850,
)
# if uploaded_file is not None:
#     xmlstr = ElementTree.tostring(uploaded_file, encoding='utf8')   

#     st.write(xmlstr)
# for uploaded_file in uploaded_files:
#     byte_str = uploaded_file.read()
#     text_obj = byte_str.decode('UTF-8')  # Or use the encoding you expect
#     score = converter.parse(text_obj)
    

#     mei_doc = ET.fromstring(text_obj)
#     title = mei_doc.find('mei:meiHead//mei:titleStmt/mei:title', namespaces={"mei": MEINSURI})
#     if title is not None and hasattr(title, 'text'):
#                 title = re.sub(r'\n', '', title.text).strip()
#                 title
#     parts = score.getElementsByClass(stream.Part)
#     for part in parts:
#             part

    # print(mei_doc)

    # TEST 1
if st.checkbox('T1'):
    bytes_data = file.read()
    # st.write("filename:")
    st.write(str(bytes_data))


if st.checkbox('T2'):
# # TEST 2 to read file as bytes:
    data = file.getvalue()
    st.write(data)

# # TEST 3 To convert to a string based IO:
if st.checkbox('T3'):
    data = StringIO(file.getvalue().decode("utf-8"))
    st.write(data)

# TEST 4 To read file as string:
if st.checkbox('T4'):
    data = StringIO.read()
    st.write(data)

    # # assume bytes_io is a `BytesIO` object
    # byte_str = uploaded_file.read()
    # text_obj = byte_str.decode('UTF-8')  # Or use the encoding you expect

    # piece = converter.parse(byte_str)

    # piece.metadata

    # text_obj

    # uploaded_mei = io.StringIO(text_obj) 
    # st.write(uploaded_mei)

    # piece = importScore(text_obj, verbose=True)
    # st.write(piece.metadata['composer'])
    

# local pieces for dev
# raw_prefix = '/Users/rfreedma/Documents/CRIM_Python/crim-local/CRIM-online/crim/static/mei/MEI_4.0'
# file_list = os.listdir(raw_prefix) 
# piece_list = [ ] 
# for file in file_list: 
#     name = raw_prefix + "/" + file 
#     piece_list.append(file)
#     piece_list = sorted(piece_list)

# all pieces on git:
# piece_list = []
# raw_prefix = "https://raw.githubusercontent.com/CRIM-Project/CRIM-online/master/crim/static/mei/MEI_4.0/"
# URL = "https://api.github.com/repos/CRIM-Project/CRIM-online/git/trees/990f5eb3ff1e9623711514d6609da4076257816c"
# piece_json = requests.get(URL).json()
# # pattern to filter out empty header Mass files
# pattern = 'CRIM_Mass_([0-9]{4}).mei'

# # and now the request for all the files
# for p in piece_json["tree"]:
#     p_name = p["path"]
#     if re.search(pattern, p_name):
#         pass
#     else:
#         piece_list.append(p_name)
#         piece_list = sorted(piece_list)

# all pieces from CRIM Django


# # list of piece ids from json
# def make_piece_list(json_objects):
#     piece_list = []
#     for piece in json_objects:
#         file_name = piece['piece_id']
#         piece_list.append(file_name)
   
#     return piece_list

# # list of composer_title ids from json   
# def make_composer_title_list(json_objects):
#     composer_title_list = []
#     for piece in json_objects:
#         composer_title = piece['composer']['name'] + ', ' + piece['full_title'] 
#         composer_title_list.append(composer_title)
#     return composer_title_list

# # get mei link for given piece
# def find_mei_link(piece_id, json_objects):
#     key_value_pair = ('piece_id', piece_id)
#     for json_object in json_objects:
#         if key_value_pair in json_object.items():
#             return json_object['mei_links'][0]
#     return None
    
# # Title and Introduction
# st.title("CRIM Intervals")
# st.subheader("A web application for analysis of musical patterns using the CRIM Intervals library.")
# st.write("More about CRIM Intervals at:  https://github.com/HCDigitalScholarship/intervals/blob/rich_dev_22/README.md")


# crim_url = 'https://crimproject.org/data/pieces/'
# all_pieces_json = requests.get(crim_url).json()
# json_str = json.dumps(all_pieces_json)
# json_objects = json.loads(json_str)

# # fun function to make list of pieces
# piece_list = make_piece_list(json_objects)

# composer_title_list = make_composer_title_list(json_objects)

# # select a piece
# # piece_id = st.selectbox('Select Piece To View', composer_title_list)
# piece_name = st.selectbox('Select Piece To View from CRIM Django', 
#                             piece_list)
# crim_view = 'https://crimproject.org/pieces/' + piece_name

# # based on selected piece, get the mei file link and import it
# filepath = find_mei_link(piece_name, json_objects)
# piece = importScore(filepath)

# # load mei data from GIT
# mei_git_link = "https://raw.githubusercontent.com/CRIM-Project/CRIM-online/master/crim/static/mei/MEI_4.0/" + piece_name + ".mei"

# st.subheader("Selected Piece")
# if piece_name is not None:
#     st.write(piece_name)
#     st.write(piece.metadata['composer'] + ': ' + piece.metadata['title'])
#     st.write('View Piece on CRIM: ' + crim_view)
#     show_score_checkbox = st.checkbox('Show/Hide Score with Verovio')

# # CRIM at GIT
# # piece_list = []
# # crim_git_prefix = "https://raw.githubusercontent.com/CRIM-Project/CRIM-online/master/crim/static/mei/MEI_4.0/"
# # crim_git_url = "https://api.github.com/repos/CRIM-Project/CRIM-online/git/trees/990f5eb3ff1e9623711514d6609da4076257816c"
# # piece_json = requests.get(crim_git_url).json()
# # # pattern to filter out empty header Mass files
# # pattern = 'CRIM_Mass_([0-9]{4}).mei'

# # # # and now the request for all the files
# # for p in piece_json["tree"]:
# #     name = p["path"]
# #     if re.search(pattern, name):
# #         pass
# #     else:
# #         piece_list.append(name)
# # # st.write(piece_list)
# # piece_list = sorted(piece_list)
# # piece_name = st.selectbox('Select Piece To View from CRIM@GIT', 
# #                            piece_list)
# # # based on selected piece, get the mei file link and import it
# # if piece_name is not None:
# #     filepath = crim_git_prefix + piece_name
# #     piece = importScore(filepath)
# #     st.subheader("Selected Piece")
# #     if piece_name is not None:
# #         st.write(piece_name)
# #         st.write(piece.metadata['composer'] + ': ' + piece.metadata['title'])
# #         show_score_checkbox = st.checkbox('Show/Hide Score with Verovio')


# # menu dictionaries

# interval_kinds = {'diatonic' : 'd',
#                  'chromatic' : 'c',
#                  'with quality' : 'q',
#                  'zero-based diatonic' : 'z'}

# unison_status = {'Separate Unisons' : False,
#                  'Combine Unisons' : True}

# rest_status = {'Combine Rests' : True,
#                  ' Separate Rests' : False}

# interval_order_quality = ["-P8", "-M7", "-m7", "-M6", "-m6", "-P5", "-P4", "-M3", 
#                           "-m3", "-M2", "-m2", "P1", "m2", "M2", "m3", "M3",
#                           "P4", "P5", "m6", "M6", "m7", "M7", "P8"]

# # interval_order_quality = ["-P8", "m2", "-m2", "M2", "-M2", "m3", "-m3", "M3", "-M3", "P4", "-P4", "P5", "-P5", 
# #             "m6", "-m6", "M6", "-M6", "m7", "-m7", "M7", "-M7", "P8", "-P8"]

# pitch_order = ['E-2', 'E2', 'F2', 'F#2', 'G2', 'A2', 'B-2', 'B2', 
#                 'C3', 'C#3', 'D3', 'E-3','E3', 'F3', 'F#3', 'G3', 'G#3','A3', 'B-3','B3',
#                 'C4', 'C#4','D4', 'E-4', 'E4', 'F4', 'F#4','G4', 'A4', 'B-4', 'B4',
#                 'C5', 'C#5','D5', 'E-5','E5', 'F5', 'F#5', 'G5', 'A5', 'B-5', 'B5']
# # filter and download functions
# def convertTuple(tup):
#     out = ""
#     if isinstance(tup, tuple):
#         out = ', '.join(tup)
#     return out  


# st.cache_data(experimental_allow_widgets=True)
# def filter_dataframe(df: pd.DataFrame) -> pd.DataFrame:
#     """
#     Adds a UI on top of a dataframe to let viewers filter columns

#     Args:
#         df (pd.DataFrame): Original dataframe

#     Returns:
#         pd.DataFrame: Filtered dataframe
#     """
 
#     df = df.copy()

#     modification_container = st.container()

#     with modification_container:
#         to_filter_columns = st.multiselect("Filter dataframe on", df.columns)
#         for column in to_filter_columns:
#             left, right = st.columns((1, 20))
#             left.write("↳")
#             # Treat columns with < 10 unique values as categorical
#             if is_categorical_dtype(df[column]) or df[column].nunique() < 20:
#                 user_cat_input = right.multiselect(
#                     f"Values for {column}",
#                     df[column].unique(),
#                     default=list(df[column].unique()),
#                 )
#                 df = df[df[column].isin(user_cat_input)]
#             elif is_numeric_dtype(df[column]):
#                 _min = int(df[column].min())
#                 _max = int(df[column].max())
#                 user_num_input = right.slider(
#                     f"Values for {column}",
#                     _min,
#                     _max,
#                     (_min, _max)
#                 )
#                 df = df[df[column].between(*user_num_input)]
            
#             else:
#                 user_text_input = right.text_input(
#                     f"Substring or regex in {column}",
#                 )
#                 if user_text_input:
#                     df = df[df[column].str.contains(user_text_input)]

#     return df

# # download function

# @st.cache_data
# def convert_df(filtered):
#     # IMPORTANT: Cache the conversion to prevent computation on every rerun
#     return filtered.to_csv().encode('utf-8')


# # plot functions

# # notes bar chart

# def notes_bar_chart(piece, combine_unisons_choice, combine_rests_choice):
#     nr = piece.notes(combineUnisons = combine_unisons_choice,
#                               combineRests = combine_rests_choice)
#     nr_counts = nr.apply(pd.Series.value_counts).fillna(0).astype(int).reset_index().copy()  
#     nr_counts.rename(columns = {'index':'pitch'}, inplace = True)  
#     nr_counts['pitch'] = pd.Categorical(nr_counts["pitch"], categories=pitch_order)  
#     nr_counts = nr_counts.sort_values(by = "pitch").dropna().copy()
#     voices = nr.columns.to_list()   
#     # Stacked bar chart using plotly
#     nr_chart = px.bar(nr_counts, x="pitch", y=voices, title="Distribution of Pitches in " + piece_name)
#     # st.plotly_chart(pitch_chart, use_container_width = True)
#     nr = piece.detailIndex(nr)
#     return nr, nr_chart

# # melodic interval bar chart

# def mel_interval_bar_chart(_piece, combine_unisons_choice, combine_rests_choice, kind_choice, directed, compound):
#     nr = piece.notes(combineUnisons = combine_unisons_choice,
#                               combineRests = combine_rests_choice)
#     mel = piece.melodic(df = nr, 
#                         kind = kind_choice,
#                         directed = directed,
#                         compound = compound)#.fillna('')
#     # count up the values in each item column--sum for each pitch.  
#     # make a copy 
#     mel_counts = mel.apply(pd.Series.value_counts).fillna(0).astype(int).reset_index().copy()
#     # rename the index column to something more useful
#     mel_counts.rename(columns = {'index':'interval'}, inplace = True)
#     # apply the categorical list and sort.  
#     if interval_kinds[select_kind] == 'q':
#         mel_counts['interval'] = pd.Categorical(mel_counts["interval"], categories=interval_order_quality)
#     mel_counts = mel_counts.sort_values(by = "interval").dropna().copy()
#     mel_counts.index.rename('interval', inplace=True)
#     voices = mel.columns.to_list()

#     # temp
#     mel = piece.detailIndex(mel)

#     # set the figure size, type and colors
#     mel_chart = px.bar(mel_counts, x="interval", y=voices, title="Distribution of Melodic Intervals in " + piece_name)
#     # st.plotly_chart(fig, use_container_width = True)
#     return mel, mel_chart

    

# # function for harmonic bar chart

# def har_interval_bar_chart(piece, directed, compound, kind_choice):
#     har = piece.harmonic(kind = kind_choice, 
#                          directed = directed,
#                          compound = compound).fillna('')
#     # count up the values in each item column--sum for each pitch. make a copy 
#     har_counts = har.apply(pd.Series.value_counts).fillna(0).astype(int).reset_index().copy()
#     # rename the index column to something more useful
#     har_counts.rename(columns = {'index':'interval'}, inplace = True)
#     # apply the categorical list and sort.  
#     if interval_kinds[select_kind] == 'q':
#         har_counts['interval'] = pd.Categorical(har_counts["interval"], categories=interval_order_quality)
#     har_counts = har_counts.sort_values(by = "interval").dropna().copy()
#     har_counts.index.rename('interval', inplace=True)
#     voices = har.columns.to_list()
#     # set the figure size, type and colors
#     har_chart = px.bar(har_counts, x="interval", y=voices, title="Distribution of Harmonic Intervals in " + piece_name)
    
#     har = piece.detailIndex(har)
#     return har, har_chart

# # function for ngram heatmap

# def ngram_heatmap(piece, combine_unisons_choice, kind_choice, directed, compound, length_choice):
#     # find entries for model
#     nr = piece.notes(combineUnisons = combine_unisons_choice)
#     mel = piece.melodic(df = nr, 
#                         kind = kind_choice,
#                         directed = directed,
#                         compound = compound,
#                         end = False)

#     # this is for entries only
#     if entries_only == True:    
#         # pass the following ngrams to the plot below as first df
#         entry_ngrams = piece.entries(df = mel, 
#                                     n = length_choice, 
#                                     thematic = True, 
#                                     anywhere = True,
#                                     exclude = ['Rest'])

#         # pass the ngram durations below to the plot as second df
#         entry_ngrams_duration = piece.durations(df = mel, 
#                                             n =length_choice, 
#                                             mask_df = entry_ngrams)
#         # make the heatmap
#         entry_ng_heatmap = viz.plot_ngrams_heatmap(entry_ngrams, 
#                                          entry_ngrams_duration, 
#                                          selected_patterns=[], 
#                                          voices=[], 
#                                          heatmap_width= 1000,
#                                          heatmap_height=300, 
#                                          includeCount=True)
#         # rename entry_ngrams df as mel_ngrams for display
#         entry_ngrams_detail = piece.detailIndex(entry_ngrams, offset = False)
        
#         return entry_ngrams_detail, entry_ng_heatmap
#     # this is for all mel ngrams (iof entries is False in form)
#     else:
#         mel_ngrams = piece.ngrams(df = mel, n = length_choice, exclude = ['Rest'])

#         mel_ngrams_duration = piece.durations(df = mel, 
#                                           n =length_choice)
        
#         ng_heatmap = viz.plot_ngrams_heatmap(mel_ngrams, 
#                                          mel_ngrams_duration, 
#                                          selected_patterns=[], 
#                                          voices=[], 
#                                          heatmap_width = 1000,
#                                          heatmap_height=300, 
#                                          includeCount=True)
        
#         mel_ngrams_detail = piece.detailIndex(mel_ngrams, offset = False)  

#         return mel_ngrams_detail, ng_heatmap
# # hr function

# def homorhythm_streamlit(length_choice, full_hr_choice):
#     hr = piece.homorhythm(ngram_length=length_choice, 
#                     full_hr=full_hr_choice)
#     voices_list = list(piece.notes().columns)
#     hr[voices_list] = hr[voices_list].applymap(convertTuple).fillna('-')
#     hr['hr_voices'] = hr['hr_voices'].apply(', '.join)
#     hr['syllable_set'] = hr['syllable_set'].apply(lambda x: ''.join(map(str, x[0]))).copy()

#     return hr

# # p type function

# def presentation_types_streamlit(piece, 
#                                  length_choice, 
#                                  limit_entries_choice,
#                                  body_flex_choice, 
#                                  head_flex_choice,
#                                  hidden_types_choice,
#                                  combine_unisons_choice): 
    
#     p_types = piece.presentationTypes(melodic_ngram_length = length_choice, 
#                                       limit_to_entries = limit_entries_choice,
#                                       body_flex = body_flex_choice, 
#                                       head_flex = head_flex_choice,
#                                       include_hidden_types = hidden_types_choice,
#                                       combine_unisons = combine_unisons_choice)
    
# #     # presentationTypes(self, melodic_ngram_length=4, limit_to_entries=True,
# #     #                       body_flex=0, head_flex=1, include_hidden_types=False,
# #     #                       combine_unisons=False)
# #     # p_types = piece.detailIndex(p_types)#.apply(lambda x: ', '.join(map(str, x))).copy()
# #     st.write(p_types)
#     return p_types

# # score tool
# # TRUE shows the score


# if show_score_checkbox:
#     # insert html within Streamlit, using components()
    
#     components.html(
        
#         """
#         <div class="panel-body">
#         <div id="app" class="panel" style="border: 1px solid lightgray; min-height: 800px;"></div>
#     </div>

#     <script type="module">
#         import 'https://editor.verovio.org/javascript/app/verovio-app.js';

#         // Create the app - here with an empty option object
#         const app = new Verovio.App(document.getElementById("app"), {});

#         // Load a file (MEI or MusicXML)

#         fetch('"""+mei_git_link+"""')
#             .then(function(response) {
#                 return response.text();
#             })
#             .then(function(text) {
#                 app.loadData(text);
#             });
#     </script>
#         """,
#         height=800,
#         # width=850,
#     )

# # FALSE shows a blank bit of HTML
# else:
#     components.html(
        
#         """
#         <div class="panel-body">
#         """,
#         height=1,
#         # width=850,
#     ) 

# # form for notes

# if st.sidebar.checkbox("Explore Notes"):

#     st.subheader("Explore Notes")

#     with st.form("Note Settings"):
#         combine_unisons_choice = st.selectbox(
#             "Combine Unisons", [False, True])
#         combine_rests_choice = st.selectbox(
#             "Combine Rests", [True, False])
#         # form submission button
#         submitted = st.form_submit_button("Submit")
#         if submitted:
#             for key in st.session_state.keys():
#                 del st.session_state[key]
#             # run the function here, passing in settings from the form above
#             nr, nr_chart = notes_bar_chart(piece,
#                             combine_unisons_choice, 
#                             combine_rests_choice)
#             # Set up session state for these returns
#             if "nr_chart" not in st.session_state:
#                 st.session_state.nr_chart = nr_chart
 
#             if "nr" not in st.session_state:
#                 st.session_state.nr = nr
    
#     # and use the session state variables for display
#     if 'nr_chart' not in st.session_state:
#         pass
#     else:
#         st.plotly_chart(st.session_state.nr_chart, use_container_width = True)
#     if 'nr' not in st.session_state:
#         pass
#     else:
#         filtered_nr = filter_dataframe(st.session_state.nr.fillna('-'))
#         st.dataframe(filtered_nr, use_container_width = True)
#         csv = convert_df(filtered_nr)
#         st.download_button(
#             label="Download Filtered Data as CSV",
#             data=csv,
#             file_name = piece_name + '_notes_rests_results.csv',
#             mime='text/csv',
#             )

# # form for melodic
# if st.sidebar.checkbox("Explore Melodic Intervals"):
#     st.subheader("Explore Melodic Intervals")

#     with st.form("Melodic Interval Settings"):
#         combine_unisons_choice = st.selectbox(
#             "Combine Unisons", [False, True])
#         combine_rests_choice = st.selectbox(
#             "Combine Rests", [True, False])
#         select_kind = st.selectbox(
#             "Select Interval Kind", 
#             ["diatonic", "chromatic", "with quality", "zero-based diatonic"])
#         kind_choice = interval_kinds[select_kind]
#         directed = st.selectbox(
#             "Select Directed Interval Status",
#             [True, False])
#         compound = st.selectbox(
#             "Select Compound Interval Status",
#             [True, False])
#         # form submission button
#         submitted = st.form_submit_button("Update and Submit")
#         if submitted:
#             # run the function here, passing in settings from the form above
#             for key in st.session_state.keys():
#                 del st.session_state[key]
#             mel, mel_chart = mel_interval_bar_chart(piece, 
#                                     combine_unisons_choice, 
#                                     combine_rests_choice, 
#                                     kind_choice,
#                                     directed,
#                                     compound)
#             # Set up session state for these returns
#             if "mel_chart" not in st.session_state:
#                 st.session_state.mel_chart = mel_chart
 
#             if "mel" not in st.session_state:
#                 st.session_state.mel = mel
    
#     # and use the session state variables for display
#     if 'mel_chart' not in st.session_state:
#         pass
#     else:
#         st.plotly_chart(st.session_state.mel_chart, use_container_width = True)
#     if 'mel' not in st.session_state:
#         pass
#     else:
#         filtered_mel = filter_dataframe(st.session_state.mel.fillna('-'))
#         st.dataframe(filtered_mel, use_container_width = True)
#         csv = convert_df(filtered_mel)
#         st.download_button(
#             label="Download Filtered Data as CSV",
#             data=csv,
#             file_name = piece_name + '_melodic_results.csv',
#             mime='text/csv',
#             )

# # form for harmonic
# if st.sidebar.checkbox("Explore Harmonic Intervals"):
#     st.subheader("Explore Harmonic Intervals")
#     with st.form("Harmonic Interval Settings"):
#         directed = st.selectbox(
#             "Select Directed Interval Status",
#             [True, False])
#         compound = st.selectbox(
#             "Select Compound Interval Status",
#             [True, False])
#         select_kind = st.selectbox(
#             "Select Interval Kind", 
#             ["diatonic", "chromatic", "with quality", "zero-based diatonic"])
#         kind_choice = interval_kinds[select_kind]
#         # form submission button
#         submitted = st.form_submit_button("Submit")
#         if submitted:
#             # clear the session states
#             for key in st.session_state.keys():
#                 del st.session_state[key]
#             # run the function here, passing in settings from the form above
#             har, har_chart = har_interval_bar_chart(piece, 
#                                 directed,
#                                 compound, 
#                                 kind_choice)
#             # Set up session state for these returns
#             if "har_chart" not in st.session_state:
#                 st.session_state.har_chart = har_chart
 
#             if "har" not in st.session_state:
#                 st.session_state.har = har
# # and use the session state variables for display
#     if 'har_chart' not in st.session_state:
#         pass
#     else:
#         st.plotly_chart(st.session_state.har_chart, use_container_width = True)

#     if 'har' not in st.session_state:
#         pass
#     else:
#         filtered_har = filter_dataframe(st.session_state.har.fillna('-'))
#         st.dataframe(filtered_har, use_container_width = True)
#         csv = convert_df(filtered_har)
#         st.download_button(
#             label="Download Filtered Data as CSV",
#             data=csv,
#             file_name = piece_name + '_harmonic_results.csv',
#             mime='text/csv',
#             )           
 
# # ngram form
# if st.sidebar.checkbox("Explore ngrams"):
#     st.subheader("Explore nGrams")
#     with st.form("Ngram Settings"):
#         combine_unisons_choice = st.selectbox(
#             "Combine Unisons", [False, True])
#         directed = st.selectbox(
#             "Select Directed Interval Status",
#             [True, False])
#         compound = st.selectbox(
#             "Select Compound Interval Status",
#             [True, False])
#         select_kind = st.selectbox(
#             "Select Interval Kind", 
#             ["diatonic", "chromatic", "with quality", "zero-based diatonic"])
#         kind_choice = interval_kinds[select_kind]
#         length_choice = st.number_input('Select ngram Length', value=3, step=1)
#         entries_only = st.selectbox(
#             "Melodic Entries Only?",
#             [True, False])
#         # submit ngram form
#         submitted = st.form_submit_button("Submit")
    
#         if submitted:
#             for key in st.session_state.keys():
#                 del st.session_state[key]
#             ngrams, heatmap = ngram_heatmap(piece, 
#                           combine_unisons_choice, 
#                           kind_choice, 
#                           directed, 
#                           compound, 
#                           length_choice)
#             if "ngrams" not in st.session_state:
#                 st.session_state.ngrams = ngrams
#             if 'heatmap' not in st.session_state:
#                 st.session_state.heatmap = heatmap
#     if 'heatmap' not in st.session_state:
#         pass
#     else:
#         st.altair_chart(st.session_state.heatmap, use_container_width = True)
    
#     if 'ngrams' not in st.session_state:
#         pass
#     else:
#         filtered_ngrams = filter_dataframe(st.session_state.ngrams.applymap(convertTuple).fillna('-'))
#         st.dataframe((filtered_ngrams), use_container_width = True)
#         csv = convert_df(filtered_ngrams)
#         st.download_button(
#             label="Download Filtered Data as CSV",
#             data=csv,
#             file_name = piece_name + '_ngram_results.csv',
#             mime='text/csv',
#             )           
            
# # cadence form
# if st.sidebar.checkbox("Explore Cadences"):
#     st.subheader("Explore Cadences")
#     # the full table of cad
#     if st.checkbox("Show Full Cadence Table"):
#         cadences = piece.cadences()
#         st.subheader("Detailed View of Cadences")
#         filtered_cadences = filter_dataframe(cadences)
#         st.dataframe(filtered_cadences, use_container_width = True)
#         # possible Verovio Cadences use.  Needs to adapt renderer?
#         # if st.button("Print Filtered Cadences with Verovio"):
#         #     output = piece.verovioCadences(df = filtered_cadences)
#         #     components.html(output)

#     # summary of tone and type
#     if st.checkbox("Summary of Cadences by Tone and Type"):
#         cadences = piece.cadences()
#         grouped = cadences.groupby(['Tone', 'CadType']).size().reset_index(name='counts')
#         st.subheader("Summary of Cadences by Tone and Type")
#         grouped
#     # radar plots
#     if st.button("Show Basic Radar Plot"):
#         st.subheader("Basic Radar Plot")    
#         radar = piece.cadenceRadarPlot(combinedType=False, displayAll=False, renderer='streamlit')
#         st.plotly_chart(radar, use_container_width=True)
#     if st.button("Show Advanced Radar Plot"):
#         st.subheader("Advanced Radar Plot")    
#         radar = piece.cadenceRadarPlot(combinedType=True, displayAll=True, renderer='streamlit')
#         st.plotly_chart(radar, use_container_width=True)


# if st.sidebar.checkbox("Explore Homorhythm"):
#     st.subheader("Explore Homorhythm")
#     with st.form("Homorhythm Settings"):
#         full_hr_choice = st.selectbox(
#             "Select HR Full Status",
#             [True, False])
#         length_choice = st.number_input('Select ngram Length', value=4, step=1)
#         submitted = st.form_submit_button("Submit")
#         if submitted:
#             for key in st.session_state.keys():
#                 del st.session_state[key]
#             hr = homorhythm_streamlit(full_hr_choice, length_choice)

#             if "hr" not in st.session_state:
#                 st.session_state.hr = hr
# # and use the session state variables for display
#     if 'hr' not in st.session_state:
#         pass

#     else:
#         filtered_hr = filter_dataframe(st.session_state.hr.fillna('-'))
#         st.dataframe(filtered_hr, use_container_width = True)
#         csv = convert_df(filtered_hr)
#         st.download_button(
#             label="Download Filtered Data as CSV",
#             data=csv,
#             file_name = piece_name + '_homorhytym_results.csv',
#             mime='text/csv',
#             )           

# if st.sidebar.checkbox("Explore Presentation Types"):
#     st.subheader("Explore Presentation Types")
#     with st.form("Presentation Type Settings"):
#         combine_unisons_choice = st.selectbox(
#             "Combine Unisons", [False, True])
#         length_choice = st.number_input('Select ngram Length', value=4, step=1) 
#         head_flex_choice = st.number_input('Select Head Flex', value=1, step=1) 
#         body_flex_choice = st.number_input('Select Body Flex', value=0, step=1) 
#         limit_entries_choice = st.selectbox(
#             "Limit to Melodic Entries", [False, True])
#         hidden_types_choice = st.selectbox(
#             "Include Hidden Presentation Types", [False, True])
#         # form submission button
#         submitted = st.form_submit_button("Update and Submit")
#         if submitted:
#             for key in st.session_state.keys():
#                 del st.session_state[key]
#             p_types = presentation_types_streamlit(piece, 
#                                                    length_choice,
#                                                    limit_entries_choice,
#                                                    body_flex_choice,
#                                                    head_flex_choice,
#                                                    hidden_types_choice,
#                                                    combine_unisons_choice)
            
#             p_types["Measures_Beats"] = p_types["Measures_Beats"].apply(lambda x: ', '.join(map(str, x))).copy()
#             p_types["Melodic_Entry_Intervals"] = p_types["Melodic_Entry_Intervals"].apply(lambda x: ', '.join(map(str, x))).copy()
#             p_types["Offsets"]= p_types["Offsets"].apply(lambda x: ', '.join(map(str, x))).copy()
#             p_types["Soggetti"]= p_types["Soggetti"].apply(lambda x: ', '.join(map(str, x))).copy()
#             # p_types ["Time_Entry_Intervals"]= p_types["Time_Entry_Intervals"].apply(lambda x: ', '.join(map(str, x))).copy()
#             p_types["Time_Entry_Intervals"]= p_types["Time_Entry_Intervals"].apply(lambda x: ', '.join(map(str, x))).copy()

#             # Set up session state for these returns
#             if "p_types" not in st.session_state:
#                 st.session_state.p_types = p_types

#         # and use the session state variables for display
#     if 'p_types' not in st.session_state:
#         pass
#     else:
#         filtered_p_types = filter_dataframe(st.session_state.p_types)
#         st.dataframe(filtered_p_types, use_container_width = True)
#         csv = convert_df(filtered_p_types)
#         st.download_button(
#             label="Download Filtered Data as CSV",
#             data=csv,
#             file_name = piece_name + '_p_types_results.csv',
#             mime='text/csv',
#             )
