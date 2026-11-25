"""Explore Melodic Ngrams"""
import streamlit as st
from crim_app.common import *
from crim_app.filters import *

piece, corpus, corpus_length, crim_piece_selections, uploaded_files_list = get_selection()
from crim_app.ngrams import *

STATE_KEY = 'mel_ngrams'
st.subheader("Explore Melodic Ngrams")
with st.expander("How to use this tool"):
    st.markdown("""
    **About this tool**
    This tool finds recurring sequences of melodic intervals — called ngrams — of a specified length
    within a piece or corpus. Each ngram captures a consecutive run of intervals in a single voice,
    making it possible to identify melodic patterns, motives, and their location in the score.

    **Key settings**
    - **Ngram Length** — the number of consecutive intervals in each pattern. 3 is a common starting
      point for motives; longer values find more specific patterns.
    - **Combine Unisons** — if True, consecutive repeated pitches are treated as sustained, so no
      unison interval is recorded between them.
    - **Interval Kind** — how intervals are represented: Diatonic, With Quality, Chromatic, or
      Zero-based Diatonic (see Melodic Intervals for full descriptions).
    - **Directed** — if True, ascending and descending intervals are distinguished.
      If False, only absolute size is reported.
    - **Compound** — if True, intervals larger than an octave are kept as-is.
      If False, they are reduced to simple intervals.
    - **Melodic Entries** — which ngrams to keep:
        - *Entries only (after rest or fermata)* (default) — only the occurrences that actually begin
          after a rest or fermata (or at the start), for patterns that enter this way more than once.
        - *Entry patterns, all occurrences* — patterns that appear at least once as an entry (after a
          rest or fermata, or at the start of the piece) and occur more than once; every occurrence of
          such a pattern is shown, whether or not that occurrence follows a rest.
        - *All ngrams* — every ngram in every voice.
    - **Include Count** — if True, a bar chart above each heat map shows how many times each pattern occurs.
    - **Show Paired Plots** (two or more pieces only) — treats the **first piece you selected** as the
      *model* and every other piece as a *derivative* (for example, the movements of a Mass based on
      that model). Instead of one heat map per piece, the page shows a **pair** of heat maps for each
      derivative: the model on top, the derivative below. Both maps in a pair show **only the patterns
      the model and that derivative share**, so each derivative is limited to ngrams found in the
      model. This works with any Melodic Entries setting and with the pattern filter. The table, counts
      and Verovio excerpts are likewise limited to patterns found in the model. To change which piece
      is the model, change the order in which pieces are selected in the sidebar.

    **Reading the results**
    - The **heat map** shows where each ngram pattern appears across the voices and measures of the
      piece. Each row is a voice; each bar is one ngram, from its start to its end.
    - Beneath each chart's title, a smaller line lists the **settings** used to find the ngrams
      (for example `melodic: diatonic, directed, compound · n = 4 · thematic entries`), followed by
      the number of patterns selected, if you have narrowed them down.
    - Each piece has its own heat map, so if you select multiple pieces you can compare their patterns visually.
      With **Show Paired Plots**, the maps come in pairs (model + derivative) instead, each pair headed
      with the two pieces' names.
    - **Matching colors indicate matching ngrams**, in every heat map on the page: a pattern has the
      same color in each piece of a corpus.
    - Use the **pattern filter** to focus on specific ngrams: the heat maps, the table and the Verovio
      excerpts all follow it.
    - The charts are interactive: click a pattern (in the count chart or the heat map) to highlight it.
    - The **table** can be viewed as individual ngram locations (by voice, measure, and beat) or as
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
    with st.form("Ngram Settings"):
        _fc = st.columns(4)   # settings side by side
        combine_unisons_choice = _fc[0].selectbox("Combine Unisons", [False, True])
        directed = _fc[1].selectbox("Select Directed Interval Status", [True, False])
        compound = _fc[2].selectbox("Select Compound Interval Status", [True, False])
        select_kind = _fc[3].selectbox("Select Interval Kind",
                                   ["diatonic", "chromatic", "with quality", "zero-based diatonic"])
        length_choice = _fc[0].number_input('Select ngram Length', value=3, step=1, min_value=1)
        entry_mode = _fc[1].selectbox("Melodic Entries", list(ENTRY_MODES))
        include_count = _fc[2].selectbox("Include Count of Ngrams", [True, False])
        paired = (_fc[3].selectbox("Show Paired Plots", [False, True])
                  if corpus_length > 1 else False)
        submitted = st.form_submit_button("Submit")

if submitted:
    with st.spinner("Finding ngrams…"):
        results = [(p, melodic_ngram_data(p, combine_unisons_choice, interval_kinds[select_kind],
                                          directed, compound, int(length_choice),
                                          entry_mode=entry_mode))
                   for p in pieces]
    store_ngram_results(STATE_KEY, results, include_count, int(length_choice), paired=paired)
    st.session_state[STATE_KEY]['entry_mode'] = entry_mode
    st.session_state[STATE_KEY]['combine_unisons'] = combine_unisons_choice

# the chart subtitle says "thematic entries" for both entry modes, so name the mode in the title
_mode = st.session_state.get(STATE_KEY, {}).get('entry_mode', "All ngrams")
_title = "Melodic N-grams" if _mode == "All ngrams" else f"Melodic N-grams ({_mode})"
filtered_ngrams = ngram_results_section(STATE_KEY, _title, corpus=corpus_length > 1)

# ---------------------------------------------------------------- Verovio
if filtered_ngrams is not None:
    st.markdown("#### View Filtered Ngrams with Verovio")
    st.warning("⚠️ Verovio rendering uses the **filtered** ngram results only. "
               "Please filter to a meaningful subset before rendering.")
    n_ng = len(filtered_ngrams)
    if n_ng > 20:
        st.warning(f"There are {n_ng} ngrams in the filtered list. Consider filtering to 20 or fewer before rendering.")
    if st.checkbox("Show each ngram in the table in notation (highlighted)",
                   key="ngrams_show_notation"):
        results = st.session_state[STATE_KEY]
        n_notes = results['length'] + 1          # n intervals span n + 1 notes
        combine = results.get('combine_unisons', False)
        piece_by_title = {p.metadata['title']: p for p in pieces}
        meta_cols = ['Composer', 'Title', 'Date', 'Measure', 'Beat', 'Offset']
        voice_cols = [c for c in filtered_ngrams.columns if c not in meta_cols]
        st.subheader("Ngram Excerpts")
        st.caption("Highlighted notes are the notes of each ngram, in every voice listed.")
        for _, row in filtered_ngrams.iterrows():
            ng_piece = piece_by_title.get(row["Title"])
            if ng_piece is None:
                continue
            voice_patterns = {v: row[v] for v in voice_cols
                              if pd.notna(row[v]) and str(row[v]).strip() != ''}
            if not voice_patterns:
                continue
            # Offset comes from detailIndex(offset=True); older stored results lack it
            start = (row["Offset"] if "Offset" in row.index
                     else offset_at(ng_piece, row["Measure"], row["Beat"]))
            if start is None:
                continue
            ids, span = merge_spans(
                [note_ids_in_span(ng_piece, v, start, n_notes, combine) for v in voice_patterns])
            if not ids or span is None:
                continue
            m1, m2 = span
            voices_str = ", ".join(f"{v}: {p}" for v, p in voice_patterns.items())
            caption = (f"**{row['Composer']}**, *{row['Title']}* — **Measure** {int(row['Measure'])}, "
                       f"**Beat** {row['Beat']} | **Voices/Ngrams:** {voices_str}")
            st.divider()
            for i, svg in enumerate(render_highlighted_excerpt(ng_piece.path, m1, m2, tuple(ids))):
                show_svg(svg, caption if i == 0 else "")
