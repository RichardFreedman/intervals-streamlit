import streamlit as st
from pathlib import Path
import requests
from requests.sessions import DEFAULT_REDIRECT_LIMIT
import base64
import verovio
import os
# from streamlit import caching
import requests
import re

import intervals
from intervals import * 
from intervals import main_objs
import intervals.visualizations as viz
import pandas as pd
import re
import altair as alt 
from ipywidgets import interact
from pandas.io.json import json_normalize
from pyvis.network import Network
import glob as glob
import os
from IPython.display import SVG
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.figure_factory as ff

import streamlit.components.v1 as components

from os import listdir 
import os.path 

path = '/Users/rfreedma/Documents/CRIM_Python/crim-local/CRIM-online/crim/static/mei/MEI_4.0'
file_list = os.listdir(path) 
piece_list = [ ] 
for file in file_list: 
    name = path + "/" + file 
    piece_list.append(name)

first_piece = file_list[0]
piece = path + "/" + file 


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

# select a piece
piece_name = st.sidebar.selectbox('Select Piece To View', file_list)
st.title("CRIM Intervals")
st.header("Scores | Patterns | Plots")
# display name of selected piece
st.sidebar.write('You selected:', piece_name)

# and create full URL to use in the Verovio html block below
filepath = path + "/" + piece_name
piece = importScore(filepath)

show_score_checkbox = st.sidebar.checkbox('Show/Hide Score')

# menu dictionaries

interval_kinds = {'diatonic' : 'd',
                 'chromatic' : 'c',
                 'with quality' : 'q',
                 'zero-based diatonic' : 'z'}

unison_status = {'Separate Unisons' : False,
                 'Combine Unisons' : True}

rest_status = {'Combine Rests' : True,
                 ' Separate Rests' : False}

length_choice = st.sidebar.number_input('Select NGram Length', value=5, step=1)

# sidebar for notes/rests

notes_menu = st.sidebar.checkbox("Explore Notes and Rests")

if notes_menu:

    # metadata about piece
    st.subheader("Selected Piece")
    st.write(piece_name)
    st.write(piece.metadata['composer'] + " :" + piece.metadata['title'])

    st.subheader("Select Notes Search Criteria")

    select_combine_unisons = st.selectbox(
        "Select Unison Status",
        ["Separate Unisons", "Combine Unisons"])
    select_combine_rests = st.selectbox(
        "Select Rest Status",
        ["Combine Rests", "Separate Rests"])
    
    st.subheader("Run Notes and Rests Search")
    notes_button = st.button("Get Notes and Rests")

    if notes_button:
       
        notes_rests = piece.notes(combineUnisons = unison_status[select_combine_unisons],
                              combineRests = rest_status[select_combine_rests]).fillna('')
        
        if 'notes_rests' not in st.session_state:
            st.session_state.notes_rests = notes_rests
        
        notes_rests_results = piece.detailIndex(notes_rests).fillna('')
        st.write(notes_rests_results)

        pitch_order = ['E-2', 'E2', 'F2', 'F#2', 'G2', 'A2', 'B-2', 'B2', 
                'C3', 'C#3', 'D3', 'E-3','E3', 'F3', 'F#3', 'G3', 'G#3','A3', 'B-3','B3',
                'C4', 'C#4','D4', 'E-4', 'E4', 'F4', 'F#4','G4', 'A4', 'B-4', 'B4',
                'C5', 'C#5','D5', 'E-5','E5', 'F5', 'F#5', 'G5', 'A5', 'B-5', 'B5']
        
        # %matplotlib inline  
        nr = piece.notes().fillna('-')  
        nr = nr.apply(pd.Series.value_counts).fillna(0).astype(int).reset_index().copy()  
        nr.rename(columns = {'index':'pitch'}, inplace = True)  
        nr['pitch'] = pd.Categorical(nr["pitch"], categories=pitch_order)  
        nr = nr.sort_values(by = "pitch").dropna().copy()
        voices = nr.columns.to_list()   
        md = piece.metadata  
        for key, value in md.items():  
            st.write(key, ':', value)
        # Stacked bar chart using plotly
        pitch_chart = px.bar(nr, x="pitch", y=voices, title="Distribution of Pitches in This Piece")
        st.plotly_chart(pitch_chart)


# sidebar for melodic menu
melodic_menu = st.sidebar.checkbox("Explore Melodic Intervals")

if melodic_menu:
    # metadata about piece
    st.subheader("Selected Piece")
    st.write(piece_name)
    st.write(piece.metadata['composer'] + " :" + piece.metadata['title'])

    st.subheader("Select Melodic Intervals Search Criteria")
    # the selection menu
    select_kind = st.selectbox(
        "Select Interval Kind", 
        ["diatonic", "chromatic", "with quality", "zero-based diatonic"])
    # passing result of selection menu to dictionary of kinds; result to mel below
    kind_choice = interval_kinds[select_kind]

    # option to use results of notes/rests
    use_notes_rests_settings = st.checkbox("Use Settings from Notes and Rests Search")

    st.subheader("Run Melodic Interval Search")
    melodic_button = st.button("Get Melodic Intervals")

    if melodic_button:
        st.subheader("Results")
        # option to use settings from NR
        if use_notes_rests_settings:
            notes_rests = piece.notes(combineUnisons = unison_status[select_combine_unisons],
                              combineRests = rest_status[select_combine_rests])
            mel = piece.melodic(df = notes_rests, kind= kind_choice).fillna('')
            st.dataframe(mel)

            int_order = ["P1", "m2", "-m2", "M2", "-M2", "m3", "-m3", "M3", "-M3", "P4", "-P4", "P5", "-P5", 
                    "m6", "-m6", "M6", "-M6", "m7", "-m7", "M7", "-M7", "P8", "-P8"]
            # count up the values in each item column--sum for each pitch.  
            # make a copy 
            mel = piece.melodic()
            mel = mel.fillna("-")
            # count up the values in each item column--sum for each pitch.  
            # make a copy 
            mel = mel.apply(pd.Series.value_counts).fillna(0).astype(int).reset_index().copy()
            # rename the index column to something more useful
            mel.rename(columns = {'index':'interval'}, inplace = True)
            # mel.index.rename('interval', inplace=True)
            # apply the categorical list and sort
            mel['interval'] = pd.Categorical(mel["interval"], categories=int_order)
            mel = mel.sort_values(by = "interval").dropna().copy()
            mel.index.rename('interval', inplace=True)
            voices = mel.columns.to_list()
            # # # set the figure size, type and colors
            fig = px.bar(mel, x="interval", y=voices, title="Distribution of Intervals in This Piece")
            st.plotly_chart(fig)  
           

            # st.subheader("Interval Summary")       
            # st.write(mel.stack().value_counts())
    #       

    
        else:
            notes_rests = piece.notes()
            mel = piece.melodic(df = notes_rests, kind= kind_choice).fillna('')
            st.dataframe(mel)

            int_order = ["P1", "m2", "-m2", "M2", "-M2", "m3", "-m3", "M3", "-M3", "P4", "-P4", "P5", "-P5", 
                    "m6", "-m6", "M6", "-M6", "m7", "-m7", "M7", "-M7", "P8", "-P8"]
            # count up the values in each item column--sum for each pitch.  
            # make a copy 
            mel = piece.melodic()
            mel = mel.fillna("-")
            # count up the values in each item column--sum for each pitch.  
            # make a copy 
            mel = mel.apply(pd.Series.value_counts).fillna(0).astype(int).reset_index().copy()
            # rename the index column to something more useful
            mel.rename(columns = {'index':'interval'}, inplace = True)
            # mel.index.rename('interval', inplace=True)
            # apply the categorical list and sort
            mel['interval'] = pd.Categorical(mel["interval"], categories=int_order)
            mel = mel.sort_values(by = "interval").dropna().copy()
            mel.index.rename('interval', inplace=True)
            voices = mel.columns.to_list()
            # # # set the figure size, type and colors
            fig = px.bar(mel, x="interval", y=voices, title="Distribution of Intervals in This Piece")
            st.plotly_chart(fig)    

            # st.subheader("Interval Summary")       
            # st.write(mel.stack().value_counts())
        # chart
int_order = ["P1", "m2", "-m2", "M2", "-M2", "m3", "-m3", "M3", "-M3", "P4", "-P4", "P5", "-P5", 
                    "m6", "-m6", "M6", "-M6", "m7", "-m7", "M7", "-M7", "P8", "-P8"]
# count up the values in each item column--sum for each pitch.  
# make a copy 
# mel = piece.melodic()
# mel = mel.fillna("-")
# # count up the values in each item column--sum for each pitch.  
# # make a copy 
# mel = mel.apply(pd.Series.value_counts).fillna(0).astype(int).reset_index().copy()
# # rename the index column to something more useful
# mel.rename(columns = {'index':'interval'}, inplace = True)
# # mel.index.rename('interval', inplace=True)
# # apply the categorical list and sort
# mel['interval'] = pd.Categorical(mel["interval"], categories=int_order)
# mel = mel.sort_values(by = "interval").dropna().copy()
# mel.index.rename('interval', inplace=True)
# voices = mel.columns.to_list()
# # # # set the figure size, type and colors
# fig = px.bar(mel, x="interval", y=voices, title="Distribution of Intervals in This Piece")
# st.plotly_chart(fig)


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
        fetch('"""+filepath+"""')
            .then(function(response) {
                return response.text();
            })
            .then(function(text) {
                app.loadData(text);
            });
    </script>
        """,
        height=800,
        width=850,
    )
# FALSE shows a blank bit of HTML
else:
    components.html(
        
        """
        <div class="panel-body">
        """,
        height=1,
        width=850,
    )
# st.sidebar.write('You selected:', piece)
st.sidebar.subheader("Explore Cadences")
# the full table of cad
if st.sidebar.checkbox("Show Full Cadence Table"):
    cadences = piece.cadences()
    st.subheader("Detailed View of Cadences")
    cadences
# summary of tone and type
if st.sidebar.checkbox("Summary of Cadences by Tone and Type"):
    cadences = piece.cadences()
    grouped = cadences.groupby(['Tone', 'CadType']).size().reset_index(name='counts')
    st.subheader("Summary of Cadences by Tone and Type")
    grouped
# radar plots
if st.sidebar.button("Show Basic Radar Plot"):
    st.subheader("Basic Radar Plot")    
    radar = piece.cadenceRadarPlot(combinedType=False, displayAll=False, renderer='streamlit')
    st.plotly_chart(radar, use_container_width=True)
if st.sidebar.button("Show Advanced Radar Plot"):
    st.subheader("Advanced Radar Plot")    
    radar = piece.cadenceRadarPlot(combinedType=True, displayAll=True, renderer='streamlit')
    st.plotly_chart(radar, use_container_width=True)

# import streamlit as st

# selected_option = st.session_state.get("selected_option", "")

# option1 = st.selectbox("Option 1", options=["Option 1A", "Option 1B"])
# option2 = st.selectbox("Option 2", options=["Option 2A", "Option 2B"])

# selected_option = selected_option + ", " + option1 + ", " + option2

# st.write(f"Selected options: {selected_option}")
# df = st.session_state.notes_rests.fillna('nothing')
# df = df.replace(to_replace='^-$', value=np.nan, regex=True)
# st.write(df)

