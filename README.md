# intervals-streamlit

# A Streamlit Web Application for CRIM Intervals

[Learn about CRIM Intervals]( https://github.com/HCDigitalScholarship/intervals/blob/main/README.md)

[Learn about Streamlit](https://docs.streamlit.io/library/api-reference)

## Use it Online

[intervals-streamlit.crimproject.org](https://intervals-streamlit.crimproject.org/)

## Run it Locally on your Own Computer

Running the app on your own machine is much faster than the shared online version. Everything below
is done in a terminal; the first setup takes about 15 minutes, and after that starting the app is
two commands.

### 1. Install VS Code

[Download Visual Studio Code](https://code.visualstudio.com/download) and install it. We use its
built-in terminal (**Terminal → New Terminal**) for every step below. Optionally, install the
**Python** extension from Microsoft (Extensions icon in the left-hand bar).

### 2. Install Python with Miniconda

[Miniconda](https://www.anaconda.com/docs/getting-started/miniconda/install) is a small installer
that provides Python and the `conda` command for creating *virtual environments*: self-contained sets
of libraries kept separate from everything else on your computer.

- Download the Miniconda installer for your system from the link above and run it with the default
  options. (On a Mac, choose the Apple Silicon or Intel version to match your machine.)
- When it finishes, **quit and reopen VS Code**, open a terminal, and check it works:

```
conda --version
```

> **Windows:** if `conda` is not recognised, open **Anaconda Prompt (miniconda3)** from the Start
> menu, run `conda init powershell`, then quit and reopen VS Code.
>
> **Mac:** if `conda` is not found, run `~/miniconda3/bin/conda init zsh`, then open a new terminal.

### 3. Create the Environment

Create an environment named `streamlit_intervals` with Python 3.11 (type **y** to confirm):

```
conda create -n streamlit_intervals python=3.11
```

Then activate it:

```
conda activate streamlit_intervals
```

The start of your terminal prompt should now read `(streamlit_intervals)`.

### 4. Get the Code

Install `git` into the environment (if you don't already have it), move to the folder where you want
the code to live, and clone the repository:

```
conda install git
cd ~/Documents
git clone https://github.com/RichardFreedman/intervals-streamlit.git
cd intervals-streamlit
```

To browse the files, use **File → Open Folder…** in VS Code and choose `intervals-streamlit`.

### 5. Install the Requirements

With the environment active and the terminal inside `intervals-streamlit`, run:

```
pip install -r requirements.txt
```

This installs Streamlit, CRIM Intervals and everything they depend on. It takes a few minutes.

### 6. Run the App

```
python -m streamlit run streamlit_app.py
```

> Use `python -m streamlit` rather than plain `streamlit`. If another copy of Streamlit is installed
> elsewhere on your computer, plain `streamlit` may start that one instead, and you'll see
> `ModuleNotFoundError: No module named 'crim_intervals'`.

After a few seconds the app opens in your web browser (if it doesn't, open the **Local URL** shown in
the terminal, usually http://localhost:8501).

- Choose pieces from CRIM, or upload your own MEI or MusicXML files, in the **sidebar**.
- Move between the analysis pages (Notes, Melodic Intervals, Cadences, Voice Ranges & Species …)
  using the links at the top of the sidebar. Your selected pieces stay loaded as you switch pages.

To stop the app, click in the terminal and press **Ctrl + C**.

### Next Time

```
conda activate streamlit_intervals
cd ~/Documents/intervals-streamlit
python -m streamlit run streamlit_app.py
```

### Updating

To get the latest version of the app and of CRIM Intervals:

```
conda activate streamlit_intervals
cd ~/Documents/intervals-streamlit
git pull
pip install --upgrade -r requirements.txt
```

## How the App is Organized (for contributors)

| Path | What it holds |
|---|---|
| `streamlit_app.py` | Entry point: page navigation and the sidebar piece picker |
| `app_pages/` | One file per analysis page (notes, melodic, cadences, ranges & species, …) |
| `crim_app/common.py` | Shared imports, constants, piece loading and chart helpers |
| `crim_app/filters.py` | Interactive table filters used by the pages |
| `crim_app/ngrams.py` | Cached ngram heat-map builders |
| `requirements.txt` | Python dependencies (also used by Streamlit Community Cloud) |
