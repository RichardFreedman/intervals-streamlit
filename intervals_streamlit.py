
import streamlit as st
import streamlit.components.v1 as components
import requests
import sys, os
import re
sys.path.append(os.path.join(os.path.dirname(__file__), '../', 'intervals'))
from intervals.main_objs import *
# the import above assumes that the parent "intervals" directory is a sibling of this intervals-streamlit directory

piece_list = []
raw_prefix = "https://raw.githubusercontent.com/CRIM-Project/CRIM-online/master/crim/static/mei/MEI_4.0/"
URL = "https://api.github.com/repos/CRIM-Project/CRIM-online/git/trees/990f5eb3ff1e9623711514d6609da4076257816c"
piece_json = requests.get(URL).json()

pattern = 'CRIM_Mass_([0-9]{4}).mei'
# build a list of all the file names
for p in piece_json["tree"]:
    p_name = p["path"]
    if re.search(pattern, p_name):
        pass
    else:
        piece_list.append(p_name)

# display name of selected piece
piece = st.selectbox('Select Piece To View', piece_list)
st.write('You selected:', piece)

# and create full URL to use in the Verovio html block below
tune = raw_prefix + "/" + piece

# insert html within Streamlit, using components()
components.html("""
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
    st.write("Detailed View of Cadences")
    st.dataframe(cadences)

    grouped = cadences.groupby(['Tone', 'CadType']).size().reset_index(name='counts')
    st.write("Summary of Cadences")
    st.dataframe(grouped)

    st.write("Radar Plot of Cadences")
    radar = piece.cadenceRadarPlot(combinedType=True, displayAll=True, renderer='streamlit')
    st.plotly_chart(radar, use_container_width=True)