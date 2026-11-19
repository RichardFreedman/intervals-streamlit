"""Explore Harmonic Intervals"""
import streamlit as st
from crim_app.common import *
from crim_app.filters import *

piece, corpus, corpus_length, crim_piece_selections, uploaded_files_list = get_selection()

# harmonic functions
@st.cache_data(**PIECE_CACHE)
def piece_har(piece, kind_choice, directed, compound, against_low):
    nr = piece.notes()
    nr = piece.numberParts(nr)
    har = piece.harmonic(df=nr,
                         kind = kind_choice, 
                         directed = directed,
                         compound = compound,
                         againstLow = against_low).fillna('')
    har = piece.detailIndex(har)
    # har = har.reset_index()
    har = har.assign(Composer=piece.metadata['composer'], Title=piece.metadata['title'], Date=piece.metadata['date'])
    cols_to_move = ['Composer', 'Title', 'Date']
    har = har[cols_to_move + [col for col in har.columns if col not in cols_to_move]]
    har = har.reset_index()
    # Drop the Measure, Beat, and Date columns
    har_clean = har.drop(columns=['Measure', 'Beat', 'Date'])

    # Identify the id_vars and value_vars
    id_vars = ['Composer', 'Title']
    value_vars = [col for col in har_clean.columns if col not in id_vars]

    # Melt the DataFrame
    har_melted = pd.melt(
        har_clean,
        id_vars=id_vars,
        value_vars=value_vars,
        var_name='Voices',
        value_name='Interval'
    )
    
    har_melted = har_melted.dropna().copy()
    
    
    # pd.melt drops the settings crim_intervals recorded on har; keep them for chart titles
    return carry_settings(har_melted, har)

@st.cache_data(**PIECE_CACHE)
def corpus_har(corpus, kind_choice, directed, compound, against_low):
    
    func = ImportedPiece.notes  # <- NB there are no parentheses here
    list_of_dfs = corpus.batch(func = func, 
                                # kwargs = {'combineUnisons': combine_unisons_choice, 'combineRests': combine_rests_choice}, 
                                metadata=False)
    
    func1 = ImportedPiece.numberParts
    list_of_dfs = corpus.batch(func = func1,
                               kwargs = {'df': list_of_dfs},
                               metadata=False)
    
    
    func2 = ImportedPiece.harmonic
    list_of_dfs = corpus.batch(func = func2,
                               kwargs = {'df': list_of_dfs,
                                         'kind' : kind_choice, 
                                         'directed' : directed, 
                                         'compound' : compound, 
                                         'againstLow' : against_low},
                               metadata = False)
    func3 = ImportedPiece.detailIndex
    list_of_dfs = corpus.batch(func = func3, 
                            kwargs = {'df': list_of_dfs}, 
                            metadata = True)
    har = pd.concat(list_of_dfs)
    har = har.reset_index()
    # Drop the Measure, Beat, and Date columns
    har_clean = har.drop(columns=['Measure', 'Beat', 'Date'])

    # Identify the id_vars and value_vars
    id_vars = ['Composer', 'Title']
    value_vars = [col for col in har_clean.columns if col not in id_vars]

    # Melt the DataFrame
    har_melted = pd.melt(
        har_clean,
        id_vars=id_vars,
        value_vars=value_vars,
        var_name='Voices',
        value_name='Interval'
    )

    har_melted = har_melted.dropna().copy()

    # pd.melt drops the settings crim_intervals recorded on har; keep them for chart titles
    return carry_settings(har_melted, har)


# harmonic form

search_type = "har"
st.subheader("Explore Harmonic Intervals")
with st.expander("How to use this tool"):
    st.markdown("""
    **About this tool**
    This tool examines the intervals between simultaneously sounding voices, revealing the vertical
    harmony of a piece or corpus. Rather than melodic motion within a single part, harmonic intervals
    describe the relationships between pairs of voices at each moment.

    **Key settings**
    - **Interval Kind** — how intervals are represented:
      - *Diatonic* — scale-step distance only, e.g. "3" for any third
      - *With Quality* — diatonic with quality, e.g. "M3" or "m3"
      - *Chromatic* — distance in semitones, e.g. "4" for a major third
      - *Zero-based Diatonic* — like diatonic but unisons are "0" rather than "1"
    - **Directed** — if True, intervals above the reference voice are positive and below are negative.
      If False, only absolute size is reported.
    - **Compound** — if True, intervals larger than an octave are kept as-is (e.g. a tenth stays "10").
      If False, they are reduced to their simple equivalent within an octave.
    - **Calculate Intervals Only Against Lowest Voice** — if True, each voice is measured only against
      the lowest sounding voice, giving a figured-bass style view. If False, all possible voice pairs
      are calculated.

    **Reading the results**
    - The chart shows the distribution of harmonic intervals in the piece or corpus, according to
      the settings selected above.
    - Color grouping options allow you to view the distribution by Composer, Title, or Voice pair.
      The table automatically follows the same grouping.

    [Know the code — CRIM Intervals harmonic interval documentation](https://github.com/HCDigitalScholarship/intervals/blob/main/tutorial/07_Harmonic_Intervals_Sonorities.md) ·
    [Charts with Plotly](https://github.com/HCDigitalScholarship/intervals/blob/main/tutorial/17_Visualizations_Summary.md#bar-charts-with-melodic-and-harmonic-intervals)
    """)
if len(crim_piece_selections) == 0 and len(uploaded_files_list)== 0:
    st.write("**No Files Selected! Please Select or Upload One or More Pieces.**")
else:
    form_col = st.container()
    with form_col:
     with st.form("Harmonic Interval Settings"):
        _fc = st.columns(4)   # settings side by side
        directed = _fc[0].selectbox(
            "Select Directed Interval Status",
            [True, False])
        compound = _fc[1].selectbox(
            "Select Compound Interval Status",
            [True, False])
        select_kind = _fc[2].selectbox(
            "Select Interval Kind", 
            ["diatonic", "chromatic", "with quality", "zero-based diatonic"])
        kind_choice = interval_kinds[select_kind]
        against_low = _fc[3].selectbox("Calculate Intervals Only Against Lowest Voice", 
                                [False, True])
        # form submission button
        submitted = st.form_submit_button("Update and Submit")
        if submitted:
            # run the function here, passing in settings from the form above
            if 'har' in st.session_state:
                del st.session_state.har
            # run the function here, passing in settings from the form above
            if corpus_length == 1:
                har = piece_har(piece,
                            kind_choice,
                            directed,
                            compound,
                            against_low)
            elif corpus_length > 1:
                har = corpus_har(st.session_state.corpus,
                            kind_choice,
                            directed,
                            compound,
                            against_low)
            
            if "har" not in st.session_state:
                st.session_state.har = har
    # and use the session state variables for display
    if 'har' not in st.session_state:
        pass
    else:
        # count up the values in each item column--sum for each pitch. make a copy 
        if len(st.session_state.har.fillna('')) > 100000:
            print("Results are too large to display; please filter again")
        else:
            filtered_har = filter_dataframe_har(st.session_state.har.fillna(''))
            har_source = st.session_state.har   # carries the crim_intervals settings
            st.write("Did you **change the filter**?  If so, please **Update and Submit form**")    
            # for one piece
            if corpus_length  == 1: 
                # 
                har = filtered_har.data.copy()
                
                if interval_kinds[select_kind] == 'q':
                    har_interval_counts = har.groupby(['Composer', 'Title', 'Voices', 'Interval']).size().reset_index(name='Count')
                    # remove rests
                    har_int_counts_no_rest = har_interval_counts[har_interval_counts['Interval'] != 'Rest']
                    # har_int_counts_no_rest['Interval'] = har_int_counts_no_rest['Interval'].astype('int64')
                    # apply the categorical list and sort.  
                    har_int_counts_no_rest['Interval'] = pd.CategoricalIndex(har_int_counts_no_rest['Interval'], categories=interval_order_quality, ordered=True)
                    sorted_har = har_int_counts_no_rest.sort_values('Interval').reset_index(drop=True)
                else:
                    har_interval_counts = har.groupby(['Composer', 'Title', 'Voices', 'Interval']).size().reset_index(name='Count')
                    # remove rests
                    har_int_counts_no_rest = har_interval_counts[har_interval_counts['Interval'] != 'Rest']
                    # har_int_counts_no_rest['Interval'] = har_int_counts_no_rest['Interval'].astype('int64')
                    # sorting
                    sorted_har = har_int_counts_no_rest.sort_values(by='Interval', ascending=True)
                    
                composer = har.iloc[0]['Composer']
                title = har.iloc[0]['Title']

                # view by voices toggle
                view_by_voices_har = st.checkbox("View by Voices", value=True, key='har_single_view_by_voices')

                if view_by_voices_har:
                    chart_data_har = sorted_har
                    table_data_har = sorted_har
                    har_chart = px.bar(chart_data_har,
                                    x='Interval',
                                    y='Count',
                                    color='Voices',
                                    title=settings_title(f"Distribution of Harmonic Intervals in {composer}, {title}", har_source))
                    har_chart.update_layout(xaxis_title="Interval",
                                            yaxis_title="Count",
                                            legend_title="Voices")
                else:
                    chart_data_har = (
                        sorted_har.groupby('Interval', as_index=False)['Count']
                        .sum()
                        .sort_values('Interval')
                        .reset_index(drop=True)
                    )
                    table_data_har = chart_data_har
                    har_chart = px.bar(chart_data_har,
                                    x='Interval',
                                    y='Count',
                                    title=settings_title(f"Distribution of Harmonic Intervals in {composer}, {title}", har_source,
                                                         'voice pairs combined'))
                    har_chart.update_layout(xaxis_title="Interval",
                                            yaxis_title="Count")

                # and show results
                pio.templates.default = 'plotly'

                container = st.container()
                col1, col2 = container.columns([10, 2])

                # Plot chart in first column
                with col1:
                    st.plotly_chart(har_chart, use_container_width=True)

                # Add download button in second column
                with col2:
                    st.markdown("")
                    if st.button('📥 Prepare Harmonic Chart for Download', key='har_corpus_download'):
                        st.download_button(
                            label="Download the Chart",
                            data=plotly_fig_to_html(har_chart.to_json(), f"Harmonic Interval Chart - {composer} - {title}"),
                            file_name=f"{composer}_{title}_har_chart.html",
                            mime="text/html"
                        )

                if st.checkbox("Show Table of Harmonic Intervals"):
                    st.dataframe(table_data_har, use_container_width=True)

                    st.download_button(
                        label="Download Filtered Harmonic Data as CSV",
                        data=table_data_har.to_csv(index=False),
                        file_name=f'{composer}_{title}_harmonic_intervals.csv',
                        mime='text/csv',
                        key=7,
                        )
            # # for corpus
            elif corpus_length > 1:
                har = filtered_har.data.copy()
                if interval_kinds[select_kind] == 'q':
                    # remove rests
                    har_interval_counts = har.groupby(['Composer', 'Title', 'Voices', 'Interval']).size().reset_index(name='Count')
                    har_int_counts_no_rest = har_interval_counts[har_interval_counts['Interval'] != 'Rest']
                    # apply the categorical list and sort.
                    har_int_counts_no_rest['Interval'] = pd.CategoricalIndex(har_int_counts_no_rest['Interval'], categories=interval_order_quality, ordered=True)
                    sorted_har = har_int_counts_no_rest.sort_values('Interval').reset_index(drop=True)
                else:
                    har_interval_counts = har.groupby(['Composer', 'Title', 'Voices', 'Interval']).size().reset_index(name='Count')
                    # remove rests
                    har_interval_counts_no_rest = har_interval_counts[har_interval_counts['Interval'] != 'Rest']
                    # sorting
                    sorted_har = har_interval_counts_no_rest.sort_values(by='Interval', ascending=True)

                # make plot
                color_grouping = st.radio(
                    "Select Color Grouping",
                    ['Composer', 'Title', 'Voices'],
                    index=0,  # Pre-select the first option (default)
                    horizontal=True,  # Display options horizontally
                    captions=["Color by Composer", "Color by Title", "Color by Voices"],
                    key='har_color_grouping'
                )
                har_chart = px.bar(sorted_har, 
                                x='Interval', 
                                y='Count',
                                color=color_grouping,
                                title=settings_title("Distribution of Harmonic Intervals in Corpus", har_source,
                                                     f"colored by {color_grouping.lower()}", n_pieces_label(har)))
                har_chart.update_layout(xaxis_title="Interval", 
                                        yaxis_title="Count",
                                        legend_title=color_grouping)
        
            # show results
            # and show results
                pio.templates.default = 'plotly'

                container = st.container()
                col1, col2 = container.columns([10, 2])
                
                # Plot chart in first column
                with col1:
                    st.plotly_chart(har_chart, use_container_width=True)
                    
                # Add download button in second column
                with col2:
                    st.markdown("")
                    if st.button('📥 Prepare Harmonic Chart for Download', key='har_single_download'):
                        st.download_button(
                            label="Download the Chart",
                            data=plotly_fig_to_html(har_chart.to_json(), "Corpus Harmonic Interval Chart"),
                            file_name="corpus_har_chart.html",
                            mime="text/html"
                        )

                if st.checkbox("Show Table of Harmonic Intervals"):
                    table_har = (
                        sorted_har.groupby([color_grouping, 'Interval'], as_index=False)['Count']
                        .sum()
                        .sort_values([color_grouping, 'Interval'])
                        .reset_index(drop=True)
                    )
                    st.dataframe(table_har, use_container_width=True)

                    st.download_button(
                        label="Download Filtered Harmonic Data as CSV",
                        data=table_har.to_csv(index=False),
                        file_name='corpus_harmonic_intervals.csv',
                        mime='text/csv',
                        key=8,
                        ) 

