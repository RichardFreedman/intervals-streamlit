"""Explore Notes"""
import streamlit as st
from crim_app.common import *
from crim_app.filters import *

piece, corpus, corpus_length, crim_piece_selections, uploaded_files_list = get_selection()

# notes piece
@st.cache_data(**PIECE_CACHE)
def piece_notes(piece, combine_unisons_choice, combine_rests_choice):
    nr = piece.notes(combineUnisons = combine_unisons_choice,
                            combineRests = combine_rests_choice)
    nr = piece.numberParts(nr)
    nr = piece.detailIndex(nr)

    nr = nr.assign(Composer=piece.metadata['composer'], Title=piece.metadata['title'], Date=piece.metadata['date'])
    cols_to_move = ['Composer', 'Title', 'Date']
    nr = nr[cols_to_move + [col for col in nr.columns if col not in cols_to_move]]
    nr = nr.reset_index()
    # Drop the Measure, Beat, and Date columns
    nr_clean = nr.drop(columns=['Measure', 'Beat', 'Date'])

    # Identify the id_vars and value_vars
    id_vars = ['Composer', 'Title']
    value_vars = [col for col in nr_clean.columns if col not in id_vars]

    # Melt the DataFrame
    nr_melted = pd.melt(
        nr_clean,
        id_vars=id_vars,
        value_vars=value_vars,
        var_name='Voice',
        value_name='Note'
    )
    
    nr_melted = nr_melted.dropna().copy()
    # pd.melt drops the settings crim_intervals recorded on nr; keep them for chart titles
    return carry_settings(nr_melted, nr)


@st.cache_data(**PIECE_CACHE)
def corpus_notes(corpus, combine_unisons_choice, combine_rests_choice):
    func = ImportedPiece.notes  # <- NB there are no parentheses here
    list_of_dfs = corpus.batch(func = func, 
                                kwargs = {'combineUnisons': combine_unisons_choice, 'combineRests': combine_rests_choice}, 
                                metadata=False)
    func1 = ImportedPiece.numberParts
    list_of_dfs = corpus.batch(func = func1,
                               kwargs = {'df': list_of_dfs},
                               metadata=False)
    func2 = ImportedPiece.detailIndex
    list_of_dfs = corpus.batch(func = func2, 
                            kwargs = {'df': list_of_dfs}, 
                            metadata = True)
    
    nr = pd.concat(list_of_dfs)
   
    # reset index to get meas and beat out of the index
    nr = nr.reset_index()
    # Drop the Measure, Beat, and Date columns
    nr_clean = nr.drop(columns=['Measure', 'Beat', 'Date'])

    # Identify the id_vars and value_vars
    id_vars = ['Composer', 'Title']
    value_vars = [col for col in nr_clean.columns if col not in id_vars]

    # Melt the DataFrame
    nr_melted = pd.melt(
        nr_clean,
        id_vars=id_vars,
        value_vars=value_vars,
        var_name='Voice',
        value_name='Note'
    )

    nr_melted = nr_melted.dropna().copy()
    # pd.melt drops the settings crim_intervals recorded on nr; keep them for chart titles
    return carry_settings(nr_melted, nr)
    

# notes form

# search_type = "ngram"
st.subheader("Explore Notes")
with st.expander("How to use this tool"):
    st.markdown("""
    **About this tool**
    This tool counts all the notes (by pitch class and octave) in the selected piece(s).

    **Key settings**
    - **Combine Unisons** — if True, consecutive repetitions of the same pitch in a voice are treated as
      one continuous note rather than separate entries.
    - **Combine Rests** — if True, consecutive rests in a voice are merged into a single extended rest
      rather than appearing as individual entries.

    **Reading the results**
    - The results table shows a **count of each note** (identified by pitch class and octave) for each
      voice part or staff, along with Composer and Title.
    - Use this to compare which pitches are most or least common across voices, or across pieces in a corpus.
    - The **bar chart** displays the count of each pitch and octave combination in ascending order.
      By default, voices are shown in different colors. You can combine them into a single distribution
      using the chart settings.
    - **Note:** if you change the **View by Voice** setting, uncheck and re-check **Show Table** to
      refresh the table with the updated view.

    [Know the code — CRIM Intervals notes and rests documentation](https://github.com/HCDigitalScholarship/intervals/blob/main/tutorial/02_Notes_Rests.md) ·
    [Charts with Plotly](https://github.com/HCDigitalScholarship/intervals/blob/main/tutorial/17_Visualizations_Summary.md#bar-graphs-of-notes-in-each-voice)
    """)
if len(crim_piece_selections) == 0 and len(uploaded_files_list)== 0:
    st.write("**No Files Selected! Please Select or Upload One or More Pieces.**")
else:

    form_col = st.container()
    with form_col:
     with st.form("Note Settings"):
        _fc = st.columns(2)   # settings side by side
        combine_unisons_choice = _fc[0].selectbox(
            "Combine Unisons", [False, True])
        combine_rests_choice = _fc[1].selectbox(
            "Combine Rests", [True, False])
        # form submission button
        submitted = st.form_submit_button("Update and Run Search")       
        if submitted:
            # for one piece

            if 'nr' in st.session_state:
                    del st.session_state.nr

            if corpus_length == 1:
                nr = piece_notes(piece,
                            combine_unisons_choice, 
                            combine_rests_choice)
            # # for corpus
            elif corpus_length > 1:
                nr = corpus_notes(st.session_state.corpus,
                        combine_unisons_choice, 
                        combine_rests_choice) 
            if "nr" not in st.session_state:
                    st.session_state.nr = nr

    # and use the session state variables for display
    if 'nr' not in st.session_state:
        pass
    else:
        # filter the nr results
        if len(st.session_state.nr.fillna('')) > 100000:
            print("Results are too large to display; please filter again")
        else:
            filtered_nr = filter_dataframe_nr(st.session_state.nr.fillna(''))
            st.write("Did you **change the filter**?  If so, please **Update and Submit form**")   
            nr = filtered_nr.data.copy()
            nr_source = st.session_state.nr   # carries the crim_intervals settings
            # for one piece
            if corpus_length == 1:
                composer = nr.iloc[0]["Composer"]
                title = nr.iloc[0]["Title"]
                chart_title = settings_title(f"Distribution of Notes in {composer}, {title}", nr_source)
                nr_counts = nr.groupby(['Composer', 'Title', 'Voice', 'Note']).size().reset_index(name='Count')
                nr_counts['Note'] = pd.CategoricalIndex(nr_counts['Note'], categories=pitch_order, ordered=True)
                sorted_nr = nr_counts.sort_values('Note').reset_index(drop=True)

                # view by voice toggle
                view_by_voice = st.checkbox("View by Voice", value=True, key='notes_single_view_by_voice')

                if view_by_voice:
                    chart_data = sorted_nr
                    table_data = sorted_nr
                    nr_chart = px.bar(chart_data,
                                    x='Note',
                                    y='Count',
                                    color='Voice',
                                    title=chart_title)
                    nr_chart.update_layout(xaxis_title="Note",
                                            yaxis_title="Count",
                                            legend_title="Voice")
                else:
                    chart_data = (
                        sorted_nr.groupby('Note', as_index=False)['Count']
                        .sum()
                        .sort_values('Note')
                        .reset_index(drop=True)
                    )
                    _tbl = sorted_nr.copy()
                    _tbl['Note'] = _tbl['Note'].astype(str)
                    table_data = (
                        _tbl.groupby(['Composer', 'Title', 'Note'], as_index=False)['Count']
                        .sum()
                        .sort_values(['Composer', 'Title', 'Note'])
                        .reset_index(drop=True)
                    )
                    nr_chart = px.bar(chart_data,
                                    x='Note',
                                    y='Count',
                                    title=settings_title(f"Distribution of Notes in {composer}, {title}",
                                                         nr_source, 'voices combined'))
                    nr_chart.update_layout(xaxis_title="Note",
                                            yaxis_title="Count")

                # and show results
                pio.templates.default = 'plotly'

                container = st.container()
                col1, col2 = container.columns([10, 2])

                # Plot chart in first column
                with col1:
                    st.plotly_chart(nr_chart, use_container_width=True)

                # Add download button in second column
                with col2:
                    st.markdown("")
                    if st.button('📥 Prepare Notes Chart for Download', key='notes_corpus_download'):
                        st.download_button(
                            label="Download the Chart",
                            data=plotly_fig_to_html(nr_chart.to_json(), f"Note Chart - {composer} - {title}"),
                            file_name=f"{composer}_{title}_notes_chart.html",
                            mime="text/html"
                        )

                if st.checkbox("Show Table of Notes"):
                    st.dataframe(table_data, use_container_width=True)

                    st.download_button(
                        label="Download Filtered Notes Data as CSV",
                        data=table_data.to_csv(index=False),
                        file_name = piece.metadata['title'] + '_notes_results.csv',
                        mime='text/csv',
                        key=1,
                        )
                # Create container for chart and button
                
            # for corpus:
            if corpus_length > 1:  
                nr_counts = nr.groupby(['Composer', 'Title', 'Voice', 'Note']).size().reset_index(name='Count')
                # remove rests
                nr_counts_counts_no_rest = nr_counts[nr_counts['Note'] != 'Rest']
                # sorting
                nr_counts['Note'] = pd.CategoricalIndex(nr_counts['Note'], categories=pitch_order, ordered=True)
                sorted_nr = nr_counts.sort_values('Note').reset_index(drop=True)

                # make plot
                color_grouping = st.radio(
                    "Select Color Grouping",
                    ['Composer', 'Title', 'Voice'],
                    index=0,  # Pre-select the first option (default)
                    horizontal=True,  # Display options horizontally
                    captions=["Color by Composer", "Color by Title", "Color by Voice"],
                    key='notes_color_grouping'
                )
                nr_chart = px.bar(sorted_nr, 
                                x='Note', 
                                y='Count',
                                color=color_grouping,
                                title=settings_title("Distribution of Notes in Corpus", nr_source,
                                                     f"colored by {color_grouping.lower()}",
                                                     n_pieces_label(nr)))
                nr_chart.update_layout(xaxis_title="Note", 
                                        yaxis_title="Count",
                                        legend_title=color_grouping)
                # and show results
                # and show results
                pio.templates.default = 'plotly'
                container = st.container()
                col1, col2 = container.columns([10, 2])
                
                # Plot chart in first column
                with col1:
                    st.plotly_chart(nr_chart, use_container_width=True, )
                    # st.plotly_chart(fig, theme=None)

                    
                # Add download button in second column
                with col2:
                    st.markdown("")
                    if st.button('📥 Prepare Notes Chart for Download', key='notes_single_download'):
                        st.download_button(
                            label="Download the Chart",
                            data=plotly_fig_to_html(nr_chart.to_json(), "Notes in Corpus"),
                            file_name="corpus_notes_chart.html",
                            mime="text/html"
                        )
                
                if st.checkbox("Show Table of Notes"):
                    table_nr = (
                        sorted_nr.groupby([color_grouping, 'Note'], as_index=False)['Count']
                        .sum()
                        .sort_values([color_grouping, 'Note'])
                        .reset_index(drop=True)
                    )
                    st.dataframe(table_nr, use_container_width=True)

                    st.download_button(
                        label="Download Filtered Notes Data as CSV",
                        data=table_nr.to_csv(index=False),
                        file_name = 'corpus_notes_results.csv',
                        mime='text/csv',
                        key=2,
                        )
                # download option       
                
               
