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

    [Know the code — CRIM Intervals Model Finder documentation](https://github.com/HCDigitalScholarship/intervals/blob/main/tutorial/14_Model_Finder.md)
    """)
if corpus_length <= 1 or corpus is None:
    st.write("Please select at least two pieces to compare")
    st.stop()


@st.cache_data(**PIECE_CACHE)
def model_finder(corpus, n):
    return corpus.modelFinder(n=n)


    # Initialize session state
# if 'ready_to_download' not in st.session_state:
#     st.session_state.ready_to_download = False

# Main form for settings
form_col, _ = st.columns([1, 2])
with form_col:
 with st.form("Model Finder Settings"):
    length_choice = st.number_input('Select ngram Length', value=4, step=1)
    
    # Plot section
    soggetto_cross_plot = model_finder(corpus, int(length_choice))
    st.dataframe(soggetto_cross_plot)
    fig = px.imshow(soggetto_cross_plot, color_continuous_scale="YlGnBu", aspect="auto")
    
    if st.form_submit_button('Submit'):
        # Prepare data for download but don't show button yet
        st.session_state.plot_data = soggetto_cross_plot
    st.plotly_chart(fig)
    

# Separate section for download
if hasattr(st.session_state, 'plot_data'):
    def get_model_html():
        """Convert progress plot to HTML with preserved colors and interactivity"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Model Finder Crossplot</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body {{
                    margin: 0;
                    padding: 20px;
                    font-family: Arial, sans-serif;
                }}
                .chart-container {{
                    width: 100%;
                    height: 600px;
                }}
            </style>
        </head>
        <body>
            <div class="chart-container" id="chart"></div>
            <script>
                var figure = {fig.to_json()};
                Plotly.newPlot('chart', figure.data, figure.layout, {{
                    responsive: true,
                    displayModeBar: true,
                    displaylogo: false
                }});
            </script>
        </body>
        </html>
        """
        return html_content
    
    html_content = get_model_html()
    st.download_button(
        label="Download the Chart",
        data=html_content,
        file_name=f"model_finder.html",
        mime="text/html"
    )
else:
    pass

