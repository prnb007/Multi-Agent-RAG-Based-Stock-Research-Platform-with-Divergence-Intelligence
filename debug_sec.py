from pathlib import Path
from narrative.sec_parser import _extract_text_from_filing
import logging
import re
logging.basicConfig(level=logging.INFO)

d = list(Path("sec_filings/sec-edgar-filings/AAPL/10-Q").iterdir())[0]
text = _extract_text_from_filing(d)

# Find PART II skipping TOC
part2_match = re.search(r"(?i)PART\s+II[\s\.\-]", text[50000:])
if part2_match:
    text2 = text[:50000 + part2_match.start()]
else:
    text2 = text

print(f"Len text2 (Part I): {len(text2)}")

patterns = [
    r"(?i)results\s+of\s+operations",
    r"(?i)management.{0,30}discussion.{0,30}analysis",
    r"(?i)overview\b.{0,100}(revenue|net\s+sales|operating)",
]
start_pos = None
# Find the LAST occurrence in Part I (to skip TOC)
for pattern in patterns:
    matches = list(re.finditer(pattern, text2))
    if matches:
        start_pos = matches[-1].start()
        print(f"Matched pattern {pattern} at {start_pos}")
        break

if not start_pos:
    print("NO START POS")
    third = len(text2) // 3
    mda = text2[third: third * 2][:15000]
else:
    end_patterns = [
        r"(?i)liquidity\s+and\s+capital",
        r"(?i)critical\s+accounting",
        r"(?i)item\s*3[\.\s]*quantitative",
        r"(?i)off[\s\-]balance",
    ]
    end_pos = len(text2)
    for pattern in end_patterns:
        match = re.search(pattern, text2[start_pos + 500:])
        if match:
            end_pos = start_pos + 500 + match.start()
            print(f"Matched end pattern {pattern} at {end_pos}")
            break
    mda = text2[start_pos:end_pos]
    mda = mda[200:15200]
    
print(f"MDA length: {len(mda)}")
