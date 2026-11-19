"""Interactive DataFrame filter widgets shared by the analysis pages."""
import streamlit as st
import pandas as pd
from pandas.api.types import is_numeric_dtype

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
# for NR
# st.cache_data(experimental_allow_widgets=True)
def filter_dataframe_nr(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a UI on top of a dataframe to let viewers filter columns

    Args:
        df (pd.DataFrame): Original dataframe

    Returns:
        pd.DataFrame: Filtered dataframe
    """
 
    df = df.copy()
    modification_container = st.container()
    with modification_container:     
        _show = st.checkbox("Filter results by the contents of each column", value=False, key="show_filters_filter_dataframe_nr")
        to_filter_columns = [] if not _show else st.multiselect("Filter Notes by Various Fields", df.columns)
        if _show:
            st.write("Remember that initial choices will constrain subsequent filters!")
        if to_filter_columns:
        # here we are filtering by column
            for column in to_filter_columns:
                left, right = st.columns((1, 20))
                left.write("↳")
                # Treat columns with < 10 unique values as categorical
                # here 
                if isinstance(df[column].dtype, pd.CategoricalDtype) or df[column].nunique() < 50:
                    user_cat_input = right.multiselect(
                        f"Values for {column}",
                        df[column].unique(),
                        default=list(df[column].unique()),
                    )
                    df = df[df[column].isin(user_cat_input)]  
        # gets values for highlighted filters
        df_no_meta = df.loc[:, ~df.columns.isin(['Composer', "Title", 'Date', "Measure", "Beat"])]
        df_no_meta_col_names = df_no_meta.columns.tolist()
        df_voices_only = df[df_no_meta_col_names]
        melted = pd.melt(df_voices_only)
        values_list = melted['value'].unique()
        values_list = [i for i in values_list if i]
        values_list = [element for element in values_list if not pd.isnull(element)]
        values_list = [x for x in values_list if x != "-"]
        user_text_input = [] if not _show else st.multiselect("Filter on Notes", values_list)
        if user_text_input:
            def highlight_matching_strings(val):
                match_strings = user_text_input
                for match_string in match_strings:
                    if match_string == val:
                        return 'background-color: #ccebc4'
                return ''
            df = df.reset_index(drop=True).fillna('')
            df = df[df[df_no_meta_col_names].apply(lambda x: x.isin(user_text_input)).any(axis=1)]
            df = df.style.map(highlight_matching_strings)
        else:
            df = df.reset_index(drop=True).fillna('')
            df = df.style
    return df

# for dur
def filter_dataframe_dur(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a UI on top of a dataframe to let viewers filter columns

    Args:
        df (pd.DataFrame): Original dataframe

    Returns:
        pd.DataFrame: Filtered dataframe
    """
 
    df = df.copy()
    modification_container = st.container()
    with modification_container:     
        _show = st.checkbox("Filter results by the contents of each column", value=False, key="show_filters_filter_dataframe_dur")
        to_filter_columns = [] if not _show else st.multiselect("Filter Durations by Various Fields", df.columns)
        if _show:
            st.write("Remember that initial choices will constrain subsequent filters!")
        if to_filter_columns:
        # here we are filtering by column
            for column in to_filter_columns:
                left, right = st.columns((1, 20))
                left.write("↳")
                # Treat columns with < 10 unique values as categorical
                # here 
                if isinstance(df[column].dtype, pd.CategoricalDtype) or df[column].nunique() < 50:
                    user_cat_input = right.multiselect(
                        f"Values for {column}",
                        df[column].unique(),
                        default=list(df[column].unique()),
                    )
                    df = df[df[column].isin(user_cat_input)]  
        # gets values for highlighted filters
        df_no_meta = df.loc[:, ~df.columns.isin(['Composer', "Title", 'Date', "Measure", "Beat"])]
        df_no_meta_col_names = df_no_meta.columns.tolist()
        df_voices_only = df[df_no_meta_col_names]
        melted = pd.melt(df_voices_only)
        values_list = melted['value'].unique()
        values_list = [i for i in values_list if i]
        values_list = [element for element in values_list if not pd.isnull(element)]
        values_list = [x for x in values_list if x != "-"]
        user_text_input = [] if not _show else st.multiselect("Filter on Notes", values_list)
        if user_text_input:
            def highlight_matching_strings(val):
                match_strings = user_text_input
                for match_string in match_strings:
                    if match_string == val:
                        return 'background-color: #ccebc4'
                return ''
            df = df.reset_index(drop=True).fillna('')
            df = df[df[df_no_meta_col_names].apply(lambda x: x.isin(user_text_input)).any(axis=1)]
            df = df.style.map(highlight_matching_strings)
        else:
            df = df.reset_index(drop=True).fillna('')
            df = df.style
    return df

# for MEL
# st.cache_data(experimental_allow_widgets=True)
def filter_dataframe_mel(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a UI on top of a dataframe to let viewers filter columns

    Args:
        df (pd.DataFrame): Original dataframe

    Returns:
        pd.DataFrame: Filtered dataframe
    """
 
    df = df.copy()
    modification_container = st.container()
    with modification_container:
        _show = st.checkbox("Filter results by the contents of each column", value=False, key="show_filters_filter_dataframe_mel")
        to_filter_columns = [] if not _show else st.multiselect("Filter Melodic Intervals by Various Fields", df.columns)
        if _show:
            st.write("Remember that initial choices will constrain subsequent filters!")
        if to_filter_columns:
        # here we are filtering by column
        # to_filter_columns = st.multiselect("Limit by Composer, Title, Date, or Voice", df.columns)
            for column in to_filter_columns:
                left, right = st.columns((1, 20))
                left.write("↳")
                # Treat columns with < 10 unique values as categorical
                # here 
                if isinstance(df[column].dtype, pd.CategoricalDtype) or df[column].nunique() < 50:
                    user_cat_input = right.multiselect(
                        f"Values for {column}",
                        df[column].unique(),
                        default=list(df[column].unique()),
                    )
                    df = df[df[column].isin(user_cat_input)]
        # gets values for highlighted filters
        df_no_meta = df.loc[:, ~df.columns.isin(['Composer', "Title", 'Date'])]
        df_no_meta_col_names = df_no_meta.columns.tolist()
        df_voices_only = df[df_no_meta_col_names]
        melted = pd.melt(df_voices_only)
        values_list = melted['value'].unique()
        values_list = [i for i in values_list if i]
        values_list = [element for element in values_list if not pd.isnull(element)]
        values_list = [x for x in values_list if x != "-"]
        user_text_input = [] if not _show else st.multiselect("Filter on Intervals", values_list)
        if user_text_input:
            def highlight_matching_strings(val):
                match_strings = user_text_input
                for match_string in match_strings:
                    if match_string == val:
                        return 'background-color: #ccebc4'
                return ''
            df = df.reset_index(drop=True).fillna('')
            df = df[df[df_no_meta_col_names].apply(lambda x: x.isin(user_text_input)).any(axis=1)]
            df = df.style.map(highlight_matching_strings)
        else:
            df = df.reset_index(drop=True).fillna('')
            df = df.style   
    return df
#for har
# st.cache_data(experimental_allow_widgets=True)
def filter_dataframe_har(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a UI on top of a dataframe to let viewers filter columns

    Args:
        df (pd.DataFrame): Original dataframe

    Returns:
        pd.DataFrame: Filtered dataframe
    """
 
    df = df.copy()
    modification_container = st.container()
    with modification_container:    
        _show = st.checkbox("Filter results by the contents of each column", value=False, key="show_filters_filter_dataframe_har")
        to_filter_columns = [] if not _show else st.multiselect("Filter Harmonic Intervals by Various Fields", df.columns)
        if _show:
            st.write("Remember that initial choices will constrain subsequent filters!")
        if to_filter_columns:
        # here we are filtering by column
        # to_filter_columns = st.multiselect("Limit by Composer, Title, Date, or Voice", df.columns)
            for column in to_filter_columns:
                left, right = st.columns((1, 20))
                left.write("↳")
                # Treat columns with < 10 unique values as categorical
                # here 
                if isinstance(df[column].dtype, pd.CategoricalDtype) or df[column].nunique() < 50:
                    user_cat_input = right.multiselect(
                        f"Values for {column}",
                        df[column].unique(),
                        default=list(df[column].unique()),
                    )
                    df = df[df[column].isin(user_cat_input)]      
        # gets values for highlighted filters
        df_no_meta = df.loc[:, ~df.columns.isin(['Composer', "Title", 'Date'])]
        df_no_meta_col_names = df_no_meta.columns.tolist()
        df_voices_only = df[df_no_meta_col_names]
        melted = pd.melt(df_voices_only)
        values_list = melted['value'].unique()
        values_list = [i for i in values_list if i]
        values_list = [element for element in values_list if not pd.isnull(element)]
        user_text_input = [] if not _show else st.multiselect("Filter on Intervals", values_list)
        if user_text_input:
            def highlight_matching_strings(val):
                match_strings = user_text_input
                for match_string in match_strings:
                    if match_string == val:
                        return 'background-color: #ccebc4'
                return ''
            df = df.reset_index(drop=True).fillna('')
            df = df[df[df_no_meta_col_names].apply(lambda x: x.isin(user_text_input)).any(axis=1)]
            df = df.style.map(highlight_matching_strings)
        else:
            df = df.reset_index(drop=True).fillna('')
            df = df.style
    return df

# for NG
# st.cache_data(experimental_allow_widgets=True)
def filter_dataframe_ng(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a UI on top of a dataframe to let viewers filter columns

    Args:
        df (pd.DataFrame): Original dataframe

    Returns:
        pd.DataFrame: Filtered dataframe
    """
 
    df = df.copy()
    modification_container = st.container()
    with modification_container:       
        _show = st.checkbox("Filter results by the contents of each column", value=False, key="show_filters_filter_dataframe_ng")
        to_filter_columns = [] if not _show else st.multiselect("Filter Ngrams by Various Fields", df.columns)
        if _show:
            st.write("Remember that initial choices will constrain subsequent filters!")
        if to_filter_columns:
        # here we are filtering by column
        # to_filter_columns = st.multiselect("Limit by Composer, Title, Date, or Voice", df.columns)
            for column in to_filter_columns:
                left, right = st.columns((1, 20))
                left.write("↳")
                # Treat columns with < 10 unique values as categorical
                # here 
                if isinstance(df[column].dtype, pd.CategoricalDtype) or df[column].nunique() < 50:
                    user_cat_input = right.multiselect(
                        f"Values for {column}",
                        df[column].unique(),
                        default=list(df[column].unique()),
                    )
                    df = df[df[column].isin(user_cat_input)] 
        # gets values for highlighted filters
        df_no_meta = df.loc[:, ~df.columns.isin(['Composer', "Title", 'Date'])]
        df_no_meta_col_names = df_no_meta.columns.tolist()
        df_voices_only = df[df_no_meta_col_names]
        melted = pd.melt(df_voices_only)
        values_list = melted['value'].unique()
        values_list = [i for i in values_list if i]
        values_list = [element for element in values_list if not pd.isnull(element)]
        user_text_input = [] if not _show else st.multiselect("Filter on Ngrams", values_list)
        if user_text_input:
            def highlight_matching_strings(val):
                match_strings = user_text_input
                for match_string in match_strings:
                    if match_string == val:
                        return 'background-color: #ccebc4'
                return ''
            df = df.reset_index(drop=True).fillna('')
            df = df[df[df_no_meta_col_names].apply(lambda x: x.isin(user_text_input)).any(axis=1)]
            df = df.style.map(highlight_matching_strings)
        else:
            df = df.reset_index(drop=True).fillna('')
            df = df.style
    return df

def filter_ngrams_by_pattern(df: pd.DataFrame, key=None, return_selected=False):
    """
    Shows a list of unique ngram patterns found across all voice columns,
    lets the user select which ones to keep, and returns the filtered dataframe
    (and, with return_selected=True, the selected patterns, or None if all
    patterns are kept).
    """
    df = df.copy()
    meta_cols = ['Composer', 'Title', 'Date', 'Measure', 'Beat']
    voice_cols = [c for c in df.columns if c not in meta_cols]
    # Collect all unique ngram patterns across voice columns
    all_patterns = pd.unique(df[voice_cols].values.ravel())
    all_patterns = sorted([p for p in all_patterns if p and not pd.isnull(p)])
    show = st.checkbox("Filter by ngram pattern", value=False,
                       key=f"show_{key}" if key else "show_ngram_pattern_filter")
    selected = (st.multiselect("Select Ngram Patterns to Display", all_patterns, default=all_patterns,
                               key=key) if show else [])
    if selected:
        mask = df[voice_cols].apply(lambda col: col.isin(selected)).any(axis=1)
        df = df[mask].reset_index(drop=True)
    if not return_selected:
        return df
    return df, (selected if selected and len(selected) < len(all_patterns) else None)

#for hr
# st.cache_data(experimental_allow_widgets=True)
def filter_dataframe_hr(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a UI on top of a dataframe to let viewers filter columns

    Args:
        df (pd.DataFrame): Original dataframe

    Returns:
        pd.DataFrame: Filtered dataframe
    """
 
    df = df.copy()
    modification_container = st.container()
    with modification_container:      
        _show = st.checkbox("Filter results by the contents of each column", value=False, key="show_filters_filter_dataframe_hr")
        to_filter_columns = [] if not _show else st.multiselect("Filter the Homorhythm Results", df.columns)
        if _show:
            st.write("Remember that initial choices will constrain subsequent filters!")
        # here we are filtering by column
        # to_filter_columns = st.multiselect("Limit by Composer, Title, Date, or Voice", df.columns)
        for column in to_filter_columns:
            left, right = st.columns((1, 20))
            left.write("↳")
            # Treat columns with < 10 unique values as categorical
            # here 
            if isinstance(df[column].dtype, pd.CategoricalDtype) or df[column].nunique() < 50:
                user_cat_input = right.multiselect(
                    f"Values for {column}",
                    df[column].unique(),
                    default=list(df[column].unique()),
                )
                df = df[df[column].isin(user_cat_input)]
            elif is_numeric_dtype(df[column]):
                _min = int(df[column].min())
                _max = int(df[column].max())
                user_num_input = right.slider(
                    f"Values for {column}",
                    _min,
                    _max,
                    (_min, _max)
                )
                df = df[df[column].between(*user_num_input)]
            else:
                user_text_input = right.text_input(
                    f"Substring or regex in {column}",
                )
                if user_text_input:
                    df = df[df[column].str.contains(user_text_input)]
    return df

#for ptypes
# st.cache_data(experimental_allow_widgets=True)
def filter_dataframe_ptypes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a UI on top of a dataframe to let viewers filter columns

    Args:
        df (pd.DataFrame): Original dataframe

    Returns:
        pd.DataFrame: Filtered dataframe
    """
    if df is not None:
        df = df.copy()
        modification_container = st.container()
        with modification_container:     
            _show = st.checkbox("Filter results by the contents of each column", value=False, key="show_filters_filter_dataframe_ptypes")
            to_filter_columns = [] if not _show else st.multiselect("Filter the Presentation Type Results", df.columns)
            if _show:
                st.write("Remember that initial choices will constrain subsequent filters!")
            # here we are filtering by column
            # to_filter_columns = st.multiselect("Limit by Composer, Title, Date, or Voice", df.columns)
            for column in to_filter_columns:
                left, right = st.columns((1, 20))
                left.write("↳")
                # Treat columns with < 10 unique values as categorical
                # here 
                if isinstance(df[column].dtype, pd.CategoricalDtype) or df[column].nunique() < 50:
                    user_cat_input = right.multiselect(
                        f"Values for {column}",
                        df[column].unique(),
                        default=list(df[column].unique()),
                    )
                    df = df[df[column].isin(user_cat_input)]
                elif is_numeric_dtype(df[column]):
                    _min = int(df[column].min())
                    _max = int(df[column].max())
                    user_num_input = right.slider(
                        f"Values for {column}",
                        _min,
                        _max,
                        (_min, _max)
                    )
                    df = df[df[column].between(*user_num_input)]
                else:
                    user_text_input = right.text_input(
                        f"Substring or regex in {column}",
                    )
                    if user_text_input:
                        df = df[df[column].str.contains(user_text_input)]
        return df
#for cads
# st.cache_data(experimental_allow_widgets=True)
def filter_dataframe_cads(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a UI on top of a dataframe to let viewers filter columns

    Args:
        df (pd.DataFrame): Original dataframe

    Returns:
        pd.DataFrame: Filtered dataframe
    """
 
    df = df.copy()
    modification_container = st.container()
    with modification_container:     
        _show = st.checkbox("Filter results by the contents of each column", value=False, key="show_filters_filter_dataframe_cads")
        to_filter_columns = [] if not _show else st.multiselect("Filter the Cadence Results", df.columns)
        if _show:
            st.write("Remember that initial choices will constrain subsequent filters!")
        # here we are filtering by column
        # to_filter_columns = st.multiselect("Limit by Composer, Title, Date, or Voice", df.columns)
        for column in to_filter_columns:
            left, right = st.columns((1, 20))
            left.write("↳")
            # Treat columns with < 10 unique values as categorical
            # here 
            if isinstance(df[column].dtype, pd.CategoricalDtype) or df[column].nunique() < 50:
                user_cat_input = right.multiselect(
                    f"Values for {column}",
                    df[column].unique(),
                    default=list(df[column].unique()),
                )
                df = df[df[column].isin(user_cat_input)]
            elif is_numeric_dtype(df[column]):
                _min = int(df[column].min())
                _max = int(df[column].max())
                user_num_input = right.slider(
                    f"Values for {column}",
                    _min,
                    _max,
                    (_min, _max)
                )
                df = df[df[column].between(*user_num_input)]
            else:
                user_text_input = right.text_input(
                    f"Substring or regex in {column}",
                )
                if user_text_input:
                    df = df[df[column].str.contains(user_text_input)]
    return df
