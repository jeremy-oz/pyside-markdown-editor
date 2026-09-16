# Copyright (C) 2026 Jeremy Chen
# SPDX-License-Identifier: BSD-3-Clause
from __future__ import annotations

"""User preferences: a small QSettings-backed model and its dialog."""

from dataclasses import dataclass

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import (QCheckBox, QDialog, QDialogButtonBox, QFormLayout,
                               QSpinBox, QVBoxLayout, QWidget)


@dataclass
class Preferences:
    """The options with a home in Edit > Preferences.

    ``show_source`` is the launch state of the Markdown source pane; the View
    menu toggle still flips it for the session. The image limits are applied
    to the preview as CSS ``max-width`` / ``max-height`` so images scale down
    to fit, never up. ``image_max_height`` of 0 means no height limit.
    """

    show_source: bool = False
    image_max_width: int = 100   # percent of the preview width
    image_max_height: int = 600  # pixels, 0 = unlimited

    @classmethod
    def load(cls) -> Preferences:
        s = QSettings()
        return cls(
            show_source=s.value("view/showSource", cls.show_source, type=bool),
            image_max_width=s.value("preview/imageMaxWidth", cls.image_max_width, type=int),
            image_max_height=s.value("preview/imageMaxHeight", cls.image_max_height, type=int),
        )

    def save(self) -> None:
        s = QSettings()
        s.setValue("view/showSource", self.show_source)
        s.setValue("preview/imageMaxWidth", self.image_max_width)
        s.setValue("preview/imageMaxHeight", self.image_max_height)

    def image_style_script(self) -> str:
        """JavaScript that pushes the image limits into the preview page."""
        width = f"{self.image_max_width}%"
        height = f"{self.image_max_height}px" if self.image_max_height > 0 else "none"
        return (f"document.documentElement.style.setProperty('--img-max-width', '{width}');"
                f"document.documentElement.style.setProperty('--img-max-height', '{height}');")


class PreferencesDialog(QDialog):

    def __init__(self, prefs: Preferences, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Preferences")

        self._show_source = QCheckBox("Show the Markdown source pane on launch")
        self._show_source.setChecked(prefs.show_source)

        self._image_width = QSpinBox()
        self._image_width.setRange(10, 100)
        self._image_width.setSuffix(" %")
        self._image_width.setValue(prefs.image_max_width)
        self._image_width.setToolTip("Images wider than this share of the preview are scaled down")

        self._image_height = QSpinBox()
        self._image_height.setRange(0, 10000)
        self._image_height.setSingleStep(50)
        self._image_height.setSuffix(" px")
        self._image_height.setSpecialValueText("No limit")
        self._image_height.setValue(prefs.image_max_height)
        self._image_height.setToolTip("Images taller than this are scaled down; 0 for no limit")

        form = QFormLayout()
        form.addRow(self._show_source)
        form.addRow("Maximum image width:", self._image_width)
        form.addRow("Maximum image height:", self._image_height)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                   | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def preferences(self) -> Preferences:
        return Preferences(
            show_source=self._show_source.isChecked(),
            image_max_width=self._image_width.value(),
            image_max_height=self._image_height.value(),
        )
