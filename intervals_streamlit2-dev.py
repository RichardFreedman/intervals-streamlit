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
import random
from tempfile import NamedTemporaryFile

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



def show_score(mei_git_url):
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

        fetch('"""+mei_git_url+"""')
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

# for key in st.session_state.keys():
#     del st.session_state[key]

# Title and Introduction
st.title("CRIM Intervals")
st.subheader("A web application for analysis of musical patterns using the CRIM Intervals library.")
st.write("More about CRIM Intervals at:  https://github.com/HCDigitalScholarship/intervals/blob/rich_dev_22/README.md")


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


    st.dataframe(st.session_state.metadata, use_container_width=True)  

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
        st.dataframe(st.session_state.metadata, use_container_width=True)  


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

    st.dataframe(st.session_state.corpus_metadata, use_container_width=True)

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


# CRIM at GIT
# piece_list = []
# crim_git_prefix = "https://raw.githubusercontent.com/CRIM-Project/CRIM-online/master/crim/static/mei/MEI_4.0/"
# crim_git_url = "https://api.github.com/repos/CRIM-Project/CRIM-online/git/trees/990f5eb3ff1e9623711514d6609da4076257816c"
# piece_json = requests.get(crim_git_url).json()
# # pattern to filter out empty header Mass files
# pattern = 'CRIM_Mass_([0-9]{4}).mei'

# # # and now the request for all the files
# for p in piece_json["tree"]:
#     name = p["path"]
#     if re.search(pattern, name):
#         pass
#     else:
#         piece_list.append(name)
# # st.write(piece_list)
# piece_list = sorted(piece_list)
# piece_name = st.selectbox('Select Piece To View from CRIM@GIT', 
#                            piece_list)
# # based on selected piece, get the mei file link and import it
# if piece_name is not None:
#     filepath = crim_git_prefix + piece_name
#     piece = importScore(filepath)
#     st.subheader("Selected Piece")
#     if piece_name is not None:
#         st.write(piece_name)
#         st.write(piece.metadata['composer'] + ': ' + piece.metadata['title'])
#         show_score_checkbox = st.checkbox('Show/Hide Score with Verovio')


# menu dictionaries

interval_kinds = {'diatonic' : 'd',
                 'chromatic' : 'c',
                 'with quality' : 'q',
                 'zero-based diatonic' : 'z'}

unison_status = {'Separate Unisons' : False,
                 'Combine Unisons' : True}

rest_status = {'Combine Rests' : True,
                 ' Separate Rests' : False}

interval_order_quality = ["-P8", "-M7", "-m7", "-M6", "-m6", "-P5", "-P4", "-M3", 
                          "-m3", "-M2", "-m2", "P1", "m2", "M2", "m3", "M3",
                          "P4", "P5", "m6", "M6", "m7", "M7", "P8"]

# interval_order_quality = ["-P8", "m2", "-m2", "M2", "-M2", "m3", "-m3", "M3", "-M3", "P4", "-P4", "P5", "-P5", 
#             "m6", "-m6", "M6", "-M6", "m7", "-m7", "M7", "-M7", "P8", "-P8"]

pitch_order = ['E-2', 'E2', 'F2', 'F#2', 'G2', 'A2', 'B-2', 'B2', 
                'C3', 'C#3', 'D3', 'E-3','E3', 'F3', 'F#3', 'G3', 'G#3','A3', 'B-3','B3',
                'C4', 'C#4','D4', 'E-4', 'E4', 'F4', 'F#4','G4', 'A4', 'B-4', 'B4',
                'C5', 'C#5','D5', 'E-5','E5', 'F5', 'F#5', 'G5', 'A5', 'B-5', 'B5']

# filter and download functions
def convertTuple(tup):
    out = ""
    if isinstance(tup, tuple):
        out = ', '.join(tup)
    return out  


st.cache_data(experimental_allow_widgets=True)
def filter_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a UI on top of a dataframe to let viewers filter columns

    Args:
        df (pd.DataFrame): Original dataframe

    Returns:
        pd.DataFrame: Filtered dataframe
    """
 
    df = df.copy()

    modification_container = st.container()

    with modification_container:
        to_filter_columns = st.multiselect("Filter dataframe on", df.columns)
        for column in to_filter_columns:
            left, right = st.columns((1, 20))
            left.write("↳")
            # Treat columns with < 10 unique values as categorical
            if is_categorical_dtype(df[column]) or df[column].nunique() < 20:
                user_cat_input = right.multiselect(
                    f"Values for {column}",
                    df[column].unique(),
                    default=list(df[column].unique()),
                )
                df = df[df[column].isin(user_cat_input)]
            elif is_numeric_dtype(df[column]):
                _min = int(df[column].min())
                _max = int(df[column].max())
                user_num_input = right.slider(
                    f"Values for {column}",
                    _min,
                    _max,
                    (_min, _max)
                )
                df = df[df[column].between(*user_num_input)]
            
            else:
                user_text_input = right.text_input(
                    f"Substring or regex in {column}",
                )
                if user_text_input:
                    df = df[df[column].str.contains(user_text_input)]

    return df

# download function for filtered results
@st.cache_data
def convert_df(filtered):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return filtered.to_csv().encode('utf-8')

# intervals functions and forms

# notes piece
# @st.cache_data
def piece_notes(piece, combine_unisons_choice, combine_rests_choice):
    nr = piece.notes(combineUnisons = combine_unisons_choice,
                            combineRests = combine_rests_choice)
    nr = piece.detailIndex(nr)
    # nr = nr.reset_index()
    nr = nr.assign(Composer=piece.metadata['composer'], Title=piece.metadata['title'], Date=piece.metadata['date'])
    cols_to_move = ['Composer', 'Title', 'Date']
    nr = nr[cols_to_move + [col for col in nr.columns if col not in cols_to_move]]
    
    
    return nr
# @st.cache_data
def corpus_notes(corpus, combine_unisons_choice, combine_rests_choice):
    func = ImportedPiece.notes  # <- NB there are no parentheses here
    list_of_dfs = corpus.batch(func = func, 
                                kwargs = {'combineUnisons': combine_unisons_choice, 'combineRests': combine_rests_choice}, 
                                metadata=False)
    func2 = ImportedPiece.detailIndex
    list_of_dfs = corpus.batch(func = func2, 
                            kwargs = {'df': list_of_dfs}, 
                            metadata = True)
    rev_list_of_dfs = [df.reset_index() for df in list_of_dfs]
    nr = pd.concat(rev_list_of_dfs)
    cols_to_move = ['Composer', 'Title', 'Date']
    nr = nr[cols_to_move + [col for col in nr.columns if col not in cols_to_move]]
    return nr

# notes form
if st.sidebar.checkbox("Explore Notes"):
    st.subheader("Explore Notes")
    st.write("Did you **change the piece list**?  If so, please select **Update and Submit from Form**")

    with st.form("Note Settings"):
        combine_unisons_choice = st.selectbox(
            "Combine Unisons", [False, True])
        combine_rests_choice = st.selectbox(
            "Combine Rests", [True, False])
        # form submission button
        submitted = st.form_submit_button("Update and Run Search")
        
        if submitted:
            # for one piece

            if 'nr' in st.session_state:
                    del st.session_state.nr

            if corpus_length == 1:
                nr = piece_notes(piece,
                            combine_unisons_choice, 
                            combine_rests_choice)
            # # for corpus
            elif corpus_length > 1:
                nr = corpus_notes(st.session_state.corpus,
                        combine_unisons_choice, 
                        combine_rests_choice) 
            if "nr" not in st.session_state:
                    st.session_state.nr = nr

    # and use the session state variables for display
    if 'nr' not in st.session_state:
        pass
    else:
        # filter the nr results
        st.write("Did you **change the piece list**?  If so, please select **Update and Submit from Form**")
        st.write("Filter Results by Contents of Each Column")
        # filtered_nr = filter_dataframe(st.session_state.nr).fillna('-')
        # for one piece
        if corpus_length == 1:
            # filtered_nr = filter_dataframe(st.session_state.nr.fillna('-'))
            filtered_nr = filter_dataframe(st.session_state.nr).fillna('-')
            nr_no_mdata = filtered_nr.drop(['Composer', 'Title', "Date"], axis=1)
            # nr_counts = nr_no_mdata.apply(pd.Series.value_counts).fillna(0).astype(int).reset_index().copy()  
            nr_counts = nr_no_mdata.apply(pd.Series.value_counts).fillna(0).reset_index().copy()  

            nr_counts.rename(columns = {'index':'pitch'}, inplace = True) 
            # apply categorical for order
            nr_counts['pitch'] = pd.Categorical(nr_counts["pitch"], categories=pitch_order)  
            nr_counts = nr_counts.sort_values(by = "pitch").dropna().copy()
            voices = nr_counts.columns.to_list() 
        # Show results
            nr_chart = px.bar(nr_counts, x="pitch", y=voices, title="Distribution of Pitches in " + piece.metadata['title'])
            st.plotly_chart(nr_chart, use_container_width = True)
            
            st.dataframe(filtered_nr, use_container_width = True)
            # download option
            csv = convert_df(filtered_nr)
            st.download_button(
                label="Download Filtered Data as CSV",
                data=csv,
                file_name = piece.metadata['title'] + '_notes_results.csv',
                mime='text/csv',
                )
        # for corpus:
        if corpus_length > 1:
            
            st.write("Did you **change the piece list**?  If so, please select **Update and Submit from Form**")
            # filtered_nr = filter_dataframe(st.session_state.nr.fillna('-'))
            filtered_nr = filter_dataframe(st.session_state.nr).fillna('-')
            nr_no_mdata = filtered_nr.drop(['Composer', 'Title', "Date", "Measure", "Beat"], axis=1)
            # nr_counts = nr_no_mdata.apply(pd.Series.value_counts).fillna(0).astype(int).reset_index().copy()  
            nr_counts = nr_no_mdata.apply(pd.Series.value_counts).fillna(0).reset_index().copy()  

            nr_counts.rename(columns = {'index':'pitch'}, inplace = True) 
            # apply categorical for order
            nr_counts['pitch'] = pd.Categorical(nr_counts["pitch"], categories=pitch_order)  
            nr_counts = nr_counts.sort_values(by = "pitch").dropna().copy()
            voices = nr_counts.columns.to_list() 
            # Show results
            nr_chart = px.bar(nr_counts, x="pitch", y=voices, title="Distribution of Pitches in " + ', '.join(titles))
            st.plotly_chart(nr_chart, use_container_width = True)
            
            st.dataframe(filtered_nr, use_container_width = True)
    # download option
        
            csv = convert_df(filtered_nr)
            st.download_button(
                label="Download Filtered Data as CSV",
                data=csv,
                file_name = 'corpus_notes_results.csv',
                mime='text/csv',
                )
        
# melodic functions
# @st.cache_data
def piece_mel(piece, combine_unisons_choice, combine_rests_choice, kind_choice, directed, compound):
    nr = piece.notes(combineUnisons = combine_unisons_choice,
                              combineRests = combine_rests_choice)
    mel = piece.melodic(df = nr, 
                        kind = kind_choice,
                        directed = directed,
                        compound = compound)
    mel = piece.detailIndex(mel)
    # mel = mel.reset_index()
    mel = mel.assign(Composer=piece.metadata['composer'], Title=piece.metadata['title'], Date=piece.metadata['date'])
    cols_to_move = ['Composer', 'Title', 'Date']
    mel = mel[cols_to_move + [col for col in mel.columns if col not in cols_to_move]]

    return mel

# @st.cache_data
def corpus_mel(corpus, combine_unisons_choice, combine_rests_choice, kind_choice, directed, compound):
    func = ImportedPiece.notes  # <- NB there are no parentheses here
    list_of_dfs = corpus.batch(func = func, 
                                kwargs = {'combineUnisons': combine_unisons_choice, 'combineRests': combine_rests_choice}, 
                                metadata=False)
    func2 = ImportedPiece.melodic
    list_of_dfs = corpus.batch(func = func2,
                               kwargs = {'df' : list_of_dfs, 'kind' : kind_choice, 'directed' : directed, 'compound' : compound},
                               metadata = False)
    func3 = ImportedPiece.detailIndex
    list_of_dfs = corpus.batch(func = func3, 
                            kwargs = {'df': list_of_dfs}, 
                            metadata = True)
    mel = pd.concat(list_of_dfs)
    cols_to_move = ['Composer', 'Title', 'Date']
    mel = mel[cols_to_move + [col for col in mel.columns if col not in cols_to_move]]

    return mel

# melodic form
if st.sidebar.checkbox("Explore Melodic Intervals"):
    st.subheader("Explore Melodic Intervals")
    st.write("Did you **change the piece list**?  If so, please select **Update and Submit from Form**")

    with st.form("Melodic Interval Settings"):
        combine_unisons_choice = st.selectbox(
            "Combine Unisons", [False, True])
        combine_rests_choice = st.selectbox(
            "Combine Rests", [True, False])
        select_kind = st.selectbox(
            "Select Interval Kind", 
            ["diatonic", "chromatic", "with quality", "zero-based diatonic"])
        kind_choice = interval_kinds[select_kind]
        directed = st.selectbox(
            "Select Directed Interval Status",
            [True, False])
        compound = st.selectbox(
            "Select Compound Interval Status",
            [True, False])
        # form submission button
        submitted = st.form_submit_button("Update and Submit")
        if submitted:
            # run the function here, passing in settings from the form above
            if 'mel' in st.session_state:
                del st.session_state.mel
            # run the function here, passing in settings from the form above
            if corpus_length == 1:
                 mel = piece_mel(piece,
                            combine_unisons_choice, 
                            combine_rests_choice, 
                            kind_choice,
                            directed,
                            compound)
            elif corpus_length  > 1:
                 mel = corpus_mel(st.session_state.corpus,
                            combine_unisons_choice, 
                            combine_rests_choice, 
                            kind_choice,
                            directed,
                            compound)  
            if "mel" not in st.session_state:
                st.session_state.mel = mel
    
    # and use the session state variables for display
    if 'mel' not in st.session_state:
        pass
    else:
        # show corpus data for mel with filter options
        st.write("Did you **change the piece list**?  If so, please select **Update and Submit from Form**")
        st.write("Filter Results by Contents of Each Column")
        # st.dataframe(st.session_state.mel)
        filtered_mel = filter_dataframe(st.session_state.mel.fillna('-'))
        
# for one piece
        if corpus_length  == 1: 
            mel_no_mdata = filtered_mel.drop(['Composer', 'Title', "Date"], axis=1)
            mel_counts = mel_no_mdata.apply(pd.Series.value_counts).fillna(0).astype(int).reset_index().copy()
            # mel_counts = mel_no_mdata.apply(pd.Series.value_counts).fillna(0).reset_index().copy()
            mel_counts.rename(columns = {'index':'interval'}, inplace = True)
            # apply the categorical list and sort.  
            if interval_kinds[select_kind] == 'q':
                mel_counts['interval'] = pd.Categorical(mel_counts["interval"], categories=interval_order_quality)
            else:
                mel_counts = mel_counts.sort_values(by = "interval").dropna().copy()
            mel_counts.index.rename('interval', inplace=True)
            voices = mel_counts.columns.to_list() 
            mel_chart = px.bar(mel_counts, x="interval", y=voices, title="Distribution of Melodic Intervals in " + piece.metadata['title'])
            # and show results
            st.plotly_chart(mel_chart, use_container_width = True)
            st.dataframe(filtered_mel, use_container_width = True)
            csv = convert_df(filtered_mel)
            st.download_button(
                label="Download Filtered Data as CSV",
                data=csv,
                file_name = piece.metadata['title'] + '_melodic_results.csv',
                mime='text/csv',
                )
        # for corpus
        elif corpus_length > 1:
            mel_no_mdata = filtered_mel.drop(['Composer', 'Title', "Date"], axis=1)
            mel_counts = mel_no_mdata.apply(pd.Series.value_counts).fillna(0).astype(int).reset_index().copy()
            mel_counts.rename(columns = {'index':'interval'}, inplace = True)
            # apply the categorical list and sort.  
            if interval_kinds[select_kind] == 'q':
                mel_counts['interval'] = pd.Categorical(mel_counts["interval"], categories=interval_order_quality)
            else:
                mel_counts = mel_counts.sort_values(by = "interval").dropna().copy()
            mel_counts.index.rename('interval', inplace=True)
            voices = mel_counts.columns.to_list() 
            mel_chart = px.bar(mel_counts, x="interval", y=voices, title="Distribution of Melodic Intervals in " + ', '.join(titles))
            # and show results
            st.plotly_chart(mel_chart, use_container_width = True)
            st.dataframe(filtered_mel, use_container_width = True)
            csv = convert_df(filtered_mel)
            st.download_button(
                label="Download Filtered Data as CSV",
                data=csv,
                file_name = 'corpus_melodic_results.csv',
                mime='text/csv',
                )
        
# harmonic functions
# @st.cache_data
def piece_har(piece, kind_choice, directed, compound, against_low):
    har = piece.harmonic(kind = kind_choice, 
                         directed = directed,
                         compound = compound,
                         againstLow = against_low).fillna('')

    har = piece.detailIndex(har)
    # har = har.reset_index()
    har = har.assign(Composer=piece.metadata['composer'], Title=piece.metadata['title'], Date=piece.metadata['date'])
    cols_to_move = ['Composer', 'Title', 'Date']
    har = har[cols_to_move + [col for col in har.columns if col not in cols_to_move]]
    return har

# @st.cache_data
def corpus_har(corpus, kind_choice, directed, compound, against_low):
    func = ImportedPiece.harmonic
    list_of_dfs = corpus.batch(func = func,
                               kwargs = {'kind' : kind_choice, 'directed' : directed, 'compound' : compound, 'againstLow' : against_low},
                               metadata = False)
    func2 = ImportedPiece.detailIndex
    list_of_dfs = corpus.batch(func = func2, 
                            kwargs = {'df': list_of_dfs}, 
                            metadata = True)
    har = pd.concat(list_of_dfs)
    cols_to_move = ['Composer', 'Title', 'Date']
    har = har[cols_to_move + [col for col in har.columns if col not in cols_to_move]]

    return har

# harmonic form
if st.sidebar.checkbox("Explore Harmonic Intervals"):
    st.subheader("Explore Harmonic Intervals")
    with st.form("Harmonic Interval Settings"):
        directed = st.selectbox(
            "Select Directed Interval Status",
            [True, False])
        compound = st.selectbox(
            "Select Compound Interval Status",
            [True, False])
        select_kind = st.selectbox(
            "Select Interval Kind", 
            ["diatonic", "chromatic", "with quality", "zero-based diatonic"])
        kind_choice = interval_kinds[select_kind]
        against_low = st.selectbox("Calculate Intervals Only Against Lowest Voice", 
                                   [False, True])
        # form submission button
        submitted = st.form_submit_button("Update and Submit")
        if submitted:
            # run the function here, passing in settings from the form above
            if 'har' in st.session_state:
                del st.session_state.har
            # run the function here, passing in settings from the form above
            if corpus_length == 1:
                 har = piece_har(piece,
                            kind_choice,
                            directed,
                            compound,
                            against_low)
            elif corpus_length > 1:
                 har = corpus_har(st.session_state.corpus,
                            kind_choice,
                            directed,
                            compound,
                            against_low)
            
            if "har" not in st.session_state:
                st.session_state.har = har
    # and use the session state variables for display
    if 'har' not in st.session_state:
        pass
    else:
        # count up the values in each item column--sum for each pitch. make a copy 
        st.write("Did you **change the piece list**?  If so, please select **Update and Submit from Form**")
        st.write("Filter Results by Contents of Each Column")
        filtered_har = filter_dataframe(st.session_state.har.fillna('-'))
        # for one piece
        if corpus_length == 1: 
            har_no_mdata = filtered_har.drop(['Composer', 'Title', "Date"], axis=1)
            har_counts = har_no_mdata.apply(pd.Series.value_counts).fillna(0).astype(int).reset_index().copy()
            # rename the index column to something more useful
            har_counts.rename(columns = {'index':'interval'}, inplace = True)
            # apply the categorical list and sort.  
            if interval_kinds[select_kind] == 'q':
                har_counts['interval'] = pd.Categorical(har_counts["interval"], categories=interval_order_quality)
            else:
                har_counts = har_counts.sort_values(by = "interval").dropna().copy()
            har_counts.index.rename('interval', inplace=True)
            voices = har_counts.columns.to_list()
            # set the figure size, type and colors
            har_chart = px.bar(har_counts, x="interval", y=voices, title="Distribution of Harmonic Intervals in " + piece.metadata['title'])
            # show results
            st.plotly_chart(har_chart, use_container_width = True)
            st.dataframe(filtered_har, use_container_width = True)
            csv = convert_df(filtered_har)
            st.download_button(
                label="Download Filtered Data as CSV",
                data=csv,
                file_name = piece.metadata['title'] + '_harmonic_results.csv',
                mime='text/csv',
                )
        elif corpus_length > 1: 
            if 'Composer' not in filtered_har.columns:
                st.write("Did you **change the piece list**?  If so, please select **Update and Submit from Form**")
            else:
                har_no_mdata = filtered_har.drop(['Composer', 'Title', "Date"], axis=1)
                har_counts = har_no_mdata.apply(pd.Series.value_counts).fillna(0).astype(int).reset_index().copy()
                # rename the index column to something more useful
                har_counts.rename(columns = {'index':'interval'}, inplace = True)
                # apply the categorical list and sort.  
                if interval_kinds[select_kind] == 'q':
                    har_counts['interval'] = pd.Categorical(har_counts["interval"], categories=interval_order_quality)
                har_counts = har_counts.sort_values(by = "interval").dropna().copy()
                har_counts.index.rename('interval', inplace=True)
                voices = har_counts.columns.to_list()
                # set the figure size, type and colors
                har_chart = px.bar(har_counts, x="interval", y=voices, title="Distribution of Harmonic Intervals in " + ', '.join(titles))

                # show results
                st.plotly_chart(har_chart, use_container_width = True)
                st.dataframe(filtered_har, use_container_width = True)
                csv = convert_df(filtered_har)
                st.download_button(
                    label="Download Filtered Data as CSV",
                    data=csv,
                    file_name = 'corpus_harmonic_results.csv',
                    mime='text/csv',
                    )           



# function for ngram heatmap
# @st.cache_data
def ngram_heatmap(piece, combine_unisons_choice, kind_choice, directed, compound, length_choice, include_count):
    # find entries for model
    nr = piece.notes(combineUnisons = combine_unisons_choice)
    mel = piece.melodic(df = nr, 
                        kind = kind_choice,
                        directed = directed,
                        compound = compound,
                        end = False)

    # this is for entries only
    if entries_only == True:    
        # pass the following ngrams to the plot below as first df
        entry_ngrams = piece.entries(df = mel, 
                                    n = length_choice, 
                                    thematic = True, 
                                    anywhere = True,
                                    exclude = ['Rest'])

        # pass the ngram durations below to the plot as second df
        entry_ngrams_duration = piece.durations(df = mel, 
                                            n =length_choice, 
                                            mask_df = entry_ngrams)
        # make the heatmap
        entry_ng_heatmap = viz.plot_ngrams_heatmap(entry_ngrams, 
                                         entry_ngrams_duration, 
                                         selected_patterns=[], 
                                         voices=[],  
                                         includeCount=include_count)
        # rename entry_ngrams df as mel_ngrams for display
        entry_ngrams_detail = piece.detailIndex(entry_ngrams, offset = False)
        
        return entry_ngrams_detail, entry_ng_heatmap
    # this is for all mel ngrams (if entries is False in form)
    else:
        mel_ngrams = piece.ngrams(df = mel, n = length_choice, exclude = ['Rest'])

        mel_ngrams_duration = piece.durations(df = mel, 
                                          n =length_choice)
        
        ng_heatmap = viz.plot_ngrams_heatmap(mel_ngrams, 
                                         mel_ngrams_duration, 
                                         selected_patterns=[], 
                                         voices=[], 
                                         includeCount=include_count)
        
        mel_ngrams_detail = piece.detailIndex(mel_ngrams, offset = False)  

        return mel_ngrams_detail, ng_heatmap

# hr functions
# one piece
# @st.cache_data
def piece_homorhythm(piece, length_choice, full_hr_choice):
    hr = piece.homorhythm(ngram_length=length_choice, 
                    full_hr=full_hr_choice)
    # voices_list = list(piece.notes().columns)
    # hr[voices_list] = hr[voices_list].applymap(convertTuple).fillna('-')
    columns_to_keep = ['active_voices', 'number_dur_ngrams', 'hr_voices', 'syllable_set', 
           'count_lyr_ngrams', 'active_syll_voices', 'voice_match']
    hr = hr.drop(columns=[col for col in hr.columns if col not in columns_to_keep])
    hr['hr_voices'] = hr['hr_voices'].apply(', '.join)
    hr['syllable_set'] = hr['syllable_set'].apply(lambda x: ''.join(map(str, x[0]))).copy()
    hr = hr.reset_index()
    hr = hr.assign(Composer=piece.metadata['composer'], Title=piece.metadata['title'], Date=piece.metadata['date'])
    cols_to_move = ['Composer', 'Title', 'Date']
    hr = hr[cols_to_move + [col for col in hr.columns if col not in cols_to_move]]
    
    return hr
# orpus
# @st.cache_data
def corpus_homorhythm(corpus, length_choice, full_hr_choice):
    func = ImportedPiece.homorhythm
    list_of_dfs = corpus.batch(func = func,
                               kwargs = {'ngram_length' : length_choice, 'full_hr' : full_hr_choice},
                               metadata = True)
#
    rev_list_of_dfs = [df.reset_index() for df in list_of_dfs]
    hr = pd.concat(rev_list_of_dfs)
    # voices_list = list(piece.notes().columns)
    # hr[voices_list] = hr[voices_list].applymap(convertTuple).fillna('-')
    columns_to_keep = ['active_voices', 'number_dur_ngrams', 'hr_voices', 'syllable_set', 
           'count_lyr_ngrams', 'active_syll_voices', 'voice_match', 'Composer', 'Title', 'Date']
    hr = hr.drop(columns=[col for col in hr.columns if col not in columns_to_keep])
    hr['hr_voices'] = hr['hr_voices'].apply(', '.join)
    hr['syllable_set'] = hr['syllable_set'].apply(lambda x: ''.join(map(str, x[0]))).copy()
    cols_to_move = ['Composer', 'Title', 'Date']
    hr = hr[cols_to_move + [col for col in hr.columns if col not in cols_to_move]]
    
    return hr

# HR form
if st.sidebar.checkbox("Explore Homorhythm"):
    st.subheader("Explore Homorhythm")
    with st.form("Homorhythm Settings"):
        full_hr_choice = st.selectbox(
            "Select HR Full Status",
            [True, False])
        length_choice = st.number_input('Select ngram Length', value=4, step=1)
        submitted = st.form_submit_button("Update and Submit")
        if submitted:
            if 'hr' in st.session_state:
                del st.session_state.hr
            if corpus_length == 1:
                 hr = piece_homorhythm(st.session_state.piece, length_choice, full_hr_choice)
            elif corpus_length > 1:
                 hr = corpus_homorhythm(st.session_state.corpus, length_choice, full_hr_choice)
            if "hr" not in st.session_state:
                st.session_state.hr = hr
# and use the session state variables for display
    if 'hr' not in st.session_state:
        pass
    else:
        st.write("Did you **change the piece list**?  If so, please select **Update and Submit from Form**")
        st.write("Filter Results by Contents of Each Column")
        filtered_hr = filter_dataframe(st.session_state.hr.fillna('-'))
        st.dataframe(filtered_hr, use_container_width = True)
        csv = convert_df(filtered_hr)
        if corpus_length == 1:
            download_name = piece.metadata['title'] + '_homorhythm_results.csv'
        elif corpus_length > 1:
            download_name = "corpus_homorhythm_results.csv"
        st.download_button(
            label="Download Filtered Data as CSV",
            data=csv,
            
            
            
            
            file_name = download_name,
            mime='text/csv',
            ) 
        

# p type function
# piece
# @st.cache_data
def piece_presentation_types(piece, 
                            length_choice, 
                            limit_entries_choice,
                            body_flex_choice, 
                            head_flex_choice,
                            hidden_types_choice,
                            combine_unisons_choice): 
    
    p_types = piece.presentationTypes(melodic_ngram_length = length_choice, 
                                      limit_to_entries = limit_entries_choice,
                                      body_flex = body_flex_choice, 
                                      head_flex = head_flex_choice,
                                      include_hidden_types = hidden_types_choice,
                                      combine_unisons = combine_unisons_choice)
    
    # clean up for streamlit facets
    p_types["Measures_Beats"] = p_types["Measures_Beats"].apply(lambda x: ', '.join(map(str, x))).copy()
    p_types["Melodic_Entry_Intervals"] = p_types["Melodic_Entry_Intervals"].apply(lambda x: ', '.join(map(str, x))).copy()
    p_types["Offsets"]= p_types["Offsets"].apply(lambda x: ', '.join(map(str, x))).copy()
    p_types["Soggetti"]= p_types["Soggetti"].apply(lambda x: ', '.join(map(str, x))).copy()
    # p_types ["Time_Entry_Intervals"]= p_types["Time_Entry_Intervals"].apply(lambda x: ', '.join(map(str, x))).copy()
    p_types["Time_Entry_Intervals"]= p_types["Time_Entry_Intervals"].apply(lambda x: ', '.join(map(str, x))).copy()
    
    return p_types
#corpus
# @st.cache_data
def presentation_types_corpus(corpus,
                              length_choice, 
                            limit_entries_choice,
                            body_flex_choice, 
                            head_flex_choice,
                            hidden_types_choice,
                            combine_unisons_choice):
                            
    func = ImportedPiece.presentationTypes
    list_of_dfs = corpus.batch(func = func,
                               kwargs = {'melodic_ngram_length' : length_choice, 
                                      'limit_to_entries' : limit_entries_choice,
                                      'body_flex' : body_flex_choice, 
                                      'head_flex' : head_flex_choice,
                                      'include_hidden_types' : hidden_types_choice,
                                      'combine_unisons' : combine_unisons_choice},
                                        metadata = True)
    for p_types in list_of_dfs:
        # clean up for streamlit facets
        p_types["Measures_Beats"] = p_types["Measures_Beats"].apply(lambda x: ', '.join(map(str, x))).copy()
        p_types["Melodic_Entry_Intervals"] = p_types["Melodic_Entry_Intervals"].apply(lambda x: ', '.join(map(str, x))).copy()
        p_types["Offsets"]= p_types["Offsets"].apply(lambda x: ', '.join(map(str, x))).copy()
        p_types["Soggetti"]= p_types["Soggetti"].apply(lambda x: ', '.join(map(str, x))).copy()
        # p_types ["Time_Entry_Intervals"]= p_types["Time_Entry_Intervals"].apply(lambda x: ', '.join(map(str, x))).copy()
        p_types["Time_Entry_Intervals"]= p_types["Time_Entry_Intervals"].apply(lambda x: ', '.join(map(str, x))).copy()
#
    # rev_list_of_dfs = [df.reset_index() for df in list_of_dfs]
    p_types = pd.concat(list_of_dfs)

    return p_types


# p types form
if st.sidebar.checkbox("Explore Presentation Types"):
    st.subheader("Explore Presentation Types")
    with st.form("Presentation Type Settings"):
        combine_unisons_choice = st.selectbox(
            "Combine Unisons", [False, True])
        length_choice = st.number_input('Select ngram Length', value=4, step=1) 
        head_flex_choice = st.number_input('Select Head Flex', value=1, step=1) 
        body_flex_choice = st.number_input('Select Body Flex', value=0, step=1) 
        limit_entries_choice = st.selectbox(
            "Limit to Melodic Entries", [True, False])
        hidden_types_choice = st.selectbox(
            "Include Hidden Presentation Types", [False, True])
        # form submission button
        submitted = st.form_submit_button("Update and Submit")
        if submitted:
            if "p_types" in st.session_state.keys():
                del st.session_state.p_types
            # one piece
            if corpus_length == 1:
                p_types = piece_presentation_types(piece, 
                                                    length_choice,
                                                    limit_entries_choice,
                                                    body_flex_choice,
                                                    head_flex_choice,
                                                    hidden_types_choice,
                                                    combine_unisons_choice)
                

                # Set up session state for these returns
                if "p_types" not in st.session_state:
                    st.session_state.p_types = p_types
            
            # corpus
            if corpus_length > 1:
                p_types = presentation_types_corpus(st.session_state.corpus,
                              length_choice, 
                            limit_entries_choice,
                            body_flex_choice, 
                            head_flex_choice,
                            hidden_types_choice,
                            combine_unisons_choice)
                
                # Set up session state for these returns
                if "p_types" not in st.session_state:
                    st.session_state.p_types = p_types
    if 'p_types' not in st.session_state:
        pass
    else:
        st.write("Did you **change the piece list**?  If so, please select **Update and Submit from Form**")
        st.write("Filter Results by Contents of Each Column")
        filtered_p_types = filter_dataframe(st.session_state.p_types)
        st.dataframe(filtered_p_types, use_container_width = True)
        csv = convert_df(filtered_p_types)
        if corpus_length == 1:
            download_name = piece.metadata['title'] + '_p_type_results.csv'
        elif corpus_length > 1:
            download_name = "corpus_p_type_results.csv"
        st.download_button(
            label="Download Filtered Data as CSV",
            data=csv,
            file_name = download_name,
            mime='text/csv',
            )

 
# ngram form
if st.sidebar.checkbox("Explore ngrams"):
    st.subheader("Explore nGrams")
    if corpus_length == 0:
        st.write("Please select one or more pieces")
    elif corpus_length == 1:
        with st.form("Ngram Settings"):
            combine_unisons_choice = st.selectbox(
                "Combine Unisons", [False, True])
            directed = st.selectbox(
                "Select Directed Interval Status",
                [True, False])
            compound = st.selectbox(
                "Select Compound Interval Status",
                [True, False])
            select_kind = st.selectbox(
                "Select Interval Kind", 
                ["diatonic", "chromatic", "with quality", "zero-based diatonic"])
            kind_choice = interval_kinds[select_kind]
            length_choice = st.number_input('Select ngram Length', value=3, step=1)
            entries_only = st.selectbox(
                "Melodic Entries Only?",
                [True, False])
            include_count = st.selectbox("Include Count of Ngrams", [True, False])
            # submit ngram form
            submitted = st.form_submit_button("Submit")
        #here we need separate sections for the _combined_ ngs (as a corpus function)
        # vs one heatmap for each piece in the corpus
        # put the corpus ngs in session state, then pass to filter below
        # display each heatmap on its own
            if submitted:
                key_list = ['ngrams', 'heatmap']
                for key in key_list:
                    if key in st.session_state.keys():
                        del st.session_state[key]
                ngrams, heatmap = ngram_heatmap(piece, 
                            combine_unisons_choice, 
                            kind_choice, 
                            directed, 
                            compound, 
                            length_choice,
                            include_count)
                if "ngrams" not in st.session_state:
                    st.session_state.ngrams = ngrams
                if 'heatmap' not in st.session_state:
                    st.session_state.heatmap = heatmap
        if 'heatmap' not in st.session_state:
            pass
        else:
            st.write("Did you **change the piece list**?  If so, please select **Update and Submit from Form**")
            st.subheader("Ngram Heatmap: " + piece.metadata["composer"] + ", " + piece.metadata["title"])
            st.altair_chart(st.session_state.heatmap, use_container_width = True)

            st.write("Filter Results by Contents of Each Column")
            filtered_ngrams = filter_dataframe(st.session_state.ngrams.applymap(convertTuple).fillna('-'))
            st.dataframe((filtered_ngrams), use_container_width = True)
            csv = convert_df(filtered_ngrams)
            st.download_button(
                label="Download Filtered Data as CSV",
                data=csv,
                file_name = piece.metadata['title'] + '_ngram_results.csv',
                mime='text/csv',
                )
    # for corpus
    elif corpus_length >= 2:
        with st.form("Ngram Settings"):
            combine_unisons_choice = st.selectbox(
                "Combine Unisons", [False, True])
            directed = st.selectbox(
                "Select Directed Interval Status",
                [True, False])
            compound = st.selectbox(
                "Select Compound Interval Status",
                [True, False])
            select_kind = st.selectbox(
                "Select Interval Kind", 
                ["diatonic", "chromatic", "with quality", "zero-based diatonic"])
            kind_choice = interval_kinds[select_kind]
            length_choice = st.number_input('Select ngram Length', value=3, step=1)
            entries_only = st.selectbox(
                "Melodic Entries Only?",
                [True, False])
            include_count = st.selectbox("Include Count of Ngrams", [True, False])
            # submit ngram form
            submitted = st.form_submit_button("Submit")
            st.write("Did you **change the piece list**?  If so, please select **Update and Submit from Form**")
        #here we need separate sections for the _combined_ ngs (as a corpus function)
        # vs one heatmap for each piece in the corpus
        # put the corpus ngs in session state, then pass to filter below
        # display each heatmap on its own
            if submitted:
                ngram_df_list = []
                for work in corpus_list:
                    piece = importScore(work)
                    
                    ngrams, heatmap = ngram_heatmap(piece, 
                                combine_unisons_choice, 
                                kind_choice, 
                                directed, 
                                compound, 
                                length_choice,
                                include_count)
                    ngram_df_list.append(ngrams)
                    # if "ngrams" not in st.session_state:
                    #     st.session_state.ngrams = ngrams
                    # if 'heatmap' not in st.session_state:
                    #     st.session_state.heatmap = heatmap
                    # if 'heatmap' not in st.session_state:
                    #     pass
                    st.subheader("Ngram Heatmap: " + piece.metadata["composer"] + ", " + piece.metadata["title"])
                    st.altair_chart(heatmap, use_container_width = True)
                if 'combined_ngrams' in st.session_state.keys():
                            del st.session_staten.combined_ngrams
                combined_ngrams = pd.concat(ngram_df_list)
                if "combined_ngrams" not in st.session_state:
                    st.session_state.combined_ngrams = combined_ngrams

            if "combined_ngrams" not in st.session_state:
                pass
            else:
                st.write("Filter Results by Contents of Each Column")
                st.write("Note that the Filters do NOT change the heatmaps shown above!")
                filtered_combined_ngrams = filter_dataframe(st.session_state.combined_ngrams.applymap(convertTuple).fillna('-'))
                st.dataframe((filtered_combined_ngrams), use_container_width = True)
                csv = convert_df(filtered_combined_ngrams)
                st.download_button(
                    label="Download Filtered Data as CSV",
                    data=csv,
                    file_name = 'corpus_ngram_results.csv',
                    mime='text/csv',
                    )

    
       
            
# cadence form
if st.sidebar.checkbox("Explore Cadences"):
    st.subheader("Explore Cadences")
    if corpus_length == 0:
        st.write("Please select one or more pieces")
    elif corpus_length == 1:
    # the full table of cad
        if st.checkbox("Show Full Cadence Table"):
            cadences = piece.cadences()
            st.subheader("Detailed View of Cadences")
            filtered_cadences = filter_dataframe(cadences)
            st.dataframe(filtered_cadences, use_container_width = True)
            # possible Verovio Cadences use.  Needs to adapt renderer?
            # if st.button("Print Filtered Cadences with Verovio"):
            #     output = piece.verovioCadences(df = filtered_cadences)
            #     components.html(output)
        # summary of tone and type
        if st.checkbox("Summary of Cadences by Tone and Type"):
            cadences = piece.cadences()
            grouped = cadences.groupby(['Tone', 'CadType']).size().reset_index(name='counts')
            st.subheader("Summary of Cadences by Tone and Type")
            grouped
        # radar plots
        if st.checkbox("Show Basic Radar Plot"):
            st.subheader("Basic Radar Plot")    
            radar = piece.cadenceRadarPlot(combinedType=False, displayAll=False, renderer='streamlit')
            st.plotly_chart(radar, use_container_width=True)
        if st.checkbox("Show Advanced Radar Plot"):
            st.subheader("Advanced Radar Plot")    
            radar = piece.cadenceRadarPlot(combinedType=True, displayAll=True, renderer='streamlit')
            st.plotly_chart(radar, use_container_width=True)
        if st.checkbox("Show Basic Progress Plot"):
            st.subheader("Basic Radar Plot")    
            progress = piece.cadenceProgressPlot(includeType=False, renderer='streamlit')
            st.pyplot(progress, use_container_width=True)
        if st.checkbox("Show Advanced Progress Plot"):
            st.subheader("Advanced Radar Plot")    
            progress = piece.cadenceProgressPlot(includeType=True, renderer='streamlit')
            st.pyplot(progress, use_container_width=True)
    # corpus
    elif corpus_length >= 2:
        func = ImportedPiece.cadences
        list_of_dfs = st.session_state.corpus.batch(func=func, kwargs={'keep_keys': True}, metadata=True)
        cadences = pd.concat(list_of_dfs, ignore_index=False)   
        cols_to_move = ['Composer', 'Title', 'Date']
        cadences = cadences[cols_to_move + [col for col in cadences.columns if col not in cols_to_move]] 
        if st.checkbox("Show Full Cadence Table"):
            st.subheader("Detailed View of Cadences")
            filtered_cadences = filter_dataframe(cadences)
            st.dataframe(filtered_cadences, use_container_width = True)
            # possible Verovio Cadences use.  Needs to adapt renderer?
            # if st.button("Print Filtered Cadences with Verovio"):
            #     output = piece.verovioCadences(df = filtered_cadences)
            #     components.html(output)
        # summary of tone and type
        if st.checkbox("Summary of Cadences by Tone and Type"):
            grouped = cadences.groupby(['Tone', 'CadType']).size().reset_index(name='counts')
            st.subheader("Summary of Cadences by Tone and Type")
            grouped
        # radar plots
        if st.checkbox("Show Basic Radar Plot"):
            st.subheader("Basic Radar Plot")    
            radar = st.session_state.corpus.compareCadenceRadarPlots(combinedType=False, displayAll=False, renderer='streamlit')
            st.plotly_chart(radar, use_container_width=True)
        if st.checkbox("Show Advanced Radar Plot"):
            st.subheader("Advanced Radar Plot")    
            radar = st.session_state.corpus.compareCadenceRadarPlots(combinedType=True, displayAll=True, renderer='streamlit')
            st.plotly_chart(radar, use_container_width=True)
        if st.checkbox("Show Basic Progress Plot"):
            st.subheader("Basic Radar Plot")    
            progress = st.session_state.corpus.compareCadenceProgressPlots(includeType=False, renderer='streamlit')
            st.pyplot(progress, use_container_width=True)
        if st.checkbox("Show Advanced Progress Plot"):
            st.subheader("Advanced Radar Plot")    
            progress = st.session_state.corpus.compareCadenceProgressPlots(includeType=True, renderer='streamlit')
            st.pyplot(progress, use_container_width=True)



   

