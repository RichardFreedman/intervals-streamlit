"""Model Finder"""
import streamlit as st
from crim_app.common import *
from crim_app.filters import *

piece, corpus, corpus_length, crim_piece_selections, uploaded_files_list = get_selection()

st.subheader("Model Finder")
with st.expander("How to use this tool"):
    st.markdown("""
    **About this tool**
    The Model Finder compares melodic ngram patterns across all pieces in your corpus, identifying
    shared soggetti (subjects) between works. It requires at least two pieces. Use this to discover
    which pieces share melodic material — useful for tracing models, borrowings, or common stylistic
    patterns across composers or repertoire groups.

    **Key settings**
    - **Ngram Length** — the number of consecutive melodic intervals in each pattern. 4 is a common
      starting point; shorter values find more general similarities, longer values find more specific ones.

    **Reading the results**
    - The **cross-plot heatmap** shows the proportion of shared entry ngrams between each pair of
      pieces. Values range from 0 (no shared patterns) to 1.0 (100% shared — expected when a piece
      is compared to itself). Higher values suggest a stronger melodic relationship between two works.
    - Rows and columns represent pieces; darker cells indicate more shared melodic material.
    - The **table** shows the raw proportions behind the heatmap.
    - Use the download button to save the interactive chart as an HTML file.
    - **Note:** this tool requires at least two pieces to be selected.

    [Know the code — CRIM Intervals Model Finder documentation](https://github.com/HCDigitalScholarship/intervals/blob/main/tutorial/16_Model_Finder.md)
    """)
if corpus_length <= 1 or corpus is None:
    st.write("Please select at least two pieces to compare")
    st.stop()


@st.cache_data(**PIECE_CACHE)
def model_finder(corpus, n):
    return corpus.modelFinder(n=n)


# ---------------------------------------------------------------- settings
form_col, _ = st.columns([1, 3])
with form_col:
    with st.form("Model Finder Settings"):
        length_choice = st.number_input('Select ngram Length', value=4, step=1, min_value=1)
        submitted = st.form_submit_button('Submit')

if submitted:
    with st.spinner("Comparing entries across the corpus…"):
        st.session_state.model_finder_result = (int(length_choice),
                                                model_finder(corpus, int(length_choice)))

# ---------------------------------------------------------------- results (full width)
if 'model_finder_result' in st.session_state:
    n, soggetto_cross_plot = st.session_state.model_finder_result
    n_pieces = len(soggetto_cross_plot.index)
    fig = px.imshow(soggetto_cross_plot, color_continuous_scale="YlGnBu", aspect="auto",
                    text_auto='.2f', zmin=0, zmax=1,
                    labels=dict(color="Shared entries"))
    fig.update_layout(title=f"Shared Melodic Entries between Pieces<br><sup>n = {n} · {n_pieces} pieces</sup>",
                      height=max(450, 60 * n_pieces + 250))
    fig.update_xaxes(tickangle=-45, title=None)
    fig.update_yaxes(title=None)
    show_plotly(fig, f"model_finder_n{n}.html", 'model_finder')
    with st.expander("Table of shared entries"):
        st.dataframe(soggetto_cross_plot, use_container_width=True)
        st.download_button("Download as CSV", soggetto_cross_plot.to_csv(),
                           file_name=f"model_finder_n{n}.csv", mime='text/csv', key='model_finder_csv')
