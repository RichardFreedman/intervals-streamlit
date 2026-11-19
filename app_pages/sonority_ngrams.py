"""Explore Sonority Ngrams (corpus.sonority_ngrams + viz.sonority_ngram_progress)."""
import streamlit as st
from crim_app.common import *
from crim_app.filters import *

piece, corpus, corpus_length, crim_piece_selections, uploaded_files_list = get_selection()

st.subheader("Explore Sonority Ngrams")
with st.expander("How to use this tool"):
    st.markdown("""
    **About this tool**
    Sonority ngrams are short sequences of sonorities (the intervals above the lowest voice at each
    moment), each paired with the melodic motion of the bass, for example `-M2_10/1_Held_9/1_Held_8/1_M2_10/1`.
    Because they ignore which voice sings what, they are good at finding **block repetitions**:
    passages that return, within a piece or across pieces, even when the voices are redistributed.

    **Key settings**
    - **Ngram Length** — how many consecutive sonorities to include in each pattern. Start with 3–4.
    - **Sort** — alphabetize intervals within each sonority before forming ngrams. Useful for finding
      the same chord regardless of voice ordering.
    - **Minimum Beat Strength** — keeps only sonorities on beats of a given metric weight:
      0.0 = all beats, 0.25 = moderate beats, 0.5 = strong beats, 1.0 = downbeats only.
    - **Compound** — if True, intervals larger than an octave are kept as-is; if False, they are
      reduced to within an octave.

    **Reading the plot**
    - Each ngram pattern has its own row, and each dot is one occurrence, placed by how far through
      the piece it falls (Progress, from 0 at the start to 1 at the end). Colors show the piece.
    - With rows in order of first appearance, **a diagonal climb** is new material; **a dot that falls
      back below the climb** is a return to a pattern heard earlier; **several dots on one horizontal
      line** are a pattern that recurs.
    - Most four-sonority ngrams occur only once, so set the **minimum count** to 2 to see only the
      recurring patterns. With a corpus, this shows the patterns **shared** among the pieces.
    - **One panel per piece** makes it easier to compare where the same patterns fall in each piece.
    - Beneath the title, a smaller line lists the settings behind the chart: the ngram settings,
      then the count filter and row order chosen here.
    - Hover over a dot to see the ngram, the piece, its measure and beat, and how many times the
      pattern occurs. The table and CSV follow the same filters as the plot.

    [Know the code — sonority ngrams](https://github.com/HCDigitalScholarship/intervals/blob/main/tutorial/07_Harmonic_Intervals_Sonorities.md#sonority-n-grams-with-the-bass-line) ·
    [Sonority n-gram progress plots](https://github.com/HCDigitalScholarship/intervals/blob/main/tutorial/17_Visualizations_Summary.md#sonority-n-gram-progress-plots)
    """)


@st.cache_data(**PIECE_CACHE)
def get_sonority_ngrams(son_corpus, ngram_length, compound, sort, minimum_beat_strength, include_offset):
    son = son_corpus.sonority_ngrams(ngram_length=ngram_length, include_offset=include_offset,
                                     include_progress=True, compound=compound, sort=sort,
                                     minimum_beat_strength=minimum_beat_strength)
    return son.dropna(subset=['Low_Sonority'])


if corpus_length == 0:
    st.write("Please select one or more pieces")
    st.stop()

form_col = st.container()
with form_col:
    with st.form("Sonority Ngram Settings"):
        _fc = st.columns(4)   # settings side by side
        ngram_length = _fc[0].number_input('Select ngram Length', value=4, step=1, min_value=1)
        compound = _fc[1].selectbox("Select Compound Interval Status", [True, False])
        sort = _fc[2].selectbox("Sort Intervals within Sonority", [False, True])
        minimum_beat_strength = _fc[3].number_input(
            'Minimum Beat Strength (0.0 = all beats, 0.5 = strong beats, 1.0 = downbeats only)',
            value=0.0, min_value=0.0, max_value=1.0, step=0.25)
        include_offset = _fc[0].selectbox("Include Offset Column in Table", [False, True])
        submitted = st.form_submit_button("Submit")

if submitted:
    son_corpus = CorpusBase([piece]) if corpus_length == 1 else st.session_state.corpus
    with st.spinner("Finding sonority ngrams…"):
        st.session_state.sonority_ngrams = get_sonority_ngrams(
            son_corpus, int(ngram_length), compound, sort, minimum_beat_strength, include_offset)

if "sonority_ngrams" not in st.session_state:
    st.stop()

son_ng = st.session_state.sonority_ngrams
if son_ng.empty:
    st.info("No sonority ngrams found with these settings.")
    st.stop()

# Filter rows by column contents (e.g. Title). The plot counts patterns in
# the filtered rows; filter_dataframe_ng keeps the settings on its .data.
son_data = filter_dataframe_ng(son_ng).data
son_data = son_data[son_data['Low_Sonority'].astype(str) != '']
if son_data.empty:
    st.info("No sonority ngrams match these filters.")
    st.stop()

# ---------------------------------------------------------------- plot
@st.fragment
def sonority_plot_fragment(son_data):
    totals = son_data['Low_Sonority'].value_counts()
    max_total = int(totals.max())
    c1, c2, c3 = st.columns(3)
    count_range = c1.slider("Pattern count (across all pieces shown)", 1, max(max_total, 2),
                            (1, max(max_total, 2)), key='son_ng_count_range',
                            help="Use a minimum of 2 to see only patterns that recur.")
    order = c2.radio("Row order", ['first', 'count', 'alpha'], horizontal=True, key='son_ng_order',
                     format_func={'first': 'First appearance', 'count': 'Frequency',
                                  'alpha': 'Alphabetical'}.get)
    facet = c3.toggle("One panel per piece", value=False, key='son_ng_facet',
                      disabled=son_data['Title'].nunique() < 2)
    min_count, max_count = count_range
    try:
        fig = viz.sonority_ngram_progress(son_data, min_count=min_count,
                                          max_count=None if max_count >= max_total else max_count,
                                          order=order, facet=facet)
    except ValueError as e:
        st.info(str(e))
        return None
    name = (safe_filename(piece.metadata.get('composer'), piece.metadata.get('title'))
            if corpus_length == 1 else "corpus")
    show_plotly(fig, f"{name}_sonority_ngrams.html", 'son_ng')

    # table and CSV follow the same count filter
    kept = totals[(totals >= min_count) & (totals <= max_count)].index
    filtered = son_data[son_data['Low_Sonority'].isin(kept)]
    mode = st.radio("Table View", ["Sonority Ngrams by Composer, Title, Measure and Beat",
                                   "Sonority Ngrams with Corpus Count",
                                   "Sonority Count by Composer and Title"],
                    horizontal=True, key='son_ng_table_mode')
    if mode.startswith("Sonority Ngrams by"):
        table = filtered.copy()
        for col in ['Sonority', 'Low Line']:
            if col in table.columns:
                table[col] = table[col].map(lambda v: ', '.join(map(str, v)) if isinstance(v, (list, tuple)) else v)
        table['Measure'] = pd.to_numeric(table['Measure'], errors='coerce').round(0).astype('Int64')
        table['Beat'] = pd.to_numeric(table['Beat'], errors='coerce').round(2)
    elif mode.endswith("Corpus Count"):
        table = (filtered.groupby('Low_Sonority').size().reset_index(name='Count')
                         .sort_values('Count', ascending=False).reset_index(drop=True))
    else:
        table = (filtered.groupby(['Composer', 'Title', 'Low_Sonority']).size().reset_index(name='Count')
                         .sort_values(['Composer', 'Title', 'Count'], ascending=[True, True, False])
                         .reset_index(drop=True))
    st.caption(f"{len(kept)} patterns · " + " · ".join(settings_parts(son_data)))
    if st.checkbox('Show Table', key='son_ng_show_table'):
        st.dataframe(table, use_container_width=True, hide_index=True)
    st.download_button("Download Filtered Sonority Ngram Data as CSV", table.to_csv(index=False),
                       file_name=f"{name}_sonority_ngram_results.csv", mime='text/csv', key='son_ng_csv')


sonority_plot_fragment(son_data)
