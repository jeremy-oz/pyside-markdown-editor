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
uv tool install git+ssh://git@git.kimichen.org:2222/neo/pyside-markdown-editor.git
markdown-editor
```

Upgrade later with `uv tool upgrade pyside-markdown-editor`. From a checkout, for development:

```bash
uv run markdown-editor          # or: uv run -m markdowneditor
```

The first run downloads PySide6 (Qt WebEngine is a large wheel, allow a few minutes).

## Layout

Source is the `markdowneditor` package under `src/`.

| File | Role |
|---|---|
| `__main__.py` | Entry point (`main()`): creates the `QApplication` and shows the window |
| `mainwindow.py` | Menu actions (New, Open, Save, Save As, Exit), dirty-state tracking, wires editor to preview |
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
