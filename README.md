# Rex Beta loses the SGR reset at the right margin, so the next row inherits the previous background

Rex Beta (macOS) does not apply the `ESC[0m` that follows a write which reaches the
last column. The background of that row survives, and the next row's erase-in-line
(`ESC[2K`) uses it — because erase-in-line is background-colour-erase (BCE) and
takes the current background. The result: every row below a styled block is painted
with that block's colour.

This is a terminal-level bug. Any fullscreen TUI that pads its lines to the pane
width and appends a reset hits it. Pi's renderer does exactly that, which is how we
found it: the whole panel turns green, intermittently, after a tool result.

## Reproduce

Any Rex Beta pane; captured at 163×47 with the dark theme.

```sh
python3 repro.py          # rows below the block turn green
python3 repro.py short    # control: one column short of the margin, clean
```

Expected in both modes: the block is green, and every row below it stays on the
default background.

Actual in `flood`: every row below the block, down to the last row of the pane, is
green.

| `python3 repro.py` | `python3 repro.py short` |
|---|---|
| ![flood](screens/flood.png) | ![control](screens/control.png) |

The two modes write the same bytes except for one column of padding.

## Why

Each block row is written as:

```
ESC[<row>;1H  ESC[2K  ESC[48;2;37;65;49m  <cols spaces>  ESC[0m
```

- With `pad = cols`, the reset arrives when the cursor is parked at the right margin
  with autowrap disabled (`ESC[?7l`). Rex does not apply it, so the background stays
  green.
- The next row's `ESC[2K` erases with the current background, painting that row green,
  and so on for the rest of the frame.
- With `pad = cols - 1`, the reset arrives before the margin and is applied; the frame
  stays clean.

## Real-world case

`pi-tui`, the renderer behind Pi, pads every rendered line to the pane width and
appends the reset, so the reset always lands exactly at the margin. `screens/pi.png`
is a real Pi frame in Rex: the transcript is green because it is full of tool blocks,
but the editor and status bar below it are green too — rows Pi never colours. The
frame is intermittent: it depends on whether the frame's earlier rows leave the
background unreset when the erase happens.

![Pi panel flooded green](screens/pi.png)

## What does not work

Emitting the reset before the erase does not help. Rex paints the erase with the
background of the previous row's *last cell*, not the current SGR state, so a reset
that arrives after the previous row is already painted changes nothing:

```
ESC[<row>;1H  ESC[0m  ESC[2K  <line>
```

Measured in the same Rex pane: the rows below a full-width green block still turn
green (78.4% of the editor band, the same as without the reset).

## Workaround

Keep the last column of a styled row on the default background. Pad the styled line
to `cols - 1`, then emit the reset: the row's last cell is default, and the next row's
erase inherits that. This is what `repro.py short` does, and it stays clean.

## Who to talk to

Rex is built by [Superlogical](https://www.superlogical.com/): Mitchell Hashimoto
(creator of Ghostty, co-founder of HashiCorp), Jack Pearkes, Alasdair Monk and Hector
Simpson. Rex is in public beta and free; the docs are at
<https://www.superlogical.com/rex/docs/>.

## Environment

- Rex Beta (`com.superlogical.rex`) on macOS 27, dark theme, 163×47 pane.
- Reproducer is pure `python3` + ANSI: no Pi, no plugin, no Rex internals.
