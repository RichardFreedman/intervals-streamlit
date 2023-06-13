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
from pandas.io.json import json_normalize
from pyvis.network import Network
import glob as glob
from IPython.display import SVG
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.figure_factory as ff
import streamlit.components.v1 as components
from os import listdir 
import os.path 

# local pieces for dev
# raw_prefix = '/Users/rfreedma/Documents/CRIM_Python/crim-local/CRIM-online/crim/static/mei/MEI_4.0'
# file_list = os.listdir(raw_prefix) 
# piece_list = [ ] 
# for file in file_list: 
#     name = raw_prefix + "/" + file 
#     piece_list.append(file)
#     piece_list = sorted(piece_list)

# all pieces on git:
piece_list = []
raw_prefix = "https://raw.githubusercontent.com/CRIM-Project/CRIM-online/master/crim/static/mei/MEI_4.0/"
URL = "https://api.github.com/repos/CRIM-Project/CRIM-online/git/trees/990f5eb3ff1e9623711514d6609da4076257816c"
piece_json = requests.get(URL).json()
# pattern to filter out empty header Mass files
pattern = 'CRIM_Mass_([0-9]{4}).mei'

# and now the request for all the files
for p in piece_json["tree"]:
    p_name = p["path"]
    if re.search(pattern, p_name):
        pass
    else:
        piece_list.append(p_name)
        piece_list = sorted(piece_list)

# select a piece
piece_name = st.selectbox('Select Piece To View', piece_list)
st.title("CRIM Intervals")

# # and create full URL to use in the Verovio html block below
filepath = raw_prefix + "/" + piece_name
piece = importScore(filepath)

# display file name and metadata
st.write(piece_name)
st.write(piece.metadata['composer'])
st.write(piece.metadata['title'])

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

interval_order_quality = ["-P8", "-M7", "-m7", "-M6", "-m6", "-P5", "-P4", "-M3", 
                          "-m3", "-M2", "-m2", "P1", "m2", "M2", "m3", "M3",
                          "P4", "P5", "m6", "M6", "m7", "M7", "P8"]

# interval_order_quality = ["-P8", "m2", "-m2", "M2", "-M2", "m3", "-m3", "M3", "-M3", "P4", "-P4", "P5", "-P5", 
#             "m6", "-m6", "M6", "-M6", "m7", "-m7", "M7", "-M7", "P8", "-P8"]

pitch_order = ['E-2', 'E2', 'F2', 'F#2', 'G2', 'A2', 'B-2', 'B2', 
                'C3', 'C#3', 'D3', 'E-3','E3', 'F3', 'F#3', 'G3', 'G#3','A3', 'B-3','B3',
                'C4', 'C#4','D4', 'E-4', 'E4', 'F4', 'F#4','G4', 'A4', 'B-4', 'B4',
                'C5', 'C#5','D5', 'E-5','E5', 'F5', 'F#5', 'G5', 'A5', 'B-5', 'B5']

# plot functions

# notes bar chart
def notes_bar_chart(piece, combine_unisons_choice, combine_rests_choice):
    nr = piece.notes(combineUnisons = combine_unisons_choice,
                              combineRests = combine_rests_choice)
    nr = nr.apply(pd.Series.value_counts).fillna(0).astype(int).reset_index().copy()  
    nr.rename(columns = {'index':'pitch'}, inplace = True)  
    nr['pitch'] = pd.Categorical(nr["pitch"], categories=pitch_order)  
    nr = nr.sort_values(by = "pitch").dropna().copy()
    voices = nr.columns.to_list()   
    # Stacked bar chart using plotly
    pitch_chart = px.bar(nr, x="pitch", y=voices, title="Distribution of Pitches in " + piece_name)
    st.plotly_chart(pitch_chart, use_container_width = True)

# melodic interval bar chart
def mel_interval_bar_chart(piece, combine_unisons_choice, combine_rests_choice, kind_choice, directed, compound):
    nr = piece.notes(combineUnisons = combine_unisons_choice,
                              combineRests = combine_rests_choice)
    mel = piece.melodic(df = nr, 
                        kind = kind_choice,
                        directed = directed,
                        compound = compound)#.fillna('')
    # count up the values in each item column--sum for each pitch.  
    # make a copy 
    mel = mel.apply(pd.Series.value_counts).fillna(0).astype(int).reset_index().copy()
    # rename the index column to something more useful
    mel.rename(columns = {'index':'interval'}, inplace = True)
    # apply the categorical list and sort.  
    if interval_kinds[select_kind] == 'q':
        mel['interval'] = pd.Categorical(mel["interval"], categories=interval_order_quality)
    mel = mel.sort_values(by = "interval").dropna().copy()
    mel.index.rename('interval', inplace=True)
    voices = mel.columns.to_list()
    # set the figure size, type and colors
    fig = px.bar(mel, x="interval", y=voices, title="Distribution of Melodic Intervals in " + piece_name)
    st.plotly_chart(fig, use_container_width = True)

def har_interval_bar_chart(piece, directed, compound, kind_choice):
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

def ngram_heatmap(piece, combine_unisons_choice, kind_choice, directed, compound, length_choice):
    # find entries for model
    nr = piece.notes(combineUnisons = combine_unisons_choice)
    mel = piece.melodic(df = nr, 
                        kind = kind_choice,
                        directed = directed,
                        compound = compound,
                        end = False)
    
    mel_ngrams = piece.ngrams(df = mel, n = length_choice)

    # pass the following ngrams to the plot below as first df
    entry_ngrams = piece.entries(df = mel, 
                                 n = length_choice, 
                                 thematic = True, 
                                 anywhere = True)

    # pass the ngram durations below to the plot as second df
    mel_ngrams_duration = piece.durations(df = mel, 
                                          n =length_choice, 
                                          mask_df = entry_ngrams)
    # this is for entries only
    if entries_only == True:    
        ng_heatmap = viz.plot_ngrams_heatmap(entry_ngrams, 
                                         mel_ngrams_duration, 
                                         selected_patterns=[], 
                                         voices=[], 
                                         heatmap_width= 1000,
                                         heatmap_height=300, 
                                         includeCount=True)
        # rename entry_ngrams df as mel_ngrams for display
        mel_ngrams = piece.detailIndex(entry_ngrams, offset = True)
        # display the results
        st.subheader("Table of Ngrams for " + piece_name)
        st.dataframe(mel_ngrams, use_container_width = True)
        st.subheader("Ngram Heatmap for " + piece_name)
        st.altair_chart(ng_heatmap, use_container_width = True)
    # this is for all mel ngrams (iof entries is False in form)
    else:
        mel_ngrams = piece.ngrams(interval_settings = (kind_choice, directed, compound), 
                                  n = length_choice)  
        
        mel_ngrams = piece.detailIndex(mel_ngrams, offset = True)
        
        ng_heatmap = viz.plot_ngrams_heatmap(mel_ngrams, 
                                         mel_ngrams_duration, 
                                         selected_patterns=[], 
                                         voices=[], 
                                         heatmap_width = 1000,
                                         heatmap_height=300, 
                                         includeCount=True)
        
        # display the results
        st.dataframe(mel_ngrams, use_container_width = True)
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
            notes_bar_chart(piece,
                            combine_unisons_choice, 
                            combine_rests_choice)

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
        submitted = st.form_submit_button("Submit")
        if submitted:
            # run the function here, passing in settings from the form above
            mel_interval_bar_chart(piece, 
                                combine_unisons_choice, 
                                combine_rests_choice, 
                                kind_choice,
                                directed,
                                compound)
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

