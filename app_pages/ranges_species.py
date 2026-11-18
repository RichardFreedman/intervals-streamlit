"""Voice Ranges & Melodic Species (new in crim-intervals 2.0.86)."""
import streamlit as st
from crim_app.common import *

piece, corpus, corpus_length, crim_piece_selections, uploaded_files_list = get_selection()

st.subheader("Voice Ranges & Melodic Species")
with st.expander("How to use this tool"):
    st.markdown("""
    **About this tool**
    Two of the main ways to describe the mode of a Renaissance piece are the **range** of its voices
    and the **octave species** its melodies outline, each considered together with the final.

    **Voice ranges** — rather than the absolute lowest and highest notes (which one brief excursion
    can distort), each voice's range runs from the lowest to the highest of its *most prominent*
    pitches: the **Top N** pitches that take up the most time. When all the pieces share one final,
    dotted lines mark the reference pitches for that final. Filter a corpus by final to compare
    modal ranges.

    **Melodic species** — each melodic fourth and fifth is classified by the octave species it helps
    to articulate (for example, G–D and D–G both articulate the G octave). The chart shows where in
    the piece (0 = start, 1 = end) each species is stated, either one dot per interval colored by
    voice, or summarized into sections.

    **Species and cadences** — melodic species (top) and cadences (bottom) on one timeline, for one
    piece at a time, to compare where octave species and cadence tones fall.

    [Know the code — Voice Ranges and Melodic Species tutorial](https://github.com/HCDigitalScholarship/intervals/blob/main/tutorial/13_Voice_Ranges_Melodic_Species.md)
    """)

require_selection()
subject = piece if corpus_length == 1 else corpus
name = (safe_filename(piece.metadata.get('composer'), piece.metadata.get('title'))
        if corpus_length == 1 else "corpus")


# ---------------------------------------------------------------- cached data
@st.cache_data(**PIECE_CACHE)
def get_voice_ranges(subject, top_n):
    return subject.voice_ranges(top_n=top_n)


@st.cache_data(**PIECE_CACHE)
def get_species(subject, limit_to_entries):
    return subject.melodic_species(limit_to_entries=limit_to_entries)


@st.cache_data(**PIECE_CACHE)
def get_cadences(subject):
    return subject.cadences()


def _titles(df):
    return list(dict.fromkeys(df['Title'])) if 'Title' in df.columns else []


# ---------------------------------------------------------------- voice ranges
@st.fragment
def voice_ranges_fragment():
    c1, c2, c3, c4 = st.columns(4)
    top_n = c1.number_input("Top N prominent pitches", min_value=2, max_value=20, value=7,
                            key='vr_top_n')
    with st.spinner("Finding voice ranges…"):
        vr = get_voice_ranges(subject, int(top_n))
    finals = sorted(vr['Final'].dropna().unique()) if 'Final' in vr.columns else []
    final = c2.selectbox("Final", ['All'] + finals, key='vr_final',
                         help="Reference lines are drawn when all charted pieces share one final.")
    piece_order = c3.selectbox("Order pieces", ['mass', 'range', 'alpha', 'given'], key='vr_order',
                               disabled=corpus_length == 1,
                               help="'mass': models first, then Mass movements in liturgical order.")
    voices = sorted(vr['Voice'].astype(str).unique(), key=lambda v: (not v.isdigit(), int(v) if v.isdigit() else 0, v))
    sort_voice = c4.selectbox("Sort by voice", voices, index=voices.index('2') if '2' in voices else 0,
                              key='vr_sort_voice', disabled=corpus_length == 1)
    fig = viz.voice_range_chart(vr, final=None if final == 'All' else final,
                                piece_order=piece_order, sort_voice=sort_voice)
    show_plotly(fig, f"{name}_voice_ranges.html", 'vr')
    with st.expander("Voice range table"):
        shown = vr if final == 'All' else vr[vr['Final'] == final]
        st.dataframe(shown, use_container_width=True, hide_index=True)
        st.download_button("Download as CSV", shown.to_csv(index=False),
                           file_name=f"{name}_voice_ranges.csv", mime='text/csv', key='vr_csv')


# ---------------------------------------------------------------- species
@st.fragment
def species_fragment():
    c1, c2, c3 = st.columns(3)
    limit = c1.toggle("Only leaps at entries", value=True, key='sp_entries',
                      help="Limit to fourths and fifths at the start of melodic entries.")
    detail = c2.radio("Show", ['Each interval, by voice', 'Summary by section'], key='sp_detail',
                      horizontal=True)
    bins = c3.slider("Sections", 2, 10, 5, key='sp_bins',
                     disabled=detail == 'Each interval, by voice')
    with st.spinner("Finding melodic species…"):
        sp = get_species(subject, limit)
    if sp.empty:
        st.info("No melodic species found.")
        return
    fig = viz.plot_species(sp, show_voice_detail=detail == 'Each interval, by voice',
                           progress_bins=bins)
    show_plotly(fig, f"{name}_melodic_species.html", 'sp')
    with st.expander("Melodic species table"):
        st.dataframe(sp, use_container_width=True)
        st.download_button("Download as CSV", sp.to_csv(), file_name=f"{name}_melodic_species.csv",
                           mime='text/csv', key='sp_csv')


@st.fragment
def species_cadences_fragment():
    limit = st.session_state.get('sp_entries', True)
    with st.spinner("Finding species and cadences…"):
        sp = get_species(subject, limit)
        try:
            cads = get_cadences(subject)
        except Exception as e:
            st.warning(f"Could not find cadences for this selection ({e}).")
            return
    title = None
    if corpus_length > 1:
        titles = [t for t in _titles(sp) if t in set(cads['Title'])]
        if not titles:
            st.info("No piece has both melodic species and cadences.")
            return
        title = st.selectbox("Piece", titles, key='spc_title')
    try:
        fig = viz.plot_species_cadences(sp, cads, title=title)
    except ValueError as e:
        st.info(str(e))
        return
    show_plotly(fig, f"{safe_filename(title) if title else name}_species_cadences.html", 'spc')


if st.checkbox("Voice ranges", value=True, key='show_vr'):
    voice_ranges_fragment()
if st.checkbox("Melodic species", key='show_sp'):
    species_fragment()
if st.checkbox("Melodic species with cadences", key='show_spc'):
    species_cadences_fragment()
