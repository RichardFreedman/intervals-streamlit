"""Imports, constants, data-loading helpers and selection state shared by every page.

Pages do `from crim_app.common import *`, so everything here (including the
re-exported libraries) is available to them, as it was in the single-file app.
"""
# Pages use `from crim_app.common import *`, so modules imported here (base64,
# pd, px, pio, viz, get_settings …) are re-exported to them even if
# this file doesn't use them itself.

# standard library
import ast
import base64
import os
import re

# third-party
import pandas as pd
import plotly.express as px
import plotly.io as pio
import requests
import streamlit as st
import verovio

# CRIM Intervals
from crim_intervals import CorpusBase, ImportedPiece, importScore
from crim_intervals.main_objs import SETTINGS_KEY, get_settings
import crim_intervals.visualizations as viz



# list of piece ids from json
def make_piece_list(json_objects):
    # only pieces with an MEI file can be loaded
    return [piece['piece_id'] for piece in json_objects if piece.get('mei_links')]

# list of composer_title ids from json   
def make_composer_title_list(json_objects):
    composer_title_list = []
    for piece in json_objects:
        composer_title = piece['composer']['name'] + ', ' + piece['full_title'] 
        composer_title_list.append(composer_title)
    return composer_title_list

# get mei link for given piece
def find_mei_link(piece_id, json_objects):
    key_value_pair = ('piece_id', piece_id)
    for json_object in json_objects:
        if key_value_pair in json_object.items():
            return json_object['mei_links'][0]
    return None


@st.cache_data(ttl=3600)
def fetch_crim_pieces():
    return requests.get('https://crimproject.org/data/pieces/').json()


@st.cache_data(ttl=3600)
def _fetch_mei_url(url: str) -> str:
    return requests.get(url).text

def get_mei_content(mei_source: str) -> str:
    """Return MEI XML text from a URL, local path, or inline string."""
    if mei_source.startswith('http'):
        return _fetch_mei_url(mei_source)
    elif mei_source.startswith('/') or mei_source.startswith('Music_Files/'):
        with open(mei_source, 'r') as _f:
            return _f.read()
    return mei_source

def get_verovio_toolkit():
    """Return a fresh verovio toolkit instance with resource path set."""
    tk = verovio.toolkit(False)
    tk.setResourcePath(os.path.join(os.path.dirname(verovio.__file__), 'data'))
    return tk


# ------------------------------------------------- highlighted score excerpts
# Adapted from the MCP server's notation.py: render an excerpt with Verovio and
# colour a supplied list of MEI xml:ids. music21's MEI reader stores each
# note's xml:id as note.id, and Verovio keeps those ids on the SVG <g> elements,
# so ids taken from the piece's music21 objects line up with the rendered score.

HIGHLIGHT_COLOR = "#d62728"


def note_ids_at_offset(piece, offset):
    """xml:ids of the notes sounding (attacked or held) in each voice at `offset`."""
    objs = piece._getM21Objs()          # offset index × one column per voice
    ids = []
    for col in objs.columns:
        s = objs[col].dropna()
        s = s[s.index <= offset]
        if s.empty:
            continue
        n, start = s.iloc[-1], s.index[-1]
        if not getattr(n, 'isNote', False):
            continue                      # rest (or chord) – nothing to colour
        if start + n.quarterLength <= offset:
            continue                      # note ended before the offset
        if isinstance(n.id, str):         # real xml:id, not a music21 memory id
            ids.append(n.id)
    return ids


def _voice_name(piece, voice):
    """Accept a part name ('Altus') or a staff number ('2', as numberParts gives)."""
    names = piece._getPartNames()
    if voice in names:
        return voice
    by_number = {num: name for name, num in piece._getPartNumberDict().items()}
    return by_number.get(str(voice))


def note_ids_in_span(piece, voice, start, n_notes, combine_unisons=False):
    """xml:ids of the `n_notes` notes in `voice` that begin at offset `start`.

    Notes are counted as crim_intervals counts them for melodic n-grams (so an
    n-gram of n intervals spans n + 1 notes); with combine_unisons, repeated
    pitches count once but every MEI note in them is highlighted, as are tied
    continuations. Returns (ids, (first_measure, last_measure)), or ([], None).
    """
    voice = _voice_name(piece, voice)
    if voice is None:
        return [], None
    events = piece.notes(combineUnisons=combine_unisons)[voice].dropna()
    events = events[events.index >= start]
    sounding = events[events != 'Rest']
    if sounding.empty:
        return [], None
    last = sounding.index[min(n_notes, len(sounding)) - 1]
    later = events.index[events.index > last]
    end = later[0] if len(later) else piece.score.highestTime
    objs = piece._getM21Objs()[voice].dropna()
    span = [o for o in objs[(objs.index >= start) & (objs.index < end)]
            if getattr(o, 'isNote', False)]
    ids = [o.id for o in span if isinstance(o.id, str)]
    measures = [o.measureNumber for o in span if o.measureNumber is not None]
    return ids, ((min(measures), max(measures)) if measures else None)


def as_list(value, cast=str):
    """A table cell that holds a list, a str(list) or a ', '-joined string, as a list."""
    if isinstance(value, (list, tuple)):
        items = list(value)
    else:
        text = str(value).strip()
        try:
            items = ast.literal_eval(text) if text.startswith('[') else None
        except (ValueError, SyntaxError):
            items = None
        if not isinstance(items, (list, tuple)):
            items = [t.strip() for t in text.split(',') if t.strip()]
    return [cast(i) for i in items]


def merge_spans(spans):
    """Combine [(ids, (m1, m2)), ...] into (all_ids, (first, last)) for one excerpt."""
    ids = [i for span_ids, _ in spans for i in span_ids]
    ranges = [r for _, r in spans if r]
    if not ranges:
        return ids, None
    return ids, (min(r[0] for r in ranges), max(r[1] for r in ranges))


def offset_at(piece, measure, beat):
    """Offset of the first event at (measure, beat), for tables that only keep Measure/Beat."""
    key = '_app_measure_beat_offsets'
    if key not in piece.analyses:
        idx = piece.detailIndex(piece.notes(), measure=True, beat=True, offset=True).index
        lookup = {}
        for m, b, o in zip(idx.get_level_values('Measure'), idx.get_level_values('Beat'),
                           idx.get_level_values('Offset')):
            lookup.setdefault((float(m), round(float(b), 4)), o)
        piece.analyses[key] = lookup
    return piece.analyses[key].get((float(measure), round(float(beat), 4)))


def _highlight_svg(svg: str, ids, color=HIGHLIGHT_COLOR) -> str:
    """Inject a <style> block that colours the given element ids."""
    if not ids:
        return svg
    sel = ', '.join(f'[id="{i}"], [id="{i}"] *' for i in ids)
    css = f'<style>{sel} {{ fill: {color} !important; color: {color} !important; }}</style>'
    return re.sub(r'(<svg\b[^>]*>)', lambda m: m.group(1) + css, svg, count=1)


@st.cache_data(show_spinner=False, max_entries=300)
def render_highlighted_excerpt(mei_source: str, start: int, end: int,
                               highlight_ids: tuple = (), scale: int = 45,
                               page_width: int = 2000) -> list:
    """Render measures start–end of an MEI source as SVG pages, with notes highlighted.

    Cached on (source, range, ids), so reruns of the page don't re-render.
    Returns a list of SVG strings (one per Verovio page), XML declaration stripped.
    """
    tk = get_verovio_toolkit()
    tk.setOptions({
        "scale": scale,
        "pageWidth": page_width,
        "adjustPageHeight": True,
        "breaks": "auto",
        "footer": "none",
        "header": "none",
    })
    if not tk.loadData(get_mei_content(mei_source)):
        raise ValueError(f"Verovio failed to load MEI from {mei_source[:80]}")
    tk.select({"measureRange": f"{max(1, start)}-{end}"})
    tk.redoLayout()
    pages = []
    for page in range(1, tk.getPageCount() + 1):
        svg = re.sub(r'<\?xml[^?]*\?>', '', tk.renderToSVG(page)).strip()
        pages.append(_highlight_svg(svg, highlight_ids))
    return pages


def show_svg(svg: str, caption: str = ""):
    """Display an SVG string as a base64 <img>, which renders more reliably than components.html."""
    b64 = base64.b64encode(svg.encode('utf-8')).decode()
    st.markdown(
        f'{caption}<br/><img src="data:image/svg+xml;base64,{b64}" '
        # fills the column; how large the notes look is set by page_width in
        # render_highlighted_excerpt (fewer measures per line = larger notes)
        f'style="width:100%;height:auto;margin-top:4px;"/>',
        unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def plotly_fig_to_html(fig_json: str, title: str) -> str:
    """Embed a Plotly figure JSON in a self-contained HTML file for download."""
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ margin: 0; padding: 20px; font-family: Arial, sans-serif; }}
        .chart-container {{ width: 100%; height: 600px; }}
    </style>
</head>
<body>
    <div class="chart-container" id="chart"></div>
    <script>
        var figure = {fig_json};
        Plotly.newPlot('chart', figure.data, figure.layout, {{
            responsive: true, displayModeBar: true, displaylogo: false
        }});
    </script>
</body>
</html>"""

# menu dictionaries
interval_kinds = {'diatonic' : 'd',
                 'chromatic' : 'c',
                 'with quality' : 'q',
                 'zero-based diatonic' : 'z'}
unison_status = {'Separate Unisons' : False,
                 'Combine Unisons' : True}
rest_status = {'Combine Rests' : True,
                 ' Separate Rests' : False}
interval_order_quality = ["-P15", "-M14", "-m14", "-P13", "-A12", "-d13", "-P12", "-M11", "-m11", "-P10", "-A9", 
                          "-d10", "-P9", "-M8", "-m8", "-P7", "-A6", "-d7", "-P6", "-M5", "-m5", "-P4", "-A3", 
                          "-d4", "-P3", "-M2", "-m2", "-P1", "P1", "m2", "M2", "m3", "M3", "P4", "A4", 
                          "d5", "P5", "m6", "M6", "m7", "M7", "P8", "m9", "M9", "m10", "M10", "P11", 
                          "A11", "d12", "P12", "M13", "m13", "P13", "A14", "d14", "P14", "M15", "m15", "P15"]
# interval_order_quality = ["-P8", "m2", "-m2", "M2", "-M2", "m3", "-m3", "M3", "-M3", "P4", "-P4", "P5", "-P5", 
#             "m6", "-m6", "M6", "-M6", "m7", "-m7", "M7", "-M7", "P8", "-P8"]

pitch_order = ['A#1', 'B1', 
               'C2', 'C#2', 'D2', 'D#2','E-2', 'E2', 'E#2', 'F2', 'F#2', 'G-2', 'G2', 'G#2', 'A-2', 'A2', 'A#2','B-2', 'B2', 'B#2',
               'C3', 'C#3', 'D-3','D3', 'D#3', 'E-3','E3', 'E#3', 'F3', 'F#3', 'G-3', 'F##3', 'G3', 'G#3', 'A-3', 'A3', 'A#3', 'B-3','B3', 'B#3',
               'C4', 'C#4', 'D-4','D4', 'D#4','E-4', 'E4', 'F-4', 'E#4', 'F4', 'F#4', 'G-4', 'F##4', 'G4', 'G#4', 'A-4','A4', 'A#4', 'B-4', 'B4', 'B#4',
               'C5', 'C#5','C##5', 'D-5','D5', 'D#5', 'E-5','E5', 'F-5','E#5','F5', 'F#5', 'G-5', 'F##5','G5', 'G#5', 'A-5', 'A5', 'A#5', 'B-5', 'B5',
              'C6']

dur_order = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0, 3.25, 3.5, 3.75, 
             4.0, 4.25, 4.5, 4.75, 5.0, 5.25, 5.5, 5.75, 6.0, 6.25, 6.5, 6.75, 7.0, 7.25, 7.5, 7.75, 8.0]

# for radar notes plot
category_order = {
    'C': 0, 'C#': 1, 'Db': 2, 'D' : 3, 'D#': 4, 'Eb': 5, 'E': 6, 'E#': 7, 'F': 8, 'F#': 9, 'Gb': 10, 'F##': 11,
    'G': 12, 'G#': 13, 'Ab': 14, 'A': 15, 'A#': 16, 'Bb': 17, 'B': 18, 'B#': 19
}

pitch_class_order = ['C', 'C#', 'D-', 'D', 'D#', 'E-', 'E', 'F-', 'E#', 'F', 'F#', 'G-', 'F##', 'G', 'G#', 'A-', 'A', 'A#', 'B-', 'B', 'B#', 'Rest']

# Named note orderings for weighted-notes radar — kept separate from cadence orderings
NOTE_PC_CHROMATIC = ['C', 'C#', 'D-', 'D', 'D#', 'E-', 'E', 'F-','F', 'F#', 'F##', 'G-', 'G', 'G#', 'A-', 'A', 'A#', 'B-', 'B', 'B#', 'Rest']
NOTE_PC_FIFTHS    = ['C', 'G', 'D', 'A', 'E', 'B', 'F#', 'G-', 'C#', 'D-','G#','A-', 'D#', 'E-', 'A#','B-', 'E#', 'F', 'B#', 'Rest']
NOTE_PC_DIATONIC  = ['C', 'D', 'E', 'F', 'G', 'A', 'B', 'B-', 'E-', 'A-', 'D-', 'C#', 'F#', 'G#', 'D#', 'A#', 'G-', 'F-', 'E#', 'F##', 'B#', 'Rest']
NOTE_PC_ORDERS    = {'Chromatic': NOTE_PC_CHROMATIC, 'Fifths': NOTE_PC_FIFTHS, 'Diatonic': NOTE_PC_DIATONIC}

contrasting_colors = [
        '#636EFA',  # Blue
        '#DC267F',  # Pink
        '#009E73',  # Green
        '#FFB000',  # Orange
        '#977277',  # Purple
        '#EC4899',  # Hot Pink
        '#48BB78',  # Teal
        '#ED8936',  # Coral
        '#2563EB',  # Deep Blue
        '#8338EC',  # Violet
        '#FF922B',  # Tangerine
        '#06D6A0',  # Mint
        '#EF4444',  # Red
        '#F97316',  # Carrot
        '#84CC16',  # Lime
        '#3B82F6',  # Sky Blue
        '#A855F7',  # Plum
        '#22C55E',  # Forest
        '#EA580C',  # Persimmon
        '#94A3B8',  # Slate
    ]
#old pitch order
# pitch_order = ['E-2', 'E2', 'F2', 'F#2', 'G2', 'A2', 'B-2', 'B2', 
                # 'C3', 'C#3', 'D3', 'E-3','E3', 'F3', 'F#3', 'G3', 'G#3','A3', 'B-3','B3',
                # 'C4', 'C#4','D4', 'E-4', 'E4', 'F4', 'F#4','G4', 'A4', 'B-4', 'B4',
                # 'C5', 'C#5','D5', 'E-5','E5', 'F5', 'F#5', 'G5', 'A5', 'B-5', 'B5', 'Rest']

# filter and download functions
def convertTuple(tup):
    out = ""
    if isinstance(tup, tuple):
        out = ', '.join(tup)
    return out  

def extract_letter(value):
    # Find the index of the first digit
    if value is not None:
        for i, char in enumerate(value):
            if char.isdigit():
                # Return everything before the first digit
                return value[:i]
        # If no digit is found, return the entire string
        return value


# hash helpers for @st.cache_data — piece/corpus objects aren't natively hashable.
# Prefer the load key set in load_selection() (URL or filename_size), which is
# unique per source file; fall back to metadata for objects created elsewhere.
def _hash_piece(p):
    key = getattr(p, '_app_key', None)
    if key:
        return key
    m = p.metadata
    return f"{m.get('composer', '')}/{m.get('title', '')}/{m.get('date', '')}"

def _hash_corpus(c):
    return "|".join(_hash_piece(s) for s in c.scores)

PIECE_CACHE = dict(hash_funcs={ImportedPiece: _hash_piece, CorpusBase: _hash_corpus}, ttl=3600)


# ---------------------------------------------------------------- selection
# The sidebar picker (rendered by streamlit_app.py on every page) uses these
# widget keys, so pages can read the current selection from session state.
CRIM_SELECT_KEY = 'crim_piece_selections'
UPLOAD_KEY = 'uploaded_files'


def _import_upload(file):
    """Import an uploaded MEI/MusicXML file; returns (piece, text)."""
    text_obj = file.getvalue().decode('UTF-8')
    piece = importScore(text_obj)
    piece._app_key = f"upload:{file.name}_{file.size}"
    return piece, text_obj


def _import_crim(piece_id, json_objects):
    filepath = find_mei_link(piece_id, json_objects)
    piece = importScore(filepath)   # importScore memoizes by path, server-wide
    piece._app_key = filepath
    return piece, filepath


def load_selection(json_objects):
    """Import the pieces chosen in the sidebar into st.session_state.

    Re-imports only when the selection changes (same keys as the original
    single-page app: piece / metadata / mei_source or corpus / corpus_metadata).
    """
    crim_piece_selections = st.session_state.get(CRIM_SELECT_KEY) or []
    uploaded_files_list = st.session_state.get(UPLOAD_KEY) or []
    n = len(crim_piece_selections) + len(uploaded_files_list)

    if n == 1:
        if crim_piece_selections:
            _piece_key = 'crim:' + crim_piece_selections[0]
        else:
            f = uploaded_files_list[0]
            _piece_key = f"upload:{f.name}_{f.size}"
        if st.session_state.get('_piece_load_key') != _piece_key:
            if crim_piece_selections:
                piece_id = crim_piece_selections[0]
                piece, source = _import_crim(piece_id, json_objects)
                crim_view = 'https://crimproject.org/pieces/' + piece_id
            else:
                piece, source = _import_upload(uploaded_files_list[0])
                crim_view = "Direct upload; not available on CRIM"
            st.session_state.piece = piece
            st.session_state.metadata = dict(piece.metadata, **{'CRIM View': crim_view})
            st.session_state.mei_source = source
            st.session_state._piece_load_key = _piece_key
            for _k in ['corpus', 'corpus_metadata', '_corpus_load_key']:
                st.session_state.pop(_k, None)

    elif n >= 2:
        crim_keys = sorted(crim_piece_selections)
        upload_keys = sorted(f"{f.name}_{f.size}" for f in uploaded_files_list)
        _corpus_key = str(crim_keys + upload_keys)
        if st.session_state.get('_corpus_load_key') != _corpus_key:
            scores = [_import_crim(p, json_objects)[0] for p in crim_piece_selections]
            scores += [_import_upload(f)[0] for f in uploaded_files_list]
            corpus = CorpusBase(scores)   # CorpusBase accepts ImportedPiece objects
            st.session_state.corpus = corpus
            st.session_state.corpus_metadata = [s.metadata for s in corpus.scores]
            st.session_state._corpus_load_key = _corpus_key
            for _k in ['piece', 'metadata', '_piece_load_key', 'mei_source']:
                st.session_state.pop(_k, None)
    return n


def get_selection():
    """Return (piece, corpus, corpus_length, crim_piece_selections, uploaded_files_list).

    corpus_length is 0 (nothing selected), 1 (one piece) or 2 (two or more),
    matching the flags the analysis code was written against.
    """
    crim_piece_selections = st.session_state.get(CRIM_SELECT_KEY) or []
    uploaded_files_list = st.session_state.get(UPLOAD_KEY) or []
    n = len(crim_piece_selections) + len(uploaded_files_list)
    corpus_length = min(n, 2)
    piece = st.session_state.get('piece') if corpus_length == 1 else None
    corpus = st.session_state.get('corpus') if corpus_length == 2 else None
    return piece, corpus, corpus_length, crim_piece_selections, uploaded_files_list


def require_selection():
    """Show a hint and stop the page if no piece is loaded."""
    piece, corpus, corpus_length, *_ = get_selection()
    if corpus_length == 0 or (piece is None and corpus is None):
        st.info("Select or upload one or more pieces in the sidebar to begin.")
        st.stop()



# ---------------------------------------------------------------- settings
# CRIM Intervals records the settings behind each result on df.attrs (see
# get_settings). pandas keeps them through filtering, copy, concat and
# reset_index, but pd.melt and groupby drop them, so cached functions that
# reshape a result re-attach them with carry_settings.
def carry_settings(df, source):
    """Copy the CRIM settings recorded on `source` onto `df` (returns df)."""
    settings = get_settings(source)
    if settings:
        df.attrs = {**df.attrs, SETTINGS_KEY: settings}
    return df


def settings_parts(df, *extra):
    """The settings recorded on df as short phrases (as the viz charts show
    them), followed by any extra phrases such as the chart's own options."""
    try:
        parts = viz._data_settings(df)
    except Exception:   # private helper in crim_intervals; never break a page
        parts = []
    return parts + [e for e in extra if e]


def settings_title(title, df, *extra):
    """A Plotly title with the settings as a smaller second line, matching
    the ready-made crim_intervals.visualizations charts."""
    parts = settings_parts(df, *extra)
    return f"{title}<br><sup>{' · '.join(parts)}</sup>" if parts else title


def n_pieces_label(df):
    n = df['Title'].nunique() if 'Title' in df.columns else 1
    return f"{n} pieces" if n > 1 else None


# ---------------------------------------------------------------- charts
def show_plotly(fig, filename, key):
    """Display a Plotly figure with a button to download it as standalone HTML."""
    st.plotly_chart(fig, use_container_width=True, key=f"{key}_chart")
    title = filename.rsplit('.', 1)[0]
    st.download_button("📥 Download chart (HTML)",
                       data=plotly_fig_to_html(fig.to_json(), title),
                       file_name=filename, mime="text/html", key=f"{key}_dl")


def safe_filename(*parts):
    return "_".join(re.sub(r'[^\w-]+', '_', str(p)).strip('_') for p in parts if p)
