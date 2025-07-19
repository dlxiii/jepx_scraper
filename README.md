# jepx_scraper

This project downloads spot market data from the JEPX website using Playwright.

## Installation

Install Python dependencies and the Playwright browsers:

```bash
pip install -r requirements.txt
playwright install
```

## Usage

Run the helper script with a date in `YYYY/MM/DD` format. CSV files will be written to the `csv/` directory.

```bash
python run_jepx_curve.py 2025/04/24
```

## Data storage

The repository includes a `csv/` directory containing roughly 1.4 GB of historical CSV files. If you plan to store more data, consider using [Git LFS](https://git-lfs.github.com/) or another external storage option instead of committing large files directly to Git.
