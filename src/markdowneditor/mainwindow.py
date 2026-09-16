# Copyright (C) 2022 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause
from __future__ import annotations


from PySide6.QtCore import QDir, QFile, QFileInfo, QIODevice, QSettings, QUrl, Qt, Slot
from PySide6.QtGui import QFontDatabase, QKeySequence
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (QDialog, QFileDialog, QMainWindow, QMessageBox,
                               QToolButton)

from .ui_mainwindow import Ui_MainWindow
from .document import Document
from .fileexplorer import FileExplorer
from .preferences import Preferences, PreferencesDialog
from .previewpage import PreviewPage


class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.m_file_path = ''
        self.m_content = Document()
        self._prefs = Preferences.load()
        self._ui = Ui_MainWindow()
        self._ui.setupUi(self)
        font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        self._ui.editor.setFont(font)
        self._page = PreviewPage(self)
        self._ui.preview.setPage(self._page)
        self._page.loadFinished.connect(self._applyPreviewStyle)
        QGuiApplication.styleHints().colorSchemeChanged.connect(self._applyColorScheme)

        self._ui.editor.textChanged.connect(self.plainTextEditChanged)

        self._channel = QWebChannel(self)
        self._channel.registerObject("content", self.m_content)
        self._page.setWebChannel(self._channel)

        self._loadPreview()

        self._ui.actionNew.triggered.connect(self.onFileNew)
        self._ui.actionOpen.triggered.connect(self.onFileOpen)
        self._ui.actionSave.triggered.connect(self.onFileSave)
        self._ui.actionSaveAs.triggered.connect(self.onFileSaveAs)
        self._ui.actionExit.triggered.connect(self.close)

        self._ui.editor.document().modificationChanged.connect(self._ui.actionSave.setEnabled)

        self._setupEditMenu()
        self._setupExplorer()
        self._setupSourceToggle()

        defaultTextFile = QFile(":/default.md")
        defaultTextFile.open(QIODevice.OpenModeFlag.ReadOnly)
        data = defaultTextFile.readAll()
        self._ui.editor.setPlainText(data.data().decode('utf8'))

        settings = QSettings()
        self.restoreGeometry(settings.value("window/geometry", b""))
        self.restoreState(settings.value("window/state", b""))
        self._ui.splitter.restoreState(settings.value("window/splitter", b""))

    # -- setup -------------------------------------------------------------

    def _setupEditMenu(self):
        """Edit actions act on whichever pane has focus: the source editor,
        or the preview through its web actions."""
        ui = self._ui
        editor = ui.editor
        WebAction = QWebEnginePage.WebAction
        for action, key, editor_slot, web_action in (
                (ui.actionUndo, QKeySequence.StandardKey.Undo, editor.undo, WebAction.Undo),
                (ui.actionRedo, QKeySequence.StandardKey.Redo, editor.redo, WebAction.Redo),
                (ui.actionCut, QKeySequence.StandardKey.Cut, editor.cut, WebAction.Cut),
                (ui.actionCopy, QKeySequence.StandardKey.Copy, editor.copy, WebAction.Copy),
                (ui.actionPaste, QKeySequence.StandardKey.Paste, editor.paste, WebAction.Paste),
                (ui.actionSelectAll, QKeySequence.StandardKey.SelectAll, editor.selectAll,
                 WebAction.SelectAll)):
            action.setShortcut(key)
            action.triggered.connect(
                lambda checked=False, s=editor_slot, w=web_action: self._editAction(s, w))
        editor.undoAvailable.connect(ui.actionUndo.setEnabled)
        editor.redoAvailable.connect(ui.actionRedo.setEnabled)
        editor.copyAvailable.connect(ui.actionCut.setEnabled)
        editor.copyAvailable.connect(ui.actionCopy.setEnabled)
        for action in (ui.actionUndo, ui.actionRedo, ui.actionCut, ui.actionCopy):
            action.setEnabled(False)

        ui.actionPreferences.setShortcut(QKeySequence.StandardKey.Preferences)
        ui.actionPreferences.triggered.connect(self.onPreferences)

    def _editAction(self, editor_slot, web_action):
        preview = self._ui.preview
        focus = self.focusWidget()
        if focus is not None and (focus is preview or preview.isAncestorOf(focus)):
            self._page.triggerAction(web_action)
        else:
            editor_slot()

    def _setupExplorer(self):
        self._explorer = FileExplorer(self)
        self._explorer.setSortOrder(self._prefs.explorer_sort)
        self._explorer.fileActivated.connect(self.onExplorerFileActivated)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self._explorer)
        action = self._explorer.toggleViewAction()
        action.setText("Show &file explorer")
        action.setToolTip("Show or hide the file explorer pane")
        action.setShortcut("Ctrl+Shift+E")
        self._ui.actionShowExplorer = action
        self._ui.menu_View.insertAction(self._ui.actionShowSource, action)

    def _setupSourceToggle(self):
        ui = self._ui
        ui.actionShowSource.toggled.connect(ui.editor.setVisible)
        ui.actionShowSource.setChecked(self._prefs.show_source)
        ui.editor.setVisible(self._prefs.show_source)

        # The same toggles from a right-click on the preview...
        ui.preview.addAction(ui.actionShowSource)
        ui.preview.addAction(ui.actionShowExplorer)
        ui.preview.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)

        # ...and a button in the status bar.
        button = QToolButton(self)
        button.setDefaultAction(ui.actionShowSource)
        button.setText("Source")
        button.setAutoRaise(True)
        self.statusBar().addPermanentWidget(button)

    # -- preview -----------------------------------------------------------

    def _loadPreview(self):
        """(Re)load the preview page so relative links resolve against the
        open document's folder. With no file yet, keep the qrc: origin."""
        if self.m_file_path:
            folder = QFileInfo(self.m_file_path).absolutePath()
            base = QUrl.fromLocalFile(folder + "/")
            page = QFile(":/index.html")
            page.open(QIODevice.OpenModeFlag.ReadOnly)
            html = page.readAll().data().decode('utf8')
            self._page.setBaseUrl(base)
            self._page.setHtml(html, base)
        else:
            self._page.setBaseUrl(None)
            self._ui.preview.setUrl(QUrl("qrc:/index.html"))

    @Slot()
    def _applyPreviewStyle(self):
        self._page.runJavaScript(self._prefs.preview_style_script())
        self._applyColorScheme()

    @Slot()
    def _applyColorScheme(self):
        """Pick the light or dark stylesheet. Qt WebEngine does not pass the
        desktop colour scheme through to prefers-color-scheme, so the page is
        told which variant to enable."""
        dark = QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark
        self._page.runJavaScript(
            f"window.setColorScheme && window.setColorScheme({str(dark).lower()});")

    @Slot()
    def plainTextEditChanged(self):
        self.m_content.setText(self._ui.editor.toPlainText())

    # -- files -------------------------------------------------------------

    def _confirmDiscard(self, what):
        """Ask before throwing away unsaved changes; True means go ahead."""
        if not self.isModified():
            return True
        m = f"You have unsaved changes. Do you want to {what} anyway?"
        button = QMessageBox.question(self, self.windowTitle(), m)
        return button == QMessageBox.StandardButton.Yes

    @Slot(str)
    def openPath(self, path):
        """Open a path given on the command line: a file is loaded, a folder
        is browsed in the explorer."""
        if QFileInfo(path).isDir():
            self._explorer.setRoot(path)
            self._explorer.show()
            self._ui.editor.setPlainText(
                f"## {QFileInfo(path).fileName()}\n\n"
                "Choose a file in the explorer on the left to open it.")
            self._ui.editor.document().setModified(False)
            self.statusBar().showMessage(f"Browsing {QDir.toNativeSeparators(path)}")
        else:
            self.openFile(path)

    @Slot(str)
    def openFile(self, path):
        f = QFile(path)
        name = QDir.toNativeSeparators(path)
        if not f.open(QIODevice.OpenModeFlag.ReadOnly):
            error = f.errorString()
            QMessageBox.warning(self, self.windowTitle(),
                                f"Could not open file {name}: {error}")
            return
        self.m_file_path = path
        self._loadPreview()
        data = f.readAll()
        self._ui.editor.setPlainText(data.data().decode('utf8'))
        self.statusBar().showMessage(f"Opened {name}")
        if not self._explorer.contains(path):
            self._explorer.setRoot(QFileInfo(path).absolutePath())
        self._explorer.select(path)

    def isModified(self):
        return self._ui.editor.document().isModified()

    @Slot()
    def onFileNew(self):
        if not self._confirmDiscard("create a new document"):
            return

        self.m_file_path = ''
        self._ui.editor.setPlainText("## New document")
        self._ui.editor.document().setModified(False)
        self._loadPreview()
        # A blank preview is no use; reveal the source to type into.
        self._ui.actionShowSource.setChecked(True)
        self._ui.editor.setFocus()

    @Slot()
    def onFileOpen(self):
        if not self._confirmDiscard("open a new document"):
            return
        dialog = QFileDialog(self)
        dialog.setWindowTitle("Open MarkDown File")
        dialog.setMimeTypeFilters(["text/markdown"])
        dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.openFile(dialog.selectedFiles()[0])

    @Slot(str)
    def onExplorerFileActivated(self, path):
        if path == self.m_file_path:
            return
        if not self._confirmDiscard("open another document"):
            return
        self.openFile(path)

    @Slot()
    def onFileSave(self):
        if not self.m_file_path:
            self.onFileSaveAs()
        if not self.m_file_path:
            return

        f = QFile(self.m_file_path)
        name = QDir.toNativeSeparators(self.m_file_path)
        if not f.open(QIODevice.OpenModeFlag.WriteOnly | QIODevice.OpenModeFlag.Text):
            error = f.errorString()
            QMessageBox.warning(self, self.windowTitle(),
                                f"Could not write to file {name}: {error}")
            return
        text = self._ui.editor.toPlainText()
        f.write(bytes(text, encoding='utf8'))
        f.close()
        self._ui.editor.document().setModified(False)
        self.statusBar().showMessage(f"Wrote {name}")

    @Slot()
    def onFileSaveAs(self):
        dialog = QFileDialog(self)
        dialog.setWindowTitle("Save MarkDown File")
        dialog.setMimeTypeFilters(["text/markdown"])
        dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        dialog.setDefaultSuffix("md")
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        path = dialog.selectedFiles()[0]
        self.m_file_path = path
        self.onFileSave()
        self._loadPreview()
        if not self._explorer.contains(path):
            self._explorer.setRoot(QFileInfo(path).absolutePath())
        self._explorer.select(path)

    # -- preferences -------------------------------------------------------

    @Slot()
    def onPreferences(self):
        dialog = PreferencesDialog(self._prefs, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        self._prefs = dialog.preferences()
        self._prefs.save()
        self._ui.actionShowSource.setChecked(self._prefs.show_source)
        self._explorer.setSortOrder(self._prefs.explorer_sort)
        self._applyPreviewStyle()

    def closeEvent(self, event):
        if not self._confirmDiscard("exit"):
            event.ignore()
            return
        settings = QSettings()
        settings.setValue("window/geometry", self.saveGeometry())
        settings.setValue("window/state", self.saveState())
        settings.setValue("window/splitter", self._ui.splitter.saveState())
        event.accept()
