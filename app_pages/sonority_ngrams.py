"""Explore Sonority Ngrams"""
import streamlit as st
from crim_app.common import *
from crim_app.filters import *

piece, corpus, corpus_length, crim_piece_selections, uploaded_files_list = get_selection()

search_type = "sonority_ngrams"
st.subheader("Explore Sonority Ngrams")
with st.expander("How to use this tool"):
    st.markdown("""
    **About this tool**
    Sonority ngrams group consecutive vertical sonorities into patterns of a given length,
    letting you search for recurring harmonic sequences across one or more pieces.
    In this case we combine these vertical sonorities with the corresponding melodic intervals formed in the lowest sounding voice.  
    The result is a list of complex ngrams that represent repeating patterns of sonorities (as expressed in *all* voices) as we move through the piece.
    The scatter plot shows where in the piece each ngram appears, making it possible to identify clusters of recurring harmonic areas.  A piece that traces a single diagonal line is unlikely to feature internal repetition.  But one with gaps (which then seem to appear *lower* on the chart) are sections that have *already been heard*.
                

    **Key settings**
    - **Ngram Length** — how many consecutive sonorities to include in each pattern. Start with 3–4.
    - **Sort** — alphabetize intervals within each sonority before forming ngrams. Useful for finding the same chord regardless of voice ordering.
    - **Minimum Beat Strength** — filters to sonorities on beats of a given metric weight: 0.0 = all beats, 0.25 = moderate beats, 0.5 = strong beats, 1.0 = downbeats only.
    - **Compound** — if True, intervals larger than an octave are kept as-is; if False, they are reduced to within an octave.
    - **Include Progress** — adds a 0–1 value showing where in the piece each sonority falls. Required for the scatter plot.

    **Reading the results**
    - The **scatter plot** shows where in each combination of sonority ngram and low-line appears along the "progress" of each piece.
    - Gaps in a diagonal line of ngrams for one piece will appear lower in the chart, and thus are 'echoes' of some series heard before.
    - If you are viewing a corpus, the order of the pieces in the corpus will be reflected in the order of the colors in the scatter plot.  The first piece is lowest in the plot, and the last piece is highest.  So you can see if certain ngrams appear more in early or late pieces in the corpus.
    - Use the **count filter slider** to focus on patterns that appear frequently or rarely.

    [Know the code — CRIM Intervals sonority ngram documentation](https://github.com/HCDigitalScholarship/intervals/blob/main/tutorial/09_Ngrams_Heat_Maps.md)
    """)
if corpus_length == 0:
    st.write("Please select one or more pieces")
else:
    form_col, _ = st.columns([1, 2])
    with form_col:
     with st.form("Sonority Ngram Settings"):
        ngram_length = st.number_input('Select ngram Length', value=4, step=1)
        compound = st.selectbox(
            "Select Compound Interval Status",
            [True, False])
        sort = st.selectbox(
            "Sort Intervals within Sonority",
            [False, True])
        minimum_beat_strength = st.number_input(
            'Minimum Beat Strength (0.0 = all beats, 0.5 = strong beats, 1.0 = downbeats only)',
            value=0.0, min_value=0.0, max_value=1.0, step=0.25)
        metadata_choice = st.selectbox(
            "Include Metadata (Composer, Title, Date)",
            [True, False])
        include_offset = st.selectbox(
            "Include Offset Column",
            [False, True])
        include_progress = st.selectbox(
            "Include Progress Column",
            [True, False])
        submitted = st.form_submit_button("Submit")
        if submitted:
            if 'sonority_ngrams' in st.session_state:
                del st.session_state.sonority_ngrams
            if corpus_length == 1:
                son_corpus = CorpusBase([st.session_state.piece])
            else:
                son_corpus = st.session_state.corpus
            son_ng = corpus_sonority_ngrams(
                son_corpus,
                ngram_length=int(ngram_length),
                metadata_choice=metadata_choice,
                include_offset=include_offset,
                include_progress=include_progress,
                compound=compound,
                sort=sort,
                minimum_beat_strength=minimum_beat_strength)
            son_ng = son_ng.dropna(how='all')
            if "sonority_ngrams" not in st.session_state:
                st.session_state.sonority_ngrams = son_ng

    if "sonority_ngrams" not in st.session_state:
        pass
    else:
        st.write("Filter Results by Contents of Each Column")
        filtered_son_ngrams = filter_dataframe_ng(st.session_state.sonority_ngrams)

        # bar chart of ngram pattern counts
        son_data = filtered_son_ngrams.data.copy()
        meta_cols = ['Composer', 'Title', 'Date', 'Measure', 'Beat', 'Offset', 'Progress', 'Low_Sonority']
        ngram_cols = [col for col in son_data.columns if col not in meta_cols]
        if ngram_cols:
            son_data['Pattern'] = son_data[ngram_cols].apply(
                lambda row: ' | '.join(str(v) for v in row if pd.notna(v) and str(v) != ''), axis=1)
            piece_col = 'Title' if 'Title' in son_data.columns else None

            # compute full pattern counts (no hard top-N limit)
            if piece_col:
                pattern_counts_all = son_data.groupby(['Pattern', piece_col]).size().reset_index(name='Count')
                pattern_totals = pattern_counts_all.groupby('Pattern')['Count'].sum()
            else:
                pattern_counts_all = son_data['Pattern'].value_counts().reset_index()
                pattern_counts_all.columns = ['Pattern', 'Count']
                pattern_totals = pattern_counts_all.set_index('Pattern')['Count']

            max_count = int(pattern_totals.max()) if not pattern_totals.empty else 1
            count_range = st.slider(
                "Filter by pattern count",
                min_value=1,
                max_value=max(max_count, 2),
                value=(1, max(max_count, 2)),
                key='son_ng_count_range'
            )
            min_count, max_count_sel = count_range

            kept_patterns = pattern_totals[
                (pattern_totals >= min_count) & (pattern_totals <= max_count_sel)
            ].index
            pattern_counts = pattern_counts_all[pattern_counts_all['Pattern'].isin(kept_patterns)].copy()

            scatter_cols = ['Progress', 'Low_Sonority']
            if all(c in son_data.columns for c in scatter_cols):
                hover_cols = [c for c in ['Composer', 'Title', 'Measure', 'Beat', 'Low_Sonority'] if c in son_data.columns]
                scatter_fig = px.scatter(
                    son_data,
                    x='Progress',
                    y='Low_Sonority',
                    color='Title' if 'Title' in son_data.columns else None,
                    hover_data=hover_cols,
                    title='Scatter Plot of Sonority vs Progress'
                )
                scatter_fig.update_layout(
                    title_font={'size': 12},
                    xaxis_title='Progress',
                    yaxis_title='Low Sonority',
                    legend_title='Title',
                    height=800,
                    width=1200,
                )
                st.plotly_chart(scatter_fig, use_container_width=False)
                scatter_html = scatter_fig.to_html(include_plotlyjs='cdn')
                st.download_button(
                    label="Download Scatter Plot as HTML",
                    data=scatter_html,
                    file_name='sonority_scatter.html',
                    mime='text/html',
                    key='son_scatter_html_dl',
                )

            # table and CSV reflect the same count filter
            son_data_filtered = son_data[son_data['Pattern'].isin(kept_patterns)].copy()

            son_table_mode = st.radio(
                "Table View",
                [
                    "Sonority Ngrams by Composer, Title, Measure and Beat",
                    "Sonority Ngrams with Corpus Count",
                    "Sonority Count by Composer and Title",
                ],
                horizontal=True,
                key='son_ng_table_mode'
            )

            if son_table_mode == "Sonority Ngrams by Composer, Title, Measure and Beat":
                display_df = son_data_filtered.drop(columns=['Pattern'], errors='ignore').copy()
                for col in display_df.columns:
                    display_df[col] = display_df[col].apply(
                        lambda v: ', '.join(str(x) for x in v) if isinstance(v, (list, tuple)) else v)
                if 'Measure' in display_df.columns:
                    display_df['Measure'] = pd.to_numeric(display_df['Measure'], errors='coerce').round(0).astype('Int64')
                if 'Beat' in display_df.columns:
                    display_df['Beat'] = pd.to_numeric(display_df['Beat'], errors='coerce').round(2)
                table_son = display_df

            elif son_table_mode == "Sonority Ngrams with Corpus Count":
                table_son = (
                    son_data_filtered.groupby('Pattern')
                    .size()
                    .reset_index(name='Count')
                    .sort_values('Count', ascending=False)
                    .reset_index(drop=True)
                )

            else:  # Sonority Count by Composer and Title
                group_cols = [c for c in ['Composer', 'Title', 'Pattern'] if c in son_data_filtered.columns]
                table_son = (
                    son_data_filtered.groupby(group_cols)
                    .size()
                    .reset_index(name='Count')
                    .sort_values(['Composer', 'Title', 'Count'] if 'Composer' in group_cols else ['Title', 'Count'],
                                 ascending=[True, True, False] if 'Composer' in group_cols else [True, False])
                    .reset_index(drop=True)
                )

            show_table = st.checkbox('Show Table', key='son_ng_show_table')
            if show_table:
                st.dataframe(table_son, use_container_width=True)
            st.download_button(
                label="Download Filtered Sonority Ngram Data as CSV",
                data=table_son.to_csv(index=False),
                file_name='sonority_ngram_results.csv',
                mime='text/csv',
                key='son_ng_dl',
                )

# hr functions
