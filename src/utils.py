import re
import time
import math
import logging
from typing import Dict, Any, List

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("HiverSupportAgent")

def clean_tweet_text(text: str) -> str:
    """Normalize tweet text by cleaning redundant whitespace, masking sensitive emails/phones."""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', '[EMAIL]', text)
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
    return text

class Timer:
    """Context manager for high-precision latency profiling."""
    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.end = time.perf_counter()
        self.elapsed_ms = (self.end - self.start) * 1000.0

def format_table(rows: List[Dict[str, Any]], headers: List[str] = None) -> str:
    """Zero-dependency pure Python ASCII table formatter."""
    if not rows:
        return ""
    if not headers:
        headers = list(rows[0].keys())

    # Compute column widths
    col_widths = {h: len(h) for h in headers}
    for r in rows:
        for h in headers:
            val_str = str(r.get(h, ""))
            if len(val_str) > col_widths[h]:
                col_widths[h] = len(val_str)

    # Build border lines
    sep_line = "+" + "+".join("-" * (col_widths[h] + 2) for h in headers) + "+"
    header_line = "|" + "|".join(f" {h.center(col_widths[h])} " for h in headers) + "|"
    
    lines = [sep_line, header_line, sep_line]
    for r in rows:
        row_str = "|" + "|".join(f" {str(r.get(h, '')).ljust(col_widths[h])} " for h in headers) + "|"
        lines.append(row_str)
    lines.append(sep_line)
    return "\n".join(lines)
