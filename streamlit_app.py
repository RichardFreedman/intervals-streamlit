"""CRIM Intervals Search Tools — multipage entry point.

Run with:  streamlit run streamlit_app.py

This script runs on every page view. It renders the piece picker in the
sidebar (so the selection persists as users move between pages), imports the
selected pieces once, and then hands off to the chosen page. Each analysis
page lives in app_pages/ and only its own code runs on a rerun.
"""
import streamlit as st

st.set_page_config(page_title="CRIM Intervals", layout="wide")

from crim_app.common import (CRIM_SELECT_KEY, UPLOAD_KEY, fetch_crim_pieces,
                             load_selection, make_piece_list)

json_objects = fetch_crim_pieces()

# ---------------------------------------------------------------- navigation
home = st.Page("app_pages/home.py", title="Home", icon=":material/home:", default=True)
pages = {
    "": [home],
    "Notes & Rhythm": [
        st.Page("app_pages/notes.py", title="Notes"),
        st.Page("app_pages/weighted_notes.py", title="Weighted Notes"),
        st.Page("app_pages/durations.py", title="Durations"),
        st.Page("app_pages/ranges_species.py", title="Voice Ranges & Species"),
    ],
    "Intervals": [
        st.Page("app_pages/melodic.py", title="Melodic Intervals"),
        st.Page("app_pages/harmonic.py", title="Harmonic Intervals"),
    ],
    "Ngrams": [
        st.Page("app_pages/melodic_ngrams.py", title="Melodic Ngrams"),
        st.Page("app_pages/harmonic_ngrams.py", title="Harmonic Ngrams"),
        st.Page("app_pages/sonority_ngrams.py", title="Sonority Ngrams"),
    ],
    "Structure": [
        st.Page("app_pages/cadences.py", title="Cadences"),
        st.Page("app_pages/presentation_types.py", title="Presentation Types"),
        st.Page("app_pages/model_finder.py", title="Model Finder"),
    ],
}
# The built-in menu always sits at the top of the sidebar; hide it and draw
# the same links below the piece picker instead (see the end of the sidebar).
pg = st.navigation(pages, position="hidden")

# ---------------------------------------------------------------- piece picker
with st.sidebar:
    st.markdown("### Pieces")
    st.multiselect("Select pieces from CRIM", make_piece_list(json_objects),
                   key=CRIM_SELECT_KEY)
    st.file_uploader("Upload MEI or MusicXML files", type=['mei', 'xml', 'musicxml'],
                     accept_multiple_files=True, key=UPLOAD_KEY)
    with st.spinner("Loading pieces…"):
        n_selected = load_selection(json_objects)
    if n_selected == 0:
        st.caption("No pieces selected yet.")
    elif n_selected == 1:
        md = st.session_state.get('metadata', {})
        st.caption(f"**{md.get('composer', '')}** — {md.get('title', '')}")
    else:
        st.caption(f"Corpus of {n_selected} pieces")

    # ------------------------------------------------------------ page links
    st.divider()
    for section, section_pages in pages.items():
        if section:
            st.markdown(f"**{section}**")
        for page in section_pages:
            st.page_link(page)

pg.run()
