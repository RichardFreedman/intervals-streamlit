# Revision Plan — `dev_26`

Goals: (1) adopt new CRIM Intervals features (cadence, voice-range, species and note-weight plots, corpus-level methods); (2) make the app faster on Streamlit Community Cloud by splitting the single 4,879-line script into separate pages.

---

## Phase 0 — Dependencies (do first, small commit)

| File | Change |
|---|---|
| `pyproject.toml` | `crim-intervals = ">=2.0.86"` (currently `>=2.0.70`); `streamlit = ">=1.43"` (needed for `st.navigation`, `st.fragment`) |
| `requirements.txt` | Regenerate: `poetry lock && poetry export -f requirements.txt --without-hashes -o requirements.txt`. If the export is awkward, replace `crim-intervals==2.0.72` with `crim-intervals>=2.0.86` by hand. Community Cloud reads `requirements.txt` first, so this is the file that matters for deployment. |
| `intervals_streamlit2.py` | Remove the `psutil` import (imported, never used, and not in requirements). |

Compatibility check: crim-intervals 2.0.86 pins `plotly 5.19.0`, `altair 5.2.0`, `music21 8.3.0`, `numpy <2`, `pandas >=2.2,<3`, `verovio 5.5.0` — all match what the app already pins, so no conflict expected.

Verify locally in conda: `conda activate <env> && pip install -U "crim-intervals>=2.0.86" && streamlit run intervals_streamlit2.py` before the restructure, so library regressions are separated from refactor regressions.

---

## Phase 1 — Multipage structure

### Why the current app is slow
- Every widget interaction reruns the **whole** script: all imports, ~800 lines of helper/filter definitions, piece loading, and every section whose sidebar checkbox is ticked.
- Users who tick several "Explore …" boxes pay for all of them on every click.
- Pieces are cached only per session (`st.session_state`), so each visitor re-parses the same CRIM MEI files.

### Target layout (uses `st.navigation` / `st.Page`)

```
streamlit_app.py            # entry point: page config, navigation, shared sidebar
crim_app/
  loading.py                # CRIM piece list, MEI fetch, importScore / CorpusBase, cached
  filters.py                # one generic filter_dataframe() replacing the 8 near-copies
  render.py                 # verovio helpers, plotly→HTML download, CSV download
  constants.py              # interval_kinds, pitch_order, NOTE_PC_ORDERS, colors …
pages/
  0_home.py                 # select/upload pieces, show metadata
  1_notes.py                # Notes + Weighted Notes (radar_note_plot)
  2_durations.py
  3_melodic.py              # melodic intervals
  4_harmonic.py
  5_melodic_ngrams.py
  6_harmonic_ngrams.py
  7_sonority_ngrams.py
  8_cadences.py             # table, bar, radar, progress  (library viz)
  9_ranges_species.py       # NEW: voice ranges, melodic species, species+cadences
  10_presentation_types.py
  11_model_finder.py
```

Keep `intervals_streamlit2.py` in place until the new app is verified, then remove it and update `.devcontainer/devcontainer.json` and the Community Cloud main-file setting to `streamlit_app.py`.

### Shared state
- Piece/corpus selection lives on the Home page (and a compact summary in the sidebar on every page). Store the **selection key** in `st.session_state`; pages call `get_piece()` / `get_corpus()` from `crim_app/loading.py`.
- `st.session_state` is shared across pages, so the existing `_piece_load_key` / `_corpus_load_key` logic carries over unchanged.
- Each page guards: if nothing is selected, `st.info("Select pieces on the Home page")` + `st.page_link`, then `st.stop()`.

---

## Phase 2 — Speed work within pages

1. **Cross-user caching of parsed pieces.** `@st.cache_resource` on `load_crim_piece(url)` so a popular CRIM piece is parsed once per server, not once per visitor. (Uploads stay in session state.) Keep `cache_data` for derived DataFrames.
2. **Fix cache keys.** `_hash_piece` hashes composer/title/date — two uploads with the same metadata (or blank metadata) collide. Hash on the load key (URL, or `filename_size` for uploads) instead.
3. **`st.form` for settings** on every page (Notes already does this) so changing three dropdowns triggers one run, not three.
4. **`@st.fragment` around chart and Verovio blocks**, so changing a chart option (e.g. tone ordering) reruns only that block, not the whole page.
5. **Lazy heavy work behind buttons**, storing results in `st.session_state` (per existing project rule) — especially Verovio rendering, presentation types and model finder.
6. Replace deprecated `is_categorical_dtype` with `isinstance(df[col].dtype, pd.CategoricalDtype)`.

---

## Phase 3 — New Intervals features

All new chart functions return **Plotly** figures, so each is `st.plotly_chart(fig)` plus the existing HTML-download helper.

| Page | Data | Chart | Replaces |
|---|---|---|---|
| Cadences | `piece.cadences()` / `corpus.cadences()` | `viz.cadence_bar_chart(cads, by='CadType' or 'Tone')` | app's hand-built bar charts |
| Cadences | same | `viz.cadence_radar(cads, tone_ordering=…, groupby_column='Title'/'Composer')` | app's own `cadence_radar` (≈100 lines) |
| Cadences | same | `viz.cadence_progress(cads)` | app's own `cadence_progress` (≈120 lines) and per-piece corpus loop |
| Notes | `piece.note_weights()` / `corpus.note_weights()` | `viz.radar_note_plot(nw, pitch_class_order=…)` | `piece_note_weight` / `corpus_note_weights` batch code |
| Ranges & Species (new) | `piece.voice_ranges(top_n=…)` / `corpus.voice_ranges(top_n=…, final=…)` | `viz.voice_range_chart(vr, final=…, piece_order='mass')` | — |
| Ranges & Species (new) | `piece.melodic_species()` / `corpus.melodic_species()` | `viz.plot_species(sp, show_voice_detail=…, progress_bins=…)` | — |
| Ranges & Species (new) | species + cadences, **one piece only** | `viz.plot_species_cadences(sp, cads, title=…)` | — |

Notes:
- Corpus objects now have `.cadences()`, `.note_weights()`, `.voice_ranges()`, `.melodic_species()` directly, so the app's `corpus.batch(...)` + concat wrappers for these can go.
- Expose `include_final=True` / `key_sig=True` options on cadences so users can group by final.
- Each page's "How to use" expander should link to tutorial `11_Cadences.md`, `13_Voice_Ranges_Melodic_Species.md`, `17_Visualizations_Summary.md`.

---

## Suggested commit sequence

1. Bump deps; confirm current app still runs on 2.0.86.
2. Extract `crim_app/` helpers (no behaviour change).
3. Add `streamlit_app.py` + Home page; port pages one at a time (Notes → … → Model Finder), checking each against the old app.
4. Swap cadence/notes charts to library `viz` functions; delete app-local chart code.
5. Add Ranges & Species page.
6. Caching / fragment / form pass; retire `intervals_streamlit2.py`; update devcontainer, README, Community Cloud main file.

## Testing
- Smoke test each page with: one CRIM piece, one uploaded MEI, one MusicXML upload, a 3–5 piece corpus (incl. a Mass to check `piece_order='mass'`).
- Compare timings before/after on the deployed app (first load, then a settings change on the cadence page).

## Open questions
- Keep the "Explore Homorhythm" section (currently commented out of the sidebar)? Plan assumes it stays off.
- Should Model Finder stay a separate page or move under Melodic Ngrams?
