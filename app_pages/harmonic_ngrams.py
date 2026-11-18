"""Explore Harmonic Ngrams"""
import streamlit as st
from crim_app.common import *
from crim_app.filters import *

piece, corpus, corpus_length, crim_piece_selections, uploaded_files_list = get_selection()
from crim_app.ngrams import *

search_type = "harmonic_ngrams"
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
    - **Include Count** — if True, the heat map shows how many times each pattern occurs.

    **Reading the results**
    - The **heat map** shows where each harmonic ngram pattern appears across the voices and measures
      of the piece. Color intensity indicates pattern presence (and count if enabled).
    - The **table** can be viewed as individual ngram locations (by voice, measure, and beat) or as
      a count summary of how often each pattern appears across the corpus.
    - Use the pattern filter to focus the table on specific ngrams of interest.

    [Know the code — CRIM Intervals ngram documentation](https://github.com/HCDigitalScholarship/intervals/blob/main/tutorial/09_Ngrams_Heat_Maps.md)
    """)
if corpus_length == 0:
    st.write("Please select one or more pieces")
elif corpus_length == 1:
    form_col, _ = st.columns([1, 2])
    with form_col:
     with st.form("Harmonic Ngram Settings"):
        directed = st.selectbox(
            "Select Directed Interval Status",
            [True, False])
        compound = st.selectbox(
            "Select Compound Interval Status",
            [True, False])
        select_kind = st.selectbox(
            "Select Interval Kind",
            ["diatonic", "chromatic", "with quality", "zero-based diatonic"])
        kind_choice = interval_kinds[select_kind]
        against_low = st.selectbox("Calculate Intervals Only Against Lowest Voice",
                                   [False, True])
        length_choice = st.number_input('Select ngram Length', value=3, step=1)
        include_count = st.selectbox("Include Count of Ngrams", [True, False])
        submitted = st.form_submit_button("Submit")
        if submitted:
            key_list = ['har_ngrams3', 'har_heatmap']
            for key in key_list:
                if key in st.session_state.keys():
                    del st.session_state[key]
            har_ngrams, har_heatmap = harmonic_ngram_heatmap(piece,
                                        kind_choice,
                                        directed,
                                        compound,
                                        against_low,
                                        length_choice,
                                        include_count)
            har_ngrams = har_ngrams.map(convertTuple).dropna()
            har_ngrams2 = har_ngrams.assign(Composer=piece.metadata['composer'], Title=piece.metadata['title'], Date=piece.metadata['date'])
            cols_to_move = ['Composer', 'Title', 'Date']
            har_ngrams3 = har_ngrams2[cols_to_move + [col for col in har_ngrams2.columns if col not in cols_to_move]]
            if "har_ngrams3" not in st.session_state:
                st.session_state.har_ngrams3 = har_ngrams3
            if 'har_heatmap' not in st.session_state:
                st.session_state.har_heatmap = har_heatmap
    if 'har_heatmap' not in st.session_state:
        pass
    if "har_ngrams3" not in st.session_state:
        pass
    else:
        if piece.metadata["composer"] is not None:
            st.subheader("Harmonic Ngram Heatmap: " + piece.metadata["composer"] + ", " + piece.metadata["title"])
        else:
            st.subheader("Harmonic Ngram Heatmap: " + piece.metadata["title"])
        st.altair_chart(st.session_state.har_heatmap, use_container_width=True)

        st.write("Filter Results by Contents of Each Column")
        filtered_har_ngrams = filter_dataframe_ng(st.session_state.har_ngrams3)
        har_ng_table_mode = st.radio(
            "Table View",
            ["Ngrams by Voice Pair", "Counts of Ngrams"],
            horizontal=True,
            key='har_ng_single_table_mode'
        )
        show_table = st.checkbox('Show Table', key='har_ng_show_table')
        id_vars_har = [c for c in ['Composer', 'Title', 'Date'] if c in filtered_har_ngrams.data.columns]
        voice_cols_har = [c for c in filtered_har_ngrams.data.columns if c not in id_vars_har]
        if har_ng_table_mode == "Ngrams by Voice Pair":
            mask = filtered_har_ngrams.data[voice_cols_har].apply(
                lambda col: col.notna() & (col.astype(str).str.strip() != '')
            ).any(axis=1)
            table_har_ng = filtered_har_ngrams.data[mask].reset_index(drop=True)
        else:
            melted_har_ng = (
                filtered_har_ngrams.data
                .melt(id_vars=id_vars_har, value_vars=voice_cols_har, var_name='Voice Pair', value_name='Ngram')
                .dropna(subset=['Ngram'])
            )
            melted_har_ng = melted_har_ng[melted_har_ng['Ngram'].astype(str).str.strip() != '']
            table_har_ng = (
                melted_har_ng.groupby('Ngram')
                .size()
                .reset_index(name='Count')
                .sort_values('Count', ascending=False)
                .reset_index(drop=True)
            )
        if show_table:
            st.dataframe(table_har_ng, use_container_width=True)
        st.download_button(
            label="Download Filtered Harmonic Ngram Data as CSV",
            data=table_har_ng.to_csv(index=False),
            file_name=piece.metadata['title'] + '_harmonic_ngram_results.csv',
            mime='text/csv',
            key='har_ng_dl_1',
            )
# for corpus
elif corpus_length > 1:
    form_col, _ = st.columns([1, 2])
    with form_col:
     with st.form("Harmonic Ngram Settings"):
        directed = st.selectbox(
            "Select Directed Interval Status",
            [True, False])
        compound = st.selectbox(
            "Select Compound Interval Status",
            [True, False])
        select_kind = st.selectbox(
            "Select Interval Kind",
            ["diatonic", "chromatic", "with quality", "zero-based diatonic"])
        kind_choice = interval_kinds[select_kind]
        against_low = st.selectbox("Calculate Intervals Only Against Lowest Voice",
                                   [False, True])
        length_choice = st.number_input('Select ngram Length', value=3, step=1)
        include_count = st.selectbox("Include Count of Ngrams", [True, False])
        submitted = st.form_submit_button("Submit")
        if submitted:
            har_ngram_df_list = []
            har_heatmap_list = []
            for piece in st.session_state.corpus.scores:
                har_ngrams, har_heatmap = harmonic_ngram_heatmap(piece,
                                            kind_choice,
                                            directed,
                                            compound,
                                            against_low,
                                            length_choice,
                                            include_count)
                har_ngrams = har_ngrams.map(convertTuple).dropna()
                har_ngrams2 = har_ngrams.assign(Composer=piece.metadata['composer'], Title=piece.metadata['title'], Date=piece.metadata['date'])
                cols_to_move = ['Composer', 'Title', 'Date']
                har_ngrams3 = har_ngrams2[cols_to_move + [col for col in har_ngrams2.columns if col not in cols_to_move]]
                har_ngram_df_list.append(har_ngrams3)
                har_heatmap_list.append((piece.metadata['composer'], piece.metadata['title'], har_heatmap))
            if 'combined_har_ngrams' in st.session_state.keys():
                del st.session_state.combined_har_ngrams
            if 'har_ngram_heatmaps' in st.session_state.keys():
                del st.session_state.har_ngram_heatmaps
            if len(har_ngram_df_list) > 0:
                combined_har_ngrams = pd.concat(har_ngram_df_list)
                if "combined_har_ngrams" not in st.session_state:
                    st.session_state.combined_har_ngrams = combined_har_ngrams
            if len(har_heatmap_list) > 0:
                st.session_state.har_ngram_heatmaps = har_heatmap_list

    if st.session_state.get('har_ngram_heatmaps'):
        for composer, title, har_heatmap in st.session_state.har_ngram_heatmaps:
            if composer is not None:
                st.subheader("Harmonic Ngram Heatmap: " + composer + ", " + title)
            else:
                st.subheader("Harmonic Ngram Heatmap: " + title)
            st.altair_chart(har_heatmap, use_container_width=True)

    if "combined_har_ngrams" not in st.session_state:
        pass
    else:
        st.write("Filter Results by Contents of Each Column")
        st.write("Note that the Filters do NOT change the heatmaps shown above!")
        filtered_combined_har_ngrams = filter_dataframe_ng(st.session_state.combined_har_ngrams)
        har_ng_corpus_table_mode = st.radio(
            "Table View",
            ["Ngrams by Voice Pair", "Counts of Ngrams by Composer and Title"],
            horizontal=True,
            key='har_ng_corpus_table_mode'
        )
        show_table = st.checkbox('Show Table of all Harmonic Ngrams', key='har_ng_corpus_show_table')
        id_vars_har = [c for c in ['Composer', 'Title', 'Date'] if c in filtered_combined_har_ngrams.data.columns]
        voice_cols_har = [c for c in filtered_combined_har_ngrams.data.columns if c not in id_vars_har]
        if har_ng_corpus_table_mode == "Ngrams by Voice Pair":
            mask = filtered_combined_har_ngrams.data[voice_cols_har].apply(
                lambda col: col.notna() & (col.astype(str).str.strip() != '')
            ).any(axis=1)
            table_har_ng = filtered_combined_har_ngrams.data[mask].reset_index(drop=True)
        else:
            melted_har_ng = (
                filtered_combined_har_ngrams.data
                .melt(id_vars=id_vars_har, value_vars=voice_cols_har, var_name='Voice Pair', value_name='Ngram')
                .dropna(subset=['Ngram'])
            )
            melted_har_ng = melted_har_ng[melted_har_ng['Ngram'].astype(str).str.strip() != '']
            table_har_ng = (
                melted_har_ng.groupby(['Composer', 'Title', 'Ngram'])
                .size()
                .reset_index(name='Count')
                .sort_values(['Composer', 'Title', 'Count'], ascending=[True, True, False])
                .reset_index(drop=True)
            )
        if show_table:
            st.dataframe(table_har_ng, use_container_width=True)
        st.download_button(
            label="Download Filtered Corpus Harmonic Ngram Data as CSV",
            data=table_har_ng.to_csv(index=False),
            file_name='corpus_harmonic_ngram_results.csv',
            mime='text/csv',
            key='har_ng_dl_2',
            )

