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


# Choices for the melodic "Entries" setting: label -> piece.entries(anywhere=...),
# or None for all n-grams (no entries filter).
ENTRY_MODES = {   # first is the page default
    "Entries only (after rest or fermata)": False,
    "Entry patterns, all occurrences": True,
    "All ngrams": None,
}


@st.cache_data(**PIECE_CACHE)
def melodic_ngram_data(piece, combine_unisons_choice, kind_choice, directed, compound, length_choice,
                       entry_mode="Entries only (after rest or fermata)"):
    """Return (ngrams, durations, detail) for one piece.

    ngrams/durations are the raw crim_intervals results (offset index, tuple
    patterns, settings attached) for the heat map; detail is the same n-grams
    with a Measure/Beat index for the table and Verovio rendering.

    entry_mode is a key of ENTRY_MODES. Both entry modes are thematic (the
    pattern must occur more than once); "all occurrences" also keeps the
    instances of entry patterns that don't follow a rest (anywhere=True).
    """
    nr = piece.numberParts(piece.notes(combineUnisons=combine_unisons_choice))
    mel = piece.melodic(df=nr, kind=kind_choice, directed=directed, compound=compound, end=False)
    anywhere = ENTRY_MODES[entry_mode]
    if anywhere is None:
        ngrams = piece.ngrams(df=mel, n=length_choice, exclude=['Rest'])
    else:
        ngrams = piece.entries(df=mel, n=length_choice, thematic=True, anywhere=anywhere,
                               exclude=['Rest'])
    # mask_df gives durations the same rows as ngrams: plot_ngrams_heatmap
    # pairs the two frames by row position, so extra rows misplace the bars
    durations = piece.durations(df=mel, n=length_choice, mask_df=ngrams)
    return ngrams, durations, piece.detailIndex(ngrams, offset=False)


@st.cache_data(**PIECE_CACHE)
def harmonic_ngram_data(piece, kind_choice, directed, compound, against_low, length_choice):
    """Return (ngrams, durations, detail) for one piece (see melodic_ngram_data)."""
    nr = piece.numberParts(piece.notes())
    har = piece.harmonic(df=nr, kind=kind_choice, directed=directed, compound=compound,
                         againstLow=against_low)
    ngrams = piece.ngrams(df=har, n=length_choice, exclude=['Rest'])
    durations = piece.durations(df=har, n=length_choice, mask_df=ngrams)   # see melodic_ngram_data
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


def _model_patterns(items, selected=None):
    """Patterns (tuples) of the model, i.e. the first piece in items, in order
    of first appearance, limited to the pattern strings in selected if given."""
    keep = None if selected is None else set(selected)
    return [p for p in _patterns_in_order([items[0][1]]) if keep is None or convertTuple(p) in keep]


def build_paired_heatmaps(items, selected=None, include_count=True, chart_title='N-grams'):
    """Pair the model (first item) with each other piece, as in the tutorial's
    "Heat Map of Shared Ngrams in Two or More Pieces".

    Both charts of a pair show only the patterns the model and that piece share
    (and, if given, that are in selected). Colors are registered once from the
    model, so a pattern has the same color in every pair.
    Returns a list of (label, model_chart, derivative_chart); the charts are
    None if the pair shares no patterns.
    """
    model_label, model_ng, model_dur = items[0]
    model_pats = _model_patterns(items, selected)
    pairs = []
    with _COLOR_LOCK:
        viz.color_manager.reset()
        viz.pre_register_patterns(model_pats)
        for label, ngrams, durations in items[1:]:
            present = set(_patterns_in_order([ngrams]))
            shared = [p for p in model_pats if p in present]
            if not shared:   # an empty selected_patterns would mean "all patterns"
                pairs.append((label, None, None))
                continue
            model_chart = viz.plot_ngrams_heatmap(model_ng, model_dur, selected_patterns=shared,
                                                  voices=[], includeCount=include_count,
                                                  title=f"{chart_title} in {model_label} (model)")
            deriv_chart = viz.plot_ngrams_heatmap(ngrams, durations, selected_patterns=shared,
                                                  voices=[], includeCount=include_count,
                                                  title=f"{chart_title} in {label}")
            pairs.append((label, model_chart, deriv_chart))
    return pairs


def show_paired_heatmaps(model_label, pairs):
    st.caption(f"Model: **{model_label}** (the first piece selected). Each pair shows only the "
               "patterns the model shares with the other piece.")
    for i, (label, model_chart, deriv_chart) in enumerate(pairs, start=1):
        st.markdown(f"##### Pair {i}: {model_label} · {label}")
        if model_chart is None:
            st.info(f"{label} shares none of the model's patterns (among those selected).")
            continue
        st.altair_chart(model_chart, use_container_width=True)
        st.altair_chart(deriv_chart, use_container_width=True)


def limit_table_to_model(table, items):
    """Keep only the table cells holding a pattern found in the model (the
    first item); rows left with no pattern are dropped."""
    model_strings = {convertTuple(p) for p in _model_patterns(items)}
    meta = [c for c in ['Composer', 'Title', 'Date', 'Measure', 'Beat'] if c in table.columns]
    voices = [c for c in table.columns if c not in meta]
    table = table.copy()
    table[voices] = table[voices].where(table[voices].isin(model_strings))
    return table.dropna(how='all', subset=voices).reset_index(drop=True)


def store_ngram_results(state_key, results, include_count, length, paired=False):
    """Save [(piece, (ngrams, durations, detail)), ...] and the form choices
    for display, and reset the pattern filter (its options change with the
    new results). paired: show the model (first piece) paired with each of
    the others, limited to the model's patterns (needs two or more pieces)."""
    items = [(piece_label(p), ng, dur) for p, (ng, dur, _) in results]
    paired = bool(paired) and len(items) > 1
    table = pd.concat([ngram_table(det, p) for p, (_, _, det) in results])
    st.session_state[state_key] = {
        'items': items,
        'table': limit_table_to_model(table, items) if paired else table,
        'include_count': include_count,
        'length': length,
        'paired': paired,
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
    if results.get('paired'):
        show_paired_heatmaps(results['items'][0][0],
                             build_paired_heatmaps(results['items'], selected=selected,
                                                   include_count=results['include_count'],
                                                   chart_title=chart_title))
    else:
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
