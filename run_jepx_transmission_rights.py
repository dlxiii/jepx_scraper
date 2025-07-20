from jepx_scraper import JEPX
import sys
from datetime import datetime

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python jepx_scraper.py YYYY/MM/DD --> transmission_rights")
        sys.exit(1)

    date_str = sys.argv[1]
    datetime.strptime(date_str, "%Y/%m/%d")

    jepx = JEPX()
    jepx.transmission_rights(date=date_str, debug=False)
    jepx.close_session()