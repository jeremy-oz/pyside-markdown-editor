# Copyright (C) 2026 Jeremy Chen
# SPDX-License-Identifier: BSD-3-Clause
from __future__ import annotations

"""A dockable file tree for opening Markdown files without the dialog."""

from PySide6.QtCore import QDir, QModelIndex, Qt, Signal, Slot
from PySide6.QtWidgets import QDockWidget, QFileSystemModel, QTreeView, QWidget

MARKDOWN_FILTERS = ["*.md", "*.markdown"]

# How the tree can be sorted, as (setting value, label, model column, order).
# QFileSystemModel column 0 is the name and column 3 the modification time;
# both work while the column is hidden. Folders are ordered among the files,
# as Finder does by default; QFileSystemModel has no folders-first option and
# a sort proxy is not worth it here.
NAME_COLUMN = 0
MODIFIED_COLUMN = 3
SORT_ORDERS = (
    ("name-asc", "Name (A to Z)", NAME_COLUMN, Qt.SortOrder.AscendingOrder),
    ("name-desc", "Name (Z to A)", NAME_COLUMN, Qt.SortOrder.DescendingOrder),
    ("modified-asc", "Date modified (oldest first)", MODIFIED_COLUMN,
     Qt.SortOrder.AscendingOrder),
    ("modified-desc", "Date modified (newest first)", MODIFIED_COLUMN,
     Qt.SortOrder.DescendingOrder),
)
DEFAULT_SORT = SORT_ORDERS[0][0]


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
        self._tree.activated.connect(self._onActivated)
        self.setWidget(self._tree)

        self._root = ""
        self.setSortOrder(DEFAULT_SORT)
        self.setRoot(QDir.homePath())

    def setSortOrder(self, name: str) -> None:
        """Sort the tree by one of the SORT_ORDERS setting values."""
        for value, _label, column, order in SORT_ORDERS:
            if value == name:
                self._tree.sortByColumn(column, order)
                return
        self.setSortOrder(DEFAULT_SORT)

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
