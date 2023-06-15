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


crim_url = 'https://crimproject.org/data/pieces/'
all_pieces_json = requests.get(crim_url).json()
json_str = json.dumps(all_pieces_json)
json_objects = json.loads(json_str)

# fun function to make list of pieces
piece_list = make_piece_list(json_objects)

composer_title_list = make_composer_title_list(json_objects)

# select a piece
# piece_id = st.selectbox('Select Piece To View', composer_title_list)

st.title("CRIM Intervals")
piece_name = st.selectbox('Select Piece To View', piece_list)


crim_view = 'https://crimproject.org/pieces/' + piece_name

# based on selected piece, get the mei file link and import it
filepath = find_mei_link(piece_name, json_objects)
piece = importScore(filepath)

# load mei data from GIT
mei_git_link = "https://raw.githubusercontent.com/CRIM-Project/CRIM-online/master/crim/static/mei/MEI_4.0/" + piece_name + ".mei"

# load mei for verovio from CRIM

# mei_link = 'https://crimproject.org/mei/CRIM_Model_0001.mei'
# r = requests.get(filepath)
# with open(piece_name + '.mei', 'r') as f:
#     data = f.read()


# display file name and metadata

st.subheader("Selected Piece")
st.write(piece_name)
st.write(piece.metadata['composer'] + ': ' + piece.metadata['title'])
st.write('View Piece on CRIM: ' + crim_view)
show_score_checkbox = st.checkbox('Show/Hide Score with Verovio')

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

# filter function

# filter function
st.cache_data(experimental_allow_widgets=True)
def filter_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a UI on top of a dataframe to let viewers filter columns

    Args:
        df (pd.DataFrame): Original dataframe

    Returns:
        pd.DataFrame: Filtered dataframe
    """
    # modify = st.checkbox("Filter Results", key='filter')

    # if not modify:
    #     return df

    df = df.copy()

    # Try to convert datetimes into a standard format (datetime, no timezone)
    for col in df.columns:
        if is_object_dtype(df[col]):
            try:
                df[col] = pd.to_datetime(df[col])
            except Exception:
                pass

        if is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.tz_localize(None)

    modification_container = st.container()

    with modification_container:
        to_filter_columns = st.multiselect("Filter dataframe on", df.columns)
        for column in to_filter_columns:
            left, right = st.columns((1, 20))
            left.write("↳")
            # Treat columns with < 10 unique values as categorical
            if is_categorical_dtype(df[column]) or df[column].nunique() < 10:
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
            elif is_datetime64_any_dtype(df[column]):
                user_date_input = right.date_input(
                    f"Values for {column}",
                    value=(
                        df[column].min(),
                        df[column].max(),
                    ),
                )
                if len(user_date_input) == 2:
                    user_date_input = tuple(map(pd.to_datetime, user_date_input))
                    start_date, end_date = user_date_input
                    df = df.loc[df[column].between(start_date, end_date)]
            else:
                user_text_input = right.text_input(
                    f"Substring or regex in {column}",
                )
                if user_text_input:
                    df = df[df[column].str.contains(user_text_input)]

    return df

# download function

@st.cache_data
def convert_df(filtered):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return filtered.to_csv().encode('utf-8')

# plot functions

#  

# notes bar chart
def notes_bar_chart(_piece, combine_unisons_choice, combine_rests_choice):
    nr = piece.notes(combineUnisons = combine_unisons_choice,
                              combineRests = combine_rests_choice)
    nr_counts = nr.apply(pd.Series.value_counts).fillna(0).astype(int).reset_index().copy()  
    nr_counts.rename(columns = {'index':'pitch'}, inplace = True)  
    nr_counts['pitch'] = pd.Categorical(nr_counts["pitch"], categories=pitch_order)  
    nr_counts = nr_counts.sort_values(by = "pitch").dropna().copy()

    voices = nr.columns.to_list()   
    # Stacked bar chart using plotly
    nr = nr.fillna('-')
    nr_filtered = filter_dataframe(nr)
    st.write(nr_filtered)
    pitch_chart = px.bar(nr_counts, x="pitch", y=voices, title="Distribution of Pitches in " + piece_name)
    st.plotly_chart(pitch_chart, use_container_width = True)

    # return nr, pitch_chart

# melodic interval bar chart

def mel_interval_bar_chart(_piece, combine_unisons_choice, combine_rests_choice, kind_choice, directed, compound):
    nr = piece.notes(combineUnisons = combine_unisons_choice,
                              combineRests = combine_rests_choice)
    mel = piece.melodic(df = nr, 
                        kind = kind_choice,
                        directed = directed,
                        compound = compound)#.fillna('')
    # count up the values in each item column--sum for each pitch.  
    # make a copy 
    mel_counts = mel.apply(pd.Series.value_counts).fillna(0).astype(int).reset_index().copy()
    # rename the index column to something more useful
    mel_counts.rename(columns = {'index':'interval'}, inplace = True)
    # apply the categorical list and sort.  
    if interval_kinds[select_kind] == 'q':
        mel_counts['interval'] = pd.Categorical(mel_counts["interval"], categories=interval_order_quality)
    mel_counts = mel_counts.sort_values(by = "interval").dropna().copy()
    mel_counts.index.rename('interval', inplace=True)
    voices = mel.columns.to_list()

    # set the figure size, type and colors
    fig = px.bar(mel_counts, x="interval", y=voices, title="Distribution of Melodic Intervals in " + piece_name)
    # st.plotly_chart(fig, use_container_width = True)
    return mel, fig

    

# function for harmonic bar chart

def har_interval_bar_chart(_piece, directed, compound, kind_choice):
    har = piece.harmonic(kind = kind_choice, 
                         directed = directed,
                         compound = compound).fillna('')
    # count up the values in each item column--sum for each pitch. make a copy 
    har = har.apply(pd.Series.value_counts).fillna(0).astype(int).reset_index().copy()
    # rename the index column to something more useful
    har.rename(columns = {'index':'interval'}, inplace = True)
    # apply the categorical list and sort.  
    if interval_kinds[select_kind] == 'q':
        har['interval'] = pd.Categorical(har["interval"], categories=interval_order_quality)
    har = har.sort_values(by = "interval").dropna().copy()
    har.index.rename('interval', inplace=True)
    voices = har.columns.to_list()
    # # # set the figure size, type and colors
    fig = px.bar(har, x="interval", y=voices, title="Distribution of Harmonic Intervals in " + piece_name)
    st.plotly_chart(fig, use_container_width = True)  

# function for ngram heatmap

def ngram_heatmap(_piece, combine_unisons_choice, kind_choice, directed, compound, length_choice):
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
                                    anywhere = True)

        # pass the ngram durations below to the plot as second df
        entry_ngrams_duration = piece.durations(df = mel, 
                                            n =length_choice, 
                                            mask_df = entry_ngrams)
        # make the heatmap
        entry_ng_heatmap = viz.plot_ngrams_heatmap(entry_ngrams, 
                                         entry_ngrams_duration, 
                                         selected_patterns=[], 
                                         voices=[], 
                                         heatmap_width= 1000,
                                         heatmap_height=300, 
                                         includeCount=True)
        # rename entry_ngrams df as mel_ngrams for display
        entry_ngrams_detail = piece.detailIndex(entry_ngrams, offset = True)
        # display the results
        st.subheader("Table of Ngrams for " + piece_name)
        st.dataframe(entry_ngrams_detail, use_container_width = True)
        st.subheader("Ngram Heatmap for " + piece_name)
        st.altair_chart(entry_ng_heatmap, use_container_width = True)
    # this is for all mel ngrams (iof entries is False in form)
    else:
        mel_ngrams = piece.ngrams(df = mel, n = length_choice)

        mel_ngrams_duration = piece.durations(df = mel, 
                                          n =length_choice)
        
        ng_heatmap = viz.plot_ngrams_heatmap(mel_ngrams, 
                                         mel_ngrams_duration, 
                                         selected_patterns=[], 
                                         voices=[], 
                                         heatmap_width = 1000,
                                         heatmap_height=300, 
                                         includeCount=True)
        
        mel_ngrams_detail = piece.detailIndex(mel_ngrams, offset = True)  
        # display the results
        st.dataframe(mel_ngrams_detail, use_container_width = True)
        st.altair_chart(ng_heatmap, use_container_width = True)

# score tool
# TRUE shows the score


if show_score_checkbox:
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

        fetch('"""+mei_git_link+"""')
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

# FALSE shows a blank bit of HTML
else:
    components.html(
        
        """
        <div class="panel-body">
        """,
        height=1,
        # width=850,
    ) 
# +++++++++++++++++++++
# this all works
# nr = piece.notes().fillna('-')

# filtered = filter_dataframe(nr)

# st.dataframe(filtered)



# csv = convert_df(filtered)

# st.download_button(
#     label="Download data as CSV",
#     data=csv,
#     file_name='large_df.csv',
#     mime='text/csv',
# )


# +++++++++++++++++++++
# form for notes

if st.sidebar.checkbox("Explore Notes"):

    st.subheader("Explore Notes")

    with st.form("Note Settings"):
        combine_unisons_choice = st.selectbox(
            "Combine Unisons", [False, True])
        combine_rests_choice = st.selectbox(
            "Combine Rests", [True, False])
        # form submission button
        submitted = st.form_submit_button("Submit")
        if submitted:
            # run the function here, passing in settings from the form above
            notes_output = notes_bar_chart(piece,
                            combine_unisons_choice, 
                            combine_rests_choice)
        # if len(notes_output[0]) is not None:
        #     nr_filtered = filter_dataframe(notes_output[0])
        #     st.write(nr_filtered)
        #     # st.dataframe(notes_output[0], use_container_width = True)
        # # if notes_output[1] is not None:
        # st.plotly_chart(notes_output[1], use_container_width = True)

# form for melodic
if st.sidebar.checkbox("Explore Melodic Intervals"):
    st.subheader("Explore Melodic Intervals")

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
            for key in st.session_state.keys():
                del st.session_state[key]
            mel, fig = mel_interval_bar_chart(piece, 
                                    combine_unisons_choice, 
                                    combine_rests_choice, 
                                    kind_choice,
                                    directed,
                                    compound)
            # Set up session state for these returns
            if 'fig' not in st.session_state:
                st.session_state.fig = fig
            if 'mel' not in st.session_state:
                st.session_state.mel = mel
 
    if 'fig' not in st.session_state:
        pass# and use the session state variables for display
    else:
        st.plotly_chart(st.session_state.fig, use_container_width = True)
    if 'mel' not in st.session_state:
        pass
    else:
        filtered = filter_dataframe(st.session_state.mel.fillna('-'))
        st.dataframe(filtered, use_container_width = True)
        csv = convert_df(filtered)
        st.download_button(
            label="Download Filtered Data as CSV",
            data=csv,
            file_name = piece_name + '_melodic_results.csv',
            mime='text/csv',
            )

# form for harmonic
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
        # form submission button
        submitted = st.form_submit_button("Submit")
        if submitted:
            # run the function here, passing in settings from the form above
            har_interval_bar_chart(piece, 
                                directed,
                                compound, 
                                kind_choice)
# ngram form
if st.sidebar.checkbox("Explore ngrams"):
    st.subheader("Explore nGrams")
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
        # submit ngram form
        submitted = st.form_submit_button("Submit")
        if submitted:
            ngram_heatmap(piece, 
                          combine_unisons_choice, 
                          kind_choice, 
                          directed, 
                          compound, 
                          length_choice)
# cadence form
if st.sidebar.checkbox("Explore Cadences"):
    st.subheader("Explore Cadences")
    # the full table of cad
    if st.checkbox("Show Full Cadence Table"):
        cadences = piece.cadences()
        st.subheader("Detailed View of Cadences")
        cadences
    # summary of tone and type
    if st.checkbox("Summary of Cadences by Tone and Type"):
        cadences = piece.cadences()
        grouped = cadences.groupby(['Tone', 'CadType']).size().reset_index(name='counts')
        st.subheader("Summary of Cadences by Tone and Type")
        grouped
    # radar plots
    if st.button("Show Basic Radar Plot"):
        st.subheader("Basic Radar Plot")    
        radar = piece.cadenceRadarPlot(combinedType=False, displayAll=False, renderer='streamlit')
        st.plotly_chart(radar, use_container_width=True)
    if st.button("Show Advanced Radar Plot"):
        st.subheader("Advanced Radar Plot")    
        radar = piece.cadenceRadarPlot(combinedType=True, displayAll=True, renderer='streamlit')
        st.plotly_chart(radar, use_container_width=True)


if st.sidebar.checkbox("Explore Homorhythm"):
    st.subheader("Explore Homorhythm")

if st.sidebar.checkbox("Explore Presentation Types"):
    st.subheader("Explore Presentation Types")

