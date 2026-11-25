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
    Results can be rendered as musical notation using Verovio. Open the full cadence table and tick
    **Show each cadence in the table in notation (highlighted)**: each cadence in the (filtered) table
    is shown as its own excerpt, from the measure before the cadence to the measure after, with a
    caption giving its composer, title, measure, beat, tone, type and CVFs. In each excerpt, the
    notes of the cadential voice functions are **highlighted in red at the moment of the
    perfection**, where the cadence concludes. Consider filtering to a meaningful subset before
    rendering, as large result sets will be slow.

    [Know the code — CRIM Intervals cadence documentation](https://github.com/HCDigitalScholarship/intervals/blob/main/tutorial/11_Cadences.md) ·
    [Cadence charts](https://github.com/HCDigitalScholarship/intervals/blob/main/tutorial/17_Visualizations_Summary.md#cadence-radar-plots)
    """)


def cadence_offsets(df):
    """Offset of each cadence: the `Offset` column if present, else the index (same value)."""
    return df['Offset'] if 'Offset' in df.columns else pd.Series(df.index, index=df.index)


def show_cadence_examples(filtered, offsets, piece_for_row):
    """Render each cadence row as its own excerpt (measure-1 … measure+1), with the
    notes sounding at the cadence's offset highlighted.

    piece_for_row(row) -> (ImportedPiece, mei_source) or (None, None)
    """
    n_cads = len(filtered)
    if n_cads > 20:
        st.warning(f"There are {n_cads} cadences in the filtered list. Rendering many "
                   "cadences may be slow. Consider filtering to 20 or fewer.")
    st.caption(f"Showing {n_cads} cadence(s). Highlighted notes are those of the cadential "
               "voice functions (CVFs) at the perfection, where the cadence concludes.")
    for (_, row), offset in zip(filtered.iterrows(), offsets):
        cad_piece, mei_src = piece_for_row(row)
        if cad_piece is None or not mei_src:
            continue
        meas = int(row['Measure'])
        # only the voices with a cadential voice function (PartMap), at the perfection
        part_map = cadence_part_map(cad_piece, offset)
        voices = (sorted({p for parts in part_map.values() for p in parts})
                  if part_map else None)
        ids = tuple(note_ids_at_offset(cad_piece, offset, voices=voices))
        caption = (
            f"**{row['Composer']}**, *{row['Title']}* — "
            f"**Measure** {meas}, **Beat** {row['Beat']} | **Tone** {row['Tone']} | "
            f"**Type** {row['CadType']} | **CVFs** {row['CVFs']}"
        )
        if part_map:
            caption += f" | **Voices** {describe_part_map(cad_piece, part_map)}"
        st.divider()
        try:
            pages = render_highlighted_excerpt(mei_src, meas - 1, meas + 1, ids)
        except ValueError as e:
            st.warning(f"{caption}\n\nCould not render: {e}")
            continue
        for i, svg in enumerate(pages):
            show_svg(svg, caption if i == 0 else "")


if corpus_length == 0:
    st.write("Please select one or more pieces")
    st.stop()
elif corpus_length == 1:
    title = piece.metadata['title']
    composer = piece.metadata['composer']
    _cad_single_piece_key = st.session_state.get('_piece_load_key')
    if st.session_state.get('cad_single_piece_key') != _cad_single_piece_key:
        cadences = with_voices_column(piece, piece.cadences(voice_detail=True))
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
        offsets = cadence_offsets(filtered_cadences)
        sel_cols = ['Composer', 'Title', 'Measure', 'Beat', 'Tone', 'CadType', 'CVFs',
                    'Voices', 'LeadingTones', 'Sounding', 'RelLow', 'RelTone', 'TSig', 'Progress',
                    'SinceLast', 'ToNext']
        filtered_cadences = filtered_cadences[[c for c in sel_cols if c in filtered_cadences.columns]]
        st.dataframe(filtered_cadences, use_container_width=True)
        # to download csv
        download_name = piece.metadata['title'] + '_cadence_results.csv'
        st.download_button(
            label="Download Filtered Cadence Data as CSV",
            data=filtered_cadences.to_csv(),
            file_name = download_name,
            key=14,
            mime='text/csv')
        # Verovio cadence rendering, one highlighted excerpt per row
        mei_source = st.session_state.get('mei_source', '')
        if st.checkbox("Show each cadence in the table in notation (highlighted)",
                       key="cad_show_notation"):
            if not mei_source:
                st.warning("MEI source not available for rendering.")
            else:
                st.subheader("Cadence Excerpts")
                show_cadence_examples(filtered_cadences, offsets,
                                      lambda row: (piece, mei_source))
else:
    _cad_corpus_key = st.session_state.get('_corpus_load_key')
    if st.session_state.get('cad_corpus_key') != _cad_corpus_key:
        list_of_dfs = []
        failed_pieces = []
        for piece in st.session_state.corpus.scores:
            try:
                df = with_voices_column(piece, piece.cadences(keep_keys=True, voice_detail=True))
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
        offsets = cadence_offsets(filtered_cadences)
        sel_cols = ['Composer', 'Title', 'Measure', 'Beat', 'Tone', 'CadType', 'CVFs',
                    'Voices', 'LeadingTones', 'Sounding', 'RelLow', 'RelTone', 'TSig', 'Progress',
                    'SinceLast', 'ToNext']
        filtered_cadences = filtered_cadences[[c for c in sel_cols if c in filtered_cadences.columns]]
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
        # Verovio cadence rendering (corpus), one highlighted excerpt per row
        if st.checkbox("Show each cadence in the table in notation (highlighted)",
                       key="cad_corpus_show_notation"):
            piece_by_title = {p.metadata['title']: p for p in st.session_state.corpus.scores}

            def _piece_for_row(row):
                p = piece_by_title.get(row['Title'])
                return (p, p.path) if p is not None else (None, None)

            st.subheader("Cadence Excerpts")
            show_cadence_examples(filtered_cadences, offsets, _piece_for_row)

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
