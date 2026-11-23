"""Home: introduction and metadata for the selected pieces."""
import streamlit as st
import pandas as pd
from crim_app.common import get_selection

st.title("CRIM Intervals Search Tools")
st.subheader("A web application for analysis of musical patterns using the CRIM Intervals library.")
st.markdown("[Watch a video guide to this application.](https://haverford.box.com/s/hls1cabixjpu0ergckktmnlk0uoyz1su)")
st.markdown("[Learn more about CRIM Intervals](https://github.com/HCDigitalScholarship/intervals/blob/main/tutorial/00_Concise_Guide.md)")
st.markdown("Learn more about this web application (and how to contribute or adapt it) via the [Github Repository for CRIM Intervals on Streamlit](https://github.com/RichardFreedman/intervals-streamlit/blob/main/README.md)")

st.markdown("""
**How to use:** choose pieces from CRIM or upload MEI / MusicXML files in the sidebar.
Your selection stays loaded as you move between the analysis pages listed in the sidebar.
""")

piece, corpus, corpus_length, *_ = get_selection()
if corpus_length == 0:
    st.write("**No Files Selected! Please Select or Upload One or More Pieces in the sidebar.**")
elif corpus_length == 1 and 'metadata' in st.session_state:
    st.subheader("Selected Piece")
    st.dataframe(st.session_state.metadata)
elif 'corpus_metadata' in st.session_state:
    st.subheader("Selected Corpus")
    st.dataframe(pd.DataFrame(st.session_state.corpus_metadata), hide_index=True)
