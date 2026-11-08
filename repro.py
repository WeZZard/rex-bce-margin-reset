#!/usr/bin/env python3
"""Rex Beta loses the SGR reset that follows a write reaching the right margin.

Run inside a Rex terminal:

    python3 repro.py          # rows below the block turn green
    python3 repro.py short    # control: one column short of the margin, clean

Expected in both modes: the block is green and every row below it stays on the
default background. In `flood`, every row below the block, down to the last
row, is painted with the block's background.

The program draws a full frame the way a fullscreen TUI does: park on a row,
erase it with ESC[2K, write the row, then erase and write the next one. Only
the padding width differs between the two modes.
"""

import os
import sys
import time

GREEN = "\x1b[48;2;37;65;49m"  # any background works; this one is Pi's toolSuccessBg
RESET = "\x1b[0m"

mode = sys.argv[1] if len(sys.argv) > 1 else "flood"
if mode not in ("flood", "short"):
    sys.exit(f"unknown mode {mode!r}; use 'flood' or 'short'")

cols, rows = os.get_terminal_size()
# flood: the reset lands exactly on the right margin.
# short: the reset lands one column before it.
pad = cols if mode == "flood" else cols - 1
block_rows = max(1, rows - 6)

out = sys.stdout
out.write("\x1b[?1049h\x1b[?7l\x1b[2J")  # alternate screen, no autowrap, clear

for _ in range(20):
    for row in range(1, block_rows + 1):
        out.write(f"\x1b[{row};1H\x1b[2K{GREEN}{' ' * pad}{RESET}")
    for row in range(block_rows + 1, rows + 1):
        out.write(f"\x1b[{row};1H\x1b[2K")
        out.write("this row should stay on the default background" + RESET)
    out.flush()
    time.sleep(0.05)

out.write("\x1b[1;1H")
out.flush()
time.sleep(20)            # hold the frame so it can be looked at
out.write("\x1b[?1049l")  # restore the pane
out.flush()
