"""Explore Melodic Intervals"""
import streamlit as st
from crim_app.common import *
from crim_app.filters import *

piece, corpus, corpus_length, crim_piece_selections, uploaded_files_list = get_selection()

# melodic functions
@st.cache_data(**PIECE_CACHE)
def piece_mel(piece, combine_unisons_choice, combine_rests_choice, kind_choice, directed, compound):
    nr = piece.notes(combineUnisons = combine_unisons_choice,
                              combineRests = combine_rests_choice)
    
    nr = piece.numberParts(nr)
    mel = piece.melodic(df = nr, 
                        kind = kind_choice,
                        directed = directed,
                        compound = compound)
    mel = piece.detailIndex(mel)
    # mel = mel.reset_index()
    mel = mel.assign(Composer=piece.metadata['composer'], Title=piece.metadata['title'], Date=piece.metadata['date'])
    cols_to_move = ['Composer', 'Title', 'Date']
    mel = mel[cols_to_move + [col for col in mel.columns if col not in cols_to_move]]
    mel = mel.reset_index()
    # Drop the Measure, Beat, and Date columns
    mel_clean = mel.drop(columns=['Measure', 'Beat', 'Date'])

    # Identify the id_vars and value_vars
    id_vars = ['Composer', 'Title']
    value_vars = [col for col in mel_clean.columns if col not in id_vars]

    # Melt the DataFrame
    mel_melted = pd.melt(
        mel_clean,
        id_vars=id_vars,
        value_vars=value_vars,
        var_name='Voice',
        value_name='Interval'
    )
    
    mel_melted = mel_melted.dropna().copy()
    
    
    return mel_melted

@st.cache_data(**PIECE_CACHE)
def corpus_mel(corpus, combine_unisons_choice, combine_rests_choice, kind_choice, directed, compound):
    func = ImportedPiece.notes  # <- NB there are no parentheses here
    list_of_dfs = corpus.batch(func = func, 
                                kwargs = {'combineUnisons': combine_unisons_choice, 'combineRests': combine_rests_choice}, 
                                metadata=False)
    
    func1 = ImportedPiece.numberParts
    list_of_dfs = corpus.batch(func = func1,
                               kwargs = {'df': list_of_dfs},
                               metadata=False)
    
    func2 = ImportedPiece.melodic
    list_of_dfs = corpus.batch(func = func2,
                               kwargs = {'df' : list_of_dfs, 'kind' : kind_choice, 'directed' : directed, 'compound' : compound},
                               metadata = False)
    func3 = ImportedPiece.detailIndex
    list_of_dfs = corpus.batch(func = func3, 
                            kwargs = {'df': list_of_dfs}, 
                            metadata = True)
    mel = pd.concat(list_of_dfs)
    # no longer needed for melt approach
    # reset index to get meas and beat out of the index
    mel = mel.reset_index()
    # Drop the Measure, Beat, and Date columns
    mel_clean = mel.drop(columns=['Measure', 'Beat', 'Date'])

    # Identify the id_vars and value_vars
    id_vars = ['Composer', 'Title']
    value_vars = [col for col in mel_clean.columns if col not in id_vars]

    # Melt the DataFrame
    mel_melted = pd.melt(
        mel_clean,
        id_vars=id_vars,
        value_vars=value_vars,
        var_name='Voice',
        value_name='Interval'
    )

    mel_melted = mel_melted.dropna().copy()

    return mel_melted

# melodic form

search_type = "mel"
st.subheader("Explore Melodic Intervals")
with st.expander("How to use this tool"):
    st.markdown("""
    **About this tool**
    This tool analyzes the intervallic distance between consecutive notes within each voice part,
    revealing patterns of melodic motion. Results show how pitches move step by step through the piece.

    **Key settings**
    - **Combine Unisons** — if True, consecutive repeated pitches in a voice are treated as one
      sustained note, so no unison interval is recorded between them.
    - **Combine Rests** — if True, consecutive rests are merged, reducing clutter in the interval data.
    - **Interval Kind** — how intervals are represented:
      - *Diatonic* — scale-step distance only, e.g. "3" for any third
      - *With Quality* — diatonic with quality, e.g. "M3" or "m3"
      - *Chromatic* — distance in semitones, e.g. "4" for a major third
      - *Zero-based Diatonic* — like diatonic but unisons are "0" rather than "1"
    - **Directed** — if True, ascending intervals are positive and descending are negative.
      If False, only the absolute size is reported.
    - **Compound** — if True, intervals larger than an octave are kept as-is (e.g. a tenth stays "10").
      If False, they are reduced to their simple equivalent within an octave.

    **Reading the results**
    - The chart shows the distribution of melodic intervals in the piece or corpus, according to
      the settings selected above.
    - Color grouping options allow you to view the distribution by Composer, Title, or Voice.
      The table automatically follows the same grouping.
    - **Note:** if you change the **View by Voice** setting, uncheck and re-check **Show Table** to
      refresh the table with the updated view.

    [Know the code — CRIM Intervals melodic interval documentation](https://github.com/HCDigitalScholarship/intervals/blob/main/tutorial/06_Melodic_Intervals.md)
    """)
if len(crim_piece_selections) == 0 and len(uploaded_files_list)== 0:
    st.write("**No Files Selected! Please Select or Upload One or More Pieces.**")
else:
    form_col, _ = st.columns([1, 2])
    with form_col:
     with st.form("Melodic Interval Settings"):
        combine_unisons_choice = st.selectbox(
            "Combine Unisons", [False, True])
        combine_rests_choice = st.selectbox(
            "Combine Rests", [True, False])
        select_kind = st.selectbox(
            "Select Interval Kind", 
            ["diatonic", "chromatic", "with quality", "zero-based diatonic"])
        kind_choice = interval_kinds[select_kind]
        directed = st.selectbox(
            "Select Directed Interval Status",
            [True, False])
        compound = st.selectbox(
            "Select Compound Interval Status",
            [True, False])
        # form submission button
        submitted = st.form_submit_button("Update and Submit")
        if submitted:
            # run the function here, passing in settings from the form above
            if 'mel' in st.session_state:
                del st.session_state.mel
            # run the function here, passing in settings from the form above
            if corpus_length == 1:
                mel = piece_mel(piece,
                            combine_unisons_choice, 
                            combine_rests_choice, 
                            kind_choice,
                            directed,
                            compound)
            elif corpus_length  > 1:
                mel = corpus_mel(st.session_state.corpus,
                            combine_unisons_choice, 
                            combine_rests_choice, 
                            kind_choice,
                            directed,
                            compound)  
            if "mel" not in st.session_state:
                st.session_state.mel = mel 
    # and use the session state variables for display
    if 'mel' not in st.session_state:
        pass
    else:
        # show corpus data for mel with filter options
        st.write("Filter Results by Contents of Each Column")
        # st.dataframe(st.session_state.mel)
        if len(st.session_state.mel.fillna('')) > 100000:
            print("Results are too large to display; please filter again")
        else:
            filtered_mel = filter_dataframe_mel(st.session_state.mel.fillna(''))   
            st.write("Did you **change the filter**?  If so, please **Update and Submit form**")    
            # for one piece
            if corpus_length  == 1: 
                # 
                mel = filtered_mel.data.copy()
                composer = mel.iloc[0]['Composer']
                title = mel.iloc[0]['Title']
                
                if interval_kinds[select_kind] == 'q':
                    mel_interval_counts = mel.groupby(['Composer', 'Title', 'Voice', 'Interval']).size().reset_index(name='Count')
                    # remove rests
                    mel_int_counts_no_rest = mel_interval_counts[mel_interval_counts['Interval'] != 'Rest']
                    # mel_int_counts_no_rest['Interval'] = mel_int_counts_no_rest['Interval'].astype('str')
                    # apply the categorical list and sort.  
                    mel_int_counts_no_rest['Interval'] = pd.CategoricalIndex(mel_int_counts_no_rest['Interval'], categories=interval_order_quality, ordered=True)
                    sorted_mel = mel_int_counts_no_rest.sort_values('Interval').reset_index(drop=True)
                    # st.dataframe(sorted_mel)
                else:
                    mel_interval_counts = mel.groupby(['Composer', 'Title', 'Voice', 'Interval']).size().reset_index(name='Count')
                    # remove rests
                    mel_int_counts_no_rest = mel_interval_counts[mel_interval_counts['Interval'] != 'Rest']
                    mel_int_counts_no_rest['Interval'] = mel_int_counts_no_rest['Interval'].astype('int64')
                    # sorting
                    sorted_mel = mel_int_counts_no_rest.sort_values(by='Interval', ascending=True)
                    
                # view by voice toggle
                view_by_voice_mel = st.checkbox("View by Voice", value=True, key='mel_single_view_by_voice')

                if view_by_voice_mel:
                    chart_data_mel = sorted_mel
                    table_data_mel = sorted_mel
                    mel_chart = px.bar(chart_data_mel,
                                    x='Interval',
                                    y='Count',
                                    color='Voice',
                                    title=f"Distribution of Intervals in {composer}, {title}")
                    mel_chart.update_layout(xaxis_title="Interval",
                                            yaxis_title="Count",
                                            legend_title="Voice")
                else:
                    chart_data_mel = (
                        sorted_mel.groupby('Interval', as_index=False)['Count']
                        .sum()
                        .sort_values('Interval')
                        .reset_index(drop=True)
                    )
                    table_data_mel = chart_data_mel
                    mel_chart = px.bar(chart_data_mel,
                                    x='Interval',
                                    y='Count',
                                    title=f"Distribution of Intervals in {composer}, {title}")
                    mel_chart.update_layout(xaxis_title="Interval",
                                            yaxis_title="Count")

                # and show results
                pio.templates.default = 'plotly'

                container = st.container()
                col1, col2 = container.columns([10, 2])

                # Plot chart in first column
                with col1:
                    st.plotly_chart(mel_chart, use_container_width=True)

                # Add download button in second column
                with col2:
                    st.markdown("")
                    if st.button('📥 Prepare Melodic Chart for Download', key='mel_corpus_download'):
                        st.download_button(
                            label="Download the Chart",
                            data=plotly_fig_to_html(mel_chart.to_json(), f"Melodic Interval Chart - {composer} - {title}"),
                            file_name=f"{composer}_{title}_mel_chart.html",
                            mime="text/html"
                        )

                if st.checkbox("Show Table of Melodic Intervals"):
                    st.dataframe(table_data_mel, use_container_width=True)

                    st.download_button(
                        label="Download Filtered Melodic Data as CSV",
                        data=table_data_mel.to_csv(index=False),
                        file_name=f'{composer}_{title}_melodic_intervals.csv',
                        mime='text/csv',
                        key=5,
                        )
            # # for corpus
            elif corpus_length > 1:
                mel = filtered_mel.data.copy()  
                if interval_kinds[select_kind] == 'q':
                    # remove rests
                    # mel = filtered_mel
                    mel_interval_counts = mel.groupby(['Composer', 'Title', 'Voice', 'Interval']).size().reset_index(name='Count')
                    mel_int_counts_no_rest = mel_interval_counts[mel_interval_counts['Interval'] != 'Rest']
                    # apply the categorical list and sort.
                    mel_int_counts_no_rest['Interval'] = pd.CategoricalIndex(mel_int_counts_no_rest['Interval'], categories=interval_order_quality, ordered=True)
                    sorted_mel = mel_int_counts_no_rest.sort_values('Interval').reset_index(drop=True)
                    # st.dataframe(sorted_mel)
                else:
                    mel_interval_counts = mel.groupby(['Composer', 'Title', 'Voice', 'Interval']).size().reset_index(name='Count')
                    # remove rests
                    mel_interval_counts_no_rest = mel_interval_counts[mel_interval_counts['Interval'] != 'Rest']
                    # sorting
                    sorted_mel = mel_interval_counts_no_rest.sort_values(by='Interval', ascending=True)

                # make plot
                color_grouping = st.radio(
                    "Select Color Grouping",
                    ['Composer', 'Title', 'Voice'],
                    index=0,  # Pre-select the first option (default)
                    horizontal=True,  # Display options horizontally
                    captions=["Color by Composer", "Color by Title", "Color by Voice"],
                    key='mel_color_grouping'
                )
                mel_chart = px.bar(sorted_mel, 
                                x='Interval', 
                                y='Count',
                                color=color_grouping,
                                title="Distribution of Intervals in Corpus")
                mel_chart.update_layout(xaxis_title="Interval", 
                                        yaxis_title="Count",
                                        legend_title=color_grouping)
                # and show results

                    # and show results
                pio.templates.default = 'plotly'

                container = st.container()
                col1, col2 = container.columns([10, 2])
                
                # Plot chart in first column
                with col1:
                    st.plotly_chart(mel_chart, use_container_width=True)
                    
                # Add download button in second column
                with col2:
                    st.markdown("")
                    if st.button('📥 Prepare Melodic Chart for Download', key='mel_single_download'):
                        st.download_button(
                            label="Download the Chart",
                            data=plotly_fig_to_html(mel_chart.to_json(), "Corpus Melodic Interval Chart"),
                            file_name="corpus_mel_chart.html",
                            mime="text/html"
                        )

                if st.checkbox("Show Table of Melodic Intervals"):
                    table_mel = (
                        sorted_mel.groupby([color_grouping, 'Interval'], as_index=False)['Count']
                        .sum()
                        .sort_values([color_grouping, 'Interval'])
                        .reset_index(drop=True)
                    )
                    st.dataframe(table_mel, use_container_width=True)

                    st.download_button(
                        label="Download Filtered Melodic Data as CSV",
                        data=table_mel.to_csv(index=False),
                        file_name='corpus_melodic_intervals.csv',
                        mime='text/csv',
                        key=6,
                        )
    
