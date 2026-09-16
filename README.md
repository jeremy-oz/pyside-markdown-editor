# pyside-markdown-editor

A small desktop Markdown editor with a live HTML preview. The left pane is a plain
text editor; the right pane is a Qt WebEngine view that re-renders the Markdown on
every keystroke through a `QWebChannel` bridge to [marked.js](https://github.com/markedjs/marked).

It starts life as the Qt for Python **WebEngine Markdown Editor** example, taken
verbatim (16 Sep 2026) from
<https://doc.qt.io/qtforpython-6/examples/example_webenginewidgets_markdowneditor.html>.
The upstream source lives in the `pyside-setup` monorepo at
`examples/webenginewidgets/markdowneditor`; this repo exists so it can grow on its own.

## Install

Python-only, managed with [uv](https://docs.astral.sh/uv/). As a tool on your PATH:

```bash
uv tool install git+https://github.com/jeremy-oz/pyside-markdown-editor.git
markdown-editor
```

Upgrade later with `uv tool upgrade pyside-markdown-editor`. From a checkout, for development:

```bash
uv run markdown-editor          # or: uv run -m markdowneditor
```

The first run downloads PySide6 (Qt WebEngine is a large wheel, allow a few minutes).

## Using it

Give it a path to start where you work:

```bash
markdown-editor ~/work/projects/oz-trip   # browse a folder of notes
markdown-editor notes/trip.md             # open one file
markdown-editor                           # the example document
```

A folder roots the file explorer there and shows the pane; a file is opened, with the
explorer rooted at its folder. A path that does not exist is an error, and `--help` and
`--version` behave as usual. Qt's own options (`-style`, `-platform`) still work.

The window opens showing the rendered preview only. The Markdown source pane is hidden
until you ask for it, so reading is the default and editing is one keystroke away.

| Action | Where |
|---|---|
| Show or hide the Markdown source | View › Show Markdown source, `Ctrl+E` (`⌘E`), the **Source** button in the status bar, or right-click the preview |
| Show or hide the file explorer | View › Show file explorer, `Ctrl+Shift+E`, or right-click the preview |
| Open a file from the explorer | Double-click it (or press Enter); the tree shows folders and `*.md` / `*.markdown` files, rooted at the open document's folder |
| Preferences | Edit › Preferences (`Ctrl+,`; on macOS under the app menu) |

Preferences hold the launch state of the source pane and the maximum size images are
shown at in the preview (a share of the pane width and a height in pixels; images scale
down to fit, never up). Window layout, explorer visibility and the splitter position are
remembered between runs in `QSettings` (`QtExamples` / `markdowneditor`).

## Layout

Source is the `markdowneditor` package under `src/`.

| File | Role |
|---|---|
| `__main__.py` | Entry point (`main()`): creates the `QApplication` and shows the window |
| `mainwindow.py` | Menu actions, dirty-state tracking, source-pane toggle, wires editor, explorer and preview together |
| `fileexplorer.py` | `FileExplorer` dock: a `QTreeView` over `QFileSystemModel`, filtered to Markdown files |
| `preferences.py` | `Preferences` (QSettings-backed values) and the `PreferencesDialog` |
| `document.py` | `Document` QObject exposed to JavaScript over `QWebChannel`; emits `textChanged` |
| `previewpage.py` | `QWebEnginePage` subclass that opens external links in the system browser |
| `mainwindow.ui` / `ui_mainwindow.py` | Qt Designer form and its generated Python |
| `resources/` | `index.html` preview page, `default.md`, and the `.qrc` resource file |
| `resources/3rdparty/` | `marked.js` 0.4.0 (MIT) and `markdown.css` (Apache-2.0) |
| `rc_markdowneditor.py` | Generated resource module. Regenerate after editing `resources/` |

## Regenerating generated files

```bash
cd src/markdowneditor
uv run pyside6-uic mainwindow.ui -o ui_mainwindow.py
uv run pyside6-rcc resources/markdowneditor.qrc -o rc_markdowneditor.py
```

## Licence

BSD-3-Clause, see `LICENSE`. Original code copyright The Qt Company Ltd. Third-party
web assets keep their own licences under `resources/3rdparty/`.
