# Copyright (C) 2022 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause
from __future__ import annotations

"""PySide6 Markdown Editor Example"""

import argparse
import sys
from pathlib import Path

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication

from .mainwindow import MainWindow
from . import rc_markdowneditor  # noqa: F401

try:  # installed as a package
    from importlib.metadata import version as _version
    __version__ = _version("pyside-markdown-editor")
except Exception:  # running from a plain checkout
    __version__ = "0.0.0+unknown"


def _parse(arguments: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="markdown-editor",
        description="Edit Markdown with a live preview.")
    parser.add_argument(
        "path", nargs="?", metavar="PATH",
        help="a Markdown file to open, or a folder to browse in the file explorer")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser.parse_args(arguments)


def main() -> int:
    app = QApplication(sys.argv)
    QCoreApplication.setOrganizationName("QtExamples")
    QCoreApplication.setApplicationName("markdowneditor")

    # Qt has already taken its own options (-style, -platform, ...) out of
    # app.arguments(); parse what is left as ours.
    args = _parse(app.arguments()[1:])

    path = None
    if args.path:
        path = Path(args.path).expanduser()
        if not path.exists():
            print(f"markdown-editor: {args.path}: no such file or directory", file=sys.stderr)
            return 2
        path = path.resolve()

    window = MainWindow()
    window.show()
    if path:
        window.openPath(str(path))
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
