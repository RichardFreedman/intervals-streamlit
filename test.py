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
from io import StringIO


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

def find_uploaded_piece_url(uploaded_piece_name, list_of_uploaded_piece_dicts):
    key_value_pair = ('name', uploaded_piece_name)
    for list_of_uploaded_piece_dict in list_of_uploaded_piece_dicts:
        if key_value_pair in list_of_uploaded_piece_dict.items():
            path = list_of_uploaded_piece_dict['path']
    return path

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

crim_piece_selections= st.multiselect('Select Pieces To View from CRIM Django', 
                            all_piece_list)
st.write("Upload MEI or XML files")

uploaded_files_list = st.file_uploader("File upload", type=['mei', 'xml'], accept_multiple_files=True)

# list_of_uploaded_piece_dicts = []
# for file in uploaded_files_list:
#     with NamedTemporaryFile(dir='.') as f:
#         f.write(file.getbuffer())
        # file_dict = {'name' : file.name, 'path' : f.name }
        # list_of_uploaded_piece_dicts.append(file_dict)
        # # st.write(file_dict['name'])
        # piece_names.insert(-1, file_dict['name'])
        # list_of_names.append(file)
    # st.write(list_of_names)

# st.write(list_of_uploaded_piece_dicts)
# st.write(piece_names)
        # temp_pieces.append
    # piece = importScore(f.name)

crim_view_url = ''

if len(crim_piece_selections) == 0 and len(uploaded_files_list)== 0:
    st.subheader("Please Select or Upload One or More Pieces")

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

    if "piece" not in st.session_state or "metadata" not in st.session_state:
        pass
    else:
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
        with NamedTemporaryFile(dir='.', suffix = '.mei') as f:
            f.write(file.getbuffer())
            # f.name is in fact the TEMP PATH!
            piece = importScore(f.name)
        if "piece" not in st.session_state:
            st.session_state.piece = piece
        if "metadata" not in st.session_state:
            st.session_state.metadata = piece.metadata
        st.session_state.metadata['CRIM View'] = "Direct upload; not available on CRIM"

    if "piece" not in st.session_state or "metadata" not in st.session_state:
        pass
    else:
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
            if file is not None:
                file_details = {"FileName":file.name,"FileType":file.type}
                local_dir = '/Users/rfreedma/Documents/CRIM_Python/intervals-streamlit/'
                file_path = os.path.join(local_dir, file.name)
                with open(file_path,"wb") as f: 
                    f.write(file.getbuffer())         
                corpus_list.append(file_path)
    # make corpus and session state version
    if 'corpus' in st.session_state:
        del st.session_state.corpus        
    corpus = CorpusBase(corpus_list)
    if 'corpus' not in st.session_state:
        st.session_state.corpus = corpus
    for i in range(len(corpus.scores)):
        metadata_list.append(corpus.scores[i].metadata)
    st.dataframe(metadata_list, use_container_width=True)

# st.write(uploaded_files_list)

# #  SAVE THIS!  
# corpus_list = []
# for file in uploaded_files_list:
#     if file is not None:
#         file_details = {"FileName":file.name,"FileType":file.type}
#         st.write(file_details)
#         local_dir = '/Users/rfreedma/Documents/CRIM_Python/intervals-streamlit/'
#         file_path = os.path.join(local_dir, file.name)
#         st.write("This is the path" + file_path)
        
#         with open(file_path,"wb") as f: 
#             f.write(file.getbuffer())         
#         st.success("Saved File to disk")
#         corpus_list.append(file_path)
# st.write(corpus_list)

# corpus = CorpusBase(corpus_list)
# # st.write(corpus.scores[0])
# func = ImportedPiece.notes  # <- NB there are no parentheses here
# list_of_dfs = corpus.batch(func)
# st.write(list_of_dfs[0])

# If user attempts to upload a file.
# for file in uploaded_files_list:
#        # TEST 1
#     if st.checkbox('T1'):
#         bytes_data = file.read()
#         # st.write("filename:")
#         st.write(str(bytes_data))


#     if st.checkbox('T2'):
#     # # TEST 2 to read file as bytes:
#         data = file.getvalue()
#         st.write(data)

#     # # TEST 3 To convert to a string based IO:
#     if st.checkbox('T3'):
#         data = StringIO(file.getvalue().decode("utf-8"))
#         st.write(data)

#     # TEST 4 To read file as string:
#     if st.checkbox('T4'):
#         data = StringIO.read()
#         st.write(data)
#     # if file is not None:
#     #     bytes_data = file.getvalue()

    #     # Show the image filename and image.
    #     st.write(list(uploaded_files_list))
        

# for i in range(len(uploaded_files_list)):
#     bytes_data = uploaded_files_list[i].read()  # read the content of the file in binary
#     with open(os.path.join("/tmp", uploaded_files_list[i].name), "wb") as f:
#         corpus_list.append(f.write)
# corpus = CorpusBase(corpus_list)
# # st.write(corpus.scores[0]) 
# func = ImportedPiece.notes  # <- NB there are no parentheses here
# list_of_dfs = corpus.batch(func)
# st.dataframe(list_of_dfs[0])
     # write this content elsewhere 
    # if 'corpus_metadata' in st.session_state:
    #     del st.session_state.corpus_metadata  
    # for piece in st.session_state.corpus:
    #     metadata_list.append(piece.metadata)
    # if 'corpus_metadata' not in st.session_state:
    #     st.session_state.corpus_metadata = metadata_list
    
    # if "corpus" not in st.session_state or "corpus_metadata" not in st.session_state:
    #     pass
    # else:
    #     st.dataframe( st.session_state.corpus_metadata)



# for multiple pieces
# elif len(piece_names) > 1:
    
# # make initial list of paths
    
#     for piece_name in piece_names:
#         filepath = find_mei_link(piece_name, json_objects)
#         corpus_list.append(filepath)
#     corpus = CorpusBase(corpus_list)

#     st.session_state.corpus = corpus

    
 
    # # show summary of corpus
    
    # show_metadata_summary = st.checkbox("Show Summary of Corpus and Score Options")
    # if show_metadata_summary:
    #     summary_data = []
    #     for piece_name in piece_names:
    #         position = piece_names.index(piece_name)
    #         piece_data = corpus.scores[position].metadata
    #         crim_view = 'https://crimproject.org/pieces/' + piece_name
    #         piece_data["CRIM URL"] = crim_view
    #         summary_data.append(piece_data)
    #     st.dataframe(summary_data, use_container_width = True)

    #     # option to show individual scores
    #     for piece_name in piece_names:
    #         position = piece_names.index(piece_name)
    #         piece_data = corpus.scores[position].metadata
    #         crim_view = 'https://crimproject.org/pieces/' + piece_name
    #         piece_data["View on CRIM"] = crim_view
    #         st.dataframe(piece_data, use_container_width = True)
            
    #         if "mei_file" in st.session_state:
    #             del st.session_state.mei_file
    #         mei_file = "https://raw.githubusercontent.com/CRIM-Project/CRIM-online/master/crim/static/mei/MEI_4.0/" + piece_name + ".mei"
    #         if "mei_file" not in st.session_state:
    #             st.session_state.mei_file = mei_file
    #         show_score_checkbox = st.checkbox('Show This Score with Verovio', key = position)
    #         if show_score_checkbox:
    #             show_score(st.session_state.mei_file)

# check to see that corpus is updated
# if "corpus" in st.session_state:
#     st.write(st.session_state.corpus.paths)      
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
    nr = nr.reset_index()
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

            if len(piece_names) == 1:
                nr = piece_notes(piece,
                            combine_unisons_choice, 
                            combine_rests_choice)
            # # for corpus
            elif len(piece_names) > 1:
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
        if len(piece_names) == 1:
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
            nr_chart = px.bar(nr_counts, x="pitch", y=voices, title="Distribution of Pitches in " + ', '.join(piece_names))
            st.plotly_chart(nr_chart, use_container_width = True)
            
            st.dataframe(filtered_nr, use_container_width = True)
            # download option
            csv = convert_df(filtered_nr)
            st.download_button(
                label="Download Filtered Data as CSV",
                data=csv,
                file_name = piece_name + '_notes_results.csv',
                mime='text/csv',
                )
        # for corpus:
        if len(piece_names) > 1:
            
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
            nr_chart = px.bar(nr_counts, x="pitch", y=voices, title="Distribution of Pitches in " + ', '.join(piece_names))
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
        