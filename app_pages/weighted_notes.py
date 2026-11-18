"""Explore Notes Weighted by Duration (uses note_weights + viz.radar_note_plot)."""
import streamlit as st
from crim_app.common import *

piece, corpus, corpus_length, crim_piece_selections, uploaded_files_list = get_selection()

st.subheader("Explore Weighted Notes")
with st.expander("How to use this tool"):
    st.markdown("""
    **About this tool**
    This tool calculates the relative importance of each pitch class in a piece or corpus by
    weighting notes according to their total duration. Rather than simply counting how many times
    a pitch appears, it measures how long each pitch class sounds, then scales the result as a
    proportion of the total duration. This gives a more musically meaningful picture of pitch
    emphasis than raw note counts.

    **Key settings**
    - **Exclude Rests** — show each pitch class as a share of *sounding* time only.
    - **Pitch Class Order** — the order of pitch classes around the radar plot:
      *Fifths* (circle of fifths), *Diatonic* (C D E F G A B), or *Chromatic* (by semitone).
    - **Limit to pitch classes present in data** — hides pitch classes with zero weight.
    - **One polygon per** — for a corpus, one shape per piece (Title), per Composer, or per Final.
      Durations are summed within each group.

    **Reading the results**
    - The **radar plot** shows the scaled proportion of each pitch class. Comparing shapes across
      pieces, composers or finals reveals differences in pitch emphasis — for example, modal profiles.
    - The **table** shows pitch class, total duration (in quarter notes) and scaled proportion.

    [Know the code — Visualizations tutorial](https://github.com/HCDigitalScholarship/intervals/blob/main/tutorial/17_Visualizations_Summary.md)
    """)

require_selection()
subject = piece if corpus_length == 1 else corpus
name = (safe_filename(piece.metadata.get('composer'), piece.metadata.get('title'))
        if corpus_length == 1 else "corpus")


@st.cache_data(**PIECE_CACHE)
def get_note_weights(subject):
    # include_final so a corpus can be grouped by final
    return subject.note_weights(include_rests=True, include_final=True)


@st.fragment
def weighted_notes_fragment():
    with st.spinner("Weighting notes…"):
        nw = get_note_weights(subject)
    c1, c2, c3 = st.columns(3)
    order = c1.radio("Pitch Class Order", ['Fifths', 'Diatonic', 'Chromatic'], horizontal=True,
                     key='wn_order')
    groups = {'Title': 'title', 'Composer': 'composer', 'Final': 'final'}
    group = c2.radio("One polygon per", list(groups), horizontal=True, key='wn_group',
                     disabled=corpus_length == 1)
    exclude_rests = c3.toggle("Exclude Rests", value=True, key='wn_rests')
    limit = c3.toggle("Limit to pitch classes present in data", value=True, key='wn_limit')
    fig = viz.radar_note_plot(nw, pitch_class_order=order, exclude_rests=exclude_rests,
                              limit_to_active=limit, color_grouping=groups[group])
    show_plotly(fig, f"{name}_weighted_notes.html", 'wn')

    if st.checkbox("Show Table of Weighted Notes", key='wn_table'):
        table = nw[nw['pitch_class'] != 'Rest'] if exclude_rests else nw
        st.dataframe(table, use_container_width=True, hide_index=True)
        st.download_button("Download Weighted Notes Data as CSV", table.to_csv(index=False),
                           file_name=f"{name}_weighted_notes.csv", mime='text/csv', key='wn_csv')


weighted_notes_fragment()
