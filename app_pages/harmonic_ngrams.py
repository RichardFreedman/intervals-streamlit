"""Explore Harmonic Ngrams"""
import streamlit as st
from crim_app.common import *
from crim_app.filters import *

piece, corpus, corpus_length, crim_piece_selections, uploaded_files_list = get_selection()
from crim_app.ngrams import *

STATE_KEY = 'har_ngrams'
st.subheader("Explore Harmonic Ngrams")
with st.expander("How to use this tool"):
    st.markdown("""
    **About this tool**
    This tool finds recurring sequences of harmonic intervals — called ngrams — of a specified length
    within a piece or corpus. Each ngram captures a consecutive run of vertical intervals between
    voice pairs, making it possible to identify recurring harmonic patterns and their location in
    the score.

    **Key settings**
    - **Ngram Length** — the number of consecutive harmonic intervals in each pattern. 3 is a common
      starting point; longer values find more specific patterns.
    - **Interval Kind** — how intervals are represented: Diatonic, With Quality, Chromatic, or
      Zero-based Diatonic (see Harmonic Intervals for full descriptions).
    - **Directed** — if True, intervals above and below the reference voice are distinguished.
      If False, only absolute size is reported.
    - **Compound** — if True, intervals larger than an octave are kept as-is.
      If False, they are reduced to simple intervals.
    - **Calculate Intervals Only Against Lowest Voice** — if True, each voice is measured only against
      the lowest sounding voice, giving a figured-bass style view. If False, all voice pairs are used.
    - **Include Count** — if True, a bar chart above each heat map shows how many times each pattern occurs.
    - **Show Paired Plots** (two or more pieces only) — treats the **first piece you selected** as the
      *model* and every other piece as a *derivative*. Instead of one heat map per piece, the page shows
      a **pair** of heat maps for each derivative: the model on top, the derivative below. Both maps in
      a pair show **only the patterns the model and that derivative share**, so each derivative is
      limited to ngrams found in the model. This works with the pattern filter, and the table and
      counts are likewise limited to patterns found in the model. To change which piece is the model,
      change the order in which pieces are selected in the sidebar.

    **Reading the results**
    - The **heat map** shows where each harmonic ngram pattern appears across the voice pairs and
      measures of the piece. Each row is a voice pair; each bar is one ngram.
    - Beneath each chart's title, a smaller line lists the **settings** used to find the ngrams
      (for example `harmonic: diatonic, directed, compound · n = 3`), followed by the number of
      patterns selected, if you have narrowed them down.
    - **Matching colors indicate matching ngrams**, in every heat map on the page: a pattern has the
      same color in each piece of a corpus.
    - Use the **pattern filter** to focus on specific ngrams: the heat maps and the table follow it.
    - The **table** can be viewed as individual ngram locations (by voice pair, measure, and beat) or as
      a count summary of how often each pattern appears.

    [Know the code — CRIM Intervals ngram documentation](https://github.com/HCDigitalScholarship/intervals/blob/main/tutorial/08_Ngrams_Heat_Maps.md) ·
    [Charts](https://github.com/HCDigitalScholarship/intervals/blob/main/tutorial/17_Visualizations_Summary.md#ngram-heat-maps)
    """)

if corpus_length == 0:
    st.write("Please select one or more pieces")
    st.stop()

pieces = [piece] if corpus_length == 1 else list(st.session_state.corpus.scores)

form_col = st.container()
with form_col:
    with st.form("Harmonic Ngram Settings"):
        _fc = st.columns(4)   # settings side by side
        directed = _fc[0].selectbox("Select Directed Interval Status", [True, False])
        compound = _fc[1].selectbox("Select Compound Interval Status", [True, False])
        select_kind = _fc[2].selectbox("Select Interval Kind",
                                   ["diatonic", "chromatic", "with quality", "zero-based diatonic"])
        against_low = _fc[3].selectbox("Calculate Intervals Only Against Lowest Voice", [False, True])
        length_choice = _fc[0].number_input('Select ngram Length', value=3, step=1, min_value=1)
        include_count = _fc[1].selectbox("Include Count of Ngrams", [True, False])
        paired = (_fc[2].selectbox("Show Paired Plots", [False, True])
                  if corpus_length > 1 else False)
        submitted = st.form_submit_button("Submit")

if submitted:
    with st.spinner("Finding ngrams…"):
        results = [(p, harmonic_ngram_data(p, interval_kinds[select_kind], directed, compound,
                                           against_low, int(length_choice)))
                   for p in pieces]
    store_ngram_results(STATE_KEY, results, include_count, int(length_choice), paired=paired)

ngram_results_section(STATE_KEY, "Harmonic N-grams", corpus=corpus_length > 1, voice_label='Voice Pair')
