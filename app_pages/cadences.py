"""Explore Cadences"""
import streamlit as st
from crim_app.common import *
from crim_app.filters import *

piece, corpus, corpus_length, crim_piece_selections, uploaded_files_list = get_selection()

search_type = "other"
st.subheader("Explore Cadences")
with st.expander("How to use this tool"):
    st.markdown("""
    **About this tool**
    This tool detects and classifies cadences in a piece or corpus by identifying combinations of
    cadential voice functions (CVFs) — the characteristic melodic motions each voice makes at a
    cadence. It classifies each cadence by type and goal tone, and provides detailed information
    about voice behavior, timing, and location in the score.

    **Key settings**
    There are no configuration options — just select your piece(s) and click **Update and Run Search**.
    Use the filter controls to narrow results by cadence type, tone, voices, or other columns.

    **Reading the results**
    Each row represents one cadence, with the following key columns:
    - **Measure / Beat** — location in the score
    - **CadType** — cadence classification: Clausula Vera, Authentic, Phrygian, Double Leading Tone,
      Altizans Only, Quince, Evaded, or Abandoned
    - **Tone** — the goal pitch of the cadence
    - **CVFs** — the cadential voice functions present, listed top-to-bottom as in the score.
      Upper-case letters indicate standard resolutions (C = cantizans, T = tenorizans, B = bassizans,
      A = altizans, etc.); lower-case letters indicate evaded or irregular resolutions
    - **Leading_Tones** — count of half-step resolution motions at this cadence
    - **Progress** — position in the piece from 0.0 (start) to 1.0 (end)
    - **SinceLast / ToNext** — quarter notes elapsed since the previous cadence / until the next
    - **Sounding** — number of voices sounding at the cadence

    **Visualizations**
    - The **bar chart** counts cadence types or tones, one bar per piece (or composer). Percentages
      let long and short pieces be compared fairly.
    - The **radar plot** displays the tonal "footprint" — the share of cadences on each tone — with
      one polygon per piece or per composer. Tones can be arranged diatonically, by fifths, by thirds
      or chromatically.
    - The **progress plot** shows where each cadence falls in the piece (0 = start, 1 = end), colored
      by type. With a corpus, each piece gets its own row.

    The **Voice Ranges & Species** page can also plot cadences alongside melodic species.

    **Rendering Results in Score**
    Results can be rendered as musical notation using Verovio. Consider filtering to a meaningful
    subset before rendering, as large result sets will be slow.

    [Know the code — CRIM Intervals cadence documentation](https://github.com/HCDigitalScholarship/intervals/blob/main/tutorial/11_Cadences.md) ·
    [Cadence charts](https://github.com/HCDigitalScholarship/intervals/blob/main/tutorial/17_Visualizations_Summary.md#cadence-radar-plots)
    """)


if corpus_length == 0:
    st.write("Please select one or more pieces")
    st.stop()
elif corpus_length == 1:
    title = piece.metadata['title']
    composer = piece.metadata['composer']
    _cad_single_piece_key = st.session_state.get('_piece_load_key')
    if st.session_state.get('cad_single_piece_key') != _cad_single_piece_key:
        cadences = piece.cadences()
        cadences['Title'] = title
        cadences['Composer'] = composer
        grouped_cadences = cadences.groupby(['Tone', 'CadType', 'CVFs'])['Title'].count()
        grouped_cadences = pd.DataFrame(grouped_cadences).reset_index()
        grouped_cadences = grouped_cadences.rename(columns={'Title': 'Count'})
        total_cads = grouped_cadences['Count'].sum()
        grouped_cadences = grouped_cadences[grouped_cadences['Count'] != 0]
        grouped_cadences.reset_index(drop=True, inplace=True)
        st.session_state.cad_single_cadences = cadences
        st.session_state.cad_single_grouped = grouped_cadences
        st.session_state.cad_single_piece_key = _cad_single_piece_key
        for _k in ['cad_single_radar_fig', 'cad_single_radar_key']:
            st.session_state.pop(_k, None)
    else:
        cadences = st.session_state.cad_single_cadences
        grouped_cadences = st.session_state.cad_single_grouped
        total_cads = grouped_cadences['Count'].sum()

    # the full table of cad
    if st.checkbox("Show Full Cadence Table and Render with Verovio"):
        # cadences = piece.cadences()
        st.subheader("Detailed View of Cadences")
        filtered_cadences = filter_dataframe_cads(cadences)
        sel_cols = ['Composer', 'Title', 'Measure', 'Beat', 'Tone', 'CadType', 'CVFs',
                    'LeadingTones', 'Sounding', 'RelLow', 'RelTone', 'TSig', 'Progress',
                    'SinceLast', 'ToNext']
        filtered_cadences = filtered_cadences[sel_cols]
        st.dataframe(filtered_cadences, use_container_width=True)
        # to download csv
        download_name = piece.metadata['title'] + '_cadence_results.csv'
        st.download_button(
            label="Download Filtered Cadence Data as CSV",
            data=filtered_cadences.to_csv(),
            file_name = download_name,
            key=14,
            mime='text/csv')
        # Verovio cadence rendering
        st.markdown("#### View Filtered Cadences with Verovio")
        mei_source = st.session_state.get('mei_source', '')
        if not mei_source:
            st.warning("MEI source not available for rendering.")
        else:
            n_cads = len(filtered_cadences)
            if n_cads > 20:
                st.warning(f"There are {n_cads} cadences in the filtered list. Rendering many cadences may be slow. Consider filtering to 20 or fewer.")
            if st.button("Render Cadences", key="verovio_cads_render"):
                mei_content = get_mei_content(mei_source)
                tk = get_verovio_toolkit()
                tk.loadData(mei_content)
                tk.setScale(53)
                tk.setOptions({"adjustPageHeight": True, "pageWidth": 2000})
                rendered = []
                for cad in filtered_cadences.index:
                    c_meas = filtered_cadences.loc[cad]["Measure"]
                    c_tone = filtered_cadences.loc[cad]["Tone"]
                    c_type = filtered_cadences.loc[cad]["CadType"]
                    c_beat = filtered_cadences.loc[cad]["Beat"]
                    cvfs = filtered_cadences.loc[cad]["CVFs"]
                    low = int(c_meas - 1)
                    high = int(c_meas)
                    mr = str(low) + "-" + str(high)
                    tk.select({"measureRange": mr})
                    tk.redoLayout()
                    count = tk.getPageCount()
                    for page in range(1, count + 1):
                        music = tk.renderToSVG(page)
                        label = (
                            f"**Composer:** {composer} | **Title:** {title} | "
                            f"**Measure:** {c_meas} | **Beat:** {c_beat} | "
                            f"**Tone:** {c_tone} | **Type:** {c_type} | **CVFs:** {cvfs}"
                        )
                        rendered.append((label, music))
                st.session_state.verovio_rendered = rendered
            # Display stored renders (persists across reruns)
            if st.session_state.get('verovio_rendered'):
                st.subheader("Cadence Excerpts")
                st.write(f"Showing {len(st.session_state.verovio_rendered)} excerpt(s)")
                for label, music in st.session_state.verovio_rendered:
                    st.divider()
                    svg_clean = re.sub(r'<\?xml[^?]*\?>', '', music).strip()
                    svg_b64 = base64.b64encode(svg_clean.encode('utf-8')).decode()
                    st.markdown(
                        f'{label}<br/><img src="data:image/svg+xml;base64,{svg_b64}" style="width:100%;max-width:2000px;margin-top:4px;"/>',
                        unsafe_allow_html=True
                    )
else:
    _cad_corpus_key = st.session_state.get('_corpus_load_key')
    if st.session_state.get('cad_corpus_key') != _cad_corpus_key:
        list_of_dfs = []
        failed_pieces = []
        for piece in st.session_state.corpus.scores:
            try:
                df = piece.cadences(keep_keys=True)
                df = df.assign(
                    Composer=piece.metadata['composer'],
                    Title=piece.metadata['title'],
                    Date=piece.metadata['date']
                )
                list_of_dfs.append(df)
            except Exception as _e:
                failed_pieces.append(f"{piece.metadata.get('composer', '?')}: {piece.metadata.get('title', '?')} ({_e})")
        if failed_pieces:
            st.warning("The cadence tool is designed to work only with Renaissance counterpoint.  Please check your corpus.")
        if not list_of_dfs:
            st.warning("The cadence tool is designed to work only with Renaissance counterpoint.  Please check your corpus.")
            st.stop()
        cadences_metadata = pd.concat(list_of_dfs, ignore_index=False)
        cols_to_move = ['Composer', 'Title', 'Date']
        cadences = cadences_metadata[cols_to_move + [col for col in cadences_metadata.columns if col not in cols_to_move]]
        st.session_state.cad_corpus_cadences = cadences
        st.session_state.cad_corpus_metadata = cadences_metadata
        st.session_state.cad_corpus_key = _cad_corpus_key
        for _k in ['cad_corpus_radar_fig', 'cad_corpus_radar_key']:
            st.session_state.pop(_k, None)
    else:
        cadences = st.session_state.cad_corpus_cadences
        cadences_metadata = st.session_state.cad_corpus_metadata
    if st.checkbox("Show Full Cadence Table and Render with Verovio"):
        st.subheader("Detailed View of Cadences")
        filtered_cadences = filter_dataframe_cads(cadences)
        sel_cols = ['Composer', 'Title', 'Measure', 'Beat', 'Tone', 'CadType', 'CVFs',
                    'LeadingTones', 'Sounding', 'RelLow', 'RelTone', 'TSig', 'Progress',
                    'SinceLast', 'ToNext']
        filtered_cadences = filtered_cadences[sel_cols] 
        st.dataframe(filtered_cadences, use_container_width=True)
        download_name = "corpus_cadence_results.csv"
        # filtered_cadences = filtered_cadences.to_csv().encode('utf-8')
        st.download_button(
            label="Download Filtered Corpus Cadence Data as CSV",
            data=filtered_cadences.to_csv(),
            file_name = download_name,
            mime='text/csv',
            key=15,
            )
        # Verovio cadence rendering (corpus)
        st.markdown("#### View Filtered Cadences with Verovio")
        n_cads = len(filtered_cadences)
        if n_cads > 20:
            st.warning(f"There are {n_cads} cadences in the filtered list. Rendering many cadences may be slow. Consider filtering to 20 or fewer.")
        if st.button("Render Cadences", key="verovio_corpus_cads_render"):
            # Build a title -> piece lookup from the corpus
            piece_by_title = {
                p.metadata['title']: p
                for p in st.session_state.corpus.scores
            }
            rendered = []
            for _, row in filtered_cadences.iterrows():
                cad_title = row["Title"]
                cad_composer = row["Composer"]
                c_meas = row["Measure"]
                c_tone = row["Tone"]
                c_type = row["CadType"]
                c_beat = row["Beat"]
                cvfs = row["CVFs"]
                cad_piece = piece_by_title.get(cad_title)
                if cad_piece is None:
                    continue
                mei_src = cad_piece.path
                mei_content = get_mei_content(mei_src)
                tk = get_verovio_toolkit()
                tk.loadData(mei_content)
                tk.setScale(53)
                tk.setOptions({"adjustPageHeight": True, "pageWidth": 2000})
                low = int(c_meas - 1)
                high = int(c_meas)
                mr = str(low) + "-" + str(high)
                tk.select({"measureRange": mr})
                tk.redoLayout()
                count = tk.getPageCount()
                for page in range(1, count + 1):
                    music = tk.renderToSVG(page)
                    label = (
                        f"**Composer:** {cad_composer} | **Title:** {cad_title} | "
                        f"**Measure:** {c_meas} | **Beat:** {c_beat} | "
                        f"**Tone:** {c_tone} | **Type:** {c_type} | **CVFs:** {cvfs}"
                    )
                    rendered.append((label, music))
            st.session_state.verovio_corpus_rendered = rendered
        # Display stored renders (persists across reruns)
        if 'verovio_corpus_rendered' in st.session_state:
            st.subheader("Cadence Excerpts")
            st.write(f"Showing {len(st.session_state.verovio_corpus_rendered)} excerpt(s)")
            for label, music in st.session_state.verovio_corpus_rendered:
                st.divider()
                svg_clean = re.sub(r'<\?xml[^?]*\?>', '', music).strip()
                svg_b64 = base64.b64encode(svg_clean.encode('utf-8')).decode()
                st.markdown(
                    f'{label}<br/><img src="data:image/svg+xml;base64,{svg_b64}" style="width:100%;max-width:2000px;margin-top:4px;"/>',
                    unsafe_allow_html=True
                )

# ---------------------------------------------------------------- charts
# All charts come from crim_intervals.visualizations and work the same way for
# one piece or a corpus. Each chart is a fragment, so changing its options
# reruns only that chart, not the whole page.
st.divider()
st.subheader("Charts")
TONE_ORDERINGS = ['Diatonic', 'Fifths', 'Thirds', 'Chromatic']
_cad_name = (safe_filename(cadences['Composer'].iloc[0], cadences['Title'].iloc[0])
             if corpus_length == 1 else "corpus")


def _no_cadences():
    st.info("No cadences with a tone were found to chart.")


@st.fragment
def cadence_bar_fragment(cadences):
    c1, c2, c3 = st.columns(3)
    by = c1.radio("Count by", ['CadType', 'Tone'], horizontal=True, key='cad_bar_by',
                  format_func=lambda x: {'CadType': 'Cadence type', 'Tone': 'Cadence tone'}[x])
    percent = c2.toggle("Show percentages", value=corpus_length > 1, key='cad_bar_pct')
    group = c3.radio("One bar per", ['Title', 'Composer'], horizontal=True, key='cad_bar_group',
                     disabled=corpus_length == 1)
    try:
        fig = viz.cadence_bar_chart(cadences, by=by, percent=percent, groupby_column=group)
    except ValueError:
        return _no_cadences()
    show_plotly(fig, f"{_cad_name}_cadence_bar.html", 'cad_bar')


@st.fragment
def cadence_radar_fragment(cadences):
    c1, c2, c3 = st.columns(3)
    tone_ordering = c1.radio("Tone order", TONE_ORDERINGS, horizontal=True, key='cad_radar_order')
    group = c2.radio("One polygon per", ['Title', 'Composer'], horizontal=True,
                     key='cad_radar_group', disabled=corpus_length == 1)
    limit = c3.toggle("Only tones present in the data", value=True, key='cad_radar_limit')
    try:
        fig = viz.cadence_radar(cadences, groupby_column=group, tone_ordering=tone_ordering,
                                limit_to_active=limit)
    except ValueError:
        return _no_cadences()
    fig.update_layout(title_x=0.5, title_xanchor='center')   # room for long piece names
    show_plotly(fig, f"{_cad_name}_cadence_radar.html", 'cad_radar')


@st.fragment
def cadence_progress_fragment(cadences):
    try:
        fig = viz.cadence_progress(cadences)
    except ValueError:
        return _no_cadences()
    show_plotly(fig, f"{_cad_name}_cadence_progress.html", 'cad_progress')


if st.checkbox("Bar chart of cadence types or tones", key='cad_show_bar'):
    cadence_bar_fragment(cadences)
if st.checkbox("Radar plot of cadence tones", key='cad_show_radar'):
    cadence_radar_fragment(cadences)
if st.checkbox("Progress plot (where cadences fall in each piece)", key='cad_show_progress'):
    cadence_progress_fragment(cadences)
