# Copyright (C) 2022 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause
from __future__ import annotations

from PySide6.QtGui import QDesktopServices
from PySide6.QtWebEngineCore import QWebEnginePage


class PreviewPage(QWebEnginePage):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._base_url = None

    def setBaseUrl(self, url):
        """The file: URL of the open document's folder, or None for qrc:/."""
        self._base_url = url

    def acceptNavigationRequest(self, url, type, isMainFrame):
        # Allow qrc:/index.html, and the page we load ourselves with setHtml()
        # (which arrives as a typed data: navigation, never a link click).
        # Every other link (http, other local files) opens outside the preview.
        if url.scheme() == "qrc":
            return True
        if (isMainFrame and url.scheme() == "data"
                and type == QWebEnginePage.NavigationType.NavigationTypeTyped):
            return True
        QDesktopServices.openUrl(url)
        return False
