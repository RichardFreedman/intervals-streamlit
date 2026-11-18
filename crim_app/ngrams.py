"""Cached ngram heat-map builders shared by the melodic and harmonic ngram pages."""
import streamlit as st
from crim_app.common import *

# function for ngram heatmap
@st.cache_data(**PIECE_CACHE)
def ngram_heatmap(piece, combine_unisons_choice, kind_choice, directed, compound, length_choice, include_count, entries_only=False):
    # find entries for model
    nr = piece.notes(combineUnisons = combine_unisons_choice)

    nr = piece.numberParts(nr)

    mel = piece.melodic(df = nr, 
                        kind = kind_choice,
                        directed = directed,
                        compound = compound,
                        end = False)
    mel_detail = piece.detailIndex(mel)
    # this is for entries only
    if entries_only == True:
        # pass the following ngrams to the plot below as first df
        entry_ngrams = piece.entries(df = mel,
                                    n = length_choice, 
                                    thematic = True, 
                                    anywhere = True,
                                    exclude = ['Rest'])
        # pass the ngram durations below to the plot as second df
        entry_ngrams_duration = piece.durations(df = mel, 
                                            n =length_choice, 
                                            mask_df = entry_ngrams)
        # make the heatmap
        entry_ng_heatmap = viz.plot_ngrams_heatmap(entry_ngrams, 
                                         entry_ngrams_duration, 
                                         selected_patterns=[], 
                                         voices=[],  
                                         includeCount=include_count)
        # rename entry_ngrams df as mel_ngrams for display
        entry_ngrams_detail = piece.detailIndex(entry_ngrams, offset = False) 
        return entry_ngrams_detail, entry_ng_heatmap
    # this is for all mel ngrams (if entries is False in form)
    else:
        mel_ngrams = piece.ngrams(df = mel, n = length_choice, exclude = ['Rest'])
        mel_ngrams_duration = piece.durations(df = mel, 
                                          n =length_choice)
        
        ng_heatmap = viz.plot_ngrams_heatmap(mel_ngrams, 
                                         mel_ngrams_duration, 
                                         selected_patterns=[], 
                                         voices=[], 
                                         includeCount=include_count)
        
        mel_ngrams_detail = piece.detailIndex(mel_ngrams, offset = False)
        return mel_ngrams_detail, ng_heatmap

# function for harmonic ngram heatmap
@st.cache_data(**PIECE_CACHE)
def harmonic_ngram_heatmap(piece, kind_choice, directed, compound, against_low, length_choice, include_count):
    nr = piece.notes()
    nr = piece.numberParts(nr)
    har = piece.harmonic(df=nr,
                         kind=kind_choice,
                         directed=directed,
                         compound=compound,
                         againstLow=against_low)
    har_ngrams = piece.ngrams(df=har, n=length_choice, exclude=['Rest'])
    har_ngrams_duration = piece.durations(df=har, n=length_choice)
    ng_heatmap = viz.plot_ngrams_heatmap(har_ngrams,
                                         har_ngrams_duration,
                                         selected_patterns=[],
                                         voices=[],
                                         includeCount=include_count)
    har_ngrams_detail = piece.detailIndex(har_ngrams, offset=False)
    return har_ngrams_detail, ng_heatmap

# ngram form
