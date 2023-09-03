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
import seaborn as sns
from tempfile import NamedTemporaryFile
import random

from pandas.api.types import (
    is_categorical_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
)

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

# list of piece ids from json
def make_piece_list(json_objects):
    piece_list = []
    for piece in json_objects:
        file_name = piece['piece_id']
        piece_list.append(file_name) 
    return piece_list

# list of composer_title ids from json   
def make_composer_title_list(json_objects):
    composer_title_list = []
    for piece in json_objects:
        composer_title = piece['composer']['name'] + ', ' + piece['full_title'] 
        composer_title_list.append(composer_title)
    return composer_title_list

# get mei link for given piece
def find_mei_link(piece_id, json_objects):
    key_value_pair = ('piece_id', piece_id)
    for json_object in json_objects:
        if key_value_pair in json_object.items():
            return json_object['mei_links'][0]
    return None



# Title and Introduction
st.title("CRIM Intervals Search Tools")
st.subheader("A web application for analysis of musical patterns using the CRIM Intervals library.")
st.markdown("[Watch a video guide to this application.](https://haverford.box.com/s/tn35aynw0ogpih43ux923tbd2kma1idg)")
st.markdown("[Learn more about CRIM Intervals](https://github.com/HCDigitalScholarship/intervals)", unsafe_allow_html=True)
st.markdown("Follow detailed explanations of various CRIM Intervals methods via the [Tutorials](https://github.com/HCDigitalScholarship/intervals/blob/main/tutorial/01_Introduction_and_Corpus.md)", unsafe_allow_html=True)
st.markdown("Learn more about this web application (and how to contribute or adapt it via the [Github Repository for CRIM Intervals on Streamlit](https://github.com/RichardFreedman/intervals-streamlit/blob/main/README.md)")
# importing files
crim_url = 'https://crimproject.org/data/pieces/'
all_pieces_json = requests.get(crim_url).json()
json_str = json.dumps(all_pieces_json)
json_objects = json.loads(json_str)

# function to make list of pieces
all_piece_list = make_piece_list(json_objects)
crim_piece_selections= st.multiselect('**Select Pieces To View from CRIM Django**', 
                            all_piece_list)
# st.write("Upload MEI or XML files")

uploaded_files_list = st.file_uploader("**Upload MEI or XML files**", type=['mei', 'xml'], accept_multiple_files=True)
crim_view_url = ''
if len(crim_piece_selections) == 0 and len(uploaded_files_list)== 0:
    st.write("**No Files Selected! Please Select or Upload One or More Pieces.**")

# for one piece in CRIM
elif len(crim_piece_selections) == 1 and len(uploaded_files_list)== 0:
    piece_name = crim_piece_selections[0]
    crim_view_url = 'https://crimproject.org/pieces/' + piece_name
    url_for_verovio = "https://raw.githubusercontent.com/CRIM-Project/CRIM-online/master/crim/static/mei/MEI_4.0/" + piece_name + ".mei"

    # based on selected piece, get the mei file link and import it
    filepath = find_mei_link(piece_name, json_objects)
    keys = ['piece', 'metadata']
    for key in keys:
        if key in st.session_state.keys():
            del st.session_state[key]
    # import
    piece = importScore(filepath)
    if "piece" not in st.session_state:
        st.session_state.piece = piece
    if "metadata" not in st.session_state:
        st.session_state.metadata = piece.metadata
    st.session_state.metadata['CRIM View'] = crim_view_url
    st.dataframe(st.session_state.metadata)  

# One upload
elif len(crim_piece_selections) == 0 and len(uploaded_files_list) == 1:
    f = ''
    crim_view_url = "Direct Upload; Not from CRIM"
    keys = ['piece', 'metadata']
    for key in keys:
        if key in st.session_state.keys():
            del st.session_state[key]
    for file in uploaded_files_list:
        # KEEP THIS
        # with NamedTemporaryFile(dir='.', suffix = '.mei') as f:
        #     f.write(file.getbuffer())
        #     # f.name is in fact the TEMP PATH!
        #     piece = importScore(f.name)
        byte_str = file.read()
        text_obj = byte_str.decode('UTF-8')
        piece = importScore(text_obj) 
        if "piece" not in st.session_state:
            st.session_state.piece = piece
        if "metadata" not in st.session_state:
            st.session_state.metadata = piece.metadata
        st.session_state.metadata['CRIM View'] = "Direct upload; not available on CRIM"
        st.dataframe(st.session_state.metadata)  

# now combine the CRIM and Uploaded Files
elif (len(crim_piece_selections) > 0 and len(uploaded_files_list) > 0) or len(crim_piece_selections) > 1 or  len(uploaded_files_list) > 1:
    # set empty corpus list, so we can add files to it
    corpus_list = []
    metadata_list= []
    if len(crim_piece_selections) > 0:
        for crim_piece in crim_piece_selections:
            filepath = find_mei_link(crim_piece, json_objects)
            corpus_list.append(filepath)
    if len(uploaded_files_list) > 0:
        for file in uploaded_files_list:
            # KEEP THIS FOR TEMP WRITE METHOD
            # if file is not None:
            #     file_details = {"FileName":file.name,"FileType":file.type}
            #     local_dir = '/tempDir/'
            #     # this one for use on computer:
            #     # local_dir = '/Users/rfreedma/Documents/CRIM_Python/intervals-streamlit/'
            #     file_path = os.path.join(local_dir, file.name)
            #     with open(file_path,"wb") as f: 
            #         f.write(file.getbuffer())         
            #     corpus_list.append(file_path)
            byte_str = file.read()
            text_obj = byte_str.decode('UTF-8')
            corpus_list.append(text_obj)
    # make corpus and session state version
    if 'corpus' in st.session_state:
        del st.session_state.corpus        
    corpus = CorpusBase(corpus_list)
    if 'corpus' not in st.session_state:
        st.session_state.corpus = corpus
    if 'corpus_metadata' in st.session_state:
        del st.session_state.corpus_metadata
    for i in range(len(corpus.scores)):
        metadata_list.append(corpus.scores[i].metadata)
    if 'corpus_metadata' not in st.session_state:
        st.session_state.corpus_metadata = metadata_list
    st.dataframe(st.session_state.corpus_metadata)

# get metadata for corpus
if "corpus_metadata" not in st.session_state:
    pass
else:
    corpus_metadata_df = pd.DataFrame.from_dict(st.session_state.corpus_metadata)
    titles = corpus_metadata_df['title']
# flags for lengths of selected corpus:
if len(crim_piece_selections) == 0 and len(uploaded_files_list) == 0:
    corpus_length = 0
elif len(crim_piece_selections) == 1 and len(uploaded_files_list) == 0:
    corpus_length = 1
elif len(crim_piece_selections) == 0 and len(uploaded_files_list) == 1:
    corpus_length = 1
elif len(crim_piece_selections) + len(uploaded_files_list)  >= 2:
    corpus_length = 2

if st.sidebar.checkbox("Explore Model Finder"):
    
    st.subheader("Model Finder")
    st.write("[Know the code! Read more about CRIM Intervals cadence methods](https://github.com/HCDigitalScholarship/intervals/blob/main/tutorial/13_Model_Finder.md)", unsafe_allow_html=True)
    if corpus_length <= 1:
        st.write("Please select at least two pieces to compare")
    elif corpus_length > 1:
        corpus = CorpusBase(corpus_list)
        with st.form("Model Finder Settings"):
            length_choice = st.number_input('Select ngram Length', value=4, step=1)
            submitted = st.form_submit_button("Submit")
            if submitted:
                soggetto_cross_plot = corpus.modelFinder(n=length_choice)
                st.dataframe(soggetto_cross_plot, use_container_width=True)
                fig, ax = plt.subplots()
                sns.heatmap(soggetto_cross_plot, cmap="YlGnBu", annot=False, ax=ax)
                st.write(fig)

            else:
                pass
   
