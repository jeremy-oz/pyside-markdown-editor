## Images referenced by relative path do not show in the preview

A document such as

```markdown
![First Basin and the scenic chairlift](assets/2026-09-22-cataract-gorge-first-basin.jpg)
```

renders in the preview with a broken image, even though the file exists next to the `.md`.

### Cause

The preview page is loaded from `qrc:/index.html`, and nothing tells it where the open
document lives. Two things follow, both reproduced offscreen on PySide6 6.11.2 (macOS):

1. **Relative paths resolve against the resource file system.** `assets/photo.jpg` becomes
   `qrc:/assets/photo.jpg`, and Qt logs `QResource '/assets/photo.jpg' not found or is empty`.
2. **Absolute `file://` URLs are refused too.** Chromium logs
   `Not allowed to load local resource: file:///…/assets/photo.jpg`, because a page with a
   `qrc:` origin may not fetch `file:` URLs.

`MainWindow.openFile()` only pushes the text into the editor; `m_file_path` is never passed to
the page, and `PreviewPage` has no base URL.

### Reproduce

1. Make a folder with `doc.md` containing `![x](assets/photo.jpg)` and a real `assets/photo.jpg`.
2. `markdown-editor`, File › Open, pick `doc.md`.
3. The heading renders, the image is a broken placeholder. Same with an absolute `file://` URL.

### Proposed fix (untested)

Give the preview a `file:` origin rooted at the document's folder instead of `qrc:`:

- In `MainWindow`, whenever `m_file_path` changes (open, save-as), read `index.html` from the
  resource and call `self._page.setHtml(html, QUrl.fromLocalFile(os.path.dirname(path) + "/"))`.
  With a `file:` base, `assets/photo.jpg` resolves relative to the document and `file:` images
  are allowed (`LocalContentCanAccessFileUrls` is on by default).
- Keep the `<script src="qrc:/qtwebchannel/qwebchannel.js">` and 3rd-party assets working from
  a `file:` page by making their `src`/`href` absolute `qrc:/…` URLs in `index.html`.
- `PreviewPage.acceptNavigationRequest` must then also accept the `file:` scheme for the main
  frame, or the `setHtml` load is bounced to the system browser.
- An unsaved "New document" has no folder; fall back to the current `qrc:` behaviour, or to the
  user's home directory, until it is saved.

An alternative is a custom `QWebEngineUrlSchemeHandler` that serves the document's folder, which
avoids `file:` entirely but is more code.

### Environment

pyside-markdown-editor 0.1.0, PySide6 6.11.2, Python 3.13, macOS.
