"""Explore Melodic Ngrams"""
import streamlit as st
from crim_app.common import *
from crim_app.filters import *

piece, corpus, corpus_length, crim_piece_selections, uploaded_files_list = get_selection()
from crim_app.ngrams import *

search_type = "intervals_ngrams"
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
    - **Include Count** — if True, the heat map shows how many times each pattern occurs.

    **Reading the results**
    - The **heat map** shows where each ngram pattern appears across the voices and measures of the
      piece. Each row is a voice; each vertical bar represents an ngram.  
    - Each piece has its own heat map, so if you select multiple pieces you can compare their patterns visually.
    - Matching colors indicate matching ngrams.  You can see the 'count' of each ngram above (if selected).  
    - The chart is interactive:  select one or more patterns to focus on them.         
    - The **table** can be viewed as individual ngram locations (by voice, measure, and beat) or as
      a count summary of how often each pattern appears.
    - Use the pattern filter to focus the table on specific ngrams of interest.

    [Know the code — CRIM Intervals ngram documentation](https://github.com/HCDigitalScholarship/intervals/blob/main/tutorial/09_Ngrams_Heat_Maps.md)
    """)
if corpus_length == 0:
    st.write("Please select one or more pieces")
elif corpus_length == 1:
    form_col, _ = st.columns([1, 2])
    with form_col:
     with st.form("Ngram Settings"):
        combine_unisons_choice = st.selectbox(
            "Combine Unisons", [False, True])
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
        length_choice = st.number_input('Select ngram Length', value=3, step=1)
        entries_only = st.selectbox(
            "Melodic Entries Only?",
            [True, False])
        include_count = st.selectbox("Include Count of Ngrams", [True, False])
        # submit ngram form
        submitted = st.form_submit_button("Submit")
    #here we need separate sections for the _combined_ ngs (as a corpus function)
    # vs one heatmap for each piece in the corpus
    # put the corpus ngs in session state, then pass to filter below
    # display each heatmap on its own
        if submitted:
            key_list = ['ngrams3', 'heatmap']
            for key in key_list:
                if key in st.session_state.keys():
                    del st.session_state[key]
            ngrams, heatmap = ngram_heatmap(piece, 
                        combine_unisons_choice, 
                        kind_choice, 
                        directed, 
                        compound, 
                        length_choice,
                        include_count,
                        entries_only=entries_only)
            ngrams = ngrams.map(convertTuple).dropna().reset_index()
            ngrams2 = ngrams.assign(Composer=piece.metadata['composer'], Title=piece.metadata['title'], Date=piece.metadata['date'])
            cols_to_move = ['Composer', 'Title', 'Date', 'Measure', 'Beat']
            cols_to_move = [c for c in cols_to_move if c in ngrams2.columns]
            ngrams3 = ngrams2[cols_to_move + [col for col in ngrams2.columns if col not in cols_to_move]]
            # st.write(ngrams3)
            if "ngrams3" not in st.session_state:
                st.session_state.ngrams3 = ngrams3
            if 'heatmap' not in st.session_state:
                st.session_state.heatmap = heatmap
    if 'heatmap' not in st.session_state:
        pass
    if "ngrams3" not in st.session_state:
        pass
    else:
        if piece.metadata["composer"] is not None:
            st.subheader("Ngram Heatmap: " + piece.metadata["composer"] + ", " + piece.metadata["title"])
        else:
            st.subheader("Ngram Heatmap: " + piece.metadata["title"])
        st.altair_chart(st.session_state.heatmap, use_container_width=True)

        st.write("Select Ngram Patterns to Filter")
        filtered_ngrams = filter_ngrams_by_pattern(st.session_state.ngrams3)
        ng_table_mode = st.radio(
            "Table View",
            ["Ngrams by Voice, Measure and Beat", "Counts of Ngrams"],
            horizontal=True,
            key='mel_ng_single_table_mode'
        )
        show_table = st.checkbox('Show Table', key='mel_ng_single_show_table')
        if ng_table_mode == "Ngrams by Voice, Measure and Beat":
            meta_cols_present = [c for c in ['Composer', 'Title', 'Date', 'Measure', 'Beat'] if c in filtered_ngrams.columns]
            voice_cols = [c for c in filtered_ngrams.columns if c not in meta_cols_present]
            mask = filtered_ngrams[voice_cols].apply(
                lambda col: col.notna() & (col.astype(str).str.strip() != '')
            ).any(axis=1)
            table_ng = filtered_ngrams[mask].reset_index(drop=True)
        else:
            meta_cols_present = [c for c in ['Composer', 'Title', 'Date', 'Measure', 'Beat'] if c in filtered_ngrams.columns]
            voice_cols = [c for c in filtered_ngrams.columns if c not in meta_cols_present]
            melted_ng = (
                filtered_ngrams
                .melt(id_vars=meta_cols_present, value_vars=voice_cols, var_name='Voice', value_name='Ngram')
                .dropna(subset=['Ngram'])
            )
            melted_ng = melted_ng[melted_ng['Ngram'].astype(str).str.strip() != '']
            table_ng = (
                melted_ng.groupby('Ngram')
                .size()
                .reset_index(name='Count')
                .sort_values('Count', ascending=False)
                .reset_index(drop=True)
            )
        if show_table:
            st.dataframe(table_ng, use_container_width=True)

        st.download_button(
            label="Download Filtered Ngram Data as CSV",
            data=table_ng.to_csv(index=False),
            file_name=piece.metadata['title'] + '_ngram_results.csv',
            mime='text/csv',
            key=9,
            )

        # Verovio rendering for melodic ngrams
        st.markdown("#### View Filtered Ngrams with Verovio")
        st.warning("⚠️ Verovio rendering uses the **filtered** ngram results only. Please filter to a meaningful subset before rendering.")
        n_ng = len(filtered_ngrams)
        if n_ng > 20:
            st.warning(f"There are {n_ng} ngrams in the filtered list. Consider filtering to 20 or fewer before rendering.")
        if st.button("Render Ngrams with Verovio", key="verovio_ngrams_render"):
            mei_source = st.session_state.get('mei_source', '')
            if not mei_source:
                st.warning("MEI source not available for rendering.")
            else:
                mei_content = get_mei_content(mei_source)
                tk = get_verovio_toolkit()
                tk.loadData(mei_content)
                tk.setScale(35)
                tk.setOptions({"adjustPageHeight": True, "pageWidth": 3000})
                rendered = []
                ng_composer = piece.metadata['composer']
                ng_title = piece.metadata['title']
                meta_cols = ['Composer', 'Title', 'Date', 'Measure', 'Beat']
                voice_cols = [c for c in filtered_ngrams.columns if c not in meta_cols]
                ng_pad = 2 if length_choice <= 3 else 3 if length_choice <= 5 else 5
                for _, row in filtered_ngrams.iterrows():
                    c_meas = int(row["Measure"])
                    mr = str(c_meas) + "-" + str(c_meas + ng_pad)
                    # Find voices and their ngram patterns for this row
                    voice_patterns = {v: row[v] for v in voice_cols if pd.notna(row[v]) and row[v] != ''}
                    voices_str = ", ".join(f"{v}: {p}" for v, p in voice_patterns.items())
                    tk.select({"measureRange": mr})
                    tk.redoLayout()
                    count = tk.getPageCount()
                    for page in range(1, count + 1):
                        music = tk.renderToSVG(page)
                        c_beat = row["Beat"] if "Beat" in row.index else ""
                        label = (
                            f"**Composer:** {ng_composer} | **Title:** {ng_title} | "
                            f"**Measure:** {c_meas} | **Beat:** {c_beat} | **Voices/Ngrams:** {voices_str}"
                        )
                        rendered.append((label, music))
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
# for corpus
elif corpus_length > 1:
    form_col, _ = st.columns([1, 2])
    with form_col:
     with st.form("Ngram Settings"):
        combine_unisons_choice = st.selectbox(
            "Combine Unisons", [False, True])
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
        length_choice = st.number_input('Select ngram Length', value=3, step=1)
        entries_only = st.selectbox(
            "Melodic Entries Only?",
            [True, False])
        include_count = st.selectbox("Include Count of Ngrams", [True, False])
        # submit ngram form
        submitted = st.form_submit_button("Submit")

        if submitted:
            ngram_df_list = []
            heatmap_list = []
            for piece in st.session_state.corpus.scores:
                ngrams, heatmap = ngram_heatmap(piece,
                            combine_unisons_choice,
                            kind_choice,
                            directed,
                            compound,
                            length_choice,
                            include_count,
                            entries_only=entries_only)
                ngrams = ngrams.map(convertTuple).dropna().reset_index()
                ngrams2 = ngrams.assign(Composer=piece.metadata['composer'], Title=piece.metadata['title'], Date=piece.metadata['date'])
                cols_to_move = ['Composer', 'Title', 'Date', 'Measure', 'Beat']
                cols_to_move = [c for c in cols_to_move if c in ngrams2.columns]
                ngrams3 = ngrams2[cols_to_move + [col for col in ngrams2.columns if col not in cols_to_move]]
                ngram_df_list.append(ngrams3)
                heatmap_list.append((piece.metadata['composer'], piece.metadata['title'], heatmap))
            if 'combined_ngrams' in st.session_state.keys():
                del st.session_state.combined_ngrams
            if 'ngram_heatmaps' in st.session_state.keys():
                del st.session_state.ngram_heatmaps
            if len(ngram_df_list) > 0:
                combined_ngrams = pd.concat(ngram_df_list)
                if "combined_ngrams" not in st.session_state:
                    st.session_state.combined_ngrams = combined_ngrams
            if len(heatmap_list) > 0:
                st.session_state.ngram_heatmaps = heatmap_list

    if st.session_state.get('ngram_heatmaps'):
        for composer, title, heatmap in st.session_state.ngram_heatmaps:
            if composer is not None:
                st.subheader("Ngram Heatmap: " + composer + ", " + title)
            else:
                st.subheader("Ngram Heatmap: " + title)
            st.altair_chart(heatmap, use_container_width=True)

    if "combined_ngrams" not in st.session_state:
        pass
    else:
        st.write("Select Ngram Patterns to Filter")
        st.write("Note that the Filters do NOT change the heatmaps shown above!")
        filtered_combined_ngrams = filter_ngrams_by_pattern(st.session_state.combined_ngrams)
        ng_table_mode = st.radio(
            "Table View",
            ["Ngrams by Voice, Measure and Beat", "Counts of Ngrams by Composer and Title"],
            horizontal=True,
            key='mel_ng_corpus_table_mode'
        )
        show_table = st.checkbox('Show Table of all Ngrams', key='mel_ng_corpus_show_table')
        if ng_table_mode == "Ngrams by Voice, Measure and Beat":
            meta_cols_present = [c for c in ['Composer', 'Title', 'Date', 'Measure', 'Beat'] if c in filtered_combined_ngrams.columns]
            voice_cols = [c for c in filtered_combined_ngrams.columns if c not in meta_cols_present]
            mask = filtered_combined_ngrams[voice_cols].apply(
                lambda col: col.notna() & (col.astype(str).str.strip() != '')
            ).any(axis=1)
            table_ng = filtered_combined_ngrams[mask].reset_index(drop=True)
        else:
            meta_cols_present = [c for c in ['Composer', 'Title', 'Date', 'Measure', 'Beat'] if c in filtered_combined_ngrams.columns]
            voice_cols = [c for c in filtered_combined_ngrams.columns if c not in meta_cols_present]
            melted_ng = (
                filtered_combined_ngrams
                .melt(id_vars=meta_cols_present, value_vars=voice_cols, var_name='Voice', value_name='Ngram')
                .dropna(subset=['Ngram'])
            )
            melted_ng = melted_ng[melted_ng['Ngram'].astype(str).str.strip() != '']
            table_ng = (
                melted_ng.groupby(['Composer', 'Title', 'Ngram'])
                .size()
                .reset_index(name='Count')
                .sort_values(['Composer', 'Title', 'Count'], ascending=[True, True, False])
                .reset_index(drop=True)
            )
        if show_table:
            st.dataframe(table_ng, use_container_width=True)

        st.download_button(
            label="Download Filtered Corpus Ngram Data as CSV",
            data=table_ng.to_csv(index=False),
            file_name='corpus_ngram_results.csv',
            mime='text/csv',
            key=10,
            )

        # Verovio rendering for corpus melodic ngrams
        st.markdown("#### View Filtered Ngrams with Verovio")
        st.warning("⚠️ Verovio rendering uses the **filtered** ngram results only. Please filter to a meaningful subset before rendering.")
        n_ng_corpus = len(filtered_combined_ngrams)
        if n_ng_corpus > 20:
            st.warning(f"There are {n_ng_corpus} ngrams in the filtered list. Consider filtering to 20 or fewer before rendering.")
        if st.button("Render Ngrams with Verovio", key="verovio_corpus_ngrams_render"):
            piece_by_title = {p.metadata['title']: p for p in st.session_state.corpus.scores}
            meta_cols = ['Composer', 'Title', 'Date', 'Measure', 'Beat']
            voice_cols = [c for c in filtered_combined_ngrams.columns if c not in meta_cols]
            rendered = []
            for _, row in filtered_combined_ngrams.iterrows():
                ng_title = row["Title"]
                ng_composer = row["Composer"]
                c_meas = int(row["Measure"])
                c_beat = row["Beat"] if "Beat" in row.index else ""
                voice_patterns = {v: row[v] for v in voice_cols if pd.notna(row[v]) and row[v] != ''}
                voices_str = ", ".join(f"{v}: {p}" for v, p in voice_patterns.items())
                cad_piece = piece_by_title.get(ng_title)
                if cad_piece is None:
                    continue
                mei_src = cad_piece.path
                mei_content = get_mei_content(mei_src)
                tk = get_verovio_toolkit()
                tk.loadData(mei_content)
                tk.setScale(35)
                tk.setOptions({"adjustPageHeight": True, "pageWidth": 3000})
                ng_pad = 2 if length_choice <= 3 else 3 if length_choice <= 5 else 5
                mr = str(c_meas) + "-" + str(c_meas + ng_pad)
                tk.select({"measureRange": mr})
                tk.redoLayout()
                count = tk.getPageCount()
                for page in range(1, count + 1):
                    music = tk.renderToSVG(page)
                    label = (
                        f"**Composer:** {ng_composer} | **Title:** {ng_title} | "
                        f"**Measure:** {c_meas} | **Beat:** {c_beat} | **Voices/Ngrams:** {voices_str}"
                    )
                    rendered.append((label, music))
            st.session_state.verovio_corpus_ngrams_rendered = rendered
        if st.session_state.get('verovio_corpus_ngrams_rendered'):
            st.subheader("Ngram Excerpts")
            st.write(f"Showing {len(st.session_state.verovio_corpus_ngrams_rendered)} excerpt(s)")
            for label, music in st.session_state.verovio_corpus_ngrams_rendered:
                st.divider()
                svg_clean = re.sub(r'<\?xml[^?]*\?>', '', music).strip()
                svg_b64 = base64.b64encode(svg_clean.encode('utf-8')).decode()
                st.markdown(
                    f'{label}<br/><img src="data:image/svg+xml;base64,{svg_b64}" style="width:100%;max-width:2000px;margin-top:4px;"/>',
                    unsafe_allow_html=True
                )

