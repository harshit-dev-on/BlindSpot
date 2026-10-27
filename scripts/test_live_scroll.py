"""Live headed browser test script - demonstrates smooth real-time scrolling in front of the user with zero AI tokens."""

import sys
from blindspot.runtime.scroll_test import run_live_scroll_test

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "https://www.amazon.com"
    run_live_scroll_test(target)
