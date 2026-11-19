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
    - **Melodic Entries Only** — if True, only ngrams that follow a significant break (rest, fermata,
      or section boundary) are returned, focusing on thematic entries. If False, all ngrams are included.
    - **Include Count** — if True, a bar chart above each heat map shows how many times each pattern occurs.

    **Reading the results**
    - The **heat map** shows where each ngram pattern appears across the voices and measures of the
      piece. Each row is a voice; each bar is one ngram, from its start to its end.
    - Beneath each chart's title, a smaller line lists the **settings** used to find the ngrams
      (for example `melodic: diatonic, directed, compound · n = 4 · thematic entries`), followed by
      the number of patterns selected, if you have narrowed them down.
    - Each piece has its own heat map, so if you select multiple pieces you can compare their patterns visually.
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
        entries_only = _fc[1].selectbox("Melodic Entries Only?", [True, False])
        include_count = _fc[2].selectbox("Include Count of Ngrams", [True, False])
        submitted = st.form_submit_button("Submit")

if submitted:
    with st.spinner("Finding ngrams…"):
        results = [(p, melodic_ngram_data(p, combine_unisons_choice, interval_kinds[select_kind],
                                          directed, compound, int(length_choice),
                                          entries_only=entries_only))
                   for p in pieces]
    store_ngram_results(STATE_KEY, results, include_count, int(length_choice))
    st.session_state.pop('verovio_ngrams_rendered', None)

filtered_ngrams = ngram_results_section(STATE_KEY, "Melodic N-grams", corpus=corpus_length > 1)

# ---------------------------------------------------------------- Verovio
if filtered_ngrams is not None:
    st.markdown("#### View Filtered Ngrams with Verovio")
    st.warning("⚠️ Verovio rendering uses the **filtered** ngram results only. "
               "Please filter to a meaningful subset before rendering.")
    n_ng = len(filtered_ngrams)
    if n_ng > 20:
        st.warning(f"There are {n_ng} ngrams in the filtered list. Consider filtering to 20 or fewer before rendering.")
    if st.button("Render Ngrams with Verovio", key="verovio_ngrams_render"):
        piece_by_title = {p.metadata['title']: p for p in pieces}
        length = st.session_state[STATE_KEY]['length']
        ng_pad = 2 if length <= 3 else 3 if length <= 5 else 5
        meta_cols = ['Composer', 'Title', 'Date', 'Measure', 'Beat']
        voice_cols = [c for c in filtered_ngrams.columns if c not in meta_cols]
        toolkits = {}
        rendered = []
        for _, row in filtered_ngrams.iterrows():
            ng_piece = piece_by_title.get(row["Title"])
            if ng_piece is None:
                continue
            if row["Title"] not in toolkits:   # load each piece's MEI once
                tk = get_verovio_toolkit()
                tk.loadData(get_mei_content(ng_piece.path))
                tk.setScale(35)
                tk.setOptions({"adjustPageHeight": True, "pageWidth": 3000})
                toolkits[row["Title"]] = tk
            tk = toolkits[row["Title"]]
            c_meas = int(row["Measure"])
            c_beat = row["Beat"] if "Beat" in row.index else ""
            voice_patterns = {v: row[v] for v in voice_cols if pd.notna(row[v]) and row[v] != ''}
            voices_str = ", ".join(f"{v}: {p}" for v, p in voice_patterns.items())
            tk.select({"measureRange": f"{c_meas}-{c_meas + ng_pad}"})
            tk.redoLayout()
            for page in range(1, tk.getPageCount() + 1):
                label = (f"**Composer:** {row['Composer']} | **Title:** {row['Title']} | "
                         f"**Measure:** {c_meas} | **Beat:** {c_beat} | **Voices/Ngrams:** {voices_str}")
                rendered.append((label, tk.renderToSVG(page)))
        st.session_state.verovio_ngrams_rendered = rendered
    if st.session_state.get('verovio_ngrams_rendered'):
        st.subheader("Ngram Excerpts")
        st.write(f"Showing {len(st.session_state.verovio_ngrams_rendered)} excerpt(s)")
        for label, music in st.session_state.verovio_ngrams_rendered:
            st.divider()
            svg_clean = re.sub(r'<\?xml[^?]*\?>', '', music).strip()
            svg_b64 = base64.b64encode(svg_clean.encode('utf-8')).decode()
            st.markdown(
                f'{label}<br/><img src="data:image/svg+xml;base64,{svg_b64}" style="width:100%;max-width:2000px;margin-top:4px;"/>',
                unsafe_allow_html=True
            )
