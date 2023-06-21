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
import io
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
def get_piece_data(piece, json_objects):
    key_value_pair = ('piece_id', piece)
    for json_object in json_objects:
        if key_value_pair in json_object.items():
            piece_dict = {'Composer' : json_object['composer']['name'],
                      'Title' : json_object['full_title'],
                      'Date' :  json_object['date']}     
    return piece_dict
 

# get mei link for given piece
def find_mei_link(piece_id, json_objects):
    key_value_pair = ('piece_id', piece_id)
    for json_object in json_objects:
        if key_value_pair in json_object.items():
            return json_object['mei_links'][0]
    return None

# this version loads mei from git.  it works!

mei_file = "https://raw.githubusercontent.com/CRIM-Project/CRIM-online/master/crim/static/mei/MEI_4.0/CRIM_Model_0001.mei"


show_git_score = st.checkbox("Show MEI File from Git as Score")
if show_git_score:
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

            fetch('"""+mei_file+"""')
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

    
# this is for uploading

uploaded_file = st.file_uploader("Choose a file", 
                                    accept_multiple_files = False, 
                                    label_visibility = 'visible',
                                    type = ['.mei', '.xml', '.mid'])

byte_str = uploaded_file.read()
text_obj = byte_str.decode('UTF-8')  # Or use the encoding you expect

# option to display
# st.write(text_obj)

# the 'converter' is part of Music21
score = converter.parse(text_obj)
# score


# insert html within Streamlit, using components()
show_git_score = st.checkbox("Show Uploaded file as Score")
if show_git_score:
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

        
        app.loadData('"""+text_obj+"""');

    </script>
        """,
        height=800,
        # width=850,
    )
        