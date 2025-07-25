# JEPX Spot Market Scraper

[![OpenDenki_Data JEPX Spot data](https://github.com/dlxiii/jepx_scraper/actions/workflows/jepx_spot.yml/badge.svg?branch=main)](https://github.com/dlxiii/jepx_scraper/actions/workflows/jepx_spot.yml)

This repository provides utilities for downloading daily spot market data from the [Japan Electric Power Exchange](https://www.jepx.jp/).  
It relies on Playwright to automate the JEPX website and retrieve CSV files such as bid curves, splitting area results, yearly summaries and virtual price series.

## Features

- Python API via the `JEPX` class defined in `jepx_scraper.py`.
- Command line helpers: `run_jepx_curve.py`, `run_jepx_summary.py` and
  `run_jepx_virtual_price.py`.
- Data stored under `csv/<YEAR>/` with annual summary and virtual price files in the top `csv/` folder.
- GitHub Actions workflow for scheduled scraping and artifact upload.

## Requirements

- Python 3.11 (older versions may work)
- Playwright with Chromium browsers

### Installation

```bash
pip install -r requirements.txt
playwright install
```

On Linux you may need to install extra system packages for Playwright; see the [Playwright documentation](https://playwright.dev/python/docs/intro).

## Usage

Download bid curve data for a specific date:

```bash
python run_jepx_curve.py 2025/04/24
```

Download the annual summary for the same date (the scraper picks the correct financial year):

```bash
python run_jepx_summary.py 2025/04/24
```

Download the virtual price for the same date (also using the appropriate financial year):

```bash
python run_jepx_virtual_price.py 2025/04/24
```

All CSV files will be written to `csv/<YEAR>/`. Annual summaries are named `csv/spot_summary_<YEAR>.csv`.
Virtual price data is saved as `csv/virtualprice_<YEAR>.csv` and `csv/virtualprice_diff_<YEAR>.csv`.

You can also use the `JEPX` class directly:

```python
from jepx_scraper import JEPX

jepx = JEPX()
price_df, amount_df = jepx.spot_table("2025/04/24")
jepx.close_session()
```

`spot_table` returns pandas DataFrames with 30‑minute spot price and volume tables.
The same `JEPX` instance also exposes `spot_curve`, `spot_summary` and
`spot_virtual_price` for downloading CSV files.

## Repository data

The `csv/` directory currently contains about 1.5 GB of historical data. If you plan to store more files, consider [Git LFS](https://git-lfs.github.com/) or another storage solution instead of keeping everything in Git.

## Partial clone with sparse checkout

If you only need the code and not the historical CSV files, you can enable sparse checkout to avoid downloading the `csv/` directory:

```bash
git config core.sparseCheckout true
echo /* > .git/info/sparse-checkout
echo !csv/ >> .git/info/sparse-checkout
git pull origin main     # use `master` if that is your default branch
git read-tree -mu HEAD
```

These commands check out everything except `csv/`, which significantly reduces the download size.
## Automation with GitHub Actions

The workflow file `.github/workflows/jepx.yml` runs every day at 10:30 JST, executes both scraper scripts and commits any new CSVs back to the repository. If you fork this project, enable GitHub Actions from the “Actions” tab to activate the schedule.

## Windows batch script

`batch_scraper.bat` loops over a date range and calls `run_jepx_curve.py` for each day. Adjust `START_DATE` and `END_DATE` before running if you want to backfill data on Windows.

This project is now considered complete and ready for general use.

---
Feel free to open issues or pull requests for improvements.
