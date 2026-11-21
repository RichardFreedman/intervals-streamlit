# N-gram heat map fixes: summary for reviewing crim_intervals

What we found and fixed in the Streamlit app (branch `dev_26`, November 2026), and what
still needs checking or fixing in the main library at `~/Documents/CRIM_Python/intervals`.
The line numbers below are for the local intervals repo at commit `5533eb0`. They match
the installed `crim_intervals` 2.0.87.

Test piece: `CRIM_Model_0008` (Ave Maria). Paired test: `CRIM_Model_0019` with
`CRIM_Mass_0019_1` and `_2`.

---

## 1. Durations not lined up with the n-grams they're plotted with

**Symptom.** The heat map for all n-grams drops about half its bars and draws many of the
rest at the wrong length. The entries heat map looked fine, so the two looked more alike
than they should.

**Cause.**
- `visualizations.py:308` `_process_ngrams_df_helper` melts both frames to one row per
  cell. `visualizations.py:332` then does
  `ngrams_df['end'] = ngrams_df['start'] + ngrams_duration['duration']`.
- Those two columns line up by **row position** (both have a RangeIndex after `melt`),
  not by `(offset, voice)`.
- If the duration frame has a different index, every bar after the first mismatch gets
  another n-gram's duration, or NaN, and the NaN bars are dropped by
  `dropna(how='any')` in `_plot_ngrams_df_heatmap`.
- `ngrams(..., exclude=['Rest'])` (the default) drops windows that contain rests, but
  `durations(df=mel, n=n)` without `mask_df` keeps them. So their indexes differ.

**Evidence** (Model 0008, diatonic, directed, compound, n=3):

| | ngram rows | duration rows | bars drawn | wrong end points |
|---|---|---|---|---|
| `durations` without mask | 446 | 541 | 379 of 747 | 333 |
| `durations(..., mask_df=ngrams)` | 446 | 446 | 747 of 747 | 0 |

With the notebook settings (unisons combined, not compound, n=4), the unmasked version
draws 248 of 526 bars, with 229 wrong.

**App fix.** In `crim_app/ngrams.py`, both `melodic_ngram_data` and
`harmonic_ngram_data` now always call `durations(..., mask_df=ngrams)`.

**For the library (to review):**
- [ ] `process_ngrams_df`: line rows up by label, not position. Before melting, reindex
      `ngrams_duration` to `ngrams_df.index` / columns, or merge the melted frames on
      `['start', 'voice']`. Then an unmasked duration frame can't misplace bars.
- [ ] At least warn, or raise, when `ngrams_duration.index` doesn't equal `ngrams_df.index`.
- [ ] `plot_ngrams_heatmap` docstring: say that `ngrams_duration` must come from
      `durations(df=..., n=..., mask_df=ngrams_df)`.
- [ ] Check other users of `process_ngrams_df` (`plot_ngrams_barchart`, and anything in
      `networks.py` or the corpus tools) for the same assumption.
- [ ] Tutorials: 08 and 17 always pass `mask_df` for entries. Check that no
      tutorial plots `ngrams()` output with unmasked durations.

---

## 2. "Entries only" mostly showed n-grams that aren't entries

**Symptom.** The entries heat map didn't seem to reflect entry status.

**Cause.** The app (and tutorials 08 and 17) call
`entries(df=mel, n=n, thematic=True, anywhere=True)`. In `main_objs.py:3610`, with
`anywhere=True` the method finds the patterns that occur at least once as an entry (after
a rest or fermata, or at the start), then returns **every occurrence** of those patterns
(`ret = df[df.isin(entries.stack().values)]`). Nothing in the result marks which cells
are real entries.

**Evidence** (Model 0008, n=3): `anywhere=True` gives 334 cells (24 patterns), of which
only 62 really follow a rest. `anywhere=False` gives 62 cells (13 patterns). With the
notebook settings at n=4, 61 of 251 cells are real entries.

**App fix.** The melodic page's "Melodic Entries" setting now has three options
(`ENTRY_MODES` in `crim_app/ngrams.py`):

| Option (in menu order) | Call |
|---|---|
| Entries only (after rest or fermata), the default | `entries(thematic=True, anywhere=False, exclude=['Rest'])` |
| Entry patterns, all occurrences | `entries(thematic=True, anywhere=True, exclude=['Rest'])` |
| All ngrams | `ngrams(exclude=['Rest'])` |

**For the library (to review):**
- [ ] `_data_settings` (`visualizations.py:883`, about line 910) writes
      `'thematic entries'` whatever `anywhere` is. `anywhere` is already recorded by
      `@_records_settings('entries', ('n', 'thematic', 'anywhere'))`, so the subtitle
      could say e.g. "entry patterns, all occurrences" when `anywhere=True`. The app works
      around this by naming the mode in the chart title.
- [ ] Consider a way to mark real entries in the heat map when `anywhere=True`, for
      example an `entries` flag column or mask passed to `plot_ngrams_heatmap` that sets
      opacity or outline.
- [ ] `entries` docstring: make the `anywhere` behaviour explicit, e.g. "returns all
      occurrences of entry patterns, including ones that don't follow a rest".
- [ ] Tutorials 08 and 17 call the result "entries". Consider explaining `anywhere=True`
      there.

---

## 3. `entries()` keeps n-grams that contain rests

**Cause.** `entries` has `exclude=[]` as its default (`main_objs.py:3610`) and passes it to
`self.ngrams(df, n, exclude=exclude)` (line 3641). That overrides `ngrams()`'s own
default, `exclude=['Rest']`, so entry patterns can contain `'Rest'`.

**Evidence.** The notebook code from tutorial 08 on Model 0008 (n=4) returns 251 cells, 16
of which contain `'Rest'`. With `exclude=['Rest']` it returns 235. The app passes
`exclude=['Rest']` explicitly.

**For the library (to review):**
- [ ] Should `entries(exclude=...)` default to `['Rest']`, to match `ngrams()`? Check
      whether anything depends on the current default.
- [ ] Tutorials 08 (about lines 498 and 552), 16 (about lines 266 and 278) and 17 call
      `entries` without `exclude`.

---

## 4. New: Show Paired Plots (model and derivatives)

The app's version of tutorial 08, "Heat Map of Shared Ngrams in Two or More Pieces",
on both n-gram pages.

- Shown only when two or more pieces are selected. The **first selected piece** is the
  model (the corpus keeps the sidebar's order of selection).
- For each derivative: a heading, then the model's heat map and the derivative's heat
  map. **Both are limited to the patterns the model and that derivative share** (the
  tutorial's `set(...).intersection(...)`), and the pattern filter narrows them further.
- Colors: `viz.color_manager.reset()`, then `viz.pre_register_patterns(model_patterns)`
  once, so a pattern has the same color in every pair.
- The table, counts and Verovio excerpts keep only cells whose pattern is found in the
  model.
- Code: `build_paired_heatmaps`, `show_paired_heatmaps`, `limit_table_to_model` and
  `store_ngram_results(..., paired=)` in `crim_app/ngrams.py`.

Checked on Model 0019 with Mass 0019 movements 1 and 2, with entries only and with all
n-grams. Each chart showed only shared patterns, and no pattern got two colors.

**For the library (to review):**
- [ ] `plot_ngrams_heatmap(selected_patterns=[])` means "all patterns". So an empty
      intersection plots **everything** instead of nothing. The tutorial loop would do
      this for a derivative that shares no patterns with the model. The app skips such
      pairs. In the library, consider `selected_patterns=None` for "all" and `[]` for "none".
- [ ] `viz.color_manager` is a single module-level object (shared by every Streamlit
      session). The app wraps reset, register and plot in a lock. A
      `color_manager` argument, or a context manager, in the library would be cleaner.
- [ ] A library helper (e.g. `viz.plot_paired_ngram_heatmaps(model, derivatives, ...)`)
      could replace the tutorial's hand-written loop.

---

## Open questions

- In paired mode, the model's plot shows only the patterns shared with that derivative
  (as in the tutorial), not all the model's patterns. Confirm this is the intended view.
- The old single-page app, `intervals_streamlit2.py`, still has the earlier `entries_only`
  code and the unmasked durations. It wasn't changed.
