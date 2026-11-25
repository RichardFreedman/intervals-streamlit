"""Explore Presentation Types"""
import streamlit as st
from crim_app.common import *
from crim_app.filters import *

piece, corpus, corpus_length, crim_piece_selections, uploaded_files_list = get_selection()

# piece
@st.cache_data(**PIECE_CACHE)
def piece_presentation_types(piece,
                            length_choice, 
                            limit_entries_choice,
                            body_flex_choice, 
                            head_flex_choice,
                            hidden_types_choice,
                            combine_unisons_choice):  
    p_types = piece.presentationTypes(melodic_ngram_length = length_choice, 
                                      limit_to_entries = limit_entries_choice,
                                      body_flex = body_flex_choice, 
                                      head_flex = head_flex_choice,
                                      include_hidden_types = hidden_types_choice,
                                      combine_unisons = combine_unisons_choice)   
    # clean up for streamlit facets
    if p_types is not None:
        p_types["Measures_Beats"] = p_types["Measures_Beats"].apply(lambda x: ', '.join(map(str, x))).copy()
        p_types["Melodic_Entry_Intervals"] = p_types["Melodic_Entry_Intervals"].apply(lambda x: ', '.join(map(str, x))).copy()
        p_types["Offsets"]= p_types["Offsets"].apply(lambda x: ', '.join(map(str, x))).copy()
        p_types["Soggetti"]= p_types["Soggetti"].apply(lambda x: ', '.join(map(str, x))).copy()
        # p_types ["Time_Entry_Intervals"]= p_types["Time_Entry_Intervals"].apply(lambda x: ', '.join(map(str, x))).copy()
        p_types["Time_Entry_Intervals"]= p_types["Time_Entry_Intervals"].apply(lambda x: ', '.join(map(str, x))).copy()  
        return p_types
#corpus
@st.cache_data(**PIECE_CACHE)
def presentation_types_corpus(corpus,
                              length_choice, 
                            limit_entries_choice,
                            body_flex_choice, 
                            head_flex_choice,
                            hidden_types_choice,
                            combine_unisons_choice):
                               
    func = ImportedPiece.presentationTypes
    list_of_dfs = corpus.batch(func = func,
                               kwargs = {'melodic_ngram_length' : length_choice, 
                                      'limit_to_entries' : limit_entries_choice,
                                      'body_flex' : body_flex_choice, 
                                      'head_flex' : head_flex_choice,
                                      'include_hidden_types' : hidden_types_choice,
                                      'combine_unisons' : combine_unisons_choice},
                                        metadata = True)
    # drop empty dfs:
    list_of_dfs = [df for df in list_of_dfs if df is not None and not df.empty]
    if len(list_of_dfs) > 0: 
        for p_types in list_of_dfs:
            # clean up for streamlit facets
            p_types["Measures_Beats"] = p_types["Measures_Beats"].apply(lambda x: ', '.join(map(str, x))).copy()
            p_types["Melodic_Entry_Intervals"] = p_types["Melodic_Entry_Intervals"].apply(lambda x: ', '.join(map(str, x))).copy()
            p_types["Offsets"]= p_types["Offsets"].apply(lambda x: ', '.join(map(str, x))).copy()
            p_types["Soggetti"]= p_types["Soggetti"].apply(lambda x: ', '.join(map(str, x))).copy()
            p_types["Time_Entry_Intervals"]= p_types["Time_Entry_Intervals"].apply(lambda x: ', '.join(map(str, x))).copy()
        p_types = pd.concat(list_of_dfs)
        return p_types

# p types form

search_type = "other"
st.subheader("Explore Presentation Types")
with st.expander("How to use this tool"):
    st.markdown("""
    **About this tool**
    This tool classifies contrapuntal patterns in a piece or corpus according to their presentation
    type — Fuga, PEN (Periodic Entry Notation), or ID (Imitative Duo) — based on the timing and
    melodic relationships between successive voice entries. It identifies the soggetti (subjects)
    and analyzes how they are introduced across voices.

    **Key settings**
    - **Melodic Ngram Length** — the length of the melodic pattern used to define each soggetto.
      The default of 4 works well for most Renaissance polyphony.
    - **Combine Unisons** — if True, consecutive repeated pitches are merged before analysis,
      which can help reveal commonalities obscured by text-setting repetitions.
    - **Limit to Entries** — if True, only patterns beginning after a rest or section break are
      analyzed, focusing on primary imitative entries. If False, all occurrences are included.
    - **Head Flex / Body Flex** — control how much melodic variation is permitted between matching
      soggetti. Head flex applies to the opening notes; body flex applies to the rest of the pattern.
    - **Include Hidden Types** — if True, shorter PEN or ID patterns embedded within longer fugas
      are also reported.

    **Reading the results**
    Each row represents one presentation type event, with the following columns:
    - **Measures_Beats** — the measure and beat positions of each voice entry
    - **Soggetti** — the melodic ngram patterns involved
    - **Melodic_Entry_Intervals** — the intervals between successive soggetto entries
    - **Time_Entry_Intervals** — the time gaps (in offsets) between entries
    - **Presentation_Type** — the predicted classification (Fuga, PEN, or ID)
    - **Voices** — the voice names in entry order

    **Rendering Results in Score**
    There is also an option to render each Presentation Type in your results as musical notation
    (using Verovio), with a brief summary of the metadata for that item — including composer, title,
    measures, presentation type, and other relevant information from the table. Tick
    **Show each presentation type in the table in notation (highlighted)**: in each excerpt, every
    melodic entry of the soggetto is **highlighted in red from its first note to its last**, in each
    voice that takes part, and the excerpt spans the measures from the first entry to the end of the last.
    **Note:** if your results table is large, rendering can be slow. Consider filtering to a
    meaningful subset before rendering!

    [Know the code — CRIM Intervals presentation type documentation](https://github.com/HCDigitalScholarship/intervals/blob/main/tutorial/12_Presentation_Types.md)
    """)
form_col = st.container()
with form_col:
 with st.form("Presentation Type Settings"):
    _fc = st.columns(4)   # settings side by side
    combine_unisons_choice = _fc[0].selectbox(
        "Combine Unisons", [False, True])
    length_choice = _fc[1].number_input('Select ngram Length', value=4, step=1)
    head_flex_choice = _fc[2].number_input('Select Head Flex', value=1, step=1)
    body_flex_choice = _fc[3].number_input('Select Body Flex', value=0, step=1)
    limit_entries_choice = _fc[0].selectbox(
        "Limit to Melodic Entries", [True, False])
    hidden_types_choice = _fc[1].selectbox(
        "Include Hidden Presentation Types", [False, True])
    # form submission button
    submitted = st.form_submit_button("Update and Submit")
    if submitted:
        if "p_types" in st.session_state.keys():
            del st.session_state.p_types
        # remembered for the highlighted notation below
        st.session_state.p_types_settings = {'length': int(length_choice),
                                             'combine_unisons': combine_unisons_choice}
        if corpus_length == 0:
            st.write("Please select one or more pieces")
        # one piece
        elif corpus_length == 1:
            p_types = piece_presentation_types(piece, 
                                                length_choice,
                                                limit_entries_choice,
                                                body_flex_choice,
                                                head_flex_choice,
                                                hidden_types_choice,
                                                combine_unisons_choice)         
            sel_cols = ['Composer', 'Title', 'Presentation_Type', 'Soggetti', 'Number_Entries',
                        'Measures_Beats', 'Melodic_Entry_Intervals', 'Time_Entry_Intervals',
                        'Voices', 'Flexed_Entries', 'Parallel_Entries', 'Parallel_Voice', 
                        'Count_Non_Overlaps', 'Progress', 'Offsets']
            p_types = p_types[sel_cols]
            #Set up session state for these returns
            if "p_types" not in st.session_state:
                st.session_state.p_types = p_types          
        # corpus
        if corpus_length > 1:
            p_types = presentation_types_corpus(st.session_state.corpus,
                          length_choice, 
                        limit_entries_choice,
                        body_flex_choice, 
                        head_flex_choice,
                        hidden_types_choice,
                        combine_unisons_choice)            
            sel_cols = ['Composer', 'Title', 'Presentation_Type', 'Soggetti', 'Number_Entries',
                        'Measures_Beats', 'Melodic_Entry_Intervals', 'Time_Entry_Intervals',
                        'Voices', 'Flexed_Entries', 'Parallel_Entries', 'Parallel_Voice', 
                        'Count_Non_Overlaps', 'Progress', 'Offsets']
            p_types = p_types[sel_cols]
            # Set up session state for these returns
            if "p_types" not in st.session_state:
                st.session_state.p_types = p_types
if 'p_types' not in st.session_state:
    pass
else:
    filtered_p_types = filter_dataframe_ptypes(st.session_state.p_types)
    st.dataframe(filtered_p_types, use_container_width=True)
    # csv = convert_df(filtered_p_types)
    
    if corpus_length == 1:
        download_name = piece.metadata['title'] + '_p_type_results.csv'
        if filtered_p_types is not None:
            # filtered_p_types = filtered_p_types.to_csv().encode('utf-8')
            st.download_button(
                label="Download Filtered Presentation Type Data as CSV",
                data=filtered_p_types.to_csv(),
                file_name = download_name,
                mime='text/csv',
                key=12,
                )
    elif corpus_length > 1:
        download_name = "corpus_p_type_results.csv"
        if filtered_p_types is not None:
            # filtered_p_types = filtered_p_types.to_csv().encode('utf-8')
            st.download_button(
                label="Download Filtered Corpus Presentation Type Data as CSV",
                data=filtered_p_types.to_csv(),
                file_name = download_name,
                mime='text/csv',
                key=13,
                )
    # Verovio presentation type rendering
    st.markdown("#### View Filtered Presentation Types with Verovio")
    n_ptypes = len(filtered_p_types)
    if n_ptypes > 20:
        st.warning(f"There are {n_ptypes} presentation types in the filtered list. Consider filtering to 20 or fewer.")
    if st.checkbox("Show each presentation type in the table in notation (highlighted)",
                   key="ptypes_show_notation"):
        settings = st.session_state.get('p_types_settings', {'length': 4, 'combine_unisons': False})
        n_notes = settings['length'] + 1         # soggetto of n intervals = n + 1 notes
        if corpus_length > 1:
            piece_by_title = {p.metadata['title']: p for p in st.session_state.corpus.scores}
        st.subheader("Presentation Type Excerpts")
        st.caption("Highlighted notes are the soggetto in each entry, in every voice.")
        for _, row in filtered_p_types.iterrows():
            if corpus_length > 1:
                pt_piece = piece_by_title.get(row["Title"])
                mei_src = pt_piece.path if pt_piece is not None else ''
            else:
                pt_piece, mei_src = piece, st.session_state.get('mei_source', '')
            if pt_piece is None or not mei_src:
                continue
            offsets = as_list(row["Offsets"], float)
            voices = as_list(row["Voices"])
            ids, span = merge_spans(
                [note_ids_in_span(pt_piece, v, o, n_notes, settings['combine_unisons'])
                 for o, v in zip(offsets, voices)])
            if not ids or span is None:
                continue
            caption = (
                f"**{row['Composer']}**, *{row['Title']}* — **Measures** {span[0]}–{span[1]} | "
                f"**Type** {row['Presentation_Type']} | **Voices** {', '.join(voices)} | "
                f"**Entries** {row['Number_Entries']} | **Soggetti** {row['Soggetti']} | "
                f"**Melodic Intervals** {row['Melodic_Entry_Intervals']} | "
                f"**Time Intervals** {row['Time_Entry_Intervals']} | **Flexed** {row['Flexed_Entries']} | "
                f"**Parallel** {row['Parallel_Voice']} | **Non-Overlaps** {row['Count_Non_Overlaps']}"
            )
            st.divider()
            for i, svg in enumerate(render_highlighted_excerpt(mei_src, span[0], span[1], tuple(ids), page_width=2700)):
                show_svg(svg, caption if i == 0 else "")
