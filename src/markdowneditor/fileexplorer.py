# Copyright (C) 2026 Jeremy Chen
# SPDX-License-Identifier: BSD-3-Clause
from __future__ import annotations

"""A dockable file tree for opening Markdown files without the dialog."""

from PySide6.QtCore import QDir, QModelIndex, Signal, Slot
from PySide6.QtWidgets import QDockWidget, QFileSystemModel, QTreeView, QWidget

MARKDOWN_FILTERS = ["*.md", "*.markdown"]


class FileExplorer(QDockWidget):
    """Folders and Markdown files under a root folder.

    Activating a file (double-click, or Enter on the current item) emits
    ``fileActivated`` with its path; single-click selection does nothing, so
    browsing never disturbs the open document.
    """

    fileActivated = Signal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__("Files", parent)
        self.setObjectName("fileExplorer")

        self._model = QFileSystemModel(self)
        self._model.setNameFilters(MARKDOWN_FILTERS)
        self._model.setNameFilterDisables(False)  # hide, don't grey out
        self._model.setFilter(QDir.Filter.AllDirs | QDir.Filter.Files
                              | QDir.Filter.NoDotAndDotDot)

        self._tree = QTreeView(self)
        self._tree.setModel(self._model)
        self._tree.setHeaderHidden(True)
        for column in range(1, self._model.columnCount()):
            self._tree.hideColumn(column)  # name only: no size, type, date
        self._tree.setSortingEnabled(True)
        self._tree.sortByColumn(0, self._tree.header().sortIndicatorOrder())
        self._tree.activated.connect(self._onActivated)
        self.setWidget(self._tree)

        self._root = ""
        self.setRoot(QDir.homePath())

    def root(self) -> str:
        return self._root

    def contains(self, path: str) -> bool:
        """True if ``path`` is inside the current root folder."""
        rel = QDir(self._root).relativeFilePath(path)
        return not rel.startswith("..") and not QDir.isAbsolutePath(rel)

    def setRoot(self, folder: str) -> None:
        self._root = QDir(folder).absolutePath()
        self._tree.setRootIndex(self._model.setRootPath(self._root))

    def select(self, path: str) -> None:
        """Highlight ``path`` in the tree (and expand down to it)."""
        index = self._model.index(path)
        if index.isValid():
            self._tree.setCurrentIndex(index)
            self._tree.scrollTo(index)

    @Slot(QModelIndex)
    def _onActivated(self, index: QModelIndex) -> None:
        if self._model.isDir(index):
            self._tree.setExpanded(index, not self._tree.isExpanded(index))
            return
        self.fileActivated.emit(self._model.filePath(index))
