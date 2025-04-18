import streamlit as st
st. set_page_config(layout="wide")
from pathlib import Path
import requests
from requests.sessions import DEFAULT_REDIRECT_LIMIT
import requests
import crim_intervals
from crim_intervals import * 
from crim_intervals import main_objs
import crim_intervals.visualizations as viz
import pandas as pd
import altair as alt 
import glob as glob
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.figure_factory as ff
from plotly.offline import plot
import plotly.io as pio
# import base64
import streamlit.components.v1 as components
from os import listdir 
import json
import psutil
from tempfile import NamedTemporaryFile
import random
from datetime import datetime
import time
from collections import deque
from collections import Counter
import seaborn as sns


from pandas.api.types import (
    is_categorical_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
)


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
st.markdown("[Watch a video guide to this application.](https://haverford.box.com/s/uacqpcov6oh3sosjox94sqmucmjpnd40)")
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
st.write("Upload MEI or XML files")


uploaded_files_list = st.file_uploader("**Upload MEI or XML files**", type=['mei', 'xml'], accept_multiple_files=True)
crim_view_url = ''
if len(crim_piece_selections) == 0 and len(uploaded_files_list)== 0:
    st.write("**No Files Selected! Please Select or Upload One or More Pieces.**")

# for one piece in CRIM
elif len(crim_piece_selections) == 1 and len(uploaded_files_list)== 0:
    piece_name = crim_piece_selections[0]
    crim_view_url = 'https://crimproject.org/pieces/' + piece_name
    # url_for_verovio = "https://raw.githubusercontent.com/CRIM-Project/CRIM-online/master/crim/static/mei/MEI_4.0/" + piece_name + ".mei"

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
interval_order_quality = ["-P15", "-M14", "-m14", "-P13", "-A12", "-d13", "-P12", "-M11", "-m11", "-P10", "-A9", 
                          "-d10", "-P9", "-M8", "-m8", "-P7", "-A6", "-d7", "-P6", "-M5", "-m5", "-P4", "-A3", 
                          "-d4", "-P3", "-M2", "-m2", "-P1", "P1", "m2", "M2", "m3", "M3", "P4", "A4", 
                          "d5", "P5", "m6", "M6", "m7", "M7", "P8", "m9", "M9", "m10", "M10", "P11", 
                          "A11", "d12", "P12", "M13", "m13", "P13", "A14", "d14", "P14", "M15", "m15", "P15"]
# interval_order_quality = ["-P8", "m2", "-m2", "M2", "-M2", "m3", "-m3", "M3", "-M3", "P4", "-P4", "P5", "-P5", 
#             "m6", "-m6", "M6", "-M6", "m7", "-m7", "M7", "-M7", "P8", "-P8"]

pitch_order = ['A#1', 'B1', 
               'C2', 'C#2', 'D2', 'D#2','E-2', 'E2', 'E#2', 'F2', 'F#2', 'G-2', 'G2', 'G#2', 'A-2', 'A2', 'A#2','B-2', 'B2', 'B#2',
               'C3', 'C#3', 'D-3','D3', 'D#3', 'E-3','E3', 'E#3', 'F3', 'F#3', 'G-3', 'F##3', 'G3', 'G#3', 'A-3', 'A3', 'A#3', 'B-3','B3', 'B#3',
               'C4', 'C#4', 'D-4','D4', 'D#4','E-4', 'E4', 'F-4', 'E#4', 'F4', 'F#4', 'G-4', 'F##4', 'G4', 'G#4', 'A-4','A4', 'A#4', 'B-4', 'B4', 'B#4',
               'C5', 'C#5','C##5', 'D-5','D5', 'D#5', 'E-5','E5', 'F-5','E#5','F5', 'F#5', 'G-5', 'F##5','G5', 'G#5', 'A-5', 'A5', 'A#5', 'B-5', 'B5',
              'C6']

dur_order = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0, 3.25, 3.5, 3.75, 
             4.0, 4.25, 4.5, 4.75, 5.0, 5.25, 5.5, 5.75, 6.0, 6.25, 6.5, 6.75, 7.0, 7.25, 7.5, 7.75, 8.0]

# for radar notes plot
category_order = {
    'C': 0, 'C#': 1, 'Db': 2, 'D' : 3, 'D#': 4, 'Eb': 5, 'E': 6, 'E#': 7, 'F': 8, 'F#': 9, 'Gb': 10, 'F##': 11,
    'G': 12, 'G#': 13, 'Ab': 14, 'A': 15, 'A#': 16, 'Bb': 17, 'B': 18, 'B#': 19
}

pitch_class_order = ['C', 'C#', 'D-', 'D', 'D#', 'E-', 'E', 'F-', 'E#', 'F', 'F#', 'G-', 'F##', 'G', 'G#', 'A-', 'A', 'A#', 'B-', 'B', 'B#', 'Rest']

contrasting_colors = [
        '#636EFA',  # Blue
        '#DC267F',  # Pink
        '#009E73',  # Green
        '#FFB000',  # Orange
        '#977277',  # Purple
        '#EC4899',  # Hot Pink
        '#48BB78',  # Teal
        '#ED8936',  # Coral
        '#2563EB',  # Deep Blue
        '#8338EC',  # Violet
        '#FF922B',  # Tangerine
        '#06D6A0',  # Mint
        '#EF4444',  # Red
        '#F97316',  # Carrot
        '#84CC16',  # Lime
        '#3B82F6',  # Sky Blue
        '#A855F7',  # Plum
        '#22C55E',  # Forest
        '#EA580C',  # Persimmon
        '#94A3B8',  # Slate
    ]
#old pitch order
# pitch_order = ['E-2', 'E2', 'F2', 'F#2', 'G2', 'A2', 'B-2', 'B2', 
                # 'C3', 'C#3', 'D3', 'E-3','E3', 'F3', 'F#3', 'G3', 'G#3','A3', 'B-3','B3',
                # 'C4', 'C#4','D4', 'E-4', 'E4', 'F4', 'F#4','G4', 'A4', 'B-4', 'B4',
                # 'C5', 'C#5','D5', 'E-5','E5', 'F5', 'F#5', 'G5', 'A5', 'B-5', 'B5', 'Rest']

# filter and download functions
def convertTuple(tup):
    out = ""
    if isinstance(tup, tuple):
        out = ', '.join(tup)
    return out  

def extract_letter(value):
    # Find the index of the first digit
    if value is not None:
        for i, char in enumerate(value):
            if char.isdigit():
                # Return everything before the first digit
                return value[:i]
        # If no digit is found, return the entire string
        return value
# for NR
# st.cache_data(experimental_allow_widgets=True)
@st.fragment()
def filter_dataframe_nr(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a UI on top of a dataframe to let viewers filter columns

    Args:
        df (pd.DataFrame): Original dataframe

    Returns:
        pd.DataFrame: Filtered dataframe
    """
 
    df = df.copy()
    random_id = random.randrange(1,1000)
    modification_container = st.container()
    with modification_container:     
        # random_id = random.randrange(1,1000)
        to_filter_columns = st.multiselect("Filter Notes by Various Fields", df.columns)
        st.write("Remember that initial choices will constrain subsequent filters!")
        if to_filter_columns:
        # here we are filtering by column
            for column in to_filter_columns:
                left, right = st.columns((1, 20))
                left.write("↳")
                # Treat columns with < 10 unique values as categorical
                # here 
                if is_categorical_dtype(df[column]) or df[column].nunique() < 50:
                    user_cat_input = right.multiselect(
                        f"Values for {column}",
                        df[column].unique(),
                        default=list(df[column].unique()),
                    )
                    df = df[df[column].isin(user_cat_input)]  
        # gets values for highlighted filters
        df_no_meta = df.loc[:, ~df.columns.isin(['Composer', "Title", 'Date', "Measure", "Beat"])]
        df_no_meta_col_names = df_no_meta.columns.tolist()
        df_voices_only = df[df_no_meta_col_names]
        melted = pd.melt(df_voices_only)
        values_list = melted['value'].unique()
        values_list = [i for i in values_list if i]
        values_list = [element for element in values_list if not pd.isnull(element)]
        values_list = [x for x in values_list if x != "-"]
        user_text_input = st.multiselect("Filter on Notes", values_list)
        if user_text_input:
            def highlight_matching_strings(val):
                match_strings = user_text_input
                for match_string in match_strings:
                    if match_string == val:
                        return 'background-color: #ccebc4'
                return ''
            df = df.reset_index().fillna('')
            df = df[df[df_no_meta_col_names].apply(lambda x: x.isin(user_text_input)).any(axis=1)]
            df = df.style.map(highlight_matching_strings)
        else:
            df = df.reset_index().fillna('')
            df = df.style
    return df

# for dur
@st.fragment()
def filter_dataframe_dur(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a UI on top of a dataframe to let viewers filter columns

    Args:
        df (pd.DataFrame): Original dataframe

    Returns:
        pd.DataFrame: Filtered dataframe
    """
 
    df = df.copy()
    random_id = random.randrange(1,1000)
    modification_container = st.container()
    with modification_container:     
        # random_id = random.randrange(1,1000)
        to_filter_columns = st.multiselect("Filter Durations by Various Fields", df.columns)
        st.write("Remember that initial choices will constrain subsequent filters!")
        if to_filter_columns:
        # here we are filtering by column
            for column in to_filter_columns:
                left, right = st.columns((1, 20))
                left.write("↳")
                # Treat columns with < 10 unique values as categorical
                # here 
                if is_categorical_dtype(df[column]) or df[column].nunique() < 50:
                    user_cat_input = right.multiselect(
                        f"Values for {column}",
                        df[column].unique(),
                        default=list(df[column].unique()),
                    )
                    df = df[df[column].isin(user_cat_input)]  
        # gets values for highlighted filters
        df_no_meta = df.loc[:, ~df.columns.isin(['Composer', "Title", 'Date', "Measure", "Beat"])]
        df_no_meta_col_names = df_no_meta.columns.tolist()
        df_voices_only = df[df_no_meta_col_names]
        melted = pd.melt(df_voices_only)
        values_list = melted['value'].unique()
        values_list = [i for i in values_list if i]
        values_list = [element for element in values_list if not pd.isnull(element)]
        values_list = [x for x in values_list if x != "-"]
        user_text_input = st.multiselect("Filter on Notes", values_list)
        if user_text_input:
            def highlight_matching_strings(val):
                match_strings = user_text_input
                for match_string in match_strings:
                    if match_string == val:
                        return 'background-color: #ccebc4'
                return ''
            df = df.reset_index().fillna('')
            df = df[df[df_no_meta_col_names].apply(lambda x: x.isin(user_text_input)).any(axis=1)]
            df = df.style.map(highlight_matching_strings)
        else:
            df = df.reset_index().fillna('')
            df = df.style
    return df

# for MEL
# st.cache_data(experimental_allow_widgets=True)
@st.fragment()
def filter_dataframe_mel(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a UI on top of a dataframe to let viewers filter columns

    Args:
        df (pd.DataFrame): Original dataframe

    Returns:
        pd.DataFrame: Filtered dataframe
    """
 
    df = df.copy()
    random_id = random.randrange(1,1000)
    modification_container = st.container()
    with modification_container:
        # random_id = random.randrange(1,1000)
        to_filter_columns = st.multiselect("Filter Melodic Intervals by Various Fields", df.columns)
        st.write("Remember that initial choices will constrain subsequent filters!")
        if to_filter_columns:
        # here we are filtering by column
        # to_filter_columns = st.multiselect("Limit by Composer, Title, Date, or Voice", df.columns)
            for column in to_filter_columns:
                left, right = st.columns((1, 20))
                left.write("↳")
                # Treat columns with < 10 unique values as categorical
                # here 
                if is_categorical_dtype(df[column]) or df[column].nunique() < 50:
                    user_cat_input = right.multiselect(
                        f"Values for {column}",
                        df[column].unique(),
                        default=list(df[column].unique()),
                    )
                    df = df[df[column].isin(user_cat_input)]
        # gets values for highlighted filters
        df_no_meta = df.loc[:, ~df.columns.isin(['Composer', "Title", 'Date'])]
        df_no_meta_col_names = df_no_meta.columns.tolist()
        df_voices_only = df[df_no_meta_col_names]
        melted = pd.melt(df_voices_only)
        values_list = melted['value'].unique()
        values_list = [i for i in values_list if i]
        values_list = [element for element in values_list if not pd.isnull(element)]
        values_list = [x for x in values_list if x != "-"]
        user_text_input = st.multiselect("Filter on Intervals", values_list)
        if user_text_input:
            def highlight_matching_strings(val):
                match_strings = user_text_input
                for match_string in match_strings:
                    if match_string == val:
                        return 'background-color: #ccebc4'
                return ''
            df = df.reset_index().fillna('')
            df = df[df[df_no_meta_col_names].apply(lambda x: x.isin(user_text_input)).any(axis=1)]
            df = df.style.map(highlight_matching_strings)
        else:
            df = df.reset_index().fillna('')
            df = df.style   
    return df
#for har
# st.cache_data(experimental_allow_widgets=True)
@st.fragment()
def filter_dataframe_har(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a UI on top of a dataframe to let viewers filter columns

    Args:
        df (pd.DataFrame): Original dataframe

    Returns:
        pd.DataFrame: Filtered dataframe
    """
 
    df = df.copy()
    random_id = random.randrange(1,1000)
    modification_container = st.container()
    with modification_container:    
        # random_id = random.randrange(1,1000)
        to_filter_columns = st.multiselect("Filter Harmonic Intervals by Various Fields", df.columns)
        st.write("Remember that initial choices will constrain subsequent filters!")
        if to_filter_columns:
        # here we are filtering by column
        # to_filter_columns = st.multiselect("Limit by Composer, Title, Date, or Voice", df.columns)
            for column in to_filter_columns:
                left, right = st.columns((1, 20))
                left.write("↳")
                # Treat columns with < 10 unique values as categorical
                # here 
                if is_categorical_dtype(df[column]) or df[column].nunique() < 50:
                    user_cat_input = right.multiselect(
                        f"Values for {column}",
                        df[column].unique(),
                        default=list(df[column].unique()),
                    )
                    df = df[df[column].isin(user_cat_input)]      
        # gets values for highlighted filters
        df_no_meta = df.loc[:, ~df.columns.isin(['Composer', "Title", 'Date'])]
        df_no_meta_col_names = df_no_meta.columns.tolist()
        df_voices_only = df[df_no_meta_col_names]
        melted = pd.melt(df_voices_only)
        values_list = melted['value'].unique()
        values_list = [i for i in values_list if i]
        values_list = [element for element in values_list if not pd.isnull(element)]
        user_text_input = st.multiselect("Filter on Intervals", values_list)
        if user_text_input:
            def highlight_matching_strings(val):
                match_strings = user_text_input
                for match_string in match_strings:
                    if match_string == val:
                        return 'background-color: #ccebc4'
                return ''
            df = df.reset_index().fillna('')
            df = df[df[df_no_meta_col_names].apply(lambda x: x.isin(user_text_input)).any(axis=1)]
            df = df.style.map(highlight_matching_strings)
        else:
            df = df.reset_index().fillna('')
            df = df.style
    return df

# for NG
# st.cache_data(experimental_allow_widgets=True)
@st.fragment()
def filter_dataframe_ng(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a UI on top of a dataframe to let viewers filter columns

    Args:
        df (pd.DataFrame): Original dataframe

    Returns:
        pd.DataFrame: Filtered dataframe
    """
 
    df = df.copy()
    random_id = random.randrange(1,1000)
    modification_container = st.container()
    with modification_container:       
        # random_id = random.randrange(1,1000)
        to_filter_columns = st.multiselect("Filter Ngrams by Various Fields", df.columns)
        st.write("Remember that initial choices will constrain subsequent filters!")
        if to_filter_columns:
        # here we are filtering by column
        # to_filter_columns = st.multiselect("Limit by Composer, Title, Date, or Voice", df.columns)
            for column in to_filter_columns:
                left, right = st.columns((1, 20))
                left.write("↳")
                # Treat columns with < 10 unique values as categorical
                # here 
                if is_categorical_dtype(df[column]) or df[column].nunique() < 50:
                    user_cat_input = right.multiselect(
                        f"Values for {column}",
                        df[column].unique(),
                        default=list(df[column].unique()),
                    )
                    df = df[df[column].isin(user_cat_input)] 
        # gets values for highlighted filters
        df_no_meta = df.loc[:, ~df.columns.isin(['Composer', "Title", 'Date'])]
        df_no_meta_col_names = df_no_meta.columns.tolist()
        df_voices_only = df[df_no_meta_col_names]
        melted = pd.melt(df_voices_only)
        values_list = melted['value'].unique()
        values_list = [i for i in values_list if i]
        values_list = [element for element in values_list if not pd.isnull(element)]
        user_text_input = st.multiselect("Filter on Ngrams", values_list)
        if user_text_input:
            def highlight_matching_strings(val):
                match_strings = user_text_input
                for match_string in match_strings:
                    if match_string == val:
                        return 'background-color: #ccebc4'
                return ''
            df = df.reset_index().fillna('')
            df = df[df[df_no_meta_col_names].apply(lambda x: x.isin(user_text_input)).any(axis=1)]
            df = df.style.map(highlight_matching_strings)
        else:
            df = df.reset_index().fillna('')
            df = df.style
    return df

#for hr
# st.cache_data(experimental_allow_widgets=True)
@st.fragment()
def filter_dataframe_hr(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a UI on top of a dataframe to let viewers filter columns

    Args:
        df (pd.DataFrame): Original dataframe

    Returns:
        pd.DataFrame: Filtered dataframe
    """
 
    df = df.copy()
    random_id = random.randrange(1,1000)
    modification_container = st.container()
    with modification_container:      
        to_filter_columns = st.multiselect("Filter the Homorhythm Results", df.columns)
        st.write("Remember that initial choices will constrain subsequent filters!")
        # here we are filtering by column
        # to_filter_columns = st.multiselect("Limit by Composer, Title, Date, or Voice", df.columns)
        for column in to_filter_columns:
            left, right = st.columns((1, 20))
            left.write("↳")
            # Treat columns with < 10 unique values as categorical
            # here 
            if is_categorical_dtype(df[column]) or df[column].nunique() < 50:
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

#for ptypes
# st.cache_data(experimental_allow_widgets=True)
@st.fragment()
def filter_dataframe_ptypes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a UI on top of a dataframe to let viewers filter columns

    Args:
        df (pd.DataFrame): Original dataframe

    Returns:
        pd.DataFrame: Filtered dataframe
    """
    if df is not None:
        df = df.copy()
        random_id = random.randrange(1,1000)
        modification_container = st.container()
        with modification_container:     
            to_filter_columns = st.multiselect("Filter the Presentation Type Results", df.columns)
            st.write("Remember that initial choices will constrain subsequent filters!")
            # here we are filtering by column
            # to_filter_columns = st.multiselect("Limit by Composer, Title, Date, or Voice", df.columns)
            for column in to_filter_columns:
                left, right = st.columns((1, 20))
                left.write("↳")
                # Treat columns with < 10 unique values as categorical
                # here 
                if is_categorical_dtype(df[column]) or df[column].nunique() < 50:
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
#for cads
# st.cache_data(experimental_allow_widgets=True)
@st.fragment()
def filter_dataframe_cads(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a UI on top of a dataframe to let viewers filter columns

    Args:
        df (pd.DataFrame): Original dataframe

    Returns:
        pd.DataFrame: Filtered dataframe
    """
 
    df = df.copy()
    random_id = random.randrange(1,1000)
    modification_container = st.container()
    with modification_container:     
        to_filter_columns = st.multiselect("Filter the Cadence Results", df.columns)
        st.write("Remember that initial choices will constrain subsequent filters!")
        # here we are filtering by column
        # to_filter_columns = st.multiselect("Limit by Composer, Title, Date, or Voice", df.columns)
        for column in to_filter_columns:
            left, right = st.columns((1, 20))
            left.write("↳")
            # Treat columns with < 10 unique values as categorical
            # here 
            if is_categorical_dtype(df[column]) or df[column].nunique() < 50:
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

# intervals functions and forms

# notes piece
# @st.cache_data
def piece_notes(piece, combine_unisons_choice, combine_rests_choice):
    nr = piece.notes(combineUnisons = combine_unisons_choice,
                            combineRests = combine_rests_choice)
    nr = piece.numberParts(nr)
    nr = piece.detailIndex(nr)

    nr = nr.assign(Composer=piece.metadata['composer'], Title=piece.metadata['title'], Date=piece.metadata['date'])
    cols_to_move = ['Composer', 'Title', 'Date']
    nr = nr[cols_to_move + [col for col in nr.columns if col not in cols_to_move]]
    nr = nr.reset_index()
    # Drop the Measure, Beat, and Date columns
    nr_clean = nr.drop(columns=['Measure', 'Beat', 'Date'])

    # Identify the id_vars and value_vars
    id_vars = ['Composer', 'Title']
    value_vars = [col for col in nr_clean.columns if col not in id_vars]

    # Melt the DataFrame
    nr_melted = pd.melt(
        nr_clean,
        id_vars=id_vars,
        value_vars=value_vars,
        var_name='Voice',
        value_name='Note'
    )
    
    nr_melted = nr_melted.dropna().copy()
    
    
    return nr_melted


# @st.cache_data
def corpus_notes(corpus, combine_unisons_choice, combine_rests_choice):
    func = ImportedPiece.notes  # <- NB there are no parentheses here
    list_of_dfs = corpus.batch(func = func, 
                                kwargs = {'combineUnisons': combine_unisons_choice, 'combineRests': combine_rests_choice}, 
                                metadata=False)
    func1 = ImportedPiece.numberParts
    list_of_dfs = corpus.batch(func = func1,
                               kwargs = {'df': list_of_dfs},
                               metadata=False)
    func2 = ImportedPiece.detailIndex
    list_of_dfs = corpus.batch(func = func2, 
                            kwargs = {'df': list_of_dfs}, 
                            metadata = True)
    
    nr = pd.concat(list_of_dfs)
   
    # reset index to get meas and beat out of the index
    nr = nr.reset_index()
    # Drop the Measure, Beat, and Date columns
    nr_clean = nr.drop(columns=['Measure', 'Beat', 'Date'])

    # Identify the id_vars and value_vars
    id_vars = ['Composer', 'Title']
    value_vars = [col for col in nr_clean.columns if col not in id_vars]

    # Melt the DataFrame
    nr_melted = pd.melt(
        nr_clean,
        id_vars=id_vars,
        value_vars=value_vars,
        var_name='Voice',
        value_name='Note'
    )

    nr_melted = nr_melted.dropna().copy()

    return nr_melted
    

# notes form
if st.sidebar.checkbox("Explore Notes"):
    # search_type = "ngram"
    st.subheader("Explore Notes")
    st.write("[Know the code! Read more about CRIM Intervals notes and rests methods](https://github.com/HCDigitalScholarship/intervals/blob/main/tutorial/02_Notes_Rests.md)", unsafe_allow_html=True)
    if len(crim_piece_selections) == 0 and len(uploaded_files_list)== 0:
        st.write("**No Files Selected! Please Select or Upload One or More Pieces.**")
    else:
        st.write("Did you **change the piece list**?  If so, please **Update and Submit form**")

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
            st.write("Did you **change the piece list**?  If so, please **Update and Submit form**")
            st.write("Filter Results by Contents of Each Column")
            if len(st.session_state.nr.fillna('')) > 100000:
                print("Results are too large to display; please filter again")
            else:
                filtered_nr = filter_dataframe_nr(st.session_state.nr.fillna(''))
                st.write("Did you **change the filter**?  If so, please **Update and Submit form**")   
                nr = filtered_nr.data.copy()
                # for one piece
                if corpus_length == 1:
                    composer = nr.iloc[0]["Composer"]
                    title = nr.iloc[0]["Title"]
                    nr_counts = nr.groupby(['Composer', 'Title', 'Voice', 'Note']).size().reset_index(name='Count')
                    nr_counts['Note'] = pd.CategoricalIndex(nr_counts['Note'], categories=pitch_order, ordered=True)
                    sorted_nr = nr_counts.sort_values('Note').reset_index(drop=True)

                    # make plot
                    titles = sorted_nr['Title'].unique()
                    nr_chart = px.bar(sorted_nr, 
                                    x='Note', 
                                    y='Count',
                                    color="Voice",
                                    title=f"Distribution of Notes in {composer}, {title}")
                    nr_chart.update_layout(xaxis_title="Note", 
                                            yaxis_title="Count",
                                            legend_title="Voice")
                    # and show results
                    pio.templates.default = 'plotly'

                    container = st.container()
                    col1, col2 = container.columns([10, 2])
                    
                    # Plot chart in first column
                    with col1:
                        st.plotly_chart(nr_chart, use_container_width=True)
                        
                    # Add download button in second column
                    with col2:
                        # @st.cache_data(ttl=3600)
                        def get_nr_html():
                            """Convert progress plot to HTML with preserved colors and interactivity"""
                            # Create a complete HTML file with embedded styles
                            html_content = f"""
                            <!DOCTYPE html>
                            <html>
                            <head>
                                <meta charset="utf-8">
                                <title>Note Chart - {composer} - {title}</title>
                                <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                                <style>
                                    body {{
                                        margin: 0;
                                        padding: 20px;
                                        font-family: Arial, sans-serif;
                                    }}
                                    .chart-container {{
                                        width: 100%;
                                        height: 600px;
                                    }}
                                </style>
                            </head>
                            <body>
                                <div class="chart-container" id="chart"></div>
                                <script>
                                    var figure = {nr_chart.to_json()};
                                    Plotly.newPlot('chart', figure.data, figure.layout, {{
                                        responsive: true,
                                        displayModeBar: true,
                                        displaylogo: false
                                    }});
                                </script>
                            </body>
                            </html>
                            """
                            return html_content
                    
                
                
                        st.markdown("")     
                        if st.button('📥 Prepare Notes Chart for Download'):
                            html_content = get_nr_html()
                            st.download_button(
                                label="Download the Chart",
                                data=html_content,
                                file_name=f"{composer}_{title}_notes_chart.html",
                                mime="text/html"
                            )
                    
                    if st.checkbox("Show Table of Notes"):
                        st.dataframe(sorted_nr, use_container_width = True)
                        
                        st.download_button(
                            label="Download Filtered Notes Data as CSV",
                            data=filtered_nr.data.to_csv(),
                            file_name = piece.metadata['title'] + '_notes_results.csv',
                            mime='text/csv',
                            key=1,
                            )
                    # Create container for chart and button
                    
                # for corpus:
                if corpus_length > 1:  
                    st.write("Did you **change the piece list**?  If so, please **Update and Submit form**")
                    nr_counts = nr.groupby(['Composer', 'Title', 'Voice', 'Note']).size().reset_index(name='Count')
                    # remove rests
                    nr_counts_counts_no_rest = nr_counts[nr_counts['Note'] != 'Rest']
                    # sorting
                    nr_counts['Note'] = pd.CategoricalIndex(nr_counts['Note'], categories=pitch_order, ordered=True)
                    sorted_nr = nr_counts.sort_values('Note').reset_index(drop=True)

                    # make plot
                    color_grouping = st.radio(
                        "Select Color Grouping",
                        ['Composer', 'Title', 'Voice'],
                        index=0,  # Pre-select the first option (default)
                        horizontal=True,  # Display options horizontally
                        captions=["Color by Composer", "Color by Title", "Color by Voice"]  # Add captions
                    )
                    titles = sorted_nr['Title'].unique()
                    nr_chart = px.bar(sorted_nr, 
                                    x='Note', 
                                    y='Count',
                                    color=color_grouping,
                                    title="Distribution of Notes in Corpus")
                    nr_chart.update_layout(xaxis_title="Note", 
                                            yaxis_title="Count",
                                            legend_title=color_grouping)
                    # and show results
                    # and show results
                    pio.templates.default = 'plotly'
                    container = st.container()
                    col1, col2 = container.columns([10, 2])
                    
                    # Plot chart in first column
                    with col1:
                        st.plotly_chart(nr_chart, use_container_width=True, )
                        # st.plotly_chart(fig, theme=None)

                        
                    # Add download button in second column
                    with col2:
                        # @st.cache_data(ttl=3600)
                        def get_nr_html():
                            """Convert notes plot to HTML with preserved colors and interactivity"""
                            # Create a complete HTML file with embedded styles
                            html_content = f"""
                            <!DOCTYPE html>
                            <html>
                            <head>
                                <meta charset="utf-8">
                                <title>Notes in Corpus</title>
                                <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                                <style>
                                    body {{
                                        margin: 0;
                                        padding: 20px;
                                        font-family: Arial, sans-serif;
                                    }}
                                    .chart-container {{
                                        width: 100%;
                                        height: 600px;
                                    }}
                                </style>
                            </head>
                            <body>
                                <div class="chart-container" id="chart"></div>
                                <script>
                                    var figure = {nr_chart.to_json()};
                                    Plotly.newPlot('chart', figure.data, figure.layout, {{
                                        responsive: true,
                                        displayModeBar: true,
                                        displaylogo: false
                                    }});
                                </script>
                            </body>
                            </html>
                            """
                            return html_content
                    
                
                        st.markdown("")     
                        if st.button('📥 Prepare Notes Chart for Download'):
                            html_content = get_nr_html()
                            st.download_button(
                                label="Download the Chart",
                                data=html_content,
                                file_name=f"corpus_notes_chart.html",
                                mime="text/html"
                            )
                    
                    if st.checkbox("Show Table of Notes"):
                        st.dataframe(sorted_nr, use_container_width = True)
                    
                        st.download_button(
                            label="Download Filtered Notes Data as CSV",
                            data=filtered_nr.data.to_csv(),
                            file_name = 'corpus_notes_results.csv',
                            mime='text/csv',
                            key=2,
                            )
                    # download option       
                    
                   
# durations
def piece_durs(piece):
    dur = piece.durations()
    dur = piece.numberParts(dur)
    dur = dur.assign(Composer=piece.metadata['composer'], Title=piece.metadata['title'])
    cols_to_move = ['Composer', 'Title']
    dur_clean = dur[cols_to_move + [col for col in dur.columns if col not in cols_to_move]]

    # # Identify the id_vars and value_vars
    id_vars = ['Composer', 'Title']
    value_vars = [col for col in dur_clean.columns if col not in id_vars]

    # # Melt the DataFrame
    dur_melted = pd.melt(
        dur_clean,
        id_vars=id_vars,
        value_vars=value_vars,
        var_name='Voice',
        value_name='Duration'
    )

    dur_melted = dur_melted.dropna().copy()
    
    return dur_melted   
    

# @st.cache_data
def corpus_durs(corpus):
    func = ImportedPiece.durations  # <- NB there are no parentheses here
    list_of_dfs = corpus.batch(func = func, 
                                metadata=False)
    func1 = ImportedPiece.numberParts
    list_of_dfs = corpus.batch(func = func1,
                               kwargs = {'df': list_of_dfs},
                               metadata=False)
    func2 = ImportedPiece.detailIndex
    list_of_dfs = corpus.batch(func = func2, 
                            kwargs = {'df': list_of_dfs}, 
                            metadata = True)
    dur = pd.concat(list_of_dfs)
    # reset index to get meas and beat out of the index
    dur = dur.reset_index()
    # Drop the Measure, Beat, and Date columns
    dur_clean = dur.drop(columns=['Measure', 'Beat', 'Date'])

    # Identify the id_vars and value_vars
    id_vars = ['Composer', 'Title']
    value_vars = [col for col in dur_clean.columns if col not in id_vars]

    # Melt the DataFrame
    dur_melted = pd.melt(
        dur_clean,
        id_vars=id_vars,
        value_vars=value_vars,
        var_name='Voice',
        value_name='Duration'
    )

    dur_melted = dur_melted.dropna().copy()

    return dur_melted
    

# durs form
# Durations form in sidebar
if st.sidebar.checkbox("Explore Durations"):
    # Move the main content outside of the sidebar
    st.subheader("Explore Durations")
    st.write("[Know the code! Read more about CRIM Intervals durations methods](https://github.com/HCDigitalScholarship/intervals/blob/main/tutorial/03_Durations.md)", unsafe_allow_html=True)
    
    if len(crim_piece_selections) == 0 and len(uploaded_files_list) == 0:
        st.write("**No Files Selected! Please Select or Upload One or More Pieces.**")
    else:
        st.write("Did you **change the piece list**?  If so, please **Update and Submit form**")
        
        # Form submission button
        submitted = st.button("Update and Run Search")
        
        if submitted:
            # Clear previous results if they exist
            if 'dur' in st.session_state:
                del st.session_state.dur
                
            # For one piece
            if corpus_length == 1:
                dur = piece_durs(piece)
            # For corpus
            elif corpus_length > 1:
                dur = corpus_durs(st.session_state.corpus)
                
            if "dur" not in st.session_state:
                st.session_state.dur = dur
        
        # Display results if they exist
        if 'dur' in st.session_state:
            # Filter the results
            st.write("Did you **change the piece list**?  If so, please **Update and Submit form**")
            st.write("Filter Results by Contents of Each Column")
            
            if len(st.session_state.dur.fillna('')) > 100000:
                st.write("Results are too large to display; please filter again")
            else:
                filtered_dur = filter_dataframe_dur(st.session_state.dur.fillna(''))
                st.write("Did you **change the filter**?  If so, please **Update and Submit form**")   
                dur = filtered_dur.data.copy()
                
                # For one piece
                if corpus_length == 1:
                    composer = dur.iloc[0]["Composer"]
                    title = dur.iloc[0]["Title"]
                    dur_counts = dur.groupby(['Composer', 'Title','Voice', 'Duration']).size().reset_index(name='Count')
                    sorted_dur = dur_counts.sort_values('Duration').reset_index(drop=True)
                    titles = sorted_dur["Title"].unique()
                    dur_chart = px.bar(sorted_dur, 
                                    x='Duration', 
                                    y='Count',
                                    color="Voice",
                                    title=f"Distribution of Durations in {composer}, {title}")
                    dur_chart.update_layout(xaxis_title="Duration", 
                                            yaxis_title="Count",
                                            legend_title="Voice")
                    # and show results
                    pio.templates.default = 'plotly'
                    container = st.container()
                    col1, col2 = container.columns([10, 2])
                    
                    # Plot chart in first column
                    with col1:
                        st.plotly_chart(dur_chart, use_container_width=True, )
                        # st.plotly_chart(fig, theme=None)

                        
                    # Add download button in second column
                    with col2:
                        # @st.cache_data(ttl=3600)
                        def get_nr_html():
                            """Convert dur plot to HTML with preserved colors and interactivity"""
                            # Create a complete HTML file with embedded styles
                            html_content = f"""
                            <!DOCTYPE html>
                            <html>
                            <head>
                                <meta charset="utf-8">
                                <title>Note Chart - {composer} - {title}</title>
                                <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                                <style>
                                    body {{
                                        margin: 0;
                                        padding: 20px;
                                        font-family: Arial, sans-serif;
                                    }}
                                    .chart-container {{
                                        width: 100%;
                                        height: 600px;
                                    }}
                                </style>
                            </head>
                            <body>
                                <div class="chart-container" id="chart"></div>
                                <script>
                                    var figure = {dur_chart.to_json()};
                                    Plotly.newPlot('chart', figure.data, figure.layout, {{
                                        responsive: true,
                                        displayModeBar: true,
                                        displaylogo: false
                                    }});
                                </script>
                            </body>
                            </html>
                            """
                            return html_content
                    
                
                        st.markdown("")     
                        if st.button('📥 Prepare Durations Chart for Download'):
                            html_content = get_nr_html()
                            st.download_button(
                                label="Download the Chart",
                                data=html_content,
                                file_name=f"{composer}_{title}_durations_chart.html",
                                mime="text/html"
                            )

                    if st.checkbox('Show Table of Durations'):
                        st.dataframe(sorted_dur, use_container_width = True)
                        
                        st.download_button(
                            label="Download Filtered Notes Data as CSV",
                            data=filtered_dur.data.to_csv(),
                            file_name = piece.metadata['title'] + '_notes_results.csv',
                            mime='text/csv',
                            key=3,
                            )

                # For corpus
                if corpus_length > 1:
                    st.write("Did you **change the piece list**?  If so, please **Update and Submit form**")
                    dur_counts = dur.groupby(['Composer', 'Title', 'Voice', 'Duration']).size().reset_index(name='Count')
                    sorted_dur = dur_counts.sort_values('Duration').reset_index(drop=True)

                    # plot
                    # make plot
                    color_grouping = st.radio(
                        "Select Color Grouping",
                        ['Composer', 'Title', 'Voice'],
                        index=0,  # Pre-select the first option (default)
                        horizontal=True,  # Display options horizontally
                        captions=["Color by Composer", "Color by Title", "Color by Voice"]  # Add captions
                    )
                    
                    
                    titles = dur_counts['Title'].unique()
                    dur_chart = px.bar(dur_counts, 
                                    x='Duration', 
                                    y='Count',
                                    color=color_grouping,
                                    title="Distribution of Durations in Corpus")
                    dur_chart.update_layout(xaxis_title="Note", 
                                            yaxis_title="Count",
                                            legend_title=color_grouping)

                    pio.templates.default = 'plotly'
                    container = st.container()
                    col1, col2 = container.columns([10, 2])
                    
                    # Plot chart in first column
                    with col1:
                        st.plotly_chart(dur_chart, use_container_width=True, )
                        
                    # Add download button in second column
                    with col2:
                        # @st.cache_data(ttl=3600)
                        def get_nr_html():
                            """Convert nr plot to HTML with preserved colors and interactivity"""
                            # Create a complete HTML file with embedded styles
                            html_content = f"""
                            <!DOCTYPE html>
                            <html>
                            <head>
                                <meta charset="utf-8">
                                <title>Durations in Corpus</title>
                                <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                                <style>
                                    body {{
                                        margin: 0;
                                        padding: 20px;
                                        font-family: Arial, sans-serif;
                                    }}
                                    .chart-container {{
                                        width: 100%;
                                        height: 600px;
                                    }}
                                </style>
                            </head>
                            <body>
                                <div class="chart-container" id="chart"></div>
                                <script>
                                    var figure = {dur_chart.to_json()};
                                    Plotly.newPlot('chart', figure.data, figure.layout, {{
                                        responsive: true,
                                        displayModeBar: true,
                                        displaylogo: false
                                    }});
                                </script>
                            </body>
                            </html>
                            """
                            return html_content
                    
                
                        st.markdown("")     
                        if st.button('📥 Prepare Durations Chart for Download'):
                            html_content = get_nr_html()
                            st.download_button(
                                label="Download the Chart",
                                data=html_content,
                                file_name=f"corpus_notes_chart.html",
                                mime="text/html"
                            )                    
                    if st.checkbox('Show Table of Durations'):
                        st.dataframe(filtered_dur, use_container_width=True)

                    
                        # Download option
                        st.download_button(
                            label="Download Filtered Corpus Durations Data as CSV",
                            data=filtered_dur.data.to_csv(),
                            file_name='corpus_durations_results.csv',
                            mime='text/csv',
                            key=4,
                        )

# weighted notes function

# this function gets all the notes, but also calculates the 'proportion' of notes in each piece, so that we have a normalized view of the distributions
def piece_note_weight(piece):
    metadata = piece.metadata['composer'] + ": " + piece.metadata['title']
    melted_notes = piece.notes().melt()
    melted_durations = piece.durations().melt()
    note_dur = pd.merge(melted_notes, melted_durations, left_index=True, right_index=True)
    note_dur = note_dur.dropna()
    note_dur['value_x_clean'] = note_dur['value_x'].apply(extract_letter)

    # Apply the function to the DataFrame
    note_dur['value_x_clean'] = note_dur['value_x'].apply(extract_letter)
    note_dur_sums = pd.DataFrame(note_dur.groupby('value_x_clean')['value_y'].sum()).reset_index(drop=False)
    # total (for scaled calculation)
    total_dur = note_dur_sums['value_y'].sum()
    note_dur_sums['scaled'] = note_dur_sums['value_y'].apply(lambda x: x/total_dur).round(2)
    note_dur_sums.rename(columns={"value_x_clean": "pitch_class", "value_y": "count"}, inplace=True)
    # pitch class order defined above
    note_dur_sums['pitch_class'] = pd.Categorical(note_dur_sums['pitch_class'], categories=pitch_class_order, ordered=True)
    # Sort the DataFrame
    sorted_df = note_dur_sums.sort_values('pitch_class')
    weighted_notes = sorted_df.dropna()
    weighted_notes['Composer'] = metadata[0]
    weighted_notes['Title'] = metadata[1]
    return weighted_notes


# Your corpus_note_dfs function
def corpus_note_weights(corpus):
    

    func = ImportedPiece.notes  # <- NB there are no parentheses here
    list_of_note_dfs = corpus.batch(func = func,  
                                    metadata=True)
    func2 = ImportedPiece.durations  # <- NB there are no parentheses here
    list_of_dur_dfs = corpus.batch(func = func2,  
                                    metadata=False)
    zipped_dfs = zip(list_of_note_dfs,  list_of_dur_dfs)

    weighted_note_dfs = []
    for a, b in zipped_dfs:
        # get metadata
        first_row = a.iloc[1]
        columns_of_interest = ['Composer', 'Title']
        metadata = first_row[columns_of_interest].tolist()

        # drop the same columns (we will add them back later)
        a = a.drop(columns=['Composer', 'Title', 'Date'])
        melted_notes = a.melt()
        melted_durs = b.melt()
        note_dur = pd.merge(melted_notes, melted_durs, left_index=True, right_index=True)
        note_dur = note_dur.dropna()
        note_dur['value_x_clean'] = note_dur['value_x'].apply(extract_letter)
        # Apply the function to the DataFrame
        note_dur['value_x_clean'] = note_dur['value_x'].apply(extract_letter)
        note_dur_sums = pd.DataFrame(note_dur.groupby('value_x_clean')['value_y'].sum()).reset_index(drop=False)
        # total (for scaled calculation)
        total_dur = note_dur_sums['value_y'].sum()
        note_dur_sums['scaled'] = note_dur_sums['value_y'].apply(lambda x: x/total_dur).round(2)
        note_dur_sums.rename(columns={"value_x_clean": "pitch_class", "value_y": "count"}, inplace=True)
        # pitch class order defined above
        note_dur_sums['pitch_class'] = pd.Categorical(note_dur_sums['pitch_class'], categories=pitch_class_order, ordered=True)
        # Sort the DataFrame
        sorted_df = note_dur_sums.sort_values('pitch_class')
        weighted_notes = sorted_df.dropna()
        weighted_notes['Composer'] = metadata[0] 
        weighted_notes['Title'] = metadata[1]
        weighted_note_dfs.append(weighted_notes)
    corpus_note_weights = pd.concat(weighted_note_dfs)
    return corpus_note_weights


# Your existing code for the sidebar checkbox
if st.sidebar.checkbox("Explore Notes Weighted By Durations"):
    st.subheader("Explore Weighted Notes")

    if len(crim_piece_selections) == 0 and len(uploaded_files_list) == 0:
        st.write("**No Files Selected! Please Select or Upload One or More Pieces.**")
    else:
        st.write("Did you **change the piece list**?  If so, please **Update and Submit form**")
        
        # Form submission button
        submitted = st.button("Update and Run Search")
        if submitted:
            # Clear previous results if they exist
            if 'corpus_notes_weights' in st.session_state:
                del st.session_state.corpus_notes_weights
            
            # For one piece
            if corpus_length == 1:
                corpus_notes_weights = piece_note_weight(piece)
                # Store in session state
                st.session_state.corpus_notes_weights = corpus_notes_weights
                # st.dataframe(corpus_notes_weights)
            # For corpus
            elif corpus_length > 1:
                try:
                    corpus_notes_weights = corpus_note_weights(st.session_state.corpus)
                    
                    # Debug: Check the data before storing
                    # st.write(f"Data before storing: {len(corpus_notes_weights)} rows")
                    # st.write("Data columns:", corpus_notes_weights.columns.tolist())
                    
                    # Store in session state
                    st.session_state.corpus_notes_weights = corpus_notes_weights
                except Exception as e:
                    st.error(f"Error processing corpus: {str(e)}")

        # Display results if they exist
        if 'corpus_notes_weights' in st.session_state:
            # Get the data from session state
            counted_notes_sorted = st.session_state.corpus_notes_weights
            
            # Debug: Check the retrieved data
            # st.write(f"Data retrieved from session state: {len(counted_notes_sorted)} rows")
            # st.write("Retrieved data columns:", counted_notes_sorted.columns.tolist())
            
            # Check if we have the required columns for plotting
            required_columns = ['pitch_class', 'scaled']
            missing_columns = [col for col in required_columns if col not in counted_notes_sorted.columns]
            
            if missing_columns:
                st.error(f"Missing required columns for plotting: {missing_columns}")
                st.write("Available columns:", counted_notes_sorted.columns.tolist())
            
            else:
                # Create a radar plot using Plotly Express
                try:
                    # Check if we have multiple pieces to plot
                    if 'Title' in counted_notes_sorted.columns and counted_notes_sorted['Title'].nunique() > 1:
                        container = st.container()
                        col1, col2 = container.columns([10, 2])
                        with col1:
                            # Multiple pieces plot
                            # make plot
                            color_grouping = st.radio(
                                "Select Color Grouping",
                                ['Composer', 'Title'],
                                index=0,  # Pre-select the first option (default)
                                horizontal=True,  # Display options horizontally
                                captions=["Color by Composer", "Color by Title", "Color by Voice"]  # Add captions
                            )

        
                            titles = counted_notes_sorted['Title'].unique()
                            fig = px.line_polar(
                                counted_notes_sorted,
                                r='scaled',
                                theta='pitch_class',
                                color=color_grouping,
                                line_close=True,
                                range_r=[0, counted_notes_sorted['scaled'].max() * 1.1],
                                markers=True,
                                category_orders=dict(color_grouping=list(counted_notes_sorted[color_grouping].unique())),
                                color_discrete_sequence=contrasting_colors[:len(counted_notes_sorted[color_grouping].unique())]
                            )
                            fig.update_traces(fill='toself', 
                                            mode='markers+lines',
                                            opacity=.7)
                            fig.update_layout(
                                showlegend=True,
                                legend=dict(
                                    title=color_grouping,
                                    orientation="h",
                                    yanchor="bottom",
                                    y=-0.5,
                                    xanchor="right",
                                    x=1
                                ),
                                title = 'Weighted Note Distribution in Corpus')
                            
                            st.plotly_chart(fig, use_container_width=True)
                        with col2:
                            @st.cache_data(ttl=3600)
                            def get_radar_html():
                                """Convert radar plot to HTML with preserved colors and interactivity"""
                                # Create a complete HTML file with embedded styles
                                html_content = f"""
                                <!DOCTYPE html>
                                <html>
                                <head>
                                    <meta charset="utf-8">
                                    <title>Corpus Cadence Radar Plot</title>
                                    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                                    <style>
                                        body {{
                                            margin: 0;
                                            padding: 20px;
                                            font-family: Arial, sans-serif;
                                        }}
                                        .chart-container {{
                                            width: 100%;
                                            height: 600px;
                                        }}
                                    </style>
                                </head>
                                <body>
                                    <div class="chart-container" id="chart"></div>
                                    <script>
                                        var figure = {fig.to_json()};
                                        Plotly.newPlot('chart', figure.data, figure.layout, {{
                                            responsive: true,
                                            displayModeBar: true,
                                            displaylogo: false
                                        }});
                                    </script>
                                </body>
                                </html>
                                """
                                return html_content
                                
                            if st.button('📥 Prepare Weighted Note Plot for Download'):
                                radar_html = get_radar_html()
                                st.download_button(
                                    label="Download Radar Plot",
                                    data=radar_html,
                                    file_name=f"corpus_weighted_note_plot.html",
                                    mime="text/html"
                                )
                            
                    else:
                        # Single piece plot
                        container = st.container()
                        col1, col2 = container.columns([10, 2])
                        if piece:
                            composer = piece.metadata['composer']
                            title = piece.metadata['title']
            
                            # Plot chart in first column
                            with col1:
                                fig = px.line_polar(
                                    counted_notes_sorted,
                                    r='scaled',
                                    theta='pitch_class',
                                    line_close=True,
                                    range_r=[0, counted_notes_sorted['scaled'].max() * 1.1],
                                    markers=True,
                                    category_orders=category_order
                                )
                                
                                fig.update_traces(
                                    fill='toself',
                                    fillcolor='rgba(31, 119, 180, 0.3)',
                                    line=dict(width=2)
                                )
                                
                                # Get piece name if available
                                # if 'piece' in counted_notes_sorted.columns:
                                    # piece_name = counted_notes_sorted['piece'].iloc[0]
                                # title = f"Weighted Note Distribution in {composer}, {title}"
                                
                            
                                fig.update_layout(
                                    title=title,
                                    polar=dict(
                                        radialaxis=dict(
                                            visible=True,
                                            range=[0, counted_notes_sorted['scaled'].max() * 1.1]
                                        ),
                                        
                                    ),
                                    showlegend='piece' in counted_notes_sorted.columns,
                                )
                            
                                st.plotly_chart(fig, use_container_width=True)
                            # Add download button in second column
                            with col2:
                                @st.cache_data(ttl=3600)
                                def get_radar_html():
                                    """Convert radar plot to HTML with preserved colors and interactivity"""
                                    # Create a complete HTML file with embedded styles
                                    html_content = f"""
                                    <!DOCTYPE html>
                                    <html>
                                    <head>
                                        <meta charset="utf-8">
                                        <title>Weighted Note Distribution</title>
                                        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                                        <style>
                                            body {{
                                                margin: 0;
                                                padding: 20px;
                                                font-family: Arial, sans-serif;
                                            }}
                                            .chart-container {{
                                                width: 100%;
                                                height: 600px;
                                            }}
                                        </style>
                                    </head>
                                    <body>
                                        <div class="chart-container" id="chart"></div>
                                        <script>
                                            var figure = {fig.to_json()};
                                            Plotly.newPlot('chart', figure.data, figure.layout, {{
                                                responsive: true,
                                                displayModeBar: true,
                                                displaylogo: false
                                            }});
                                        </script>
                                    </body>
                                    </html>
                                    """
                                    return html_content
                                    
                                if st.button('📥 Prepare Weighted Note Plot for Download'):
                                    radar_html = get_radar_html()
                                    st.download_button(
                                        label="Download Weighted Note Plot Plot",
                                        data=radar_html,
                                        file_name=f"{composer}_{title}_weighted_note_plot.html",
                                        mime="text/html"
                                    )
                            # Add download button in second column
                
                
                except Exception as e:
                    st.error(f"Error creating the radar plot: {str(e)}")
                    st.write("Data sample for debugging:")
                    st.write(counted_notes_sorted.head())
                    
                    # More detailed error information
                    import traceback
                    st.code(traceback.format_exc())

# melodic functions
# @st.cache_data
def piece_mel(piece, combine_unisons_choice, combine_rests_choice, kind_choice, directed, compound):
    nr = piece.notes(combineUnisons = combine_unisons_choice,
                              combineRests = combine_rests_choice)
    
    nr = piece.numberParts(nr)
    mel = piece.melodic(df = nr, 
                        kind = kind_choice,
                        directed = directed,
                        compound = compound)
    mel = piece.detailIndex(mel)
    # mel = mel.reset_index()
    mel = mel.assign(Composer=piece.metadata['composer'], Title=piece.metadata['title'], Date=piece.metadata['date'])
    cols_to_move = ['Composer', 'Title', 'Date']
    mel = mel[cols_to_move + [col for col in mel.columns if col not in cols_to_move]]
    mel = mel.reset_index()
    # Drop the Measure, Beat, and Date columns
    mel_clean = mel.drop(columns=['Measure', 'Beat', 'Date'])

    # Identify the id_vars and value_vars
    id_vars = ['Composer', 'Title']
    value_vars = [col for col in mel_clean.columns if col not in id_vars]

    # Melt the DataFrame
    mel_melted = pd.melt(
        mel_clean,
        id_vars=id_vars,
        value_vars=value_vars,
        var_name='Voice',
        value_name='Interval'
    )
    
    mel_melted = mel_melted.dropna().copy()
    
    
    return mel_melted

# @st.cache_data
def corpus_mel(corpus, combine_unisons_choice, combine_rests_choice, kind_choice, directed, compound):
    func = ImportedPiece.notes  # <- NB there are no parentheses here
    list_of_dfs = corpus.batch(func = func, 
                                kwargs = {'combineUnisons': combine_unisons_choice, 'combineRests': combine_rests_choice}, 
                                metadata=False)
    
    func1 = ImportedPiece.numberParts
    list_of_dfs = corpus.batch(func = func1,
                               kwargs = {'df': list_of_dfs},
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
    # no longer needed for melt approach
    # reset index to get meas and beat out of the index
    mel = mel.reset_index()
    # Drop the Measure, Beat, and Date columns
    mel_clean = mel.drop(columns=['Measure', 'Beat', 'Date'])

    # Identify the id_vars and value_vars
    id_vars = ['Composer', 'Title']
    value_vars = [col for col in mel_clean.columns if col not in id_vars]

    # Melt the DataFrame
    mel_melted = pd.melt(
        mel_clean,
        id_vars=id_vars,
        value_vars=value_vars,
        var_name='Voice',
        value_name='Interval'
    )

    mel_melted = mel_melted.dropna().copy()

    return mel_melted

# melodic form
if st.sidebar.checkbox("Explore Melodic Intervals"):
    search_type = "mel"
    st.subheader("Explore Melodic Intervals")
    st.write("[Know the code! Read more about CRIM Intervals melodic interval methods](https://github.com/HCDigitalScholarship/intervals/blob/main/tutorial/06_Melodic_Intervals.md)", unsafe_allow_html=True)
    if len(crim_piece_selections) == 0 and len(uploaded_files_list)== 0:
        st.write("**No Files Selected! Please Select or Upload One or More Pieces.**")
    else:
        st.write("Did you **change the piece list**?  If so, please **Update and Submit form**")
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
            st.write("Did you **change the piece list**?  If so, please **Update and Submit form**")
            st.write("Filter Results by Contents of Each Column")
            # st.dataframe(st.session_state.mel)
            if len(st.session_state.mel.fillna('')) > 100000:
                print("Results are too large to display; please filter again")
            else:
                filtered_mel = filter_dataframe_mel(st.session_state.mel.fillna(''))   
                st.write("Did you **change the filter**?  If so, please **Update and Submit form**")    
                # for one piece
                if corpus_length  == 1: 
                    # 
                    mel = filtered_mel.data.copy()
                    composer = mel.iloc[0]['Composer']
                    title = mel.iloc[0]['Title']
                    
                    if interval_kinds[select_kind] == 'q':
                        mel_interval_counts = mel.groupby(['Composer', 'Title', 'Voice', 'Interval']).size().reset_index(name='Count')
                        # remove rests
                        mel_int_counts_no_rest = mel_interval_counts[mel_interval_counts['Interval'] != 'Rest']
                        # mel_int_counts_no_rest['Interval'] = mel_int_counts_no_rest['Interval'].astype('str')
                        # apply the categorical list and sort.  
                        mel_int_counts_no_rest['Interval'] = pd.CategoricalIndex(mel_int_counts_no_rest['Interval'], categories=interval_order_quality, ordered=True)
                        sorted_mel = mel_int_counts_no_rest.sort_values('Interval').reset_index(drop=True)
                        # st.dataframe(sorted_mel)
                    else:
                        mel_interval_counts = mel.groupby(['Composer', 'Title', 'Voice', 'Interval']).size().reset_index(name='Count')
                        # remove rests
                        mel_int_counts_no_rest = mel_interval_counts[mel_interval_counts['Interval'] != 'Rest']
                        mel_int_counts_no_rest['Interval'] = mel_int_counts_no_rest['Interval'].astype('int64')
                        # sorting
                        sorted_mel = mel_int_counts_no_rest.sort_values(by='Interval', ascending=True)
                        
                    # make plot
                    titles = sorted_mel['Title'].unique()
                    mel_chart = px.bar(sorted_mel, 
                                    x='Interval', 
                                    y='Count',
                                    color="Voice",
                                    title=f"Distribution of Intervals in {composer}, {title}")
                    mel_chart.update_layout(xaxis_title="Interval", 
                                            yaxis_title="Count",
                                            legend_title="Voice")
                    # and show results
                    pio.templates.default = 'plotly'

                    container = st.container()
                    col1, col2 = container.columns([10, 2])
                    
                    # Plot chart in first column
                    with col1:
                        st.plotly_chart(mel_chart, use_container_width=True)
                        
                    # Add download button in second column
                    with col2:
                        # @st.cache_data(ttl=3600)
                        def get_mel_html():
                            """Convert dur plot to HTML with preserved colors and interactivity"""
                            # Create a complete HTML file with embedded styles
                            html_content = f"""
                            <!DOCTYPE html>
                            <html>
                            <head>
                                <meta charset="utf-8">
                                <title>Melodic Interval Chart - {composer} - {title}</title>
                                <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                                <style>
                                    body {{
                                        margin: 0;
                                        padding: 20px;
                                        font-family: Arial, sans-serif;
                                    }}
                                    .chart-container {{
                                        width: 100%;
                                        height: 600px;
                                    }}
                                </style>
                            </head>
                            <body>
                                <div class="chart-container" id="chart"></div>
                                <script>
                                    var figure = {mel_chart.to_json()};
                                    Plotly.newPlot('chart', figure.data, figure.layout, {{
                                        responsive: true,
                                        displayModeBar: true,
                                        displaylogo: false
                                    }});
                                </script>
                            </body>
                            </html>
                            """
                            return html_content
                    
                
                
                        st.markdown("")     
                        if st.button('📥 Prepare Melodic Chart for Download'):
                            html_content = get_mel_html()
                            st.download_button(
                                label="Download the Chart",
                                data=html_content,
                                file_name=f"{composer}_{title}_mel_chart.html",
                                mime="text/html"
                            )


                    if st.checkbox("Show Table of Melodic Intervals"):
                        st.dataframe(sorted_mel, use_container_width = True)
                        composer = mel.iloc[0]['Composer']
                        title = mel.iloc[0]['Title']

                        st.download_button(
                            label="Download Filtered Melodic Data as CSV",
                            data=filtered_mel.data.to_csv(),
                            file_name = f'{composer}_{title}_melodic_intervals.csv',
                            mime='text/csv',
                            key=5,
                            )
                # # for corpus
                elif corpus_length > 1:
                    mel = filtered_mel.data.copy()  
                    if interval_kinds[select_kind] == 'q':
                        # remove rests
                        # mel = filtered_mel
                        mel_interval_counts = mel.groupby(['Composer', 'Title', 'Voice', 'Interval']).size().reset_index(name='Count')
                        mel_int_counts_no_rest = mel_interval_counts[mel_interval_counts['Interval'] != 'Rest']
                        # apply the categorical list and sort.
                        mel_int_counts_no_rest['Interval'] = pd.CategoricalIndex(mel_int_counts_no_rest['Interval'], categories=interval_order_quality, ordered=True)
                        sorted_mel = mel_int_counts_no_rest.sort_values('Interval').reset_index(drop=True)
                        # st.dataframe(sorted_mel)
                    else:
                        mel_interval_counts = mel.groupby(['Composer', 'Title', 'Voice', 'Interval']).size().reset_index(name='Count')
                        # remove rests
                        mel_interval_counts_no_rest = mel_interval_counts[mel_interval_counts['Interval'] != 'Rest']
                        # sorting
                        sorted_mel = mel_interval_counts_no_rest.sort_values(by='Interval', ascending=True)

                    # make plot
                    color_grouping = st.radio(
                        "Select Color Grouping",
                        ['Composer', 'Title', 'Voice'],
                        index=0,  # Pre-select the first option (default)
                        horizontal=True,  # Display options horizontally
                        captions=["Color by Composer", "Color by Title", "Color by Voice"]  # Add captions
                    )
                    titles = sorted_mel['Title'].unique()
                    mel_chart = px.bar(sorted_mel, 
                                    x='Interval', 
                                    y='Count',
                                    color=color_grouping,
                                    title="Distribution of Intervals in Corpus")
                    mel_chart.update_layout(xaxis_title="Interval", 
                                            yaxis_title="Count",
                                            legend_title=color_grouping)
                    # and show results

                        # and show results
                    pio.templates.default = 'plotly'

                    container = st.container()
                    col1, col2 = container.columns([10, 2])
                    
                    # Plot chart in first column
                    with col1:
                        st.plotly_chart(mel_chart, use_container_width=True)
                        
                    # Add download button in second column
                    with col2:
                        # @st.cache_data(ttl=3600)
                        def get_mel_html():
                            """Convert mel plot to HTML with preserved colors and interactivity"""
                            # Create a complete HTML file with embedded styles
                            html_content = f"""
                            <!DOCTYPE html>
                            <html>
                            <head>
                                <meta charset="utf-8">
                                <title>Corpus Melodic Interval Chart </title>
                                <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                                <style>
                                    body {{
                                        margin: 0;
                                        padding: 20px;
                                        font-family: Arial, sans-serif;
                                    }}
                                    .chart-container {{
                                        width: 100%;
                                        height: 600px;
                                    }}
                                </style>
                            </head>
                            <body>
                                <div class="chart-container" id="chart"></div>
                                <script>
                                    var figure = {mel_chart.to_json()};
                                    Plotly.newPlot('chart', figure.data, figure.layout, {{
                                        responsive: true,
                                        displayModeBar: true,
                                        displaylogo: false
                                    }});
                                </script>
                            </body>
                            </html>
                            """
                            return html_content
                        
                        st.markdown("")     
                        if st.button('📥 Prepare Melodic Chart for Download'):
                            html_content = get_mel_html()
                            st.download_button(
                                label="Download the Chart",
                                data=html_content,
                                file_name=f"corpus_mel_chart.html",
                                mime="text/html"
                            )

                    if st.checkbox("Show Table of Melodic Intervals"):
                        st.dataframe(sorted_mel, use_container_width = True)
                        
                        st.download_button(
                            label="Download Filtered Melodic Data as CSV",
                            data=filtered_mel.data.to_csv(),
                            file_name = f'corpus_melodic_intervals.csv',
                            mime='text/csv',
                            key=6,
                            )
        
# harmonic functions
# @st.cache_data
def piece_har(piece, kind_choice, directed, compound, against_low):
    nr = piece.notes()
    nr = piece.numberParts(nr)
    har = piece.harmonic(df=nr,
                         kind = kind_choice, 
                         directed = directed,
                         compound = compound,
                         againstLow = against_low).fillna('')
    har = piece.detailIndex(har)
    # har = har.reset_index()
    har = har.assign(Composer=piece.metadata['composer'], Title=piece.metadata['title'], Date=piece.metadata['date'])
    cols_to_move = ['Composer', 'Title', 'Date']
    har = har[cols_to_move + [col for col in har.columns if col not in cols_to_move]]
    har = har.reset_index()
    # Drop the Measure, Beat, and Date columns
    har_clean = har.drop(columns=['Measure', 'Beat', 'Date'])

    # Identify the id_vars and value_vars
    id_vars = ['Composer', 'Title']
    value_vars = [col for col in har_clean.columns if col not in id_vars]

    # Melt the DataFrame
    har_melted = pd.melt(
        har_clean,
        id_vars=id_vars,
        value_vars=value_vars,
        var_name='Voices',
        value_name='Interval'
    )
    
    har_melted = har_melted.dropna().copy()
    
    
    return har_melted

# @st.cache_data
def corpus_har(corpus, kind_choice, directed, compound, against_low):
    
    func = ImportedPiece.notes  # <- NB there are no parentheses here
    list_of_dfs = corpus.batch(func = func, 
                                # kwargs = {'combineUnisons': combine_unisons_choice, 'combineRests': combine_rests_choice}, 
                                metadata=False)
    
    func1 = ImportedPiece.numberParts
    list_of_dfs = corpus.batch(func = func1,
                               kwargs = {'df': list_of_dfs},
                               metadata=False)
    
    
    func2 = ImportedPiece.harmonic
    list_of_dfs = corpus.batch(func = func2,
                               kwargs = {'df': list_of_dfs,
                                         'kind' : kind_choice, 
                                         'directed' : directed, 
                                         'compound' : compound, 
                                         'againstLow' : against_low},
                               metadata = False)
    func3 = ImportedPiece.detailIndex
    list_of_dfs = corpus.batch(func = func3, 
                            kwargs = {'df': list_of_dfs}, 
                            metadata = True)
    har = pd.concat(list_of_dfs)
    har = har.reset_index()
    # Drop the Measure, Beat, and Date columns
    har_clean = har.drop(columns=['Measure', 'Beat', 'Date'])

    # Identify the id_vars and value_vars
    id_vars = ['Composer', 'Title']
    value_vars = [col for col in har_clean.columns if col not in id_vars]

    # Melt the DataFrame
    har_melted = pd.melt(
        har_clean,
        id_vars=id_vars,
        value_vars=value_vars,
        var_name='Voices',
        value_name='Interval'
    )

    har_melted = har_melted.dropna().copy()

    return har_melted


# harmonic form
if st.sidebar.checkbox("Explore Harmonic Intervals"):
    search_type = "har"
    st.subheader("Explore Harmonic Intervals")
    st.write("[Know the code! Read more about CRIM Intervals harmonic interval methods](https://github.com/HCDigitalScholarship/intervals/blob/main/tutorial/07_Harmonic_Intervals.md)", unsafe_allow_html=True)
    if len(crim_piece_selections) == 0 and len(uploaded_files_list)== 0:
        st.write("**No Files Selected! Please Select or Upload One or More Pieces.**")
    else:
        st.write("Did you **change the piece list**?  If so, please **Update and Submit form**")    
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
            st.write("Did you **change the piece list**?  If so, please **Update and Submit form**")
            st.write("Filter Results by Contents of Each Column")
            if len(st.session_state.har.fillna('')) > 100000:
                print("Results are too large to display; please filter again")
            else:
                filtered_har = filter_dataframe_har(st.session_state.har.fillna(''))   
                st.write("Did you **change the filter**?  If so, please **Update and Submit form**")    
                # for one piece
                if corpus_length  == 1: 
                    # 
                    har = filtered_har.data.copy()
                    
                    if interval_kinds[select_kind] == 'q':
                        har_interval_counts = har.groupby(['Composer', 'Title', 'Voices', 'Interval']).size().reset_index(name='Count')
                        # remove rests
                        har_int_counts_no_rest = har_interval_counts[har_interval_counts['Interval'] != 'Rest']
                        # har_int_counts_no_rest['Interval'] = har_int_counts_no_rest['Interval'].astype('int64')
                        # apply the categorical list and sort.  
                        har_int_counts_no_rest['Interval'] = pd.CategoricalIndex(har_int_counts_no_rest['Interval'], categories=interval_order_quality, ordered=True)
                        sorted_har = har_int_counts_no_rest.sort_values('Interval').reset_index(drop=True)
                    else:
                        har_interval_counts = har.groupby(['Composer', 'Title', 'Voices', 'Interval']).size().reset_index(name='Count')
                        # remove rests
                        har_int_counts_no_rest = har_interval_counts[har_interval_counts['Interval'] != 'Rest']
                        # har_int_counts_no_rest['Interval'] = har_int_counts_no_rest['Interval'].astype('int64')
                        # sorting
                        sorted_har = har_int_counts_no_rest.sort_values(by='Interval', ascending=True)
                        
                    # make plot
                    titles = sorted_har['Title'].unique()
                    har_chart = px.bar(sorted_har, 
                                    x='Interval', 
                                    y='Count',
                                    color="Voices",
                                    title="Distribution of Intervals in Corpus")
                    har_chart.update_layout(xaxis_title="Interval", 
                                            yaxis_title="Count",
                                            legend_title="Voices")
                    # and show results
                    # and show results
                    pio.templates.default = 'plotly'

                    container = st.container()
                    col1, col2 = container.columns([10, 2])
                    composer = har.iloc[0]['Composer']
                    title = har.iloc[0]['Title']
                    
                    # Plot chart in first column
                    with col1:
                        st.plotly_chart(har_chart, use_container_width=True)
                        
                    # Add download button in second column
                    with col2:
                        # @st.cache_data(ttl=3600)
                        def get_har_html():
                            """Convert har plot to HTML with preserved colors and interactivity"""
                            # Create a complete HTML file with embedded styles
                            html_content = f"""
                            <!DOCTYPE html>
                            <html>
                            <head>
                                <meta charset="utf-8">
                                <title>Harmonic Interval Chart - {composer} - {title}</title>
                                <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                                <style>
                                    body {{
                                        margin: 0;
                                        padding: 20px;
                                        font-family: Arial, sans-serif;
                                    }}
                                    .chart-container {{
                                        width: 100%;
                                        height: 600px;
                                    }}
                                </style>
                            </head>
                            <body>
                                <div class="chart-container" id="chart"></div>
                                <script>
                                    var figure = {har_chart.to_json()};
                                    Plotly.newPlot('chart', figure.data, figure.layout, {{
                                        responsive: true,
                                        displayModeBar: true,
                                        displaylogo: false
                                    }});
                                </script>
                            </body>
                            </html>
                            """
                            return html_content
                    
                
                
                        st.markdown("")     
                        if st.button('📥 Prepare Harmonic Chart for Download'):
                            html_content = get_har_html()
                            st.download_button(
                                label="Download the Chart",
                                data=html_content,
                                file_name=f"{composer}_{title}_har_chart.html",
                                mime="text/html"
                            )


                    if st.checkbox("Show Table of Harmonic Intervals"):
                        st.dataframe(sorted_mel, use_container_width = True)
                        composer = har.iloc[0]['Composer']
                        title = har.iloc[0]['Title']

                        st.download_button(
                            label="Download Filtered Melodic Data as CSV",
                            data=filtered_har.data.to_csv(),
                            file_name = f'{composer}_{title}_harmonic_intervals.csv',
                            mime='text/csv',
                            key=7,
                            )
                # # for corpus
                elif corpus_length > 1:
                    har = filtered_har.data.copy()  
                    if interval_kinds[select_kind] == 'q':
                        # remove rests
                        har_interval_counts = har.groupby(['Composer', 'Title', 'Voices', 'Interval']).size().reset_index(name='Count')
                        har_int_counts_no_rest = har_interval_counts[har_interval_counts['Interval'] != 'Rest']
                        # apply the categorical list and sort.
                        har_int_counts_no_rest['Interval'] = pd.CategoricalIndex(har_int_counts_no_rest['Interval'], categories=interval_order_quality, ordered=True)
                        sorted_mel = har_int_counts_no_rest.sort_values('Interval').reset_index(drop=True)
                    else:
                        har_interval_counts = har.groupby(['Composer', 'Title', 'Voices', 'Interval']).size().reset_index(name='Count')
                        # remove rests
                        har_interval_counts_no_rest = har_interval_counts[har_interval_counts['Interval'] != 'Rest']
                        # sorting
                        sorted_har = har_interval_counts_no_rest.sort_values(by='Interval', ascending=True)

                    # make plot
                    color_grouping = st.radio(
                        "Select Color Grouping",
                        ['Composer', 'Title', 'Voices'],
                        index=0,  # Pre-select the first option (default)
                        horizontal=True,  # Display options horizontally
                        captions=["Color by Composer", "Color by Title", "Color by Voices"]  # Add captions
                    )
                    titles = sorted_har['Title'].unique()
                    har_chart = px.bar(sorted_har, 
                                    x='Interval', 
                                    y='Count',
                                    color=color_grouping,
                                    title="Distribution of Intervals in Corpus")
                    har_chart.update_layout(xaxis_title="Interval", 
                                            yaxis_title="Count",
                                            legend_title=color_grouping)
            
                # show results
                # and show results
                    pio.templates.default = 'plotly'

                    container = st.container()
                    col1, col2 = container.columns([10, 2])
                    
                    # Plot chart in first column
                    with col1:
                        st.plotly_chart(har_chart, use_container_width=True)
                        
                    # Add download button in second column
                    with col2:
                        # @st.cache_data(ttl=3600)
                        def get_har_html():
                            """Convert har plot to HTML with preserved colors and interactivity"""
                            # Create a complete HTML file with embedded styles
                            html_content = f"""
                            <!DOCTYPE html>
                            <html>
                            <head>
                                <meta charset="utf-8">
                                <title>Corpus Harmonic Interval Chart </title>
                                <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                                <style>
                                    body {{
                                        margin: 0;
                                        padding: 20px;
                                        font-family: Arial, sans-serif;
                                    }}
                                    .chart-container {{
                                        width: 100%;
                                        height: 600px;
                                    }}
                                </style>
                            </head>
                            <body>
                                <div class="chart-container" id="chart"></div>
                                <script>
                                    var figure = {har_chart.to_json()};
                                    Plotly.newPlot('chart', figure.data, figure.layout, {{
                                        responsive: true,
                                        displayModeBar: true,
                                        displaylogo: false
                                    }});
                                </script>
                            </body>
                            </html>
                            """
                            return html_content
                        
                        st.markdown("")     
                        if st.button('📥 Prepare Harmonic Chart for Download'):
                            html_content = get_har_html()
                            st.download_button(
                                label="Download the Chart",
                                data=html_content,
                                file_name=f"corpus_har_chart.html",
                                mime="text/html"
                            )

                    if st.checkbox("Show Table of Harmonic Intervals"):
                        st.dataframe(sorted_har, use_container_width = True)
                        
                        st.download_button(
                            label="Download Filtered Harmonic Data as CSV",
                            data=filtered_mel.data.to_csv(),
                            file_name = f'corpus_harmonic_intervals.csv',
                            mime='text/csv',
                            key=8,
                            ) 

# function for ngram heatmap
# @st.cache_data
def ngram_heatmap(piece, combine_unisons_choice, kind_choice, directed, compound, length_choice, include_count):
    # find entries for model
    nr = piece.notes(combineUnisons = combine_unisons_choice)

    nr = piece.numberParts(nr)

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
# ngram form
if st.sidebar.checkbox("Explore Ngrams and Heatmaps"):
    search_type = "intervals_ngrams"
    st.subheader("Explore nGrams and Heatmaps")
    st.write("[Know the code! Read more about CRIM Intervals ngram methods](https://github.com/HCDigitalScholarship/intervals/blob/main/tutorial/09_Ngrams_Heat_Maps.md)", unsafe_allow_html=True)
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
                key_list = ['ngrams3', 'heatmap']
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
                ngrams = ngrams.map(convertTuple).dropna()
                ngrams2 = ngrams.assign(Composer=piece.metadata['composer'], Title=piece.metadata['title'], Date=piece.metadata['date'])
                cols_to_move = ['Composer', 'Title', 'Date']
                ngrams3 = ngrams2[cols_to_move + [col for col in ngrams2.columns if col not in cols_to_move]]
                # st.write(ngrams3)
                if "ngrams3" not in st.session_state:
                    st.session_state.ngrams3 = ngrams3
                if 'heatmap' not in st.session_state:
                    st.session_state.heatmap = heatmap
        if 'heatmap' not in st.session_state:
            pass
        if "ngrams3" not in st.session_state:
            pass
        else:
            st.write("Did you **change the piece list**?  If so, please **Update and Submit form**")
            if piece.metadata["composer"] is not None:
                st.subheader("Ngram Heatmap: " + piece.metadata["composer"] + ", " + piece.metadata["title"])
            else:
                st.subheader("Ngram Heatmap: " + piece.metadata["title"])
            st.altair_chart(st.session_state.heatmap, use_container_width = True)

            st.write("Filter Results by Contents of Each Column") 
            filtered_ngrams = filter_dataframe_ng(st.session_state.ngrams3)
            # update
            show_table = st.checkbox('Show Table')
            if show_table:
                st.table(filtered_ngrams)
            
            # csv = convert_df(filtered_ngrams.data)
            # filtered_ngrams = filtered_ngrams.to_csv().encode('utf-8')
            st.download_button(
                label="Download Filtered Ngram Data as CSV",
                data=filtered_ngrams.data.to_csv(),
                file_name = piece.metadata['title'] + '_ngram_results.csv',
                mime='text/csv',
                key=9,
                )
    # for corpus
    elif corpus_length > 1:
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
            st.write("Did you **change the piece list**?  If so, please **Update and Submit form**")

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
                    ngrams = ngrams.map(convertTuple).dropna()
                    ngrams2 = ngrams.assign(Composer=piece.metadata['composer'], Title=piece.metadata['title'], Date=piece.metadata['date'])
                    cols_to_move = ['Composer', 'Title', 'Date']
                    ngrams3 = ngrams2[cols_to_move + [col for col in ngrams2.columns if col not in cols_to_move]]
                    ngram_df_list.append(ngrams3)
                    if piece.metadata["composer"] is not None:
                        st.subheader("Ngram Heatmap: " + piece.metadata["composer"] + ", " + piece.metadata["title"])
                    else:
                        st.subheader("Ngram Heatmap: " + piece.metadata["title"])
                    st.altair_chart(heatmap, use_container_width = True)
                if 'combined_ngrams' in st.session_state.keys():
                    del st.session_state.combined_ngrams
                if len(ngram_df_list) > 0:
                    combined_ngrams = pd.concat(ngram_df_list)
                    if "combined_ngrams" not in st.session_state:
                        st.session_state.combined_ngrams = combined_ngrams

        if "combined_ngrams" not in st.session_state:
            pass
        else:
            st.write("Filter Results by Contents of Each Column")
            st.write("Note that the Filters do NOT change the heatmaps shown above!")
            filtered_combined_ngrams = filter_dataframe_ng(st.session_state.combined_ngrams)
            # update
            show_table = st.checkbox('Show Table of all Ngrams')
            if show_table:
                st.table(filtered_combined_ngrams)
            
            # csv = convert_df(filtered_combined_ngrams.data)
            # filtered_combined_ngrams = filtered_combined_ngrams.to_csv().encode('utf-8')
            st.download_button(
                label="Download Filtered Corpus Ngram Data as CSV",
                data=filtered_combined_ngrams.data.to_csv(),
                file_name = 'corpus_ngram_results.csv',
                mime='text/csv',
                key=10,
                )            
# hr functions
# one piece
@st.cache_data
def piece_homorhythm(piece, length_choice, full_hr_choice):
    hr = piece.homorhythm(ngram_length=length_choice, 
                    full_hr=full_hr_choice)
    # Check if hr is None or empty
    if hr is None or hr.empty:
        # Define the required columns
        columns_to_keep = ['active_voices', 'number_dur_ngrams', 'hr_voices', 'syllable_set',  
           'count_lyr_ngrams', 'active_syll_voices', 'voice_match']
        # Return an empty DataFrame with the required columns
        return pd.DataFrame(columns=columns_to_keep)
    # fix update error for type
    hr.fillna(0, inplace=True)
    # voices_list = list(piece.notes().columns)
    # hr[voices_list] = hr[voices_list].map(convertTuple).fillna('-')
    columns_to_keep = ['active_voices', 'number_dur_ngrams', 'hr_voices', 'syllable_set', 
           'count_lyr_ngrams', 'active_syll_voices', 'voice_match']
    hr = hr.drop(columns=[col for col in hr.columns if col not in columns_to_keep])
    hr['hr_voices'] = hr['hr_voices'].apply(', '.join)
    hr['syllable_set'] = hr['syllable_set'].apply(lambda x: ''.join(map(str, x[0]))).copy()
    # hr = piece.emaAddresses(df=hr, mode='h')
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
    # func2 = ImportedPiece.emaAddresses
    # list_of_hr_with_ema = corpus.batch(func = func2,
    #                                    kwargs = {'df': list_of_dfs, 'mode' : 'h'},
    #                                    metadata = True)
#
    # Filter out DataFrames with zero length
    list_of_dfs = [df for df in list_of_dfs if df is not None and len(df) >  0]
    rev_list_of_dfs = [df.reset_index() for df in list_of_dfs]
    if len(rev_list_of_dfs) > 0:
        hr = pd.concat(rev_list_of_dfs)
        # voices_list = list(piece.notes().columns)
        # hr[voices_list] = hr[voices_list].map(convertTuple).fillna('-')
        columns_to_keep = ['active_voices', 'number_dur_ngrams', 'hr_voices', 'syllable_set', 
            'count_lyr_ngrams', 'active_syll_voices', 'voice_match', 'Composer', 'Title', 'Date']
        hr = hr.drop(columns=[col for col in hr.columns if col not in columns_to_keep])
        hr['hr_voices'] = hr['hr_voices'].apply(', '.join)
        hr['syllable_set'] = hr['syllable_set'].apply(lambda x: ''.join(map(str, x[0]))).copy()
        cols_to_move = ['Composer', 'Title', 'Date']
        hr = hr[cols_to_move + [col for col in hr.columns if col not in cols_to_move]]
        return hr

# HR form--now commented out for Ditigal Ocean
# if st.sidebar.checkbox("Explore Homorhythm"):
    search_type = "other"
    st.subheader("Explore Homorhythm")
    st.write("[Know the code! Read more about the CRIM Intervals homorhythm method](https://github.com/HCDigitalScholarship/intervals/blob/main/tutorial/10_Lyrics_Homorhythm.md)", unsafe_allow_html=True)

    with st.form("Homorhythm Settings"):
        full_hr_choice = st.selectbox(
            "Select HR Full Status",
            [True, False])
        length_choice = st.number_input('Select ngram Length', value=4, step=1)
        submitted = st.form_submit_button("Update and Submit")
        if submitted:
            if 'hr' in st.session_state:
                del st.session_state.hr
            if corpus_length == 0:
                st.write("Please select one or more pieces")
            elif corpus_length == 1:
                 hr = piece_homorhythm(st.session_state.piece, length_choice, full_hr_choice)
            elif corpus_length > 1:
                 hr = corpus_homorhythm(st.session_state.corpus, length_choice, full_hr_choice)
            if "hr" not in st.session_state:
                st.session_state.hr = hr
# and use the session state variables for display
    if 'hr' not in st.session_state:
        pass
    else:
        st.write("Did you **change the piece list**?  If so, please **Update and Submit form**")
        st.write("Filter Results by Contents of Each Column")
        filtered_hr = filter_dataframe_hr(st.session_state.hr.fillna('-'))
        st.dataframe(filtered_hr, use_container_width = True)
        # csv = convert_df(filtered_hr)
        if corpus_length == 1:
            download_name = piece.metadata['title'] + '_homorhythm_results.csv'
        elif corpus_length > 1:
            download_name = "corpus_homorhythm_results.csv"
        # filtered_hr = filtered_hr.to_csv().encode('utf-8')
        st.download_button(
            label="Download Filtered Homorhythm Data as CSV",
            data=filtered_hr.to_csv(),
            file_name = download_name,
            mime='text/csv',
            key=11,
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
    if p_types is not None:
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
    # drop empty dfs:
    list_of_dfs = [df for df in list_of_dfs if df is not None and not df.empty]
    if len(list_of_dfs) > 0: 
        for p_types in list_of_dfs:
            # clean up for streamlit facets
            p_types["Measures_Beats"] = p_types["Measures_Beats"].apply(lambda x: ', '.join(map(str, x))).copy()
            p_types["Melodic_Entry_Intervals"] = p_types["Melodic_Entry_Intervals"].apply(lambda x: ', '.join(map(str, x))).copy()
            p_types["Offsets"]= p_types["Offsets"].apply(lambda x: ', '.join(map(str, x))).copy()
            p_types["Soggetti"]= p_types["Soggetti"].apply(lambda x: ', '.join(map(str, x))).copy()
            p_types["Time_Entry_Intervals"]= p_types["Time_Entry_Intervals"].apply(lambda x: ', '.join(map(str, x))).copy()
        p_types = pd.concat(list_of_dfs)
        return p_types

# p types form
if st.sidebar.checkbox("Explore Presentation Types"):
    search_type = "other"
    st.subheader("Explore Presentation Types")
    st.write("[Know the code! Read more about CRIM Intervals presentation type methods](https://github.com/HCDigitalScholarship/intervals/blob/main/tutorial/12_Presentation_Types.md)", unsafe_allow_html=True)
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
            if corpus_length == 0:
                st.write("Please select one or more pieces")
            # one piece
            elif corpus_length == 1:
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
        st.write("Did you **change the piece list**?  If so, please **Update and Submit form**")
        st.write("Filter Results by Contents of Each Column")
        filtered_p_types = filter_dataframe_ptypes(st.session_state.p_types)
        st.dataframe(filtered_p_types, use_container_width = True)
        # csv = convert_df(filtered_p_types)
        
        if corpus_length == 1:
            download_name = piece.metadata['title'] + '_p_type_results.csv'
            if filtered_p_types is not None:
                # filtered_p_types = filtered_p_types.to_csv().encode('utf-8')
                st.download_button(
                    label="Download Filtered Presentation Type Data as CSV",
                    data=filtered_p_types.to_csv(),
                    file_name = download_name,
                    mime='text/csv',
                    key=12,
                    )
        elif corpus_length > 1:
            download_name = "corpus_p_type_results.csv"
            if filtered_p_types is not None:
                # filtered_p_types = filtered_p_types.to_csv().encode('utf-8')
                st.download_button(
                    label="Download Filtered Corpus Presentation Type Data as CSV",
                    data=filtered_p_types.to_csv(),
                    file_name = download_name,
                    mime='text/csv',
                    key=13,
                    )
# def cadence_radar(cadences):
#     # Define the category order for cad tones
#     category_order = {
#         'C': 0, 'D': 1, 'E-': 2, 'E': 3, 'F': 4, 'G': 5, 'A': 6, 'B-': 7
#     }
#     # Get all unique titles for this final
#     titles = cadences['Title'].unique()
#     # Create a list to store our count data
#     count_data = []
#     # For each title, count the occurrences of each tone
#     for title in titles:
#         title_data = cadences[cadences['Title'] == title]
#         # Count occurrences of each Tone for this Title
#         for tone in category_order.keys():
#             count = len(title_data[title_data['Tone'] == tone])
#             count_data.append({
#                 'Title': title,
#                 'Tone': tone,
#                 'count': count
#             })
#     # Convert to DataFrame
#     count_df = pd.DataFrame(count_data)
#     count_df = count_df[count_df['count'] > 0]
#     # calculate % for each cadence vs total number of cadences for each piece
#     title_sums = count_df.groupby('Title')['count'].sum().reset_index()
#     title_sums.rename(columns={'count': 'TitleSum'}, inplace=True)
#     # Merge the sums back to the original DataFrame
#     count_df = count_df.merge(title_sums, on='Title', how='left')
#     # Calculate percentage
#     count_df['Percentage'] = np.round((count_df['count'] / count_df['TitleSum']) * 100)
#     # Create the radar plot with Plotly Express
#     fig = px.line_polar(
#         count_df, 
#         r='Percentage',       
#         theta='Tone', 
#         line_close=True,
#         color='Title',
#         markers=True,
#         category_orders={'Tone': sorted(category_order.keys(), key=lambda x: category_order[x])}
#     )
#     # Update traces to fill the area
#     fig.update_traces(
#         fill='toself',
#         line=dict(width=2)
#     )
#     # Update layout with size control and legend positioning
#     fig.update_layout(
#         # Control the size of the plot
#         width=800,  # Width in pixels
#         height=600,  # Height in pixels
#         # Position the legend
#         legend=dict(
#         orientation="v",  # Vertical layout
#         yanchor="top",  # Vertical centering
#         y=0.5,  # Vertical position
#         xanchor="center",  # Right alignment
#         # x=1,  # Offset from right edge
#         title={
#             'text': 'Titles',
#             'side': 'top',
#             'font_size': 12
#         },
#         itemsizing='constant',
#         itemwidth=30,
#         bordercolor="black",
#         borderwidth=1,
#         bgcolor="rgba(255,255,255,0.8)"
#     ),
#     # Add right margin to accommodate legend
    
#         # Add title
#         title_text="Relative Distribution of Cadence Tones in Corpus",
#         title_x=0.5,  # Center the title
#         # Adjust margins if needed
#         polar=dict(
#             radialaxis=dict(
#                 visible=True,
#                 title='Percentage'
#             )
#         )
#     )
#     return fig
def cadence_radar(cadences):
    # Define constants at function scope
    CATEGORY_ORDER = {
        'C': 0, 'D': 1, 'E-': 2, 'E': 3, 'F': 4,
        'G': 5, 'A': 6, 'B-': 7
    }
    
    # Get unique titles and create base DataFrame
    titles = cadences['Title'].unique()
    base_data = []
    
    # Vectorized approach using groupby operations
    grouped = cadences.groupby(['Title', 'Tone']).size().reset_index(name='count')
    
    # Calculate percentages efficiently
    title_sums = grouped.groupby('Title')['count'].sum()
    grouped['Percentage'] = (grouped['count'] / grouped['Title'].map(title_sums)) * 100
    
    # Create radar plot
    fig = px.line_polar(
        grouped[grouped['count'] > 0],
        r='Percentage',
        theta='Tone',
        line_close=True,
        color='Title',
        markers=True,
        category_orders={'Tone': sorted(CATEGORY_ORDER.keys(), key=lambda x: CATEGORY_ORDER[x])}
    )
    
    # Apply optimizations
    fig.update_traces(fill='toself', line=dict(width=2))
    
    # Update layout with bottom legend
    fig.update_layout(
        width=800,
        height=600,
        legend=dict(
            orientation="h",  # Horizontal layout for better space usage
            yanchor="bottom",
            y=-0.4,           # Position below plot
            xanchor="center",
            x=0.5,            # Center horizontally
            xref="container", # Scale with container
            yref="container", # Scale with container
            title=dict(
                text="Titles",
                side="top",
                font_size=12
            ),
            itemsizing='constant',
            itemwidth=30,
            bordercolor="black",
            borderwidth=1,
            bgcolor="rgba(255,255,255,0.8)"
        ),
        title=dict(text="Relative Distribution of Cadence Tones in Corpus", x=0.5),
        polar=dict(
            radialaxis=dict(visible=True, title='Percentage')
        ),
        margin=dict(b=120)  # Bottom margin for legend
    )
    
    return fig
# progress

custom_tone_order = ['E-', 'B-', 'F', 'C', 'G', 'D', 'A', 'E', 'B']  


def cadence_progress(cadences, composer, title):
    # Define custom ordering for CadTypes
    custom_order = [
        'Authentic', 'Evaded Authentic', 
        'Clausula Vera', 'Evaded Clausula Vera', 'Abandoned Clausula Vera', 'Phrygian Clausula Vera',
        'Double Leading Tone', 'Evaded Double Leading Tone', 'Abandoned Double Leading Tone',
        'Altizans Only', 'Phrygian Altizans', 'Evaded Altizans Only',
        'Phrygian', 'Reinterpreted', 'Quince', 'Leaping Contratenor'
    ]
    
    # Define color mappings grouped by cadence type
    # Create the base colors dictionary
    base_colors = {
        'Authentic': '#FF0000',              # Pure Red
        'Clausula Vera': '#0000FF',          # Pure Blue
        'Double Leading Tone': '#00FF00',    # Pure Green
        'Altizans Only': '#800080',          # Purple (maximally different from red)
        'Phrygian': '#00FF00',               # Pure Green
        'Reinterpreted': '#00FFFF',          # Cyan
        'Quince': '#4B0082',                 # Indigo
        'Leaping Contratenor': '#000000',    # Black
        'Phrygian Clausula Vera': '#FF00FF'  # Magenta
    }

    # Create lighter versions for modified cadences
    color_mapping = base_colors.copy()
    # Evaded versions (50% lighter)
    color_mapping['Evaded Authentic'] = '#FF6666'     # Lighter red
    color_mapping['Evaded Clausula Vera'] = '#6666FF' # Lighter blue
    color_mapping['Evaded Double Leading Tone'] = '#66FF66' # Lighter green
    color_mapping['Evaded Altizans Only'] = '#CC99CC' # Lighter purple
    color_mapping['Evaded Phrygian'] = '#66FF66'      # Lighter green
    color_mapping['Evaded Reinterpreted'] = '#99FFFF' # Lighter cyan
    color_mapping['Evaded Quince'] = '#9966CC'       # Lighter indigo
    color_mapping['Evaded Phrygian Clausula Vera'] = '#FF66FF' # Lighter magenta
    # Abandoned versions (75% lighter)
    color_mapping['Abandoned Clausula Vera'] = '#CCCCFF' # Much lighter blue
    color_mapping['Abandoned Double Leading Tone'] = '#CCFFCC' # Much lighter green
    color_mapping['Abandoned Phrygian'] = '#FFE5CC'    # Much lighter orange
    color_mapping['Abandoned Authentic'] = '#FFCCCC'  # Much lighter red
    color_mapping['Abandoned Phrygian Clausula Vera'] = '#FFCCFF' # Much lighter magenta

    # def cadence_progress(cadences, composer, title):
    # Ensure the Tone column is categorical with correct ordering
    cadences['Tone'] = pd.Categorical(
        cadences['Tone'],
        categories=custom_tone_order,
        ordered=True
    )
    
    # Create figure with explicit category ordering
    fig = px.scatter(
        cadences,
        x='Progress',
        y='Tone',
        color='CadType',
        color_discrete_map=color_mapping,
        category_orders={'Tone': custom_tone_order}
    )
    
    # Configure Y-axis to show E- at bottom
    fig.update_layout(
        yaxis=dict(
            categoryorder='array',
            categoryarray=custom_tone_order,
            autorange=True,
            fixedrange=True,
            scaleanchor='y',
            scaleratio=1,
            showgrid=True,
            showticklabels=True
        ),
        yaxis_range=[None, None]  # Allow Plotly to determine range
    )
    
    # Update marker properties
    fig.update_traces(marker=dict(size=25))
    
    # Customize layout
    fig.update_layout(
        title=f'Progress of Cadences in {composer}: {title}',
        legend=dict(
            title_text="Cadence Type",
            orientation="v",
            yanchor="bottom",
            y=-0.5,
            xanchor="right",
            x=1
        )
    )
    
    return fig
    
    # fig = px.scatter(
    #     cadences,
    #     x='Progress',
    #     y='Tone',
    #     color='CadType',
    #     color_discrete_map=color_mapping,
    #     category_orders={'Tone': custom_tone_order}
    # )
    
    # # Update marker properties
    # fig.update_traces(marker=dict(size=25))
    
    # # Customize layout
    # fig.update_layout(
    #     title=f'Progress of Cadences in {composer}: {title}',
    #     legend=dict(
    #         title_text="Cadence Type",
    #         orientation="v",
    #         yanchor="bottom",
    #         y=-0.5,
    #         xanchor="right",
    #         x=1
    #     )
    # )
    
    # return fig

# cadence form
if st.sidebar.checkbox("Explore Cadences"):
    
    search_type = "other"
    st.subheader("Explore Cadences")
    st.write("[Know the code! Read more about CRIM Intervals cadence methods](https://github.com/HCDigitalScholarship/intervals/blob/main/tutorial/11_Cadences.md)", unsafe_allow_html=True)
    
    # st.write("Did you **change the piece list**?  If so, please **Click Update Cadence Results**")
    # if st.button("Update Cadence Results"):
    if corpus_length == 0:
        st.write("Please select one or more pieces")
    elif corpus_length == 1:
        title = piece.metadata['title']
        composer = piece.metadata['composer']
        cadences = piece.cadences()
        cadences['Title'] = title
        cadences['Composer'] = composer
        grouped_cadences = cadences.groupby(['Tone', 'CadType', 'CVFs'])['Title'].count()
        grouped_cadences = pd.DataFrame(grouped_cadences).reset_index()
        grouped_cadences = grouped_cadences.rename(columns={'Title': 'Count'})
        total_cads = grouped_cadences['Count'].sum()
        grouped_cadences = grouped_cadences[grouped_cadences['Count'] != 0]
        grouped_cadences.reset_index(drop=True, inplace=True)
    
        # the full table of cad
        if st.checkbox("Show Full Cadence Table"):
            # cadences = piece.cadences()
            st.subheader("Detailed View of Cadences")
            filtered_cadences = filter_dataframe_cads(cadences)
            st.dataframe(filtered_cadences, use_container_width = True)
            # to download csv
            download_name = piece.metadata['title'] + '_cadence_results.csv'
            st.download_button(
                label="Download Filtered Cadence Data as CSV",
                data=filtered_cadences.to_csv(),
                file_name = download_name,
                key=14,
                mime='text/csv')
            # possible Verovio Cadences use.  Needs to adapt renderer?
            # if st.button("Print Filtered Cadences with Verovio"):
            #     output = piece.verovioCadences(df = filtered_cadences)
            #     components.html(output)
        # summary of tone and type
        # Your existing chart creation code remains unchanged
        if st.checkbox("Chart of Cadences by Tone and Type"):
            st.subheader("Chart of Cadence Tones and Types") 
            grouped = cadences.groupby(['Tone', 'CadType']).size().reset_index(name='Count')
            
            # Create the chart with explicit color preservation
            cad_chart = px.bar(
                grouped,
                x='Tone',
                y='Count',
                color='CadType',
                barmode='stack',
                title=f"Cadence Tones and Types in {composer}, {title}",
                template="plotly_white"  # Ensures consistent styling
            )
            
            # Enhance layout for better preservation
            cad_chart.update_layout(
                xaxis_title="Cadence Final Tone",
                yaxis_title="Count",
                font=dict(family="Arial", size=14),
                title_font_size=20,
                title_x=0.5,
                width=1000,
                height=400,
                legend=dict(orientation="v"),
                showlegend=True,
                title=dict(
                    text=f"Cadence Tones and Types in {composer}, {title}",
                    x=0.5,  # Centers the title horizontally
                    xanchor='center',  # Ensures proper centering
                    font=dict(size=20)  # Maintains title size),
                    )
            )
            
            # Create container for chart and button
            container = st.container()
            col1, col2 = container.columns([10, 2])
            
            # Plot chart in first column
            with col1:
                st.plotly_chart(cad_chart, use_container_width=True)
                
            # Add download button in second column
            with col2:
                @st.cache_data(ttl=3600)  # Cache for 1 hour
                def get_html_content():
                    """Convert Plotly figure to HTML string with preserved colors"""
                    return pio.to_html(
                        cad_chart,
                        include_plotlyjs='cdn',
                        full_html=False,
                        config=dict(
                            displayModeBar=True,  # Enable toolbar
                            responsive=True,
                            scrollZoom=True,
                            displaylogo=False,
                            modeBarButtonsToRemove=['lasso2d', 'select2d'],
                            title=f"Cadence Tones and Types in {composer}, {title}"
                        )
                    )
        
                st.markdown("")     
                if st.button('📥 Prepare Chart for Download'):
                    html_content = get_html_content()
                    st.download_button(
                        label="Download the Chart",
                        data=html_content,
                        file_name=f"{composer}_{title}_cadence_chart.html",
                        mime="text/html"
                    )

        # Radar plots
        if st.checkbox("Show Radar Plot"):
            st.subheader("Radar Plot of Cadences")
            
            # Create container for chart and button
            container = st.container()
            col1, col2 = container.columns([10, 2])
            
            # Plot chart in first column
            with col1:
                radar_new = cadence_radar(cadences)
                
                # Explicitly set colors for each trace
                for i, trace in enumerate(radar_new.data):
                    trace.update(
                        marker=dict(color=px.colors.qualitative.Alphabet[i % len(px.colors.qualitative.Alphabet)]),
                        line=dict(color=px.colors.qualitative.Alphabet[i % len(px.colors.qualitative.Alphabet)])
                    )
                
                radar_new.update_layout(
                    template="plotly_white",
                    showlegend=True,
                    legend=dict(orientation="v",  # Changed from 'h' to 'v' for vertical layout
                                yanchor="bottom",  # Changed from 'bottom' to 'middle'
                                y=0.5,  # Changed from -0.7 to 0.5
                                xanchor="right",  # Keep right alignment
                                x=1.05,  # Keep right offset
                                title={'text': 'Titles',
                                    'side': 'top',
                                    'font_size': 12},
                                    itemsizing='constant',
                                    itemwidth=30,
                                        bordercolor="black",
                                        borderwidth=1,
                                        bgcolor="rgba(255,255,255,0.8)"
                                )
                )
                # st.plotly_chart(radar_new, use_container_width=True)
                st.container().plotly_chart(radar_new, use_container_width=True)

                
            # Add download button in second column
            with col2:
                @st.cache_data(ttl=3600)
                def get_radar_html():
                    """Convert radar plot to HTML with preserved colors and interactivity"""
                    # Create a complete HTML file with embedded styles
                    html_content = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <title>Radar Plot - {composer} - {title}</title>
                        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                        <style>
                            body {{
                                margin: 40px;
                                padding: 20px;
                                font-family: Arial, sans-serif;
                            }}
                            .chart-container {{
                                width: 400px;
                                height: 400px;
                            }}
                        </style>
                    </head>
                    <body>
                        <div class="chart-container" id="chart"></div>
                        <script>
                            var figure = {radar_new.to_json()};
                            Plotly.newPlot('chart', figure.data, figure.layout, {{
                                responsive: true,
                                displayModeBar: true,
                                displaylogo: false
                            }});
                        </script>
                    </body>
                    </html>
                    """
                    return html_content
                    
                if st.button('📥 Prepare Radar Plot for Download'):
                    radar_html = get_radar_html()
                    st.download_button(
                        label="Download Radar Plot",
                        data=radar_html,
                        file_name=f"{composer}_{title}_radar_plot.html",
                        mime="text/html"
                    )

        # Progress plot
        if st.checkbox("Show Progress Plot"):
            st.subheader("Progress Plot of Cadences")
            
            # Create container for chart and button
            container = st.container()
            col1, col2 = container.columns([10, 2])
            
            # Plot chart in first column
            with col1:
                progress_plot = cadence_progress(cadences, composer, title)
                
                progress_plot.update_layout(
                    # template="plotly_white",
                    showlegend=True,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=-0.3,
                        xanchor="center",
                        x=0.5
                    )
                )
                st.plotly_chart(progress_plot, use_container_width=True)
                
            # Add download button in second column
            with col2:
                @st.cache_data(ttl=3600)
                def get_progress_html():
                    """Convert progress plot to HTML with preserved colors and interactivity"""
                    # Create a complete HTML file with embedded styles
                    html_content = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <title>Progress Plot - {composer} - {title}</title>
                        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                        <style>
                            body {{
                                margin: 0;
                                padding: 20px;
                                font-family: Arial, sans-serif;
                            }}
                            .chart-container {{
                                width: 100%;
                                height: 600px;
                            }}
                        </style>
                    </head>
                    <body>
                        <div class="chart-container" id="chart"></div>
                        <script>
                            var figure = {progress_plot.to_json()};
                            Plotly.newPlot('chart', figure.data, figure.layout, {{
                                responsive: true,
                                displayModeBar: true,
                                displaylogo: false
                            }});
                        </script>
                    </body>
                    </html>
                    """
                    return html_content
                    
                if st.button('📥 Prepare Progress Plot for Download'):
                    progress_html = get_progress_html()
                    st.download_button(
                        label="Download Progress Plot",
                        data=progress_html,
                        file_name=f"{composer}_{title}_progress_plot.html",
                        mime="text/html"
                    )
    # corpus
    elif corpus_length >= 2:
        func = ImportedPiece.cadences
        list_of_dfs = st.session_state.corpus.batch(func=func, kwargs={'keep_keys': True}, metadata=True)
        
        cadences_metadata = pd.concat(list_of_dfs, ignore_index=False)   
        cols_to_move = ['Composer', 'Title', 'Date']
        cadences = cadences_metadata[cols_to_move + [col for col in cadences_metadata.columns if col not in cols_to_move]] 
        if st.checkbox("Show Full Cadence Table"):
            st.subheader("Detailed View of Cadences")
            filtered_cadences = filter_dataframe_cads(cadences)
            st.dataframe(filtered_cadences, use_container_width = True)
            download_name = "corpus_cadence_results.csv"
            # filtered_cadences = filtered_cadences.to_csv().encode('utf-8')
            st.download_button(
                label="Download Filtered Corpus Cadence Data as CSV",
                data=filtered_cadences.to_csv(),
                file_name = download_name,
                mime='text/csv',
                key=15,
                )
            # possible Verovio Cadences use.  Needs to adapt renderer?
            # if st.button("Print Filtered Cadences with Verovio"):
            #     output = piece.verovioCadences(df = filtered_cadences)
            #     components.html(output)
        # summary of tone and type
        if st.checkbox("Chart of Cadences by Tone and Type"):
            st.subheader("Chart of Cadence Tones and Types") 
            grouped = cadences.groupby(['Tone', 'CadType']).size().reset_index(name='Count')
            
            # Create the chart with explicit color preservation
            cad_chart = px.bar(
                grouped,
                x='Tone',
                y='Count',
                color='CadType',
                barmode='stack',
                title=f"Cadence Tones and Types in Corpus",
                template="plotly_white"  # Ensures consistent styling
            )
            
            # Enhance layout for better preservation
            cad_chart.update_layout(
                xaxis_title="Cadence Final Tone",
                yaxis_title="Count",
                font=dict(family="Arial", size=14),
                title_font_size=20,
                title_x=0.5,
                width=1000,
                height=400,
                legend=dict(orientation="v"),
                showlegend=True,
                title=dict(
                    text=f"Cadence Tones and Types in Corpus",
                    x=0.5,  # Centers the title horizontally
                    xanchor='center',  # Ensures proper centering
                    font=dict(size=20)  # Maintains title size),
                    )
            )
            
            # Create container for chart and button
            container = st.container()
            col1, col2 = container.columns([10, 2])
            
            # Plot chart in first column
            with col1:
                st.plotly_chart(cad_chart, use_container_width=True)
                
            # Add download button in second column
            with col2:
                @st.cache_data(ttl=3600)  # Cache for 1 hour
                def get_html_content():
                    """Convert Plotly figure to HTML string with preserved colors"""
                    return pio.to_html(
                        cad_chart,
                        include_plotlyjs='cdn',
                        full_html=False,
                        config=dict(
                            displayModeBar=True,  # Enable toolbar
                            responsive=True,
                            scrollZoom=True,
                            displaylogo=False,
                            modeBarButtonsToRemove=['lasso2d', 'select2d'],
                            title=f"Cadence Tones and Types in Corpus"
                        )
                    )
        
                st.markdown("")     
                if st.button('📥 Prepare Chart for Download'):
                    html_content = get_html_content()
                    st.download_button(
                        label="Download the Chart",
                        data=html_content,
                        file_name=f"corpus_cadence_chart.html",
                        mime="text/html"
                    )
        # radar plots
        if st.checkbox('Show Radar Plot'):
            st.subheader("Combined Radar Plot of Cadences in Corpus") 
            # Create container for chart and button
            container = st.container()
            col1, col2 = container.columns([10, 2])
            
            # Plot chart in first column
            with col1:
                radar_new = cadence_radar(cadences)
                
                # Explicitly set colors for each trace
                for i, trace in enumerate(radar_new.data):
                    trace.update(
                        marker=dict(color=px.colors.qualitative.Alphabet[i % len(px.colors.qualitative.Alphabet)]),
                        line=dict(color=px.colors.qualitative.Alphabet[i % len(px.colors.qualitative.Alphabet)])
                    )
                
                radar_new.update_layout(
                    template="plotly_white",
                    showlegend=True,
                    legend=dict(orientation="v",  # Changed from 'h' to 'v' for vertical layout
                                yanchor="bottom",  # Changed from 'bottom' to 'middle'
                                y=0.5,  # Changed from -0.7 to 0.5
                                xanchor="right",  # Keep right alignment
                                x=1.05,  # Keep right offset
                                title={'text': 'Titles',
                                    'side': 'top',
                                    'font_size': 12},
                                    itemsizing='constant',
                                    itemwidth=30,
                                        bordercolor="black",
                                        borderwidth=1,
                                        bgcolor="rgba(255,255,255,0.8)"
                                ),
                    title=dict(text=f"Cadences in Corpus",
                            x=0.5,  # Centers the title horizontally
                            xanchor='center',  # Ensures proper centering
                            font=dict(size=20)  # Maintains title size),
                            )
                )
                # st.plotly_chart(radar_new, use_container_width=True)
                st.container().plotly_chart(radar_new, use_container_width=True)

                
            # Add download button in second column
            with col2:
                @st.cache_data(ttl=3600)
                def get_radar_html():
                    """Convert radar plot to HTML with preserved colors and interactivity"""
                    # Create a complete HTML file with embedded styles
                    html_content = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <title>Radar Plot in Corpus</title>
                        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                        <style>
                            body {{
                                margin: 0;
                                padding: 40px;
                                font-family: Arial, sans-serif;
                            }}
                            .chart-container {{
                                width: 800px;
                                height: 800px;
                            }}
                        </style>
                    </head>
                    <body>
                        <div class="chart-container" id="chart"></div>
                        <script>
                            var figure = {radar_new.to_json()};
                            Plotly.newPlot('chart', figure.data, figure.layout, {{
                                responsive: true,
                                displayModeBar: true,
                                displaylogo: false
                            }});
                        </script>
                    </body>
                    </html>
                    """
                    return html_content
                    
                if st.button('📥 Download Radar Plot'):
                    radar_html = get_radar_html()
                    st.download_button(
                        label="Download Radar Plot",
                        data=radar_html,
                        file_name=f"corpus_radar_plot.html",
                        mime="text/html"
                    )
            # old code
            # radar_new = cadence_radar(cadences)
            # st.plotly_chart(radar_new, use_container_width=True)
        # old radar from Intervals
        # if st.checkbox("Show Basic Radar Plot"):
        #     st.subheader("Radar Plot of Cadences") 
        #     # radar = st.session_state.cadence_radar(cadences)
        #     radar = st.session_state.corpus.compareCadenceRadarPlots(combinedType=False, displayAll=False, renderer='streamlit')
        #     st.plotly_chart(radar, use_container_width=True)
        # if st.checkbox("Show Advanced Radar Plot"):
        #     st.subheader("Advanced Radar Plot")    
        #     radar = st.session_state.corpus.compareCadenceRadarPlots(combinedType=True, displayAll=True, renderer='streamlit')
        #     st.plotly_chart(radar, use_container_width=True)
        if st.checkbox("Show Progress Charts"):
            st.subheader("Progress Plot of Cadences for each Piece in Corpus")
            titles = cadences_metadata["Title"].unique()
            for idx, title in enumerate(titles):
                filtered_cadences = cadences_metadata[cadences_metadata['Title'] == title]
                composer = filtered_cadences.iloc[1]['Composer']
                
                # Create container for chart and button
                container = st.container()
                col1, col2 = container.columns([10, 2])
                
                # Plot chart in first column
                with col1:
                    progress_plot = cadence_progress(filtered_cadences, composer, title)
                    
                    progress_plot.update_layout(
                        template="plotly_white",
                        showlegend=True,
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=-0.3,
                            xanchor="center",
                            x=0.5
                        )
                    )
                    st.plotly_chart(progress_plot, use_container_width=True)
                
                # Add download button in second column
                with col2:
                    @st.cache_data(ttl=3600)
                    def get_progress_html(progress_plot, composer, title):
                        """Convert progress plot to HTML with preserved colors and interactivity"""
                        # Create a complete HTML file with embedded styles
                        html_content = f"""
                        <!DOCTYPE html>
                        <html>
                        <head>
                        <meta charset="utf-8">
                        <title>Progress Plot - {composer} - {title}</title>
                        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                        <style>
                        body {{
                            margin: 0;
                            padding: 20px;
                            font-family: Arial, sans-serif;
                        }}
                        .chart-container {{
                            width: 100%;
                            height: 600px;
                        }}
                        </style>
                        </head>
                        <body>
                        <div class="chart-container" id="chart"></div>
                        <script>
                        var figure = {progress_plot.to_json()};
                        Plotly.newPlot('chart', figure.data, figure.layout, {{
                            responsive: true,
                            displayModeBar: true,
                            displaylogo: false
                        }});
                        </script>
                        </body>
                        </html>
                        """
                        return html_content

                    # Inside your loop:
                    with col2:
                        if st.button('📥 Prepare This Progress Plot for Download', key=f"download_{idx}"):
                            progress_html = get_progress_html(progress_plot, composer, title)
                            st.download_button(
                                label="Download This Progress Plot",
                                data=progress_html,
                                file_name=f"{composer}_{title}_progress_plot.html",
                                mime="text/html"
                            )
                                
                # cadence_progress(filtered_cadences, composer, title)
                # st.plotly_chart(cadence_progress(filtered_cadences, composer, title), use_container_width=True)
        # old progress from intervals
        # if st.checkbox("Basic Progress Chart"):    
        #     st.subheader("Basic Progress Chart")
        #     progress = st.session_state.corpus.compareCadenceProgressPlots(includeType=False, renderer='streamlit')
        #     st.pyplot(progress, use_container_width=True)
        # if st.checkbox("Show Advanced Progress Chart"):
        #     st.subheader("Advanced Progress Chart")    
        #     progress = st.session_state.corpus.compareCadenceProgressPlots(includeType=True, renderer='streamlit')
        #     st.pyplot(progress, use_container_width=True)

if st.sidebar.checkbox("Explore Model Finder"):
    st.subheader("Model Finder")
    st.write("[Know the code! Read more about CRIM Intervals cadence methods](https://github.com/HCDigitalScholarship/intervals/blob/main/tutorial/13_Model_Finder.md)", unsafe_allow_html=True)
    if corpus_length <= 1:
        st.write("Please select at least two pieces to compare")
    elif corpus_length > 1:
        corpus = CorpusBase(corpus_list)
        # Initialize session state
# if 'ready_to_download' not in st.session_state:
#     st.session_state.ready_to_download = False

# Main form for settings
    with st.form("Model Finder Settings"):
        length_choice = st.number_input('Select ngram Length', value=4, step=1)
        
        # Plot section
        soggetto_cross_plot = corpus.modelFinder(n=length_choice)
        st.dataframe(soggetto_cross_plot)
        fig = px.imshow(soggetto_cross_plot, color_continuous_scale="YlGnBu", aspect="auto")
        
        if st.form_submit_button('Submit'):
            # Prepare data for download but don't show button yet
            st.session_state.plot_data = soggetto_cross_plot
        st.plotly_chart(fig)
        

    # Separate section for download
    if hasattr(st.session_state, 'plot_data'):
        def get_model_html():
            """Convert progress plot to HTML with preserved colors and interactivity"""
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Model Finder Crossplot</title>
                <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                <style>
                    body {{
                        margin: 0;
                        padding: 20px;
                        font-family: Arial, sans-serif;
                    }}
                    .chart-container {{
                        width: 100%;
                        height: 600px;
                    }}
                </style>
            </head>
            <body>
                <div class="chart-container" id="chart"></div>
                <script>
                    var figure = {fig.to_json()};
                    Plotly.newPlot('chart', figure.data, figure.layout, {{
                        responsive: true,
                        displayModeBar: true,
                        displaylogo: false
                    }});
                </script>
            </body>
            </html>
            """
            return html_content
        
        html_content = get_model_html()
        st.download_button(
            label="Download the Chart",
            data=html_content,
            file_name=f"model_finder.html",
            mime="text/html"
        )
    else:
        pass
   
