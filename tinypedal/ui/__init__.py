#  TinyPedal is an open-source overlay application for racing simulation.
#  Copyright (C) 2022-2026 TinyPedal developers, see contributors.md file
#
#  This file is part of TinyPedal.
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Application UI, style
"""

from PySide2.QtGui import QGuiApplication, QPalette
from PySide2.QtWidgets import QApplication


def set_style_palette(color_theme: str):
    """Set style palette"""
    if color_theme == "Dark":
        palette_theme = palette_dark()
    else:
        palette_theme = palette_light()

    palette = QGuiApplication.palette()
    group_active = QPalette.Active
    group_inactive = QPalette.Inactive
    group_disabled = QPalette.Disabled
    for color_active, color_inactive, color_disabled, color_role in palette_theme:
        palette.setColor(group_active, color_role, color_active)
        palette.setColor(group_inactive, color_role, color_inactive)
        palette.setColor(group_disabled, color_role, color_disabled)
    QApplication.setPalette(palette)


def palette_light():
    """Set palette light"""
    return (
        #   Active   Inactive   Disabled  Role
        ("#F0F0F0", "#F0F0F0", "#E8E8E8", QPalette.Window),
        ("#050505", "#050505", "#808080", QPalette.WindowText),
        ("#FFFFFF", "#FFFFFF", "#EEEEEE", QPalette.Base),
        ("#EBEBEB", "#EBEBEB", "#DBDBDB", QPalette.AlternateBase),
        ("#FFFFFF", "#FFFFFF", "#FFFFFF", QPalette.ToolTipBase),
        ("#050505", "#050505", "#050505", QPalette.ToolTipText),
        ("#050505", "#050505", "#050505", QPalette.PlaceholderText),
        ("#050505", "#050505", "#808080", QPalette.Text),
        ("#F0F0F0", "#F0F0F0", "#F0F0F0", QPalette.Button),
        ("#050505", "#050505", "#808080", QPalette.ButtonText),
        ("#FFFFFF", "#FFFFFF", "#FFFFFF", QPalette.BrightText),
        ("#FFFFFF", "#FFFFFF", "#FFFFFF", QPalette.Light),
        ("#E3E3E3", "#E3E3E3", "#F7F7F7", QPalette.Midlight),
        ("#A0A0A0", "#A0A0A0", "#A0A0A0", QPalette.Dark),
        ("#CCCCCC", "#CCCCCC", "#CCCCCC", QPalette.Mid),
        ("#111111", "#111111", "#050505", QPalette.Shadow),
        ("#0088DD", "#555555", "#CCCCCC", QPalette.Highlight),
        ("#FFFFFF", "#F0F0F0", "#555555", QPalette.HighlightedText),
        ("#0088DD", "#0088DD", "#808080", QPalette.Link),
        ("#FF00FF", "#FF00FF", "#808080", QPalette.LinkVisited),
    )


def palette_dark():
    """Set palette dark"""
    return (
        #   Active   Inactive   Disabled  Role
        ("#333333", "#333333", "#2A2A2A", QPalette.Window),
        ("#FAFAFA", "#FAFAFA", "#808080", QPalette.WindowText),
        ("#222222", "#222222", "#333333", QPalette.Base),
        ("#2A2A2A", "#2A2A2A", "#3A3A3A", QPalette.AlternateBase),
        ("#333333", "#333333", "#333333", QPalette.ToolTipBase),
        ("#FAFAFA", "#FAFAFA", "#FAFAFA", QPalette.ToolTipText),
        ("#FAFAFA", "#FAFAFA", "#FAFAFA", QPalette.PlaceholderText),
        ("#FAFAFA", "#FAFAFA", "#808080", QPalette.Text),
        ("#333333", "#333333", "#303030", QPalette.Button),
        ("#FAFAFA", "#FAFAFA", "#888888", QPalette.ButtonText),
        ("#FFFFFF", "#FFFFFF", "#FFFFFF", QPalette.BrightText),
        ("#AAAAAA", "#AAAAAA", "#484848", QPalette.Light),
        ("#999999", "#999999", "#383838", QPalette.Midlight),
        ("#555555", "#555555", "#181818", QPalette.Dark),
        ("#444444", "#444444", "#222222", QPalette.Mid),
        ("#222222", "#222222", "#0E0E0E", QPalette.Shadow),
        ("#0088DD", "#CCCCCC", "#444444", QPalette.Highlight),
        ("#FAFAFA", "#181818", "#999999", QPalette.HighlightedText),
        ("#22AAFF", "#22AAFF", "#808080", QPalette.Link),
        ("#FF22FF", "#FF22FF", "#808080", QPalette.LinkVisited),
    )


def set_style_window(base_font_pt: int) -> str:
    """Set style window (not affecting overlay)"""
    # Scale font (point size)
    font_pt_item_name = 1.2 * base_font_pt
    font_pt_item_button = 1.05 * base_font_pt
    font_pt_item_toggle = 1.0 * base_font_pt
    font_pt_text_browser = 0.9 * base_font_pt
    font_pt_app_name = 1.4 * base_font_pt

    # Size
    border_radius_button = 0.1  # em

    # Color
    palette = QApplication.palette()
    palette.setCurrentColorGroup(QPalette.Active)
    color_active_window_text = palette.windowText().color().name()
    color_active_window = palette.window().color().name()
    color_active_base = palette.base().color().name()
    color_active_highlighted_text = palette.highlightedText().color().name()
    color_active_highlight = palette.highlight().color().name()

    palette.setCurrentColorGroup(QPalette.Inactive)
    color_inactive_highlighted_text = palette.highlightedText().color().name()
    color_inactive_highlight = palette.highlight().color().name()

    palette.setCurrentColorGroup(QPalette.Disabled)
    color_disabled_window_text = palette.windowText().color().name()
    color_disabled_highlighted_text = palette.highlightedText().color().name()
    color_disabled_highlight = palette.highlight().color().name()

    style = f"""
        /* Misc */
        QSizeGrip {{
            image: none;
            width: 4px;
        }}
        QToolTip {{
            color: {color_active_window_text};
            background: {color_active_window};
            border: 1px solid {color_disabled_window_text};
        }}

        /* Main status bar */
        AppWindow QStatusBar > QPushButton {{
            font-size: {font_pt_text_browser}pt;
            border: none;
            padding: 0.1em 0.2em;
        }}
        AppWindow QStatusBar > QPushButton::hover {{
            color: {color_active_highlighted_text};
            background: {color_active_highlight};
        }}
        AppWindow QStatusBar > QPushButton::menu-indicator {{
            image: none;
            width: 0;
        }}

        /* Notify bar */
        NotifyBar QPushButton {{
            font-weight: bold;
            padding: 0.2em;
            border: none;
            color: {color_active_highlighted_text};
        }}
        NotifyBar QPushButton::menu-indicator {{
            image: none;
            width: 0;
        }}
        NotifyBar UpdatesNotifyButton {{
            background: #638;
        }}

        /* Module list (tab) */
        ModuleList QListView {{
            font-size: {font_pt_item_name}pt;
            outline: none;
        }}
        ModuleList QListView::item {{
            border: none;
            min-height: 1.75em;
            color: {color_active_window_text};
        }}
        ModuleList QListView::item:selected {{
            background: transparent;
        }}
        ModuleList QListView::item:hover {{
            background: {color_disabled_highlight};
        }}
        ModuleControlItem QPushButton {{
            border-radius: {border_radius_button}em;
            height: none;
            margin: 0.25em 0.25em 0.25em 0;
        }}
        ModuleControlItem #buttonConfig {{
            font-size: {font_pt_item_button}pt;
            color: {color_disabled_window_text};
            padding: 0 0.2em;
        }}
        ModuleControlItem #buttonToggle {{
            font-size: {font_pt_item_toggle}pt;
            font-weight: bold;
            color: {color_disabled_highlighted_text};
            background: {color_disabled_highlight};
            min-width: 2em;
        }}
        ModuleControlItem #buttonToggle::checked,
        ModuleControlItem #buttonConfig::checked {{
            color: {color_inactive_highlighted_text};
            background: {color_inactive_highlight};
        }}
        ModuleControlItem #buttonToggle::hover,
        ModuleControlItem #buttonConfig::hover,
        ModuleControlItem #buttonToggle::checked:hover,
        ModuleControlItem #buttonConfig::checked:hover {{
            color: {color_active_highlighted_text};
            background: {color_active_highlight};
        }}

        /* Preset list (tab) */
        PresetList QListView {{
            font-size: {font_pt_item_name}pt;
            outline: none;
        }}
        PresetList QListView::item {{
            border: none;
            min-height: 1.75em;
        }}
        PresetList QListView::item:selected {{
            selection-color: {color_active_highlighted_text};
            background: {color_active_highlight};
        }}
        PresetTagItem QLabel {{
            font-size: {font_pt_item_button}pt;
            color: {color_active_highlighted_text};
            margin: 0.25em 0.25em 0.25em 0;
            border-radius: {border_radius_button}em;
        }}

        /* Preset transfer (dialog) */
        PresetTransfer QListView {{
            outline: none;
            background: {color_active_window};
        }}
        PresetTransfer QListView::item {{
            border: none;
            min-height: 1.75em;
        }}
        PresetTransfer QListView::item:selected {{
            selection-color: {color_active_highlighted_text};
            background: {color_disabled_highlight};
        }}
        PresetTransfer QListView QCheckBox {{
            font-size: {font_pt_item_name}pt;
            margin: 0.25em 0.25em 0.25em 0.25em;
            border-radius: {border_radius_button}em;
        }}
        PresetTransfer ListHeader {{
            background: {color_active_base};
        }}
        PresetTransfer ListHeader QLabel {{
            font-size: {font_pt_item_name}pt;
            color: {color_disabled_highlighted_text};
            padding: 0 0.1em;
        }}
        PresetTransfer ListHeader CompactButton {{
            border: none;
            font-size: {font_pt_item_button}pt;
            padding: 0.2em;
        }}
        PresetTransfer ListHeader CompactButton::checked {{
            color: {color_inactive_highlighted_text};
            background: {color_inactive_highlight};
        }}
        PresetTransfer ListHeader CompactButton::hover,
        PresetTransfer ListHeader CompactButton::checked:hover {{
            color: {color_active_highlighted_text};
            background: {color_active_highlight};
        }}

        /* Spectate list (tab) */
        SpectateList QListView {{
            font-size: {font_pt_item_button}pt;
            outline: none;
        }}
        SpectateList QListView::item {{
            min-height: 1.75em;
            border: none;
        }}
        SpectateList QListView::item:selected {{
            selection-color: {color_active_highlighted_text};
            background: {color_active_highlight};
        }}

        /* Hotkey list (tab) */
        HotkeyList QListView {{
            font-size: {font_pt_item_name}pt;
            outline: none;
        }}
        HotkeyList QListView QLabel {{
            font-size: {font_pt_item_name}pt;
            font-weight: bold;
            color: {color_inactive_highlighted_text};
            background: {color_inactive_highlight};
        }}
        HotkeyList QListView QLabel:disabled {{
            color: {color_disabled_window_text};
            background: {color_disabled_highlight};
        }}
        HotkeyList QListView::item {{
            border: none;
            min-height: 1.75em;
            color: {color_active_window_text};
        }}
        HotkeyList QListView::item:selected {{
            background: transparent;
        }}
        HotkeyList QListView::item:hover {{
            background: {color_disabled_highlight};
        }}
        HotkeyList QListView::item:disabled {{
            color: {color_disabled_window_text};
        }}
        HotkeyConfigItem QPushButton {{
            font-size: {font_pt_item_toggle}pt;
            font-weight: bold;
            border-radius: {border_radius_button}em;
            height: none;
            margin: 0.25em 0.25em 0.25em 0;
            padding: 0 0.2em;
            color: {color_disabled_highlighted_text};
            background: {color_disabled_highlight};
        }}
        HotkeyConfigItem QPushButton::checked {{
            color: {color_inactive_highlighted_text};
            background: {color_inactive_highlight};
        }}
        HotkeyConfigItem QPushButton::hover,
        HotkeyConfigItem QPushButton::checked:hover {{
            color: {color_active_highlighted_text};
            background: {color_active_highlight};
        }}
        HotkeyConfigItem QPushButton::disabled {{
            color: {color_disabled_highlighted_text};
            background: {color_disabled_highlight};
        }}

        /* Base dialog */
        BaseDialog QStatusBar {{
            font-weight:bold;
        }}
        BaseDialog QTextBrowser {{
            font-size: {font_pt_text_browser}pt;
        }}
        BaseEditor QTableWidget DoubleClickEdit {{
            border: none;
        }}
        FuelCalculator QLineEdit[readOnly="true"]{{
            background: {color_active_window};
        }}
        FuelCalculator QLabel {{
            font-size: {font_pt_text_browser}pt;
        }}
        FuelCalculator PitStopPreview {{
            font-size: {font_pt_text_browser}pt;
            font-weight:bold;
        }}
        FuelCalculator PitStopPreview QLabel {{
            color: {color_inactive_highlighted_text};
            background: {color_inactive_highlight};
            font-weight:bold;
        }}
        About QLabel {{
            font-size: {font_pt_text_browser}pt;
        }}
        About QTextBrowser {{
            border: none;
        }}
        About #labelAppName {{
            font-size: {font_pt_app_name}pt;
        }}
    """
    return style
