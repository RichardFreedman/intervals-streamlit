"""Explore Durations"""
import streamlit as st
from crim_app.common import *
from crim_app.filters import *

piece, corpus, corpus_length, crim_piece_selections, uploaded_files_list = get_selection()

# durations
@st.cache_data(**PIECE_CACHE)
def piece_durs(piece):
    # combineRests=False: each written rest keeps its own length. Combined rests
    # (the default for notes()) merge a voice's whole wait before an entry into
    # one long "duration" (40 or 60 quarter notes), which swamps the chart.
    nr = piece.notes(combineRests=False)
    dur = piece.durations(df=nr)
    dur = piece.numberParts(dur)
    dur = dur.assign(Composer=piece.metadata['composer'], Title=piece.metadata['title'])
    cols_to_move = ['Composer', 'Title']
    dur_clean = dur[cols_to_move + [col for col in dur.columns if col not in cols_to_move]]

    # # Identify the id_vars and value_vars
    id_vars = ['Composer', 'Title']
    value_vars = [col for col in dur_clean.columns if col not in id_vars]

    # # Melt the DataFrame
    dur_melted = pd.melt(
        dur_clean,
        id_vars=id_vars,
        value_vars=value_vars,
        var_name='Voice',
        value_name='Duration'
    )

    dur_melted = dur_melted.dropna().copy()
    
    # pd.melt drops the settings crim_intervals recorded on dur; keep them for chart titles
    return carry_settings(dur_melted, dur)
    1

@st.cache_data(**PIECE_CACHE)
def corpus_durs(corpus):
    func1 = ImportedPiece.notes  # <- NB there are no parentheses here
    # combineRests=False: keep each written rest separate (see piece_durs)
    list_of_note_dfs = corpus.batch(func = func1,
                                kwargs = {'combineRests': False},
                                metadata=False)
    func2 = ImportedPiece.durations  # <- NB there are no parentheses here
    list_of_dur_dfs = corpus.batch(func = func2,
                                 kwargs = {'df': list_of_note_dfs},
                                metadata=False)
    func3 = ImportedPiece.numberParts
    list_of_number_dfs = corpus.batch(func = func3,
                               kwargs = {'df': list_of_dur_dfs},
                               metadata=False)
    func4 = ImportedPiece.detailIndex
    list_of_det_dfs = corpus.batch(func = func4, 
                            kwargs = {'df': list_of_number_dfs}, 
                            metadata = True)
    dur = pd.concat(list_of_det_dfs)
    # reset index to get meas and beat out of the index
    dur = dur.reset_index()
    # Drop the Measure, Beat, and Date columns
    dur_clean = dur.drop(columns=['Measure', 'Beat', 'Date'])

    # Identify the id_vars and value_vars
    id_vars = ['Composer', 'Title']
    value_vars = [col for col in dur_clean.columns if col not in id_vars]

    # Melt the DataFrame
    dur_melted = pd.melt(
        dur_clean,
        id_vars=id_vars,
        value_vars=value_vars,
        var_name='Voice',
        value_name='Duration'
    )

    dur_melted = dur_melted.dropna().copy()

    # pd.melt drops the settings crim_intervals recorded on dur; keep them for chart titles
    return carry_settings(dur_melted, dur)
    

# durs form
# Durations form in sidebar

# Move the main content outside of the sidebar
st.subheader("Explore Durations")
with st.expander("How to use this tool"):
    st.markdown("""
    **About this tool**
    This tool analyzes the lengths of notes and rests in the selected piece(s), showing how often
    each duration value appears across voices. Durations are expressed as float values in
    quarter-note units (e.g., 1.0 = quarter note, 2.0 = half note, 0.5 = eighth note).

    **Key settings**
    There are no configuration options for this tool — just select your piece(s) and click
    **Update and Run Search**.
    - **View by Voice** — when checked, the chart and table break down durations separately for
      each voice. When unchecked, all voices are combined into a single distribution.

    **Reading the results**
    - The **bar chart** shows how often each duration value appears, ordered from shortest to longest.
      Voices are shown in different colors when "View by Voice" is checked.
    - The **table** shows Composer, Title, Voice (if by voice), Duration, and Count.
    - Common values: 0.5 = eighth note, 1.0 = quarter note, 1.5 = dotted quarter,
      2.0 = half note, 3.0 = dotted half, 4.0 = whole note, 8.0 = breve.
    - **Rests** are counted one written rest at a time (they are not combined), so a voice
      that waits several bars before it enters adds several breve rests, not one very long rest.
    - **Note:** if you change the **View by Voice** setting, uncheck and re-check **Show Table** to
      refresh the table with the updated view.

    [Know the code — CRIM Intervals durations documentation](https://github.com/HCDigitalScholarship/intervals/blob/main/tutorial/03_Durations.md)
    """)

if len(crim_piece_selections) == 0 and len(uploaded_files_list) == 0:
    st.write("**No Files Selected! Please Select or Upload One or More Pieces.**")
else:
    # exclude_rests = st.checkbox("Exclude Rests", value=False, key="dur_exclude_rests")
    # Form submission button
    submitted = st.button("Update and Run Search", key="durations_search")

    if submitted:
        # Clear previous results if they exist
        if 'dur' in st.session_state:
            del st.session_state.dur
            
        # For one piece
        if corpus_length == 1:
            dur = piece_durs(piece)
        # For corpus
        elif corpus_length > 1:
            dur = corpus_durs(st.session_state.corpus)
            
        if "dur" not in st.session_state:
            st.session_state.dur = dur
    
    # Display results if they exist
    if 'dur' in st.session_state:

        if len(st.session_state.dur.fillna('')) > 100000:
            st.write("Results are too large to display; please filter again")
        else:
            filtered_dur = filter_dataframe_dur(st.session_state.dur.fillna(''))
            dur_source = st.session_state.dur   # carries the crim_intervals settings
            dur = filtered_dur.data.copy()

            # For one piece
            if corpus_length == 1:
                composer = dur.iloc[0]["Composer"]
                title = dur.iloc[0]["Title"]
                dur_counts = dur.groupby(['Composer', 'Title', 'Voice', 'Duration']).size().reset_index(name='Count')
                sorted_dur = dur_counts.sort_values('Duration').reset_index(drop=True)

                # view by voice toggle
                view_by_voice_dur = st.checkbox("View by Voice", value=True, key='dur_single_view_by_voice')

                if view_by_voice_dur:
                    chart_data_dur = sorted_dur
                    table_data_dur = sorted_dur
                    dur_chart = px.bar(chart_data_dur,
                                    x='Duration',
                                    y='Count',
                                    color='Voice',
                                    title=settings_title(f"Distribution of Durations in {composer}, {title}", dur_source, 'rests not combined'))
                    dur_chart.update_layout(xaxis_title="Duration",
                                            yaxis_title="Count",
                                            legend_title="Voice")
                else:
                    chart_data_dur = (
                        sorted_dur.groupby('Duration', as_index=False)['Count']
                        .sum()
                        .sort_values('Duration')
                        .reset_index(drop=True)
                    )
                    table_data_dur = (
                        sorted_dur.groupby(['Composer', 'Title', 'Duration'], as_index=False)['Count']
                        .sum()
                        .sort_values(['Composer', 'Title', 'Duration'])
                        .reset_index(drop=True)
                    )
                    dur_chart = px.bar(chart_data_dur,
                                    x='Duration',
                                    y='Count',
                                    title=settings_title(f"Distribution of Durations in {composer}, {title}", dur_source, 'rests not combined',
                                                         'voices combined'))
                    dur_chart.update_layout(xaxis_title="Duration",
                                            yaxis_title="Count")

                # and show results
                pio.templates.default = 'plotly'
                container = st.container()
                col1, col2 = container.columns([10, 2])

                # Plot chart in first column
                with col1:
                    st.plotly_chart(dur_chart, use_container_width=True)

                # Add download button in second column
                with col2:
                    st.markdown("")
                    if st.button('📥 Prepare Durations Chart for Download', key='dur_corpus_download'):
                        st.download_button(
                            label="Download the Chart",
                            data=plotly_fig_to_html(dur_chart.to_json(), f"Duration Chart - {composer} - {title}"),
                            file_name=f"{composer}_{title}_durations_chart.html",
                            mime="text/html"
                        )

                if st.checkbox('Show Table of Durations'):
                    st.dataframe(table_data_dur, use_container_width=True)

                    st.download_button(
                        label="Download Filtered Durations Data as CSV",
                        data=table_data_dur.to_csv(index=False),
                        file_name=piece.metadata['title'] + '_durations_results.csv',
                        mime='text/csv',
                        key=3,
                        )

            # For corpus
            if corpus_length > 1:
                dur_counts = dur.groupby(['Composer', 'Title', 'Voice', 'Duration']).size().reset_index(name='Count')
                sorted_dur = dur_counts.sort_values('Duration').reset_index(drop=True)

                # plot
                # make plot
                color_grouping = st.radio(
                    "Select Color Grouping",
                    ['Composer', 'Title', 'Voice'],
                    index=0,  # Pre-select the first option (default)
                    horizontal=True,  # Display options horizontally
                    captions=["Color by Composer", "Color by Title", "Color by Voice"],
                    key='dur_color_grouping'
                )
                
                titles = dur_counts['Title'].unique()
                dur_chart = px.bar(dur_counts, 
                                x='Duration', 
                                y='Count',
                                color=color_grouping,
                                title=settings_title("Distribution of Durations in Corpus", dur_source, 'rests not combined',
                                                     f"colored by {color_grouping.lower()}", n_pieces_label(dur)))
                dur_chart.update_layout(xaxis_title="Duration", 
                                        yaxis_title="Count",
                                        legend_title=color_grouping)

                pio.templates.default = 'plotly'
                container = st.container()
                col1, col2 = container.columns([10, 2])
                
                # Plot chart in first column
                with col1:
                    st.plotly_chart(dur_chart, use_container_width=True, )
                    
                # Add download button in second column
                with col2:
                    st.markdown("")
                    if st.button('📥 Prepare Durations Chart for Download', key='dur_single_download'):
                        st.download_button(
                            label="Download the Chart",
                            data=plotly_fig_to_html(dur_chart.to_json(), "Durations in Corpus"),
                            file_name="corpus_durations_chart.html",
                            mime="text/html"
                        )                    
                if st.checkbox('Show Table of Durations'):
                    table_dur = (
                        sorted_dur.groupby([color_grouping, 'Duration'], as_index=False)['Count']
                        .sum()
                        .sort_values([color_grouping, 'Duration'])
                        .reset_index(drop=True)
                    )
                    st.dataframe(table_dur, use_container_width=True)

                    # Download option
                    st.download_button(
                        label="Download Filtered Corpus Durations Data as CSV",
                        data=table_dur.to_csv(index=False),
                        file_name='corpus_durations_results.csv',
                        mime='text/csv',
                        key=4,
                    )

# weighted notes function updated

# helper 

