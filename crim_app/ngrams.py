"""N-gram data and heat maps shared by the melodic and harmonic ngram pages.

The n-grams are cached; the heat maps are not, so they can follow the pattern
filter. Charts come from crim_intervals.visualizations.plot_ngrams_heatmap,
which adds the settings recorded on the n-gram DataFrame (and any selected
patterns) as a subtitle.
"""
import threading

import streamlit as st
from crim_app.common import *
from crim_app.filters import convertTuple, filter_ngrams_by_pattern

# viz.color_manager is a single module-level object shared by every session
# on the server. build_ngram_heatmaps resets it and registers all patterns
# before drawing, so a pattern has the same color in every heat map drawn
# together; the lock stops two sessions from interleaving that sequence.
_COLOR_LOCK = threading.Lock()


@st.cache_data(**PIECE_CACHE)
def melodic_ngram_data(piece, combine_unisons_choice, kind_choice, directed, compound, length_choice,
                       entries_only=False):
    """Return (ngrams, durations, detail) for one piece.

    ngrams/durations are the raw crim_intervals results (offset index, tuple
    patterns, settings attached) for the heat map; detail is the same n-grams
    with a Measure/Beat index for the table and Verovio rendering.
    """
    nr = piece.numberParts(piece.notes(combineUnisons=combine_unisons_choice))
    mel = piece.melodic(df=nr, kind=kind_choice, directed=directed, compound=compound, end=False)
    if entries_only:
        ngrams = piece.entries(df=mel, n=length_choice, thematic=True, anywhere=True, exclude=['Rest'])
        durations = piece.durations(df=mel, n=length_choice, mask_df=ngrams)
    else:
        ngrams = piece.ngrams(df=mel, n=length_choice, exclude=['Rest'])
        durations = piece.durations(df=mel, n=length_choice)
    return ngrams, durations, piece.detailIndex(ngrams, offset=False)


@st.cache_data(**PIECE_CACHE)
def harmonic_ngram_data(piece, kind_choice, directed, compound, against_low, length_choice):
    """Return (ngrams, durations, detail) for one piece (see melodic_ngram_data)."""
    nr = piece.numberParts(piece.notes())
    har = piece.harmonic(df=nr, kind=kind_choice, directed=directed, compound=compound,
                         againstLow=against_low)
    ngrams = piece.ngrams(df=har, n=length_choice, exclude=['Rest'])
    durations = piece.durations(df=har, n=length_choice)
    return ngrams, durations, piece.detailIndex(ngrams, offset=False)


def ngram_table(detail, piece):
    """Detail n-grams as strings, with Composer/Title/Date/Measure/Beat columns first."""
    table = detail.map(convertTuple).dropna().reset_index()
    table = table.assign(Composer=piece.metadata['composer'], Title=piece.metadata['title'],
                         Date=piece.metadata['date'])
    front = [c for c in ['Composer', 'Title', 'Date', 'Measure', 'Beat'] if c in table.columns]
    return table[front + [c for c in table.columns if c not in front]]


def piece_label(piece):
    composer, title = piece.metadata.get('composer'), piece.metadata.get('title')
    return f"{composer}: {title}" if composer else str(title)


def _patterns_in_order(ngrams_list):
    """Every pattern (tuple) in the n-gram DataFrames, in order of first appearance."""
    seen = {}
    for ngrams in ngrams_list:
        for p in ngrams.stack().dropna():
            if isinstance(p, tuple):
                seen.setdefault(p, None)
    return list(seen)


def build_ngram_heatmaps(items, selected=None, include_count=True, chart_title='N-grams'):
    """Draw one heat map per piece with the same colors for the same pattern.

    items: list of (label, ngrams, durations), with the raw results returned by
    melodic_ngram_data / harmonic_ngram_data.
    selected: the pattern strings chosen in filter_ngrams_by_pattern, or None
    for all patterns. Patterns not in a piece are simply absent from its chart.
    Returns a list of (label, chart); chart is None if the piece has none of
    the selected patterns.
    """
    all_patterns = _patterns_in_order([ng for _, ng, _ in items])
    by_string = {convertTuple(p): p for p in all_patterns}
    chosen = None
    if selected is not None and len(selected) < len(by_string):
        chosen = [by_string[s] for s in selected if s in by_string]
    charts = []
    with _COLOR_LOCK:
        viz.color_manager.reset()
        # register the shown patterns first, so they get the curated palette
        viz.pre_register_patterns(chosen if chosen is not None else all_patterns)
        for label, ngrams, durations in items:
            patterns_here = chosen
            if chosen is not None:
                present = set(_patterns_in_order([ngrams]))
                patterns_here = [p for p in chosen if p in present]
                if not patterns_here:
                    charts.append((label, None))
                    continue
            chart = viz.plot_ngrams_heatmap(ngrams, durations,
                                            selected_patterns=patterns_here or [],
                                            voices=[], includeCount=include_count,
                                            title=f"{chart_title} in {label}")
            charts.append((label, chart))
    return charts


def show_ngram_heatmaps(charts):
    for label, chart in charts:
        if chart is None:
            st.info(f"{label}: none of the selected patterns occur in this piece.")
        else:
            st.altair_chart(chart, use_container_width=True)


def store_ngram_results(state_key, results, include_count, length):
    """Save [(piece, (ngrams, durations, detail)), ...] and the form choices
    for display, and reset the pattern filter (its options change with the
    new results)."""
    st.session_state[state_key] = {
        'items': [(piece_label(p), ng, dur) for p, (ng, dur, _) in results],
        'table': pd.concat([ngram_table(det, p) for p, (_, _, det) in results]),
        'include_count': include_count,
        'length': length,
    }
    st.session_state.pop(f"{state_key}_patterns", None)


def ngram_count_table(filtered, corpus, voice_label='Voice'):
    """Counts of each pattern (per Composer/Title for a corpus)."""
    meta = [c for c in ['Composer', 'Title', 'Date', 'Measure', 'Beat'] if c in filtered.columns]
    voices = [c for c in filtered.columns if c not in meta]
    melted = (filtered.melt(id_vars=meta, value_vars=voices, var_name=voice_label, value_name='Ngram')
                      .dropna(subset=['Ngram']))
    melted = melted[melted['Ngram'].astype(str).str.strip() != '']
    if corpus:
        return (melted.groupby(['Composer', 'Title', 'Ngram']).size().reset_index(name='Count')
                      .sort_values(['Composer', 'Title', 'Count'], ascending=[True, True, False])
                      .reset_index(drop=True))
    return (melted.groupby('Ngram').size().reset_index(name='Count')
                  .sort_values('Count', ascending=False).reset_index(drop=True))


def ngram_results_section(state_key, chart_title, corpus, voice_label='Voice'):
    """Pattern filter, heat maps that follow it, and the table/CSV.

    Returns the filtered table (for Verovio rendering), or None if there are
    no results yet.
    """
    results = st.session_state.get(state_key)
    if not results:
        return None
    st.caption("Filter by pattern to focus the heat maps and the table below on the patterns you keep.")
    filtered, selected = filter_ngrams_by_pattern(results['table'], key=f"{state_key}_patterns",
                                                  return_selected=True)
    show_ngram_heatmaps(build_ngram_heatmaps(results['items'], selected=selected,
                                             include_count=results['include_count'],
                                             chart_title=chart_title))

    mode = st.radio("Table View", ["Ngrams by Voice, Measure and Beat",
                                   "Counts of Ngrams" + (" by Composer and Title" if corpus else "")],
                    horizontal=True, key=f"{state_key}_table_mode")
    if mode.startswith("Ngrams by"):
        meta = [c for c in ['Composer', 'Title', 'Date', 'Measure', 'Beat'] if c in filtered.columns]
        voices = [c for c in filtered.columns if c not in meta]
        mask = filtered[voices].apply(lambda col: col.notna() & (col.astype(str).str.strip() != '')).any(axis=1)
        table = filtered[mask].reset_index(drop=True)
    else:
        table = ngram_count_table(filtered, corpus, voice_label=voice_label)
    if st.checkbox('Show Table', key=f"{state_key}_show_table"):
        st.dataframe(table, use_container_width=True)
    name = 'corpus' if corpus else safe_filename(results['items'][0][0])
    st.download_button("Download Filtered Ngram Data as CSV", data=table.to_csv(index=False),
                       file_name=f"{name}_{state_key}_results.csv", mime='text/csv',
                       key=f"{state_key}_csv")
    return filtered
