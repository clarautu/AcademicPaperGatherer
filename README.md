# AcademicPaperGatherer

**AcademicPaperGatherer (APG)** is a modular Python tool that automates the collection, filtering, and preparation of academic papers from Google Scholar and ArXiv. Designed to streamline literature reviews and support large language model (LLM) workflows, it converts papers into plain text and extracts useful metadata for further analysis.

Originally developed as part of the *Scholarly AI Analyzer* project, APG can also be installed and used independently as a global command line interface (CLI) tool.

---

## Key Features

- **Google Scholar & ArXiv Integration**: Gather results from one or both sources using the same query.  
- **Prompt-to-Search Conversion**: Transforms user prompts into valid search queries.  
- **Modular Design**: Run the full pipeline or any module individually.
- **Result and File Collection**: Gathers links and attempts to download full-text PDFs and any directly referenced articles.
- **Relevance Filtering**: Filters out unrelated papers and removes duplicates based on the original prompt.
- **Metadata Extraction & Text Conversion**: Extracts author, title, abstract, and other metadata; converts papers to plaintext for use in downstream Natural Language Processing (NLP) tasks.

---

## Modules

Each component can run independently or as part of the full pipeline:

| Module | Description |
|--------|-------------|
| **ResultGatherer** | Gathers the specified number of results from Google Scholar using the supplied prompt. Returns a list of dictionaries. |
| **FileGatherer** | Downloads PDF files referenced by the gathered results and extracts metadata. |
| **TextConverterAndExtractor** | Visits each result and attempts to gather the directly referenced article and/or any referenced articles on the page. Filters based on relevance to the prompt. Extracts metadata (title, keywords, authors, modification date) and saves relevant articles. |
| **ArxivScraper** | Gathers research papers and their metadata from ArXiv. Supports optional inclusion in the full pipeline via `--include_arxiv`. |

---

## Installation

### Option 1: Local, Script-Based Method

```bash
git clone https://github.com/clarautu/AcademicPaperGatherer.git
cd AcademicPaperGatherer
pip install -r requirements.txt
```
This method allows for local running of the script in the install directory with
```bash
python run.py <command> [options]
```

### Option 2: Install via pip

```bash
git clone https://github.com/clarautu/AcademicPaperGatherer.git
cd AcademicPaperGatherer
pip install .
```
This installs the tool globally and allows for running anywhere with
```bash
APG <command> [options]
```

## Usage

This tool can run its full pipeline or individual modules using subcommands.

### General Syntax

```bash
python run.py <command> [options]
```

### Subcommands

#### `all` — Run the full pipeline | Optionally includes ArXiv scraping

Locally
```bash
python run.py all --query "search query" --directory "output directory" [options]
```
or globally
```bash
APG all --query "search query" --directory "output directory" [options]
```

**Required:**
- `--query` – search query used to gather results
- `--directory` – directory to save files to

**Optional:**
- `--total_results` – number of results to gather (default: 100)
- `--year_start` – start of year range (e.g., 2010)
- `--year_end` – end of year range (e.g., 2024)
- `--meta_can_be_missing` – flag that allow files with missing metadata
- `--include_arxiv` – flag that includes ArXiv scraping and gathering

---

#### `arxiv` – Only run ArXiv scraping

Locally
```bash
python run.py arxiv --query "search query" --directory "output directory" [options]
```
or globally
```bash
APG arxiv --query "search query" --directory "output directory" [options]
```

**Required:**
- `--query` – search query used to gather results
- `--directory` – directory to save files to

**Optional:**
- `--total_results` – number of results to gather (default: 100)
- `--meta_can_be_missing` – flag that allow files with missing metadata

---

#### `results` — Only gather search results

Locally
```bash
python run.py results --query "search query" --directory "output directory" [options]
```
or globally
```bash
APG results --query "search query" --directory "output directory" [options]
```

**Required:**
- `--query` – search query used to gather results
- `--directory` – directory to save files to

**Optional:**
- `--total_results` – number of results to gather (default: 100)
- `--year_start` – start of year range (e.g., 2010)
- `--year_end` – end of year range (e.g., 2024)

---

#### `files` — Only gather files from an existing `results.txt` file

Locally
```bash
python run.py files --query "search query" --directory "output directory" [options]
```
or globally
```bash
APG files --query "search query" --directory "output directory" [options]
```

**Required:**
- `--query` – search query used to gather results
- `--directory` – directory to save files to

**Optional:**
- `--year_start` – start of year range (e.g., 2010)
- `--year_end` – end of year range (e.g., 2024)
- `--meta_can_be_missing` – flag that allow files with missing metadata

**Note:** Requires a `results.txt` file already present in the given directory.

---

#### `convert` — Only run text conversion and extraction

Locally
```bash
python run.py convert --directory "output directory"
```
or globally
```bash
APG convert --directory "output directory"
```

**Required:**
- `--directory` – directory to save files to

**Note:** Assumes files have already been gathered into the output directory.

---

### Examples

Run the whole pipeline (including ArXiv):

Locally
```bash
python run.py all --query "climate change" --directory "data" --include_arxiv
```
or globally
```bash
APG all --query "climate change" --directory "data" --include_arxiv
```
---

Run the whole pipeline (excluding ArXiv):

Locally
```bash
python run.py all --query "climate change" --directory "data"
```
or globally
```bash
APG all --query "climate change" --directory "data"
```
---

Only gather results from Google Scholar:

Locally
```bash
python run.py results --query "machine learning" --directory "ml_data" --total_results 50
```
or globally
```bash
APG results --query "machine learning" --directory "ml_data" --total_results 50
```
---

Only gather results from ArXiv:

Locally
```bash
python run.py arxiv --query "machine learning" --directory "ml_data" --total_results 50
```
or globally
```bash
APG arxiv --query "machine learning" --directory "ml_data" --total_results 50
```
---

Convert already-downloaded files:

Locally
```bash
python run.py convert --directory "ml_data"
```
or globally
```bash
APG convert --directory "ml_data"
```
---


## Known Limitations
#### 403 Errors
Many sites respond to automated requests with HTTP 403 errors, "Forbidden Access". The frequency of these errors varies greatly from one prompt to the next, but severely limits the number of papers that are gathered. In an attempt to combat this, several methods were explored and tested (such as free proxies, headless browsers, and user behavior mimicking) with little success.

This remains an active issue with the Google Scholar portion of this tool. Thankfully, ArXiv provides a first-party API. So, this issue does not impact the ArXiv scraping portion of this tool.

#### Google Colab
This tool does not work when run inside of Google Colab, a popular Python notebook resource. Both Colab and Google Scholar are owned by Google, which means that all of Colab's IP addresses are known and flagged by Google Scholar as automated/suspicious traffic.

## Considerations

This tool systematically pings Google Scholar/ArXiv and any returned URLs, potentially many times. As such, built in delays are added for compliance and bot-throttling reasons. Change or remove these at your own risk.
