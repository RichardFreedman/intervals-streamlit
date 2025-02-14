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
import streamlit.components.v1 as components
from os import listdir 
import json
import psutil
from tempfile import NamedTemporaryFile
import random
from datetime import datetime
import time
from collections import deque


from pandas.api.types import (
    is_categorical_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
)

# def initialize_session_state():
#     """Initialize all required session states"""
#     if 'show_monitor' not in st.session_state:
#         st.session_state.show_monitor = False
#     if 'memory_history' not in st.session_state:
#         st.session_state.memory_history = deque(maxlen=60)  # Store 60 seconds of history
#     if 'last_update_time' not in st.session_state:
#         st.session_state.last_update_time = time.time()

# def get_memory_usage():
#     """Get current memory usage of the process"""
#     process = psutil.Process(os.getpid())
#     return process.memory_info().rss / (1024 * 1024)

# def get_previous_memory():
#     """Get previous memory reading for delta calculation"""
#     if len(st.session_state.memory_history) < 2:
#         return 0
#     return st.session_state.memory_history[-2]['memory_mb']

# @st.cache_data
# def create_memory_chart():
#     # Create a DataFrame from the session state
#     df = pd.DataFrame({
#         'time': [t['time'] for t in st.session_state.memory_history],
#         'memory_mb': [t['memory_mb'] for t in st.session_state.memory_history]
#     })
    
#     # Create the figure using px.line
#     fig = px.line(
#         data_frame=df,
#         x='time',
#         y='memory_mb',
#         title='Memory Usage Over Time',
#         labels={
#             'time': 'Time (seconds)',
#             'memory_mb': 'Memory (MB)'
#         }
#     )
    
#     # Update layout
#     fig.update_layout(
#         showlegend=True,
#         height=200
#     )
    
#     return fig

# def monitor_memory():
#     """Main monitoring function that updates the display"""
#     container = st.empty()
#     while True:
#         mem_usage = get_memory_usage()
#         current_time = time.time()
#         st.session_state.memory_history.append({
#             'time': current_time,
#             'memory_mb': mem_usage
#         })
        
#         if time.time() - st.session_state.last_update_time >= 1:
#             with container.container():
#                 col1, col2 = st.columns([2, 1])
#                 with col1:
#                     st.metric(
#                         label="Memory Usage",
#                         value=f"{mem_usage:.2f} MB",
#                         delta=f"+{(mem_usage - get_previous_memory()):.2f} MB"
#                     )
#                 with col2:
#                     fig = create_memory_chart()
#                     st.plotly_chart(fig, use_container_width=True)
#             st.session_state.last_update_time = time.time()
#         time.sleep(0.1)

# # Main app
# initialize_session_state()

# st.title("Memory Monitor Control Panel")
# col1, col2 = st.columns([1, 1])
# with col1:
#     if st.button("Start Monitoring"):
#         st.session_state.show_monitor = True

# if st.session_state.show_monitor:
#     monitor_memory()


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
# download function for filtered results
# @st.cache_data
# def convert_df(_filtered):
#     # IMPORTANT: Cache the conversion to prevent computation on every rerun
#     if _filtered is not None:
#         return _filtered.to_csv().encode('utf-8')

# intervals functions and forms

# notes piece
# @st.cache_data
def piece_notes(piece, combine_unisons_choice, combine_rests_choice):
    nr = piece.notes(combineUnisons = combine_unisons_choice,
                            combineRests = combine_rests_choice)
    nr = piece.numberParts(nr)
    nr = piece.detailIndex(nr)
    nr = nr.reset_index()
    # nr = nr.reset_index()
    nr = nr.assign(Composer=piece.metadata['composer'], Title=piece.metadata['title'], Date=piece.metadata['date'])
    cols_to_move = ['Composer', 'Title', 'Measure', 'Beat', 'Date']
    nr = nr[cols_to_move + [col for col in nr.columns if col not in cols_to_move]]  
    return nr

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
    rev_list_of_dfs = [df.reset_index() for df in list_of_dfs]
    nr = pd.concat(rev_list_of_dfs)
    cols_to_move = ['Composer', 'Title', 'Measure', 'Beat', 'Date']
    nr = nr[cols_to_move + [col for col in nr.columns if col not in cols_to_move]]
    return nr

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
                # for one piece
                if corpus_length == 1:
                    nr_no_mdata = filtered_nr.data.drop(['Composer', 'Title', "Date", "Measure", "Beat"], axis=1)
                    nr_no_mdata = nr_no_mdata.map(str)
                    nr_counts = nr_no_mdata.apply(lambda x: x.value_counts(), axis=0).fillna('0').astype(int)
                    nr_counts.index = pd.CategoricalIndex(nr_counts.index, categories=pitch_order, ordered=True)
                    nr_counts = nr_counts.sort_index()
                    nr_counts = nr_counts.drop(index='Rest', errors='ignore')
                    nr_counts = nr_counts[nr_counts.index.notnull()]
                    nr_counts.drop('index', axis=1, inplace=True)
                    # Show results
                    nr_chart = px.bar(nr_counts, x=nr_counts.index.astype(str).tolist(), y=list(nr_counts.columns),
                                    title="Distribution of Pitches in " + piece.metadata['title'])
                    nr_chart.update_layout(xaxis_title="Pitch", 
                                        yaxis_title="Count",
                                        legend_title='Voices')
                    st.plotly_chart(nr_chart, use_container_width = True)
                    st.dataframe(filtered_nr, use_container_width = True)
                    # download option
                    # csv = convert_df(filtered_nr.data)
                    # filtered_nr = filtered_nr.to_csv().encode('utf-8')
                    st.download_button(
                        label="Download Filtered Notes Data as CSV",
                        data=filtered_nr.data.to_csv(),
                        file_name = piece.metadata['title'] + '_notes_results.csv',
                        mime='text/csv',
                        key=1,
                        )
                # for corpus:
                if corpus_length > 1:  
                    st.write("Did you **change the piece list**?  If so, please **Update and Submit form**")
                    nr_no_mdata = filtered_nr.data.drop(['Composer', 'Title', "Date", "Measure", "Beat"], axis=1)
                    nr_no_mdata = nr_no_mdata.map(str)
                    nr_counts = nr_no_mdata.apply(lambda x: x.value_counts(), axis=0).fillna('0').astype(int)
                    nr_counts.index = pd.CategoricalIndex(nr_counts.index, categories=pitch_order, ordered=True)
                    nr_counts = nr_counts.sort_index()
                    nr_counts = nr_counts.drop(index='Rest', errors='ignore')
                    nr_counts = nr_counts[nr_counts.index.notnull()]
                    nr_counts.drop('index', axis=1, inplace=True)         
                    # Show results
                    nr_chart = px.bar(nr_counts, x=nr_counts.index.astype(str).tolist(), y=list(nr_counts.columns), 
                                    title="Distribution of Pitches in " + ', '.join(titles))
                    nr_chart.update_layout(xaxis_title="Pitch", 
                                        yaxis_title="Count",
                                        legend_title='Voices')
                    st.plotly_chart(nr_chart, use_container_width = True)
                    
                    st.dataframe(filtered_nr, use_container_width = True)
            # download option       
                    # csv = convert_df(filtered_nr.data)
                    # filtered_nr_for_csv = filtered_nr.to_csv().encode('utf-8')
                    st.download_button(
                        label="Download Filtered Corpus Notes Data as CSV",
                        data=filtered_nr.data.to_csv(),
                        file_name = 'corpus_notes_results.csv',
                        mime='text/csv',
                        key=2,
                        )
        
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
    return mel

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
    cols_to_move = ['Composer', 'Title', 'Date']
    mel = mel[cols_to_move + [col for col in mel.columns if col not in cols_to_move]]
    return mel

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
                # for one piece
                if corpus_length  == 1: 
                    mel_no_mdata = filtered_mel.data.drop(['Composer', 'Title', "Date", "Measure", "Beat"], axis=1)
                    mel_no_mdata = mel_no_mdata.map(str)
                    mel_counts = mel_no_mdata.apply(lambda x: x.value_counts(), axis=0).fillna('0').astype(int)
                    # apply the categorical list and sort.  
                    if interval_kinds[select_kind] == 'q':
                        mel_counts = mel_counts.drop(index='')
                        mel_counts.index = pd.CategoricalIndex(mel_counts.index, categories=interval_order_quality, ordered=True)
                        mel_counts.sort_index(inplace=True)
                    else:
                        mel_counts = mel_counts.sort_index()
                        mel_counts = mel_counts.drop(index='')
                    mel_counts.index.rename('interval', inplace=True)
                    voices = mel_counts.columns.to_list() 
                    mel_chart = px.bar(mel_counts, x=mel_counts.index, y=list(mel_counts.columns), 
                                        title="Distribution of Melodic Intervals in " + piece.metadata['title'])
                    mel_chart.update_layout(xaxis_title="Interval", 
                                        yaxis_title="Count",
                                        legend_title='Voices')
                    # and show results
                    st.plotly_chart(mel_chart, use_container_width = True)
                    st.dataframe(filtered_mel, use_container_width = True)
                    #csv = convert_df(filtered_mel.data)
                    # filtered_mel = filtered_mel.to_csv().encode('utf-8')
                    st.download_button(
                        label="Download Filtered Melodic Data as CSV",
                        data=filtered_mel.data.to_csv(),
                        file_name = piece.metadata['title'] + '_melodic_results.csv',
                        mime='text/csv',
                        key=3,
                        )
                # # for corpus
                elif corpus_length > 1:
                    mel_no_mdata = filtered_mel.data.drop(['Composer', 'Title', "Date", "Measure", "Beat"], axis=1)
                    mel_no_mdata = mel_no_mdata.map(str)
                    mel_counts = mel_no_mdata.apply(lambda x: x.value_counts(), axis=0).fillna('0').astype(int)
                    # apply the categorical list and sort.  
                    if interval_kinds[select_kind] == 'q':
                        mel_counts = mel_counts.drop(index='')
                        mel_counts.index = pd.CategoricalIndex(mel_counts.index, categories=interval_order_quality, ordered=True)
                        mel_counts.sort_index(inplace=True)
                    else:
                        mel_counts = mel_counts.sort_index()
                        mel_counts = mel_counts.drop(index='')
                    mel_counts.index.rename('interval', inplace=True)
                    voices = mel_counts.columns.to_list() 
                    mel_chart = px.bar(mel_counts, x=mel_counts.index, y=list(mel_counts.columns),
                                        title="Distribution of Melodic Intervals in " + ', '.join(titles))
                    mel_chart.update_layout(xaxis_title="Interval", 
                                        yaxis_title="Count",
                                        legend_title='Voices')
                    # and show results
                    st.plotly_chart(mel_chart, use_container_width = True)
                    st.dataframe(filtered_mel, use_container_width = True)
                    #csv = convert_df(filtered_mel.data)
                    # filtered_mel = filtered_mel.to_csv().encode('utf-8')
                    st.download_button(
                        label="Download Filtered Corpus Melodic Data as CSV",
                        data=filtered_mel.data.to_csv(),
                        file_name = 'corpus_melodic_results.csv',
                        mime='text/csv',
                        key=4,
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
    return har

# @st.cache_data
def corpus_har(corpus, kind_choice, directed, compound, against_low):
    
    func = ImportedPiece.notes  # <- NB there are no parentheses here
    list_of_dfs = corpus.batch(func = func, 
                                kwargs = {'combineUnisons': combine_unisons_choice, 'combineRests': combine_rests_choice}, 
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
    cols_to_move = ['Composer', 'Title', 'Date']
    har = har[cols_to_move + [col for col in har.columns if col not in cols_to_move]]
    return har

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
                # for one piece
                if corpus_length == 1: 
                    har_no_mdata = filtered_har.data.drop(['Composer', 'Title', "Date", "Measure", "Beat"], axis=1)
                    har_no_mdata = har_no_mdata.map(str)
                    har_counts = har_no_mdata.apply(lambda x: x.value_counts(), axis=0).fillna('0').astype(int)
                    # apply the categorical list and sort.  
                    if interval_kinds[select_kind] == 'q':
                        har_counts.index = pd.Categorical(har_counts.index, categories=interval_order_quality, ordered=True)
                        har_counts = har_counts[har_counts.index.notna()]
                        har_counts.sort_index(inplace=True)
                    else:
                        har_counts = har_counts.sort_index()
                        har_counts = har_counts.drop(index=['', 'Rest'])
                    har_counts.index.rename('interval', inplace=True)
                    voices = har_counts.columns.to_list()
                    # set the figure size, type and colors
                    har_chart = px.bar(har_counts, x=har_counts.index, y=list(har_counts.columns), 
                                    title="Distribution of Harmonic Intervals in " + piece.metadata['title'])
                    har_chart.update_layout(xaxis_title="Interval", 
                                        yaxis_title="Count",
                                        legend_title='Voices')
                    # show results
                    st.plotly_chart(har_chart, use_container_width = True)
                    st.dataframe(har_counts, use_container_width = True)
                    #csv = convert_df(filtered_har.data)
                    # filtered_har = filtered_har.to_csv().encode('utf-8')
                    st.download_button(
                        label="Download Filtered Harmonic Data as CSV",
                        data=filtered_har.data.to_csv(),
                        file_name = piece.metadata['title'] + '_harmonic_results.csv',
                        mime='text/csv',
                        key=5,
                        )
                elif corpus_length > 1: 
                    if 'Composer' not in filtered_har.columns:
                        st.write("Did you **change the piece list**? If so, please **Update and Submit form**")
                    else:
                        har_no_mdata = filtered_har.data.drop(['Composer', 'Title', "Date", "Measure", "Beat"], axis=1)
                    har_no_mdata = har_no_mdata.map(str)
                    har_counts = har_no_mdata.apply(lambda x: x.value_counts(), axis=0).fillna('0').astype(int)
                    # apply the categorical list and sort.  
                    if interval_kinds[select_kind] == 'q':
                        har_counts.index = pd.Categorical(har_counts.index, categories=interval_order_quality, ordered=True)
                        har_counts = har_counts[har_counts.index.notna()]
                        har_counts.sort_index(inplace=True)
                    else:
                        har_counts = har_counts.sort_index()
                        har_counts = har_counts.drop(index=['', 'Rest'])
                    har_counts.index.rename('interval', inplace=True)
                    voices = har_counts.columns.to_list()
                        # set the figure size, type and colors
                    har_chart = px.bar(har_counts, x=har_counts.index, y=list(har_counts.columns),
                                    title="Distribution of Harmonic Intervals in " + ', '.join(titles))
                    har_chart.update_layout(xaxis_title="Interval", 
                                        yaxis_title="Count",
                                        legend_title='Voices')
                    # show results
                    st.plotly_chart(har_chart, use_container_width = True)
                    st.dataframe(filtered_har, use_container_width = True)
                    #csv = convert_df(filtered_har.data)
                    # filtered_har = filtered_har.to_csv().encode('utf-8')
                    st.download_button(
                        label="Download Filtered Corpus Harmonic Data as CSV",
                        data=filtered_har.data.to_csv(),
                        file_name = 'corpus_harmonic_results.csv',
                        mime='text/csv',
                        key=6,
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
            st.table(filtered_ngrams)
            # csv = convert_df(filtered_ngrams.data)
            # filtered_ngrams = filtered_ngrams.to_csv().encode('utf-8')
            st.download_button(
                label="Download Filtered Ngram Data as CSV",
                data=filtered_ngrams.data.to_csv(),
                file_name = piece.metadata['title'] + '_ngram_results.csv',
                mime='text/csv',
                key=6,
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
            st.table((filtered_combined_ngrams))
            # csv = convert_df(filtered_combined_ngrams.data)
            # filtered_combined_ngrams = filtered_combined_ngrams.to_csv().encode('utf-8')
            st.download_button(
                label="Download Filtered Corpus Ngram Data as CSV",
                data=filtered_combined_ngrams.data.to_csv(),
                file_name = 'corpus_ngram_results.csv',
                mime='text/csv',
                key=7,
                )            
# hr functions
# one piece
# @st.cache_data
# def piece_homorhythm(piece, length_choice, full_hr_choice):
#     hr = piece.homorhythm(ngram_length=length_choice, 
#                     full_hr=full_hr_choice)
#     # Check if hr is None or empty
#     if hr is None or hr.empty:
#         # Define the required columns
#         columns_to_keep = ['active_voices', 'number_dur_ngrams', 'hr_voices', 'syllable_set',  
#            'count_lyr_ngrams', 'active_syll_voices', 'voice_match']
#         # Return an empty DataFrame with the required columns
#         return pd.DataFrame(columns=columns_to_keep)
#     # fix update error for type
#     hr.fillna(0, inplace=True)
#     # voices_list = list(piece.notes().columns)
#     # hr[voices_list] = hr[voices_list].map(convertTuple).fillna('-')
#     columns_to_keep = ['active_voices', 'number_dur_ngrams', 'hr_voices', 'syllable_set', 
#            'count_lyr_ngrams', 'active_syll_voices', 'voice_match']
#     hr = hr.drop(columns=[col for col in hr.columns if col not in columns_to_keep])
#     hr['hr_voices'] = hr['hr_voices'].apply(', '.join)
#     hr['syllable_set'] = hr['syllable_set'].apply(lambda x: ''.join(map(str, x[0]))).copy()
#     # hr = piece.emaAddresses(df=hr, mode='h')
#     hr = hr.reset_index()
#     hr = hr.assign(Composer=piece.metadata['composer'], Title=piece.metadata['title'], Date=piece.metadata['date'])
#     cols_to_move = ['Composer', 'Title', 'Date']
#     hr = hr[cols_to_move + [col for col in hr.columns if col not in cols_to_move]]

#     return hr
# # orpus
# # @st.cache_data
# def corpus_homorhythm(corpus, length_choice, full_hr_choice):
#     func = ImportedPiece.homorhythm
#     list_of_dfs = corpus.batch(func = func,
#                                kwargs = {'ngram_length' : length_choice, 'full_hr' : full_hr_choice},
#                                metadata = True)
#     # func2 = ImportedPiece.emaAddresses
#     # list_of_hr_with_ema = corpus.batch(func = func2,
#     #                                    kwargs = {'df': list_of_dfs, 'mode' : 'h'},
#     #                                    metadata = True)
# #
#     # Filter out DataFrames with zero length
#     list_of_dfs = [df for df in list_of_dfs if df is not None and len(df) >  0]
#     rev_list_of_dfs = [df.reset_index() for df in list_of_dfs]
#     if len(rev_list_of_dfs) > 0:
#         hr = pd.concat(rev_list_of_dfs)
#         # voices_list = list(piece.notes().columns)
#         # hr[voices_list] = hr[voices_list].map(convertTuple).fillna('-')
#         columns_to_keep = ['active_voices', 'number_dur_ngrams', 'hr_voices', 'syllable_set', 
#             'count_lyr_ngrams', 'active_syll_voices', 'voice_match', 'Composer', 'Title', 'Date']
#         hr = hr.drop(columns=[col for col in hr.columns if col not in columns_to_keep])
#         hr['hr_voices'] = hr['hr_voices'].apply(', '.join)
#         hr['syllable_set'] = hr['syllable_set'].apply(lambda x: ''.join(map(str, x[0]))).copy()
#         cols_to_move = ['Composer', 'Title', 'Date']
#         hr = hr[cols_to_move + [col for col in hr.columns if col not in cols_to_move]]
#         return hr

# HR form--now commented out for Ditigal Ocean
# if st.sidebar.checkbox("Explore Homorhythm"):
#     search_type = "other"
#     st.subheader("Explore Homorhythm")
#     st.write("[Know the code! Read more about the CRIM Intervals homorhythm method](https://github.com/HCDigitalScholarship/intervals/blob/main/tutorial/10_Lyrics_Homorhythm.md)", unsafe_allow_html=True)

#     with st.form("Homorhythm Settings"):
#         full_hr_choice = st.selectbox(
#             "Select HR Full Status",
#             [True, False])
#         length_choice = st.number_input('Select ngram Length', value=4, step=1)
#         submitted = st.form_submit_button("Update and Submit")
#         if submitted:
#             if 'hr' in st.session_state:
#                 del st.session_state.hr
#             if corpus_length == 0:
#                 st.write("Please select one or more pieces")
#             elif corpus_length == 1:
#                  hr = piece_homorhythm(st.session_state.piece, length_choice, full_hr_choice)
#             elif corpus_length > 1:
#                  hr = corpus_homorhythm(st.session_state.corpus, length_choice, full_hr_choice)
#             if "hr" not in st.session_state:
#                 st.session_state.hr = hr
# # and use the session state variables for display
#     if 'hr' not in st.session_state:
#         pass
#     else:
#         st.write("Did you **change the piece list**?  If so, please **Update and Submit form**")
#         st.write("Filter Results by Contents of Each Column")
#         filtered_hr = filter_dataframe_hr(st.session_state.hr.fillna('-'))
#         st.dataframe(filtered_hr, use_container_width = True)
#         # csv = convert_df(filtered_hr)
#         if corpus_length == 1:
#             download_name = piece.metadata['title'] + '_homorhythm_results.csv'
#         elif corpus_length > 1:
#             download_name = "corpus_homorhythm_results.csv"
#         # filtered_hr = filtered_hr.to_csv().encode('utf-8')
#         st.download_button(
#             label="Download Filtered Homorhythm Data as CSV",
#             data=filtered_hr.to_csv(),
#             file_name = download_name,
#             mime='text/csv',
#             key=8,
#             ) 
        
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
                    key=8,
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
                    key=9,
                    )
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
    # the full table of cad
        if st.checkbox("Show Full Cadence Table"):
            cadences = piece.cadences()
            st.subheader("Detailed View of Cadences")
            filtered_cadences = filter_dataframe_cads(cadences)
            st.dataframe(filtered_cadences, use_container_width = True)
            # to download csv
            download_name = piece.metadata['title'] + '_cadence_results.csv'
            st.download_button(
                label="Download Filtered Cadence Data as CSV",
                data=filtered_cadences.to_csv(),
                file_name = download_name,
                key=10,
                mime='text/csv')
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
            st.subheader("Basic Progress Plot")    
            progress = piece.cadenceProgressPlot(includeType=False, renderer='streamlit')
            st.pyplot(progress, use_container_width=True)
        if st.checkbox("Show Advanced Progress Plot"):
            st.subheader("Advanced Progress Plot")    
            progress = piece.cadenceProgressPlot(includeType=True, renderer='streamlit')
            st.pyplot(progress, use_container_width=True)
    # corpus
    elif corpus_length >= 2:
        func = ImportedPiece.cadences
        if func:
            list_of_dfs = st.session_state.corpus.batch(func=func, kwargs={'keep_keys': True}, metadata=True)
            cadences = pd.concat(list_of_dfs, ignore_index=False)   
            cols_to_move = ['Composer', 'Title', 'Date']
            cadences = cadences[cols_to_move + [col for col in cadences.columns if col not in cols_to_move]] 
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
                    key=11,
                    )
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
                st.dataframe(soggetto_cross_plot)
                fig = px.imshow(soggetto_cross_plot, color_continuous_scale="YlGnBu", aspect="auto")
                st.plotly_chart(fig)
            else:
                pass
   
