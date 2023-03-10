
import streamlit as st
from pathlib import Path
import requests
from requests.sessions import DEFAULT_REDIRECT_LIMIT
import base64
import verovio
import os
from streamlit import caching
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

path = '/Users/rfreedma/Documents/CRIM_Python/CRIM-online/crim/static/mei/MEI_4.0'
file_list = os.listdir(path) 
corpus_list = [ ] 
for file in file_list: 
    name = path + "/" + file 
    corpus_list.append(name)

first_piece = file_list[0]
piece = path + "/" + file 



piece_list = []
raw_prefix = "https://raw.githubusercontent.com/CRIM-Project/CRIM-online/master/crim/static/mei/MEI_4.0/"
URL = "https://api.github.com/repos/CRIM-Project/CRIM-online/git/trees/990f5eb3ff1e9623711514d6609da4076257816c"
piece_json = requests.get(URL).json()

pattern = 'CRIM_Mass_([0-9]{4}).mei'

# save
# https://raw.githubusercontent.com/CRIM-Project/CRIM-online/master/crim/static/mei/MEI_4.0/CRIM_Mass_0001_1.mei

# and now the request for all the files
for p in piece_json["tree"]:
    p_name = p["path"]
    if re.search(pattern, p_name):
        pass
    else:
        piece_list.append(p_name)


# piece = piece_list[0]

# fullpath = raw_prefix + "/" + piece

piece = st.selectbox('Select Piece To View', piece_list)

# display name of selected piece
st.write('You selected:', piece)

# and create full URL to use in the Verovio html block below
tune = raw_prefix + "/" + piece

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
    fetch('"""+tune+"""')
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



if st.sidebar.button("Find Cadences"):

    piece = importScore(tune)
    cadences = piece.cadences()
    # # col_list = ['Measure', 'Beat', 'CadType', 'Pattern', 'Key', 'Tone','LeadingTones', 'CVFs', 'Low','RelLow','RelTone', 'Sounding', 'Progress','SinceLast','ToNext']
    # # cadences = cadences[col_list]

    st.write("Detail View of Cadences")
    cadences

    grouped = cadences.groupby(['Tone', 'CadType']).size().reset_index(name='counts')
    st.write("Summary of Cadences")
    grouped

    st.write("Radar Plot of Cadences")
    radar = piece.cadenceRadarPlot(combinedType=True, displayAll=True)
    st.plotly_chart(radar, use_container_width=True)
    # st.write(radar)