from pathlib import Path
from narrative.sec_parser import _extract_text_from_filing
import logging
import re

d = list(Path("sec_filings/sec-edgar-filings/NVDA/10-Q").iterdir())[0]
text = _extract_text_from_filing(d)

print(f"Total len: {len(text)}")
for m in re.finditer(r"(?i)results\s+of\s+operations", text):
    print(f"results of operations at {m.start()}")

for stop in [
    "CONTROLS AND PROCEDURES",
    "QUANTITATIVE AND QUALITATIVE DISCLOSURES",
    "Item 4", "ITEM 4",
]:
    for m in re.finditer(stop, text):
        print(f"STOP {stop} at {m.start()}")
