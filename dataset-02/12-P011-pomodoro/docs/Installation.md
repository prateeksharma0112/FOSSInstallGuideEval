## Installation

Requires Python 3.10+ on macOS.

```bash
git clone <this repo>
cd pomodoro
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

This installs the `pomodoro` console command (via the entry point defined
in `pyproject.toml`) into your active environment.

## Starting it

```bash
pomodoro
```

This opens the app window. Configure Focus/Break minutes, round count,
and the optional long break in the "Einstellungen" panel, then hit
**Start**. Switch to the **Statistik** tab any time to see your history.

## Building a double-clickable macOS app

If you'd rather launch Pomodoro from the Dock / Launchpad than from a
terminal, bundle it into a standalone `Pomodoro.app` with
[PyInstaller](https://pyinstaller.org/):

```bash
./packaging/build.sh
```

That script installs the build dependency (`pip install -e ".[package]"`),
renders the app icon, runs PyInstaller against
[`packaging/Pomodoro.spec`](packaging/Pomodoro.spec), and ad-hoc code-signs
the result (required to run on Apple Silicon). When it finishes:

```bash
cp -R dist/Pomodoro.app /Applications/
open /Applications/Pomodoro.app
```

The bundle is self-contained — it ships its own Python and Qt, so it runs
on any Mac (macOS 11+) without a Python install. Pass `--dmg` to also get
a `dist/Pomodoro.dmg` for copying it to another machine:

```bash
./packaging/build.sh --dmg
```

Because the app isn't signed with an Apple Developer ID, the first launch
on another Mac needs a right-click → **Open** (or *System Settings →
Privacy & Security → Open Anyway*) to get past Gatekeeper. On the machine
that built it, it just opens.

The phase-end sounds and all settings/history work exactly as in the
terminal version — see the two sections below.

## Adding your own sounds

The app plays an MP3 at the end of each Focus round and each Break. Drop
your own files into [`sounds/`](sounds/) using these exact names:

| File             | Played when...                 |
|-------------------|--------------------------------|
| `focus_end.mp3`  | a Focus round finishes          |
| `break_end.mp3`  | a short or long Break finishes  |

No MP3s are shipped in this repo (see [`sounds/README.md`](sounds/README.md)).
Without them the app doesn't crash — it just falls back to a terminal
beep and shows a small hint in the window. The lookup folder can be
overridden with the `POMODORO_SOUNDS_DIR` environment variable.

**In the packaged `Pomodoro.app`**, whatever `sounds/` files were present
at build time are bundled inside the app. To swap them afterwards without
rebuilding, drop `focus_end.mp3` / `break_end.mp3` into
`~/Library/Application Support/Pomodoro/sounds/` — that location is
checked first and wins over the bundled copies.

## Running Pomodoro in a container

The primary way to use Pomodoro is still the native macOS app above, but a
[`Dockerfile`](Dockerfile) is also provided to make it cloud-ready — the same
window, unmodified, made reachable from a plain browser tab:

```bash
docker build -t pomodoro .
docker run --rm -p 6080:6080 \
  -v pomodoro-data:/home/pomodoro/.local/share/Pomodoro \
  pomodoro
```

Then open <http://localhost:6080/vnc.html> — the actual Qt window is
rendered on a virtual display inside the container and streamed to the
browser via VNC/noVNC (see [`docker/entrypoint.sh`](docker/entrypoint.sh)).
There is no separate "web version"; it's the same app.

Two things behave differently than on macOS, both by design of what a
container is:

- **Sound and system notifications are silent.** `afplay`/`osascript` don't
  exist on Linux, and this image doesn't bridge PulseAudio/D-Bus out to the
  host — the app already degrades gracefully in that case (a terminal beep
  instead of the sound file, no notification), so nothing crashes, but you
  won't hear or see either.
- **Data only survives a restart if you mount a volume**, as in the command
  above — otherwise settings and history disappear with the container. The
  data directory can also be overridden explicitly with `POMODORO_DATA_DIR`.

## Configuration & data storage

Settings (last-used timer configuration, theme, project tag) and your
focus history are stored automatically under a per-OS user data directory
(`src/pomodoro/persistence/paths.py`) — `~/Library/Application Support/Pomodoro/`
on macOS, `~/.local/share/Pomodoro/` on Linux (including the container image,
respecting `$XDG_DATA_HOME` if set), or `%APPDATA%\Pomodoro\` on Windows.
Set `POMODORO_DATA_DIR` to use an explicit location instead:

```
settings.json   # last-used configuration (JSON)
pomodoro.db     # completed focus rounds (SQLite)
```

Every Focus round is appended to `pomodoro.db` with its timestamp,
duration, optional project tag, and whether it ran to completion —
that's the data the Statistics tab aggregates into "today / this week /
all-time" totals and the 7-day chart. Since 0.2.0, a Focus round you
cancel early is recorded too, with the time actually elapsed up to that
point, instead of being discarded; only Break phases are never recorded
at all. You can wipe this history from inside the app (Statistik tab →
"Historie zurücksetzen"), which asks for confirmation first since it
can't be undone.
