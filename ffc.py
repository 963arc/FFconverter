# FFConverter - A simple, portable video, audio, and image converter for Linux.
# Copyright (C) 2026 369ARC
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#
# Note: FFmpeg binaries bundled with this application are licensed
# separately under LGPL. See the LICENSE file for full details.

# Modules
import os
import sys

# Suppress CustomTkinter config warnings during import and initialization
original_stderr = sys.stderr
sys.stderr = open(os.devnull, "w")

try:
    import customtkinter as ctk

    # Also suppress during CTk initialization
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

finally:
    sys.stderr = original_stderr

import concurrent.futures
import re
import shutil
import subprocess
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import List, Optional, Tuple

# Check for tkinterdnd2 availability for drag-and-drop support
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD

    TKINTERDND_AVAILABLE = True
except ImportError:
    TKINTERDND_AVAILABLE = False

try:
    from send2trash import send2trash

    SEND2TRASH_AVAILABLE = True
except ImportError:
    SEND2TRASH_AVAILABLE = False

# Check for pystray availability for system tray support
try:
    import pystray
    from PIL import Image

    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False
# CTkDnD
if TKINTERDND_AVAILABLE:

    class CTkDnD(ctk.CTk, TkinterDnD.DnDWrapper):
        """
        Custom class inheriting from CustomTkinter and TkinterDnD.
        This provides a CustomTkinter-compatible root window with drag-and-drop support.
        """

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # Initialize the drag-and-drop mechanism
            self.TkdndVersion = TkinterDnD._require(self)
else:
    # Fallback to standard CTk if tkinterdnd2 is not installed
    CTkDnD = ctk.CTk

# Config
# Note: Appearance settings are already set in the import suppression block above

# Paths
CURRENT_DIR = Path(__file__).parent.absolute()

def _get_ffmpeg_path():
    if os.name == "nt":
        FFMPEG_EXE = "ffmpeg.exe"
        FFMPEG_PATHS = [
            CURRENT_DIR / "resources" / "ffmpeg" / FFMPEG_EXE,
            CURRENT_DIR / FFMPEG_EXE,
        ]
        return next(
            (str(p) for p in FFMPEG_PATHS if isinstance(p, Path) and p.exists()),
            shutil.which("ffmpeg") or "ffmpeg.exe",
        )
    else:
        # Linux/macOS - Check AppImage paths first
        appimage_ffmpeg = None
        
        # Check if running as AppImage (look for runtime marker)
        if os.environ.get("APPIMAGE"):
            appdir = os.environ.get("APPDIR", os.path.dirname(os.environ["APPIMAGE"]))
            appimage_paths = [
                Path(appdir) / "usr" / "bin" / "ffmpeg",
                Path(appdir) / "ffmpeg",
            ]
            for p in appimage_paths:
                if p.exists():
                    appimage_ffmpeg = str(p)
                    break
        
        if appimage_ffmpeg:
            return appimage_ffmpeg
        
        # Fall back to system ffmpeg
        return shutil.which("ffmpeg") or "ffmpeg"

FFMPEG_PATH = _get_ffmpeg_path()

FOLDER_ICON_PATH = CURRENT_DIR / "resources" / "images" / "folder_icon.png"

# Formats
VIDEO_FORMATS = [
    "MP4",
    "MKV",
    "MOV",
    "AVI",
    "WEBM",
    "TS",
    "M2TS",
    "FLV",
    "SWF",
    "WMV",
    "MPG",
    "MPEG",
    "MXF",
    "VOB",
    "3GP",
    "3G2",
    "OGG",
    "OGV",
    "M4V",
    "NUT",
    "DV",
    "APNG",
    "ASF",
    "WTV",
    "GXF",
    "IVF",
    "H264",
    "H265",
    "HEVC",
]
AUDIO_FORMATS = [
    "MP3",
    "AAC",
    "FLAC",
    "WAV",
    "OGG",
    "OPUS",
    "M4A",
    "WMA",
    "AIFF",
    "AC3",
    "DTS",
    "EAC3",
    "ALAC",
    "AMR",
    "MP2",
    "WV",
    "AU",
    "TTA",
]
IMAGE_FORMATS = [
    "JPG",
    "JPEG",
    "PNG",
    "WEBP",
    "GIF",
    "TIFF",
    "TIF",
    "HEIC",
    "HEIF",
    "AVIF",
    "BMP",
    "ICO",
    "TGA",
    "PDF",
    "PSD",
    "EPS",
    "AI",
    "SVG",
    "DPX",
    "Y4M",
    "PPM",
    "PBM",
    "PGM",
    "PAM",
    "PFM",
    "PCX",
    "SGI",
    "XWD",
    "SUN",
    "QOI",
    "CR2",
    "NEF",
    "ARW",
    "DNG",
    "RAF",
    "ORF",
]

# Presets
AUDIO_SETTINGS = {
    "AAC": {
        "type": "bitrate",
        "options": ["320K", "256K", "192K", "128K", "96K", "64K"],
    },
    "OGG": {
        "type": "bitrate",
        "options": ["320K", "256K", "192K", "128K", "96K", "64K"],
    },
    "M4A": {
        "type": "bitrate",
        "options": ["320K", "256K", "192K", "128K", "96K", "64K"],
    },
    "WMA": {
        "type": "bitrate",
        "options": ["320K", "256K", "192K", "128K", "96K", "64K"],
    },
    "OPUS": {
        "type": "bitrate",
        "options": ["256K", "192K", "128K", "96K", "64K", "48K"],
    },
    "AC3": {
        "type": "bitrate",
        "options": ["640K", "448K", "384K", "256K", "192K", "128K"],
    },
    "DTS": {"type": "bitrate", "options": ["1536K", "768K", "512K"]},
    "EAC3": {"type": "bitrate", "options": ["768K", "640K", "448K", "384K", "256K"]},
    "AMR": {
        "type": "bitrate",
        "options": [
            "12.2K",
            "10.2K",
            "7.95K",
            "7.40K",
            "6.70K",
            "5.90K",
            "5.15K",
            "4.75K",
        ],
    },
    "MP2": {"type": "bitrate", "options": ["384K", "256K", "192K", "128K", "96K"]},
    "WAV": {
        "type": "samplerate",
        "options": [
            "192000 HZ",
            "96000 HZ",
            "48000 HZ",
            "44100 HZ",
            "32000 HZ",
            "22050 HZ",
            "16000 HZ",
        ],
    },
    "FLAC": {
        "type": "samplerate",
        "options": [
            "192000 HZ",
            "96000 HZ",
            "48000 HZ",
            "44100 HZ",
            "32000 HZ",
            "22050 HZ",
        ],
    },
    "AIFF": {
        "type": "samplerate",
        "options": [
            "192000 HZ",
            "96000 HZ",
            "48000 HZ",
            "44100 HZ",
            "32000 HZ",
            "22050 HZ",
        ],
    },
    "ALAC": {
        "type": "samplerate",
        "options": ["192000 HZ", "96000 HZ", "48000 HZ", "44100 HZ", "32000 HZ"],
    },
    "WV": {
        "type": "bitrate",
        "options": ["768K", "512K", "384K", "256K"],
    },
    "AU": {
        "type": "samplerate",
        "options": [
            "192000 HZ",
            "96000 HZ",
            "48000 HZ",
            "44100 HZ",
            "32000 HZ",
            "22050 HZ",
            "16000 HZ",
        ],
    },
    "TTA": {
        "type": "compression",
        "options": ["0 (FASTEST)", "1", "2", "3", "4 (BEST)"],
    },
}
MP3_CBR_OPTIONS = ["320K", "256K", "192K", "128K", "96K", "64K"]
MP3_VBR_OPTIONS = [
    "V0 (HIGHEST QUALITY)",
    "V1",
    "V2 (HIGH QUALITY)",
    "V3",
    "V4",
    "V5 (GOOD QUALITY)",
    "V6",
    "V7",
    "V8",
    "V9 (SMALLEST FILE)",
]

VIDEO_QUALITY_MODES = [
    "ORIGINAL (COPY)",
    "BITRATE (CBR/VBR AVG)",
    "CRF (CONSTANT QUALITY)",
]
CRF_OPTIONS = [
    "18 (HIGHEST QUALITY)",
    "20 (HIGH QUALITY)",
    "23 (GOOD - DEFAULT)",
    "25 (MEDIUM QUALITY)",
    "28 (LOW QUALITY)",
    "30 (LOWEST QUALITY)",
]

VIDEO_QUALITY_PRESETS = [
    "8K (50M)",
    "4K (20M)",
    "1440P (10M)",
    "1080P (5M)",
    "720P (2M)",
    "480P (1.5M)",
    "360P (1M)",
]

VIDEO_FRAME_RATE_PRESETS = [
    "ORIGINAL (COPY)",
    "60",
    "59.94",
    "50",
    "30",
    "29.97",
    "25",
    "24",
    "23.976",
    "15",
]

IMAGE_SIZE_PRESETS = [
    "ORIGINAL (COPY)",
    "7680X4320 (8K)",
    "2560X1440 (2K)",
    "1920X1080 (FULL HD)",
    "1280X720 (HD)",
    "854X480 (480P)",
    "640X360 (360P)",
    "CUSTOM (WXH)",
]

IMAGE_FILTERS = [
    "ORIGINAL (NO FILTER)",
    "GRAYSCALE (BLACK & WHITE)",
    "SHARPEN (BASIC)",
    "INVERT COLORS",
]

# Help
HELP_MESSAGES = {
    # Common - General
    "default": "Hover over any option to see what it does.",
    "browse_files": "Click Browse to select your input files.",
    "output_folder": "This folder will store your converted files.",
    "change_folder": "Click to choose a different output folder.",
    "open_folder": "Click to open the output folder.",
    "convert_btn": "Click to start converting your files to the selected format.",
    
    # Video Settings
    "video_format": "Choose the output video type (mp4, mkv, avi, etc).",
    "video_quality_mode": "Select quality mode: Original (fastest), Bitrate (fixed size), or CRF (fixed quality).",
    "video_quality_value": "Set target bitrate (like 5M) or CRF quality level (18=best, 23=default).",
    "video_framerate": "Set video speed (frames per second). Keep Original for fastest conversion.",
    "video_bitrate": "Target video quality using bitrate. Higher = better quality, bigger file.",
    "video_crf_value": "CRF sets quality. Lower number = better quality. Recommended: 18-23.",
    
    # Video Toggles
    "keep_aspect_ratio": "Keep original width-to-height proportions when resizing.",
    "apply_deinterlace": "Fix old video that looks wavy, blurry, or has lines.",
    "strip_metadata": "Remove hidden info like creation date, author, software name.",
    "remove_audio": "Remove sound track from video. Creates silent video.",
    "remove_video": "Keep only audio track. Creates audio-only WAV file.",
    
    # Audio Settings
    "audio_format": "Choose output audio type (mp3, wav, flac, aac, etc).",
    "mp3_mode": "CBR = same quality always. VBR = smaller file when audio is quiet.",
    "audio_quality": "Higher number = better quality, bigger file. Lower = smaller file.",
    "mp3_mode_cbr": "Constant Bitrate: Same quality throughout the file.",
    "mp3_mode_vbr": "Variable Bitrate: Quality adjusts to save space.",
    
    # Audio Toggles
    "apply_dithering": "Apply dither to reduce quantization noise in quiet sounds.",
    "apply_limiter": "Prevent audio from being too loud. Stops digital clipping.",
    
    # Image Settings
    "image_format": "Choose output image type (jpg, png, webp, etc).",
    "image_size": "Resize image. Choose preset or enter custom width x height.",
    "image_size_custom": "Enter your own width and height in pixels.",
    "visual_filter": "Apply visual effect: Original (none), Grayscale, Sharpen, or Invert Colors.",
    
    # Image Toggles
    "image_keep_aspect_ratio": "Keep original width-to-height proportions when resizing.",
    "image_compress": "Apply maximum compression to reduce file size.",
    "image_strip_metadata": "Remove hidden info like camera model, date taken.",
    
    # Theme
    "light_theme": "Switch interface to light colors (bright background).",
    "dark_theme": "Switch interface to dark colors (dark background).",
    "btn_light": "Click to switch to light mode.",
    "btn_dark": "Click to switch to dark mode.",
    "btn_audio": "Click to switch to Audio tab for audio conversion.",
    "btn_video": "Click to switch to Video tab for video conversion.",
    "btn_image": "Click to switch to Image tab for image conversion.",
}

# App
APP_CONFIG = {
    "WINDOW_SIZE": "1187x860",
    "FILE_DIALOG_SIZE": "850x638",
    "SIZE_DIALOG_SIZE": "400x300",
    "DEFAULT_OUTPUT_DIR": str(Path.home() / "Converted"),
    "THEME_COLORS": {
        "card_bg": ("#DBDBDB", "#2B2D30"),
        "text_primary": ("#666666", "#E0E0E0"),
        "text_secondary": ("#707070", "#A0A0A0"),
        "btn_inactive": ("#9E9E9E", "#3B4049"),
        "btn_hover": ("#666666", "#4F545C"),
        "btn_active_blue": ("#3B8ED0", "#1F6AA5"),
        "btn_hover_blue": ("#36719E", "#144870"),
        "btn_green": ("#2CC985", "#00A651"),
        "btn_green_hover": ("#25A86E", "#00803E"),
        "btn_cancel": ("#E05252", "#B33A3A"),
        "btn_cancel_hover": ("#C04040", "#8C2B2B"),
        "btn_open": ("#FF4D94", "#FF9500"),  # Light: Pink | Dark: Orange
        "btn_open_hover": ("#E63980", "#E68600"),  # Deeper shades for hover
        "input_bg": ("#F0F0F0", "#343638"),
        "transparent": "transparent",
        "white": "white",
        "green": "green",
    },
}


# FileDialog
class CustomFileDialog(ctk.CTkToplevel):
    def __init__(
        self, parent, title: str = "Select Files", filetypes=None, initialdir=None
    ):
        super().__init__(parent)
        self.title(title)
        self.geometry(APP_CONFIG["FILE_DIALOG_SIZE"])
        self.transient(parent)

        self.result: Optional[List[str]] = None
        self.filetypes = filetypes or [("All Files", "*.*")]

        # FIX: Ensure initial directory is valid, otherwise fallback to Home
        init_path = Path(initialdir) if initialdir else Path.home()
        self.current_dir = init_path if init_path.exists() else Path.home()

        self.selected_files: List[str] = []
        self.clipboard_files: List[str] = []

        self._create_widgets()
        self._populate_tree()
        self._populate_file_list()
        self._bind_events()

    def _create_widgets(self):
        # Main frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Top frame for path and buttons
        top_frame = ctk.CTkFrame(main_frame)
        top_frame.pack(fill="x", padx=5, pady=5)

        self.path_entry = ctk.CTkEntry(top_frame, placeholder_text="Current directory")
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        # FIX: Bind Enter key to handle manual path typing
        self.path_entry.bind("<Return>", self._on_manual_path_entry)

        refresh_btn = ctk.CTkButton(
            top_frame,
            text="Refresh",
            command=self._refresh_all,
            width=80,
            text_color="white",
        )
        refresh_btn.pack(side="right", padx=(5, 0))

        # Content frame with tree and file list
        content_frame = ctk.CTkFrame(main_frame)
        content_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Tree view for folder navigation
        tree_frame = ctk.CTkFrame(content_frame, width=250)
        tree_frame.pack(side="left", fill="y", padx=(0, 5), pady=0)
        tree_frame.pack_propagate(False)

        tree_label = ctk.CTkLabel(
            tree_frame, text="Folders", font=ctk.CTkFont(weight="bold")
        )
        tree_label.pack(pady=(5, 0))

        # Create treeview using tkinter's Treeview
        from tkinter import ttk

        self.tree = ttk.Treeview(tree_frame, height=20, show="tree")
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)

        # Configure tree colors to match application theme
        self._configure_tree_colors()

        # File list
        self.file_listbox = ctk.CTkScrollableFrame(content_frame)
        self.file_listbox.pack(
            side="right", fill="both", expand=True, padx=(5, 0), pady=0
        )

        # Status bar
        self.status_label = ctk.CTkLabel(
            main_frame, text="Ready to select files", anchor="w"
        )
        self.status_label.pack(fill="x", padx=5, pady=(0, 5))

        # Bottom buttons
        bottom_frame = ctk.CTkFrame(
            main_frame, fg_color=APP_CONFIG["THEME_COLORS"]["transparent"]
        )
        bottom_frame.pack(fill="x", padx=5, pady=5)

        cancel_btn = ctk.CTkButton(
            bottom_frame,
            text="Cancel",
            command=self._cancel,
            fg_color=APP_CONFIG["THEME_COLORS"]["btn_cancel"],
            hover_color=APP_CONFIG["THEME_COLORS"]["btn_cancel_hover"],
        )
        cancel_btn.pack(side="right", padx=(5, 0))

        ok_btn = ctk.CTkButton(
            bottom_frame, text="OK", command=self._ok, text_color="white"
        )
        ok_btn.pack(side="right")

    def _configure_tree_colors(self):
        # Configure the treeview colors to match the application theme
        style = ttk.Style()

        # Get current theme colors
        bg_color = (
            APP_CONFIG["THEME_COLORS"]["card_bg"][1]
            if ctk.get_appearance_mode() == "Dark"
            else APP_CONFIG["THEME_COLORS"]["card_bg"][0]
        )
        fg_color = (
            APP_CONFIG["THEME_COLORS"]["text_primary"][1]
            if ctk.get_appearance_mode() == "Dark"
            else APP_CONFIG["THEME_COLORS"]["text_primary"][0]
        )
        select_bg = (
            APP_CONFIG["THEME_COLORS"]["btn_active_blue"][1]
            if ctk.get_appearance_mode() == "Dark"
            else APP_CONFIG["THEME_COLORS"]["btn_active_blue"][0]
        )

        # Configure treeview style
        style.configure(
            "Treeview",
            background=bg_color,
            foreground=fg_color,
            fieldbackground=bg_color,
            borderwidth=0,
            font=("TkDefaultFont", 10),
        )

        style.configure(
            "Treeview.Heading", background=bg_color, foreground=fg_color, borderwidth=0
        )

        style.map(
            "Treeview",
            background=[("selected", select_bg)],
            foreground=[("selected", "white")],
        )

        # Remove borders and change selection colors
        style.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])

    def _populate_file_list(self):
        # Clear existing widgets
        for widget in self.file_listbox.winfo_children():
            widget.destroy()

        try:
            # FIX: Only update the entry to reflect the current dir. DO NOT read from it here.
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, str(self.current_dir))

            # Add parent directory if not root
            if self.current_dir.parent != self.current_dir:
                parent_btn = ctk.CTkButton(
                    self.file_listbox,
                    text="..",
                    command=lambda: self._change_dir(self.current_dir.parent),
                    anchor="w",
                )
                parent_btn.pack(fill="x", padx=2, pady=1)

            # List directories first
            for item in sorted(self.current_dir.iterdir()):
                if item.is_dir():
                    btn = ctk.CTkButton(
                        self.file_listbox,
                        text=f"[DIR] {item.name}",
                        command=lambda p=item: self._change_dir(p),
                        anchor="w",
                        fg_color=APP_CONFIG["THEME_COLORS"]["transparent"],
                        hover_color=APP_CONFIG["THEME_COLORS"]["btn_inactive"],
                        text_color=APP_CONFIG["THEME_COLORS"]["text_primary"][1]
                        if ctk.get_appearance_mode() == "Dark"
                        else APP_CONFIG["THEME_COLORS"]["text_primary"][0],
                    )
                    btn.pack(fill="x", padx=2, pady=1)

            # Then files
            for item in sorted(self.current_dir.iterdir()):
                if item.is_file():
                    # Check if file matches any of the filetypes
                    if self._matches_filetype(item):
                        btn = ctk.CTkButton(
                            self.file_listbox,
                            text=item.name,
                            command=None,
                            anchor="w",
                            fg_color=APP_CONFIG["THEME_COLORS"]["transparent"],
                            text_color=APP_CONFIG["THEME_COLORS"]["text_primary"][1]
                            if ctk.get_appearance_mode() == "Dark"
                            else APP_CONFIG["THEME_COLORS"]["text_primary"][0],
                        )
                        btn.pack(fill="x", padx=2, pady=1)
                        # Store reference for selection highlighting
                        btn.file_path = item
                        # Bind single click to select single
                        btn.bind(
                            "<Button-1>", lambda e, p=item: self._select_file_single(p)
                        )
                        # Bind Ctrl+click to toggle multi-select
                        btn.bind(
                            "<Control-Button-1>", lambda e, p=item: self._toggle_file(p)
                        )

                        # FIX: Add double-click binding to select and close on a file
                        def on_file_double_click(event, path):
                            # Check if the file is currently selected (single-click toggles it)
                            if str(path) not in self.selected_files:
                                self._toggle_file(path)  # Select it if it wasn't
                            self._ok()  # Close the dialog

                        btn.bind(
                            "<Double-1>",
                            lambda e, path=item: on_file_double_click(e, path),
                        )

        except Exception as e:
            error_label = ctk.CTkLabel(
                self.file_listbox, text=f"Error accessing folder: {e}"
            )
            error_label.pack(padx=5, pady=5)

    def _on_manual_path_entry(self, event):
        # FIX: Handle manually typing path and hitting Enter
        try:
            new_path = Path(self.path_entry.get())
            if new_path.exists() and new_path.is_dir():
                self._change_dir(new_path)
            else:
                self.status_label.configure(text="Invalid directory path")
                # Reset entry to current valid dir
                self.path_entry.delete(0, "end")
                self.path_entry.insert(0, str(self.current_dir))
        except Exception:
            pass

    def _matches_filetype(self, file_path: Path) -> bool:
        """Check if file matches any of the allowed filetypes."""
        if not self.filetypes:
            return True

        file_ext = file_path.suffix.lower().lstrip(".")

        for desc, pattern in self.filetypes:
            # Allow all files if pattern is *.*
            if pattern == "*.*":
                return True

            # Handle patterns with spaces (multiple extensions like "*.mp4 *.mkv")
            patterns = pattern.split()
            for p in patterns:
                # Remove *. prefix and compare extension
                if p.startswith("*."):
                    allowed_ext = p[2:].lower()
                    if file_ext == allowed_ext:
                        return True

        return False

    def _change_dir(self, new_dir: Path):
        self.current_dir = new_dir
        self._populate_file_list()

    def _toggle_file(self, file_path: Path):
        if str(file_path) in self.selected_files:
            self.selected_files.remove(str(file_path))
        else:
            self.selected_files.append(str(file_path))
        self._update_selection_display()

    def _select_file_single(self, file_path: Path):
        self.selected_files = [str(file_path)]
        self._update_selection_display()

    def _update_selection_display(self):
        # Update button colors to show selection
        for widget in self.file_listbox.winfo_children():
            if hasattr(widget, "file_path"):
                if str(widget.file_path) in self.selected_files:
                    widget.configure(
                        fg_color=APP_CONFIG["THEME_COLORS"]["btn_active_blue"]
                    )
                else:
                    widget.configure(fg_color=APP_CONFIG["THEME_COLORS"]["transparent"])

        self.status_label.configure(text=f"Selected: {len(self.selected_files)} files")

    def _bind_events(self):
        self.bind("<Control-a>", lambda e: self._select_all())
        self.bind("<Control-c>", lambda e: self._copy_files())
        self.bind("<Control-v>", lambda e: self._paste_files())
        self.bind("<Delete>", lambda e: self._delete_to_trash())
        self.bind("<Return>", lambda e: self._ok())
        self.bind("<Escape>", lambda e: self._cancel())
        self.bind(
            "<BackSpace>",
            lambda e: (
                self._change_dir(self.current_dir.parent)
                if self.current_dir.parent != self.current_dir
                else None
            ),
        )
        self.bind("<F5>", lambda e: self._refresh_all())
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.tree.bind("<<TreeviewOpen>>", self._on_tree_expand)

    def _select_all(self):
        self.selected_files = [
            str(item)
            for item in self.current_dir.iterdir()
            if item.is_file() and self._matches_filetype(item)
        ]
        self._update_selection_display()

    def _copy_files(self):
        self.clipboard_files = self.selected_files.copy()
        self.status_label.configure(
            text=f"Copied {len(self.clipboard_files)} files to clipboard"
        )

    def _paste_files(self):
        # For now, just show a message - actual file copying would require more implementation
        if self.clipboard_files:
            self.status_label.configure(
                text=f"Would paste {len(self.clipboard_files)} files (not implemented)"
            )
        else:
            self.status_label.configure(text="No files in clipboard")

    def _delete_to_trash(self):
        # Simplified for safety
        if not self.selected_files:
            return
        if not messagebox.askyesno(
            "Delete", f"Move {len(self.selected_files)} files to trash?"
        ):
            return

        if not SEND2TRASH_AVAILABLE:
            messagebox.showerror(
                "Safe Deletion Unavailable",
                "The 'send2trash' library is missing. Safe deletion cannot be performed.",
            )
            return

        deleted = 0
        for f in self.selected_files:
            try:
                send2trash(f)
                deleted += 1
            except:
                pass

        if deleted:
            self.selected_files = []
            self._populate_file_list()

    def _delete_permanently(self):
        # Permanently delete selected files
        if not self.selected_files:
            self.status_label.configure(text="No files selected for deletion")
            return

        # Confirm permanent deletion
        file_count = len(self.selected_files)
        file_names = [Path(f).name for f in self.selected_files]
        names_display = ", ".join(file_names[:3]) + (
            "..." if len(file_names) > 3 else ""
        )

        if not messagebox.askyesno(
            "Permanent Delete",
            f"Permanently delete {file_count} file(s)?\n{names_display}\n\nThis action cannot be undone!",
        ):
            return

        deleted_count = 0
        failed_files = []

        for file_path in self.selected_files:
            try:
                path_obj = Path(file_path)
                if path_obj.is_file():
                    path_obj.unlink()  # Delete file
                elif path_obj.is_dir():
                    import shutil

                    shutil.rmtree(path_obj)  # Delete directory
                deleted_count += 1
            except Exception as e:
                failed_files.append(Path(file_path).name)
                print(f"Error deleting {file_path}: {e}")

        # Update UI
        if deleted_count > 0:
            self.status_label.configure(
                text=f"Permanently deleted {deleted_count} file(s)"
            )
            # Refresh the file list
            self._populate_file_list()
            # Clear selection
            self.selected_files = []
            self._update_selection_display()
        else:
            self.status_label.configure(text="Failed to delete files")

        if failed_files:
            messagebox.showerror(
                "Delete Error",
                f"Failed to delete: {', '.join(failed_files[:5])}{'...' if len(failed_files) > 5 else ''}",
            )

    def _ok(self):
        self.result = self.selected_files
        self.destroy()

    def _cancel(self):
        self.result = None
        self.destroy()

    def _populate_tree(self):
        # Populate the tree view with the folder structure starting from the current directory
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Add root directory
        root_path = Path.home()
        root_node = self.tree.insert(
            "", "end", text=str(root_path), open=True, values=[str(root_path)]
        )

        # Populate the tree starting from root
        self._populate_tree_recursive(root_node, root_path)

        # Expand current directory path
        self._expand_to_current_dir()

    def _populate_tree_recursive(self, parent_node, path: Path, max_depth=2):
        # Recursively populate tree nodes with directories
        try:
            if path.exists() and path.is_dir():
                # Limit depth to prevent excessive loading
                current_depth = len(
                    self.tree.item(parent_node, "values")[0].split(os.sep)
                ) - len(str(Path.home()).split(os.sep))
                if current_depth >= max_depth:
                    return

                for item in sorted(path.iterdir()):
                    if item.is_dir() and not item.name.startswith(
                        "."
                    ):  # Skip hidden directories
                        node = self.tree.insert(
                            parent_node, "end", text=item.name, values=[str(item)]
                        )
                        # Add dummy child to make it expandable
                        self.tree.insert(node, "end", text="", values=[""])
        except (PermissionError, OSError):
            # Skip directories we can't access
            pass

    def _expand_to_current_dir(self):
        # Simplified expansion
        pass

    def _on_tree_select(self, event):
        # Handle tree selection - change directory when a folder is selected
        selected_items = self.tree.selection()
        if selected_items:
            selected_item = selected_items[0]
            item_values = self.tree.item(selected_item, "values")
            if item_values:
                selected_path = Path(item_values[0])
                if selected_path.exists() and selected_path.is_dir():
                    self._change_dir(selected_path)

    def _on_tree_expand(self, event):
        # Handle tree expansion - populate children when a node is expanded
        # Get the item that was expanded
        expanded_item = self.tree.focus()
        if expanded_item:
            item_values = self.tree.item(expanded_item, "values")
            if item_values:
                expanded_path = Path(item_values[0])
                # Check if this node has dummy children that need to be replaced
                children = self.tree.get_children(expanded_item)
                if (
                    children and not self.tree.item(children[0], "values")[0]
                ):  # Dummy child
                    # Remove dummy child
                    self.tree.delete(children[0])
                    # Populate real children
                    self._populate_tree_recursive(expanded_item, expanded_path)

    def _refresh_all(self):
        # Refresh both tree and file list
        self._populate_tree()
        self._populate_file_list()

    @classmethod
    def askopenfilenames(
        cls, parent, title="Select Files", filetypes=None, initialdir=None
    ) -> Optional[List[str]]:
        dialog = cls(parent, title, filetypes, initialdir)
        dialog.wait_window()
        return dialog.result


# DirDialog
class CustomDirectoryDialog(ctk.CTkToplevel):
    def __init__(self, parent, title: str = "Select Directory", initialdir=None):
        super().__init__(parent)
        self.title(title)
        self.geometry(APP_CONFIG["FILE_DIALOG_SIZE"])
        self.transient(parent)

        self.result: Optional[str] = None

        # FIX: Ensure initial directory is valid, otherwise fallback to Home
        init_path = Path(initialdir) if initialdir else Path.home()
        self.current_dir = init_path if init_path.exists() else Path.home()

        self._create_widgets()
        self._populate_tree()
        self._populate_dir_list()
        self._bind_events()

    def _create_widgets(self):
        # Main frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Top frame for path and buttons
        top_frame = ctk.CTkFrame(main_frame)
        top_frame.pack(fill="x", padx=5, pady=5)

        self.path_entry = ctk.CTkEntry(top_frame, placeholder_text="Current directory")
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        # FIX: Bind Enter key to handle manual path typing
        self.path_entry.bind("<Return>", self._on_manual_path_entry)

        refresh_btn = ctk.CTkButton(
            top_frame,
            text="Refresh",
            command=self._refresh_all,
            width=80,
            text_color="white",
        )
        refresh_btn.pack(side="right", padx=(5, 0))

        # Content frame with tree and dir list
        content_frame = ctk.CTkFrame(main_frame)
        content_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Tree view for folder navigation
        tree_frame = ctk.CTkFrame(content_frame, width=250)
        tree_frame.pack(side="left", fill="y", padx=(0, 5), pady=0)
        tree_frame.pack_propagate(False)

        tree_label = ctk.CTkLabel(
            tree_frame, text="Folders", font=ctk.CTkFont(weight="bold")
        )
        tree_label.pack(pady=(5, 0))

        # Create treeview using tkinter's Treeview
        from tkinter import ttk

        self.tree = ttk.Treeview(tree_frame, height=20, show="tree")
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)

        # Configure tree colors to match application theme
        self._configure_tree_colors()

        # Directory list
        self.dir_listbox = ctk.CTkScrollableFrame(content_frame)
        self.dir_listbox.pack(
            side="right", fill="both", expand=True, padx=(5, 0), pady=0
        )

        # Status bar
        self.status_label = ctk.CTkLabel(
            main_frame, text="Select a directory", anchor="w"
        )
        self.status_label.pack(fill="x", padx=5, pady=(0, 5))

        # Bottom buttons
        bottom_frame = ctk.CTkFrame(
            main_frame, fg_color=APP_CONFIG["THEME_COLORS"]["transparent"]
        )
        bottom_frame.pack(fill="x", padx=5, pady=5)

        cancel_btn = ctk.CTkButton(
            bottom_frame,
            text="Cancel",
            command=self._cancel,
            fg_color=APP_CONFIG["THEME_COLORS"]["btn_cancel"],
            hover_color=APP_CONFIG["THEME_COLORS"]["btn_cancel_hover"],
        )
        cancel_btn.pack(side="right", padx=(5, 0))

        ok_btn = ctk.CTkButton(
            bottom_frame, text="OK", command=self._ok, text_color="white"
        )
        ok_btn.pack(side="right")

    def _configure_tree_colors(self):
        # Configure the treeview colors to match the application theme
        style = ttk.Style()

        # Get current theme colors
        bg_color = (
            APP_CONFIG["THEME_COLORS"]["card_bg"][1]
            if ctk.get_appearance_mode() == "Dark"
            else APP_CONFIG["THEME_COLORS"]["card_bg"][0]
        )
        fg_color = (
            APP_CONFIG["THEME_COLORS"]["text_primary"][1]
            if ctk.get_appearance_mode() == "Dark"
            else APP_CONFIG["THEME_COLORS"]["text_primary"][0]
        )
        select_bg = (
            APP_CONFIG["THEME_COLORS"]["btn_active_blue"][1]
            if ctk.get_appearance_mode() == "Dark"
            else APP_CONFIG["THEME_COLORS"]["btn_active_blue"][0]
        )

        # Configure treeview style
        style.configure(
            "Treeview",
            background=bg_color,
            foreground=fg_color,
            fieldbackground=bg_color,
            borderwidth=0,
            font=("TkDefaultFont", 10),
        )

        style.configure(
            "Treeview.Heading", background=bg_color, foreground=fg_color, borderwidth=0
        )

        style.map(
            "Treeview",
            background=[("selected", select_bg)],
            foreground=[("selected", "white")],
        )

        # Remove borders and change selection colors
        style.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])

    def _populate_dir_list(self):
        # Clear existing widgets
        for widget in self.dir_listbox.winfo_children():
            widget.destroy()

        try:
            # FIX: Only update the entry to reflect the current dir. DO NOT read from it here.
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, str(self.current_dir))

            # Add parent directory if not root
            if self.current_dir.parent != self.current_dir:
                parent_btn = ctk.CTkButton(
                    self.dir_listbox,
                    text="..",
                    command=lambda: self._change_dir(self.current_dir.parent),
                    anchor="w",
                )
                parent_btn.pack(fill="x", padx=2, pady=1)

            # List directories
            for item in sorted(self.current_dir.iterdir()):
                if item.is_dir():
                    btn = ctk.CTkButton(
                        self.dir_listbox,
                        text=f"[DIR] {item.name}",
                        command=lambda p=item: self._select_dir(p),
                        anchor="w",
                        fg_color=APP_CONFIG["THEME_COLORS"]["transparent"],
                        hover_color=APP_CONFIG["THEME_COLORS"]["btn_inactive"],
                        text_color=APP_CONFIG["THEME_COLORS"]["text_primary"][1]
                        if ctk.get_appearance_mode() == "Dark"
                        else APP_CONFIG["THEME_COLORS"]["text_primary"][0],
                    )
                    btn.pack(fill="x", padx=2, pady=1)

        except Exception as e:
            error_label = ctk.CTkLabel(
                self.dir_listbox, text=f"Error accessing folder: {e}"
            )
            error_label.pack(padx=5, pady=5)

    def _on_manual_path_entry(self, event):
        # FIX: Handle manually typing path and hitting Enter
        try:
            new_path = Path(self.path_entry.get())
            if new_path.exists() and new_path.is_dir():
                self._change_dir(new_path)
            else:
                self.status_label.configure(text="Invalid directory path")
                # Reset entry to current valid dir
                self.path_entry.delete(0, "end")
                self.path_entry.insert(0, str(self.current_dir))
        except Exception:
            pass

    def _change_dir(self, new_dir: Path):
        self.current_dir = new_dir
        self._populate_dir_list()

    def _select_dir(self, dir_path: Path):
        self.result = str(dir_path)
        self.destroy()

    def _bind_events(self):
        self.bind("<Return>", lambda e: self._ok())
        self.bind("<Escape>", lambda e: self._cancel())
        self.bind(
            "<BackSpace>",
            lambda e: (
                self._change_dir(self.current_dir.parent)
                if self.current_dir.parent != self.current_dir
                else None
            ),
        )
        self.bind("<F5>", lambda e: self._refresh_all())
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.tree.bind("<<TreeviewOpen>>", self._on_tree_expand)

    def _ok(self):
        self.result = str(self.current_dir)
        self.destroy()

    def _cancel(self):
        self.result = None
        self.destroy()

    def _populate_tree(self):
        # Populate the tree view with the folder structure starting from the current directory
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Add root directory
        root_path = Path.home()
        root_node = self.tree.insert(
            "", "end", text=str(root_path), open=True, values=[str(root_path)]
        )

        # Populate the tree starting from root
        self._populate_tree_recursive(root_node, root_path)

        # Expand current directory path
        self._expand_to_current_dir()

    def _populate_tree_recursive(self, parent_node, path: Path, max_depth=2):
        # Recursively populate tree nodes with directories
        try:
            if path.exists() and path.is_dir():
                # Limit depth to prevent excessive loading
                current_depth = len(
                    self.tree.item(parent_node, "values")[0].split(os.sep)
                ) - len(str(Path.home()).split(os.sep))
                if current_depth >= max_depth:
                    return

                for item in sorted(path.iterdir()):
                    if item.is_dir() and not item.name.startswith(
                        "."
                    ):  # Skip hidden directories
                        node = self.tree.insert(
                            parent_node, "end", text=item.name, values=[str(item)]
                        )
                        # Add dummy child to make it expandable
                        self.tree.insert(node, "end", text="", values=[""])
        except (PermissionError, OSError):
            # Skip directories we can't access
            pass

    def _expand_to_current_dir(self):
        # Simplified expansion
        pass

    def _on_tree_select(self, event):
        # Handle tree selection - change directory when a folder is selected
        selected_items = self.tree.selection()
        if selected_items:
            selected_item = selected_items[0]
            item_values = self.tree.item(selected_item, "values")
            if item_values:
                selected_path = Path(item_values[0])
                if selected_path.exists() and selected_path.is_dir():
                    self._change_dir(selected_path)

    def _on_tree_expand(self, event):
        # Handle tree expansion - populate children when a node is expanded
        # Get the item that was expanded
        expanded_item = self.tree.focus()
        if expanded_item:
            item_values = self.tree.item(expanded_item, "values")
            if item_values:
                expanded_path = Path(item_values[0])
                # Check if this node has dummy children that need to be replaced
                children = self.tree.get_children(expanded_item)
                if (
                    children and not self.tree.item(children[0], "values")[0]
                ):  # Dummy child
                    # Remove dummy child
                    self.tree.delete(children[0])
                    # Populate real children
                    self._populate_tree_recursive(expanded_item, expanded_path)

    def _refresh_all(self):
        # Refresh both tree and dir list
        self._populate_tree()
        self._populate_dir_list()

    @classmethod
    def askdirectory(
        cls, parent, title="Select Directory", initialdir=None
    ) -> Optional[str]:
        dialog = cls(parent, title, initialdir)
        dialog.wait_window()
        return dialog.result


# SizeDialog
class CustomSizeDialog(ctk.CTkToplevel):
    def __init__(self, parent, title: str = "Enter Custom Resolution"):
        super().__init__(parent)
        # Initializes a dialog window for entering custom image width and height.
        self.title(title)
        self.geometry(APP_CONFIG["SIZE_DIALOG_SIZE"])
        self.transient(parent)
        self.grab_set()

        self._center_window(parent)
        self.result: Optional[Tuple[str, str]] = None

        self._create_widgets()
        self._bind_events()

    def _center_window(self, parent):
        # Centers the dialog window relative to its parent.
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def _create_widgets(self):
        # Sets up the input fields and OK/Cancel buttons.
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        main_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(
            main_frame, text="WIDTH (W):", font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
        self.width_entry = ctk.CTkEntry(main_frame, placeholder_text="e.g., 1920")
        self.width_entry.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")

        ctk.CTkLabel(
            main_frame, text="HEIGHT (H):", font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=1, padx=10, pady=(10, 5), sticky="w")
        self.height_entry = ctk.CTkEntry(main_frame, placeholder_text="e.g., 1920")
        self.height_entry.grid(row=1, column=1, padx=10, pady=(0, 10), sticky="ew")

        ctk.CTkButton(
            main_frame, text="OK", command=self._ok_action, text_color="white"
        ).grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        ctk.CTkButton(
            main_frame,
            text="CANCEL",
            command=self._cancel_action,
            fg_color=APP_CONFIG["THEME_COLORS"]["btn_inactive"],
            hover_color=APP_CONFIG["THEME_COLORS"]["btn_hover"],
            text_color="white",
        ).grid(row=2, column=1, padx=10, pady=10, sticky="ew")

    def _bind_events(self):
        # Binds keyboard events (Enter/Escape) for action shortcuts.
        self.bind("<Return>", lambda _: self._ok_action())
        self.bind("<Escape>", lambda _: self._cancel_action())
        self.width_entry.focus_set()

    def _ok_action(self):
        # Validates input, sets result tuple, and closes the dialog.
        try:
            W = int(self.width_entry.get().strip())
            H = int(self.height_entry.get().strip())

            if W > 0 and H > 0:
                self.result = (str(W), str(H))
                if self.winfo_exists():
                    self.destroy()
            else:
                self.result = None
                if self.winfo_exists():
                    self.destroy()
        except ValueError:
            self.result = None
            if self.winfo_exists():
                self.destroy()

    def _cancel_action(self):
        # Clears the result and closes the dialog.
        self.result = None
        if self.winfo_exists():
            self.destroy()

    def show(self) -> Optional[Tuple[str, str]]:
        # Displays the dialog and waits for user interaction, returning the result.
        self.wait_window()
        return self.result


class FFConverterApp(CTkDnD):
    def __init__(self):
        super().__init__()

        self.title("FFConverter")
        self.geometry(APP_CONFIG["WINDOW_SIZE"])
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=1)

        if not TKINTERDND_AVAILABLE:
            print("Warning: Drag-and-drop disabled. Install: pip install tkinterdnd2")

        if not SEND2TRASH_AVAILABLE:
            print("Warning: Safe deletion disabled. Install: pip install send2trash")

        if not PYSTRAY_AVAILABLE:
            print("Warning: System tray icon disabled. Install: pip install pystray pillow")
        else:
            self._setup_tray_icon()

        # Vars
        default_msg = "FILE NOT SELECTED. CLICK ON BROWSE TO SELECT FILES"
        self.video_input_path = ctk.StringVar(value=default_msg)
        self.audio_input_path = ctk.StringVar(value=default_msg)
        self.image_input_path = ctk.StringVar(value=default_msg)
        self.output_dir = ctk.StringVar(value=APP_CONFIG["DEFAULT_OUTPUT_DIR"])

        # Store actual file paths for conversion (separate from display text)
        self.selected_video_files: List[str] = []
        self.selected_audio_files: List[str] = []
        self.selected_image_files: List[str] = []

        # UI variable initialization for Video, Audio, and Image conversion settings.
        self.video_format = ctk.StringVar(value=VIDEO_FORMATS[0])
        self.video_quality_mode = ctk.StringVar(value=VIDEO_QUALITY_MODES[0])
        self.video_quality_value = ctk.StringVar(value="8K (50M)")
        self.video_frame_rate = ctk.StringVar(value="ORIGINAL (COPY)")
        self.video_keep_aspect_ratio = ctk.BooleanVar(value=True)
        self.video_deinterlace = ctk.BooleanVar(value=False)
        self.video_strip_metadata = ctk.BooleanVar(value=False)
        self.video_remove_audio = ctk.BooleanVar(value=False)
        self.video_remove_video = ctk.BooleanVar(value=False)

        self.audio_format = ctk.StringVar(value=AUDIO_FORMATS[0])
        self.audio_quality = ctk.StringVar(value="320K")
        self.audio_dithering = ctk.BooleanVar(value=False)
        self.audio_limiter = ctk.BooleanVar(value=False)
        self.audio_strip_metadata = ctk.BooleanVar(value=False)
        self.mp3_mode = ctk.StringVar(value="CBR")

        self.image_format = ctk.StringVar(value=IMAGE_FORMATS[0])
        self.image_size = ctk.StringVar(value="ORIGINAL (COPY)")
        self.custom_image_dims: Optional[Tuple[str, str]] = None
        self.image_keep_aspect_ratio = ctk.BooleanVar(value=True)
        self.image_strip_metadata = ctk.BooleanVar(value=False)
        self.image_compress = ctk.BooleanVar(value=False)
        self.image_visual_filter = ctk.StringVar(value=IMAGE_FILTERS[0])

        self.video_progress_bar = None
        self.video_convert_btn = None
        self.audio_progress_bar = None
        self.audio_convert_btn = None
        self.image_progress_bar = None
        self.image_convert_btn = None

        # State variable for current tab (replaced tab_view.get())
        self.current_tab_name = "Audio"  # Default
        self.nav_buttons = {}  # Store buttons to update colors

        # ATTRIBUTE: Holds the active FFmpeg subprocess.
        self.active_conversion_process: Optional[subprocess.Popen] = None

        # ThreadPoolExecutor for managing conversion tasks
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)

        # Current Future object for tracking conversion
        self.current_future: Optional[concurrent.futures.Future] = None

        # Counter for active conversions to manage progress bar properly for batch processing
        self.conversion_counter = 0

        # Per-file progress tracking
        self.converted_files_count = 0
        self.total_files_to_convert = 0
        self.current_file_index = 0

        self.common_widgets = {tab: {} for tab in ["Video", "Audio", "Image"]}
        self.video_tab_initialized = False
        self.audio_tab_initialized = True  # Audio is default, always initialized
        self.image_tab_initialized = False
        self.ffmpeg_checked = False  # Defer FFmpeg check to first conversion

        # Tab variables for drag-and-drop
        self.tab_variables = {
            "Video": {"input": self.video_input_path, "extensions": "video formats"},
            "Audio": {"input": self.audio_input_path, "extensions": "audio formats"},
            "Image": {"input": self.image_input_path, "extensions": "image formats"},
        }

        self.folder_icon = self._load_folder_icon()
        self._create_widgets()

    # UI Helpers
    def _create_toggle_button(self, parent, text, variable, command=None, width=None):
        """Creates a toggle button that acts like a checkbox."""

        def toggle_action():
            # Toggle the boolean variable
            new_state = not variable.get()
            variable.set(new_state)
            update_visuals()
            if command:
                command()

        def update_visuals(*args):
            # Update color based on state
            if variable.get():
                btn.configure(
                    fg_color=APP_CONFIG["THEME_COLORS"]["btn_active_blue"],
                    hover_color=APP_CONFIG["THEME_COLORS"]["btn_hover_blue"],
                    text_color=APP_CONFIG["THEME_COLORS"]["white"],
                )
            else:
                # Use white text for inactive buttons in LIGHT mode to match active button text color
                btn.configure(
                    fg_color=APP_CONFIG["THEME_COLORS"]["btn_inactive"],
                    hover_color=APP_CONFIG["THEME_COLORS"]["btn_hover"],
                    text_color=APP_CONFIG["THEME_COLORS"]["white"],
                )

        # Initial Button Creation
        btn = ctk.CTkButton(
            parent,
            text=text,
            command=toggle_action,
            font=ctk.CTkFont(size=12, weight="bold"),
            height=32,
            corner_radius=6,
        )

        if width:
            btn.configure(width=width)

        # Set initial state
        update_visuals()

        # Trace variable changes (so if changed programmatically, button updates)
        # Note: We need to keep a reference to the trace to avoid garbage collection issues if needed,
        # but for simple UI this is usually fine.
        variable.trace_add("write", update_visuals)

        return btn

    def _create_card(self, parent, row, column, columnspan=1, rowspan=1, title=None):
        """Creates a card-like frame with an optional title."""
        card = ctk.CTkFrame(
            parent, fg_color=APP_CONFIG["THEME_COLORS"]["card_bg"], corner_radius=10
        )
        card.grid(
            row=row,
            column=column,
            columnspan=columnspan,
            rowspan=rowspan,
            padx=10,
            pady=5,
            sticky="nsew",
        )  # Reduced pady from 10 to 5

        # Grid configuration for the card itself
        card.grid_columnconfigure(0, weight=1)

        current_row = 0
        if title:
            title_label = ctk.CTkLabel(
                card,
                text=title,
                font=ctk.CTkFont(size=9, weight="bold"),
                text_color=APP_CONFIG["THEME_COLORS"]["text_primary"],
                anchor="center",
            )
            title_label.grid(
                row=0, column=0, columnspan=4, padx=15, pady=(15, 5), sticky="ew"
            )
            card.title_label = title_label
            current_row = 1

        return card, current_row

    def _create_section_header(self, parent, text, row, column, columnspan=1):
        """Creates a distinct section header."""
        label = ctk.CTkLabel(
            parent,
            text=text,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=APP_CONFIG["THEME_COLORS"]["text_primary"],
        )
        label.grid(
            row=row,
            column=column,
            columnspan=columnspan,
            padx=10,
            pady=(20, 5),
            sticky="w",
        )
        return label

    # Load Icon
    def _load_folder_icon(self) -> Optional[ctk.CTkImage]:
        # Attempts to load a folder icon image using PIL for the 'Open Folder' button.
        try:
            from PIL import Image

            if FOLDER_ICON_PATH.exists():
                img = Image.open(FOLDER_ICON_PATH)
                return ctk.CTkImage(light_image=img, dark_image=img, size=(20, 20))
        except Exception as e:
            print(f"Warning: Could not load folder icon: {e}")
        return None

    # Create UI
    def _create_widgets(self):
        # Sets up the custom tab navigation and content frames.

        # 0. Top Header Frame (Theme Toggler)
        self.top_header = ctk.CTkFrame(
            self, fg_color=APP_CONFIG["THEME_COLORS"]["transparent"]
        )
        self.top_header.grid(row=0, column=0, padx=20, pady=(5, 15), sticky="ew")
        self.top_header.grid_columnconfigure(0, weight=1)

        # 1. Navigation Frame (Tabs)
        self.nav_frame = ctk.CTkFrame(
            self, fg_color=APP_CONFIG["THEME_COLORS"]["card_bg"], corner_radius=10
        )
        self.nav_frame.grid(row=1, column=0, padx=10, pady=(0, 5), sticky="ew")
        self.nav_frame.grid_columnconfigure(0, weight=1)
        self.nav_frame.grid_columnconfigure(1, weight=1)
        self.nav_frame.grid_columnconfigure(2, weight=1)

        # 2. Content Frame (Bottom)
        self.content_frame = ctk.CTkFrame(
            self, fg_color=APP_CONFIG["THEME_COLORS"]["transparent"]
        )
        self.content_frame.grid(row=2, column=0, padx=0, pady=(0, 0), sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

        # 3. Create Content Tabs (Frames)
        self.audio_tab = ctk.CTkFrame(
            self.content_frame,
            corner_radius=0,
            fg_color=APP_CONFIG["THEME_COLORS"]["transparent"],
        )
        self.video_tab = ctk.CTkFrame(
            self.content_frame,
            corner_radius=0,
            fg_color=APP_CONFIG["THEME_COLORS"]["transparent"],
        )
        self.image_tab = ctk.CTkFrame(
            self.content_frame,
            corner_radius=0,
            fg_color=APP_CONFIG["THEME_COLORS"]["transparent"],
        )

        # Grid all tabs once at startup (will use tkraise() for switching)
        for tab in [self.audio_tab, self.video_tab, self.image_tab]:
            tab.grid(row=0, column=0, sticky="nsew")

        # 4. Create Navigation Buttons
        # Using separate buttons for maximum control over positioning/styling
        self.btn_audio = ctk.CTkButton(
            self.nav_frame,
            text="AUDIO",
            command=lambda: self._change_tab("Audio"),
            font=ctk.CTkFont(size=14, weight="bold"),
            height=32,
            border_width=0,
            border_spacing=10,
            text_color="white",
        )
        self.btn_audio.grid(row=0, column=0, padx=(25, 5), pady=25, sticky="ew")

        self.btn_video = ctk.CTkButton(
            self.nav_frame,
            text="VIDEO",
            command=lambda: self._change_tab("Video"),
            font=ctk.CTkFont(size=14, weight="bold"),
            height=32,
            border_width=0,
            border_spacing=10,
            text_color="white",
        )
        self.btn_video.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.btn_image = ctk.CTkButton(
            self.nav_frame,
            text="IMAGE",
            command=lambda: self._change_tab("Image"),
            font=ctk.CTkFont(size=14, weight="bold"),
            height=32,
            border_width=0,
            border_spacing=10,
            text_color="white",
        )
        self.btn_image.grid(row=0, column=2, padx=(5, 25), pady=25, sticky="ew")

        self.nav_buttons = {
            "Audio": self.btn_audio,
            "Video": self.btn_video,
            "Image": self.btn_image,
        }

        # Grid configuration for tabs
        for tab in [self.audio_tab, self.video_tab, self.image_tab]:
            tab.grid_columnconfigure(0, weight=1)
            tab.grid_rowconfigure((0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 11), weight=0)
            tab.grid_rowconfigure(9, weight=1)

        self._setup_audio_tab()
        self.audio_tab_initialized = True  # Audio is default
        self._bind_help_text_for_tab("Audio")
        self._setup_theme_toggler()
        self._setup_drag_and_drop()

        # Note: FFmpeg check deferred to first conversion attempt for faster startup

        # Initialize with Audio tab (already set up above)
        self._change_tab("Audio")

    def _change_tab(self, tab_name: str):
        self.current_tab_name = tab_name

        # Lazy-load Video/Image tabs on first access
        if tab_name == "Video" and not self.video_tab_initialized:
            self.video_tab_initialized = True
            main_frame = ctk.CTkFrame(
                self.video_tab, fg_color=APP_CONFIG["THEME_COLORS"]["card_bg"], corner_radius=10
            )
            main_frame.grid(row=0, column=0, padx=10, pady=5, sticky="nsew")
            main_frame.grid_columnconfigure(0, weight=1)
            self._setup_video_tab_content(main_frame)
            self._bind_help_text_for_tab("Video")
        elif tab_name == "Image" and not self.image_tab_initialized:
            self.image_tab_initialized = True
            main_frame = ctk.CTkFrame(
                self.image_tab, fg_color=APP_CONFIG["THEME_COLORS"]["card_bg"], corner_radius=10
            )
            main_frame.grid(row=0, column=0, padx=10, pady=5, sticky="nsew")
            main_frame.grid_columnconfigure(0, weight=1)
            self._setup_image_tab_content(main_frame)
            self._bind_help_text_for_tab("Image")

        # Update button colors first (batch update before showing new tab)
        active_color = APP_CONFIG["THEME_COLORS"]["btn_active_blue"]
        inactive_color = APP_CONFIG["THEME_COLORS"]["btn_inactive"]

        for name, btn in self.nav_buttons.items():
            btn.configure(
                fg_color=active_color if name == tab_name else inactive_color
            )

        # Update Content using tkraise() - much faster than grid_forget()/grid()
        # as it only changes Z-order without recalculating layouts
        if tab_name == "Audio":
            self.audio_tab.tkraise()
        elif tab_name == "Video":
            self.video_tab.tkraise()
        elif tab_name == "Image":
            self.image_tab.tkraise()

    # Help Text
    def _update_help_text(self, tab_key: str, key: str):
        # Changes the text in the help/tooltip label based on hover events.
        if "help_text_label" in self.common_widgets.get(tab_key, {}):
            self.common_widgets[tab_key]["help_text_label"].configure(
                text=HELP_MESSAGES.get(key, HELP_MESSAGES["default"])
            )

    # Common Tab
    def _create_common_tab_widgets(self, tab_name, tab_frame):
        # Creates the common widgets for a specific tab: Input File card, Output Folder card, and Help frame.
        # Configure grid for the tab content
        tab_frame.grid_columnconfigure(0, weight=1)

        # --- Input Section Card ---
        input_card, r = self._create_card(
            tab_frame, row=0, column=0, title="PLEASE SELECT YOUR INPUT FILE"
        )
        input_card.grid_configure(pady=5)
        input_card.grid_columnconfigure(0, weight=1)

        # Store reference to input card
        self.common_widgets[tab_name]["input_card"] = input_card

        input_var = None
        if tab_name == "Video":
            input_var = self.video_input_path
        elif tab_name == "Audio":
            input_var = self.audio_input_path
        elif tab_name == "Image":
            input_var = self.image_input_path

        if input_var is None:
            return

        browse_button = ctk.CTkButton(
            input_card,
            text="BROWSE",
            command=self._select_input_file,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=APP_CONFIG["THEME_COLORS"]["btn_active_blue"],
            hover_color=APP_CONFIG["THEME_COLORS"]["btn_hover_blue"],
            text_color="white",
        )
        browse_button.grid(row=r, column=0, padx=15, pady=(5, 10), sticky="ew")
        self.common_widgets[tab_name]["browse_button"] = browse_button

        input_label = ctk.CTkLabel(
            input_card,
            textvariable=input_var,
            anchor="center",
            wraplength=700,
            text_color=APP_CONFIG["THEME_COLORS"]["text_secondary"],
        )
        input_label.grid(row=r + 1, column=0, padx=15, pady=(0, 15), sticky="ew")
        self.common_widgets[tab_name]["input_label"] = input_label

        # --- Output Section Card (Reordered to Row 7) ---
        output_card, r_out = self._create_card(
            tab_frame, row=7, column=0, title="OUTPUT FOLDER SETTINGS"
        )
        output_card.grid_configure(pady=5)
        output_card.grid_columnconfigure(0, weight=7)
        output_card.grid_columnconfigure(1, weight=2)
        output_card.grid_columnconfigure(2, weight=1)

        self.common_widgets[tab_name]["output_card"] = output_card

        output_entry = ctk.CTkEntry(
            output_card,
            textvariable=self.output_dir,
            state="readonly",
            fg_color=APP_CONFIG["THEME_COLORS"]["input_bg"],
            border_width=2,
            border_color=APP_CONFIG["THEME_COLORS"]["white"],
        )
        output_entry.grid(
            row=r_out, column=0, padx=(15, 5), pady=(15, 15), sticky="ew"
        )  # Increased top pady since label is gone
        self.common_widgets[tab_name]["output_entry"] = output_entry

        change_btn = ctk.CTkButton(
            output_card,
            text="CHANGE",
            command=self._select_output_directory,
            width=100,
            fg_color=APP_CONFIG["THEME_COLORS"]["btn_inactive"],
            hover_color=APP_CONFIG["THEME_COLORS"]["btn_hover"],
            text_color="white",
        )
        change_btn.grid(row=r_out, column=1, padx=(5, 5), pady=(15, 15), sticky="ew")
        self.common_widgets[tab_name]["change_btn"] = change_btn

        open_btn = ctk.CTkButton(
            output_card,
            text="OPEN" if not self.folder_icon else "",
            image=self.folder_icon if self.folder_icon else None,
            width=50,
            command=self._open_output_directory,
            fg_color=APP_CONFIG["THEME_COLORS"]["btn_open"],
            hover_color=APP_CONFIG["THEME_COLORS"]["btn_open_hover"],
            text_color=APP_CONFIG["THEME_COLORS"][
                "white"
            ],  # Keeps text readable on both pink and orange
        )
        open_btn.grid(row=r_out, column=2, padx=(5, 15), pady=(15, 15), sticky="ew")
        self.common_widgets[tab_name]["open_btn"] = open_btn

        # Help Frame (Row 9 - Just above Output)
        # We'll make this less intrusive, maybe just a status line or a small card
        help_frame = ctk.CTkFrame(
            tab_frame, fg_color=APP_CONFIG["THEME_COLORS"]["transparent"], height=30
        )
        help_frame.grid(
            row=9, column=0, columnspan=3, padx=10, pady=(5, 20), sticky="ew"
        )
        help_frame.grid_columnconfigure(0, weight=1)

        help_text_label = ctk.CTkLabel(
            help_frame,
            text=HELP_MESSAGES["default"],
            anchor="center",
            justify="center",
            wraplength=750,
            text_color=APP_CONFIG["THEME_COLORS"]["text_secondary"],
            font=ctk.CTkFont(size=12, slant="italic"),
        )
        help_text_label.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        self.common_widgets[tab_name]["help_text_label"] = help_text_label

    # Video Tab
    def _setup_video_tab(self):
        # Configures the specific widgets for video conversion options.
        # Creates main frame and defers content creation for lazy loading.
        tab_name = "Video"
        tab = self.video_tab

        main_frame = ctk.CTkFrame(
            tab, fg_color=APP_CONFIG["THEME_COLORS"]["card_bg"], corner_radius=10
        )
        main_frame.grid(row=0, column=0, padx=10, pady=5, sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)

        self._setup_video_tab_content(main_frame)

    def _setup_video_tab_content(self, main_frame):
        # Builds video tab content into existing main_frame (for lazy loading)
        tab_name = "Video"
        # main_frame already passed in from _change_tab lazy loading

        # Create common widgets first
        self._create_common_tab_widgets(tab_name, main_frame)

        # --- Conversion Settings Card ---
        settings_card, r = self._create_card(
            main_frame,
            row=1,
            column=0,
            title="HERE ARE THE SETTINGS FOR YOUR DESIRED VIDEO OUTPUT",
        )

        # Configure columns for the settings card
        settings_card.grid_columnconfigure(0, weight=1, uniform="video")
        settings_card.grid_columnconfigure(1, weight=1, uniform="video")
        settings_card.grid_columnconfigure(2, weight=1, uniform="video")
        settings_card.grid_columnconfigure(3, weight=1, uniform="video")

        # Option menus for Format, Quality Mode, Quality Value, and Framerate.
        format_label = ctk.CTkLabel(
            settings_card,
            text="CONTAINER (CODEC):",
            text_color=APP_CONFIG["THEME_COLORS"]["text_primary"],
        )
        format_label.grid(row=r, column=0, padx=15, pady=(5, 5), sticky="w")
        self.common_widgets[tab_name]["format_label"] = format_label

        format_menu = ctk.CTkOptionMenu(
            settings_card, values=VIDEO_FORMATS, variable=self.video_format
        )
        format_menu.grid(row=r + 1, column=0, padx=(15, 5), pady=(0, 15), sticky="ew")
        self.common_widgets[tab_name]["format_menu"] = format_menu

        quality_mode_label = ctk.CTkLabel(
            settings_card,
            text="QUALITY MODE:",
            text_color=APP_CONFIG["THEME_COLORS"]["text_primary"],
        )
        quality_mode_label.grid(row=r, column=1, padx=5, pady=(5, 5), sticky="w")
        self.common_widgets[tab_name]["quality_mode_label"] = quality_mode_label

        self.video_quality_mode_menu = ctk.CTkOptionMenu(
            settings_card,
            values=VIDEO_QUALITY_MODES,
            variable=self.video_quality_mode,
            command=self._update_video_options,
        )
        self.video_quality_mode_menu.grid(
            row=r + 1, column=1, padx=5, pady=(0, 15), sticky="ew"
        )
        self.common_widgets[tab_name]["quality_mode_menu"] = (
            self.video_quality_mode_menu
        )

        self.quality_value_label = ctk.CTkLabel(
            settings_card,
            text="TARGET VALUE:",
            text_color=APP_CONFIG["THEME_COLORS"]["text_primary"],
        )
        self.quality_value_label.grid(row=r, column=2, padx=5, pady=(5, 5), sticky="w")
        self.common_widgets[tab_name]["quality_value_label"] = self.quality_value_label

        self.video_quality_value_menu = ctk.CTkOptionMenu(
            settings_card,
            values=["ORIGINAL (COPY)"] + VIDEO_QUALITY_PRESETS,
            variable=self.video_quality_value,
        )
        self.video_quality_value_menu.grid(
            row=r + 1, column=2, padx=5, pady=(0, 15), sticky="ew"
        )
        self.common_widgets[tab_name]["quality_value_menu"] = (
            self.video_quality_value_menu
        )

        self._update_video_options(None)

        framerate_label = ctk.CTkLabel(
            settings_card,
            text="FRAME RATE (FPS):",
            text_color=APP_CONFIG["THEME_COLORS"]["text_primary"],
        )
        framerate_label.grid(row=r, column=3, padx=(5, 15), pady=(5, 5), sticky="w")
        self.common_widgets[tab_name]["framerate_label"] = framerate_label

        framerate_menu = ctk.CTkOptionMenu(
            settings_card,
            values=VIDEO_FRAME_RATE_PRESETS,
            variable=self.video_frame_rate,
        )
        framerate_menu.grid(
            row=r + 1, column=3, padx=(5, 15), pady=(0, 15), sticky="ew"
        )
        self.common_widgets[tab_name]["framerate_menu"] = framerate_menu

        # --- Filters Card ---
        filters_card, r_filt = self._create_card(
            main_frame,
            row=2,
            column=0,
            title="HERE ARE SOME ADVANCED FILTERS YOU CAN CHOOSE FROM",
        )
        filters_card.title_label.grid_configure(
            columnspan=5
        )  # Update to span all 5 columns for proper centering

        filters_card.grid_columnconfigure(0, weight=1, uniform="video")
        filters_card.grid_columnconfigure(1, weight=1, uniform="video")
        filters_card.grid_columnconfigure(2, weight=1, uniform="video")
        filters_card.grid_columnconfigure(3, weight=1, uniform="video")
        filters_card.grid_columnconfigure(4, weight=1, uniform="video")

        ar_cb = self._create_toggle_button(
            filters_card, "KEEP ASPECT RATIO", self.video_keep_aspect_ratio
        )
        ar_cb.grid(row=r_filt, column=0, padx=(15, 5), pady=(10, 15), sticky="ew")
        self.common_widgets[tab_name]["ar_cb"] = ar_cb

        di_cb = self._create_toggle_button(
            filters_card, "DEINTERLACE", self.video_deinterlace
        )
        di_cb.grid(row=r_filt, column=1, padx=5, pady=(10, 15), sticky="ew")
        self.common_widgets[tab_name]["di_cb"] = di_cb

        sm_cb = self._create_toggle_button(
            filters_card, "STRIP METADATA", self.video_strip_metadata
        )
        sm_cb.grid(row=r_filt, column=2, padx=5, pady=(10, 15), sticky="ew")
        self.common_widgets[tab_name]["sm_cb"] = sm_cb

        # Remove Audio/Video - Two Separate Buttons with Mutual Exclusion (both on same row)
        ra_cb = self._create_toggle_button(
            filters_card,
            "REMOVE AUDIO",
            self.video_remove_audio,
            command=lambda: (
                self.video_remove_video.set(False)
                if self.video_remove_audio.get()
                else None
            ),
        )
        ra_cb.grid(row=r_filt, column=3, padx=5, pady=(10, 15), sticky="ew")
        self.common_widgets[tab_name]["ra_cb"] = ra_cb

        rv_cb = self._create_toggle_button(
            filters_card,
            "REMOVE VIDEO",
            self.video_remove_video,
            command=lambda: (
                self.video_remove_audio.set(False)
                if self.video_remove_video.get()
                else None
            ),
        )
        rv_cb.grid(row=r_filt, column=4, padx=(5, 15), pady=(10, 15), sticky="ew")
        self.common_widgets[tab_name]["rv_cb"] = rv_cb

        # Convert button and progress bar.
        # Moved to Row 8 (Below Filters)
        action_frame = ctk.CTkFrame(
            main_frame, fg_color=APP_CONFIG["THEME_COLORS"]["card_bg"], corner_radius=10
        )
        action_frame.grid(
            row=8, column=0, columnspan=3, padx=10, pady=(2, 10), sticky="ew"
        )
        action_frame.grid_columnconfigure(0, weight=1)

        self.video_convert_btn = ctk.CTkButton(
            action_frame,
            text="CONVERT",
            command=lambda: self._start_conversion("Video"),
            height=50,
            corner_radius=8,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color=APP_CONFIG["THEME_COLORS"]["btn_green"],
            hover_color=APP_CONFIG["THEME_COLORS"]["btn_green_hover"],
            text_color="white",
        )  # Green for action
        self.video_convert_btn.grid(row=0, column=0, padx=15, pady=(10, 5), sticky="ew")

        self.video_progress_bar = ctk.CTkProgressBar(
            action_frame, orientation="horizontal", height=15, corner_radius=8
        )
        self.video_progress_bar.grid(
            row=1, column=0, padx=15, pady=(5, 10), sticky="ew"
        )
        self.video_progress_bar.set(0)

    # Update Video
    def _update_video_options(self, *args):
        # Adjusts the available quality options (Bitrate vs. CRF) based on the selected mode.
        selected_mode = self.video_quality_mode.get()
        current_value = self.video_quality_value.get()

        options = []
        label_text = "VALUE:"

        if selected_mode == "ORIGINAL (COPY)":
            options = ["(N/A)"]
            label_text = "COPY MODE ACTIVE:"
            self.video_quality_value_menu.configure(state="disabled")
        elif selected_mode == "BITRATE (CBR/VBR AVG)":
            options = VIDEO_QUALITY_PRESETS
            label_text = "TARGET BITRATE:"
            self.video_quality_value_menu.configure(state="normal")
        elif selected_mode == "CRF (CONSTANT QUALITY)":
            options = CRF_OPTIONS
            label_text = "CRF VALUE (LOWER = HIGHER QUALITY):"
            self.video_quality_value_menu.configure(state="normal")

        self.quality_value_label.configure(text=label_text)
        self.video_quality_value_menu.configure(values=options)

        if current_value not in options:
            if selected_mode == "ORIGINAL (COPY)":
                self.video_quality_value.set(options[0])
            elif selected_mode == "CRF (CONSTANT QUALITY)":
                self.video_quality_value.set("23 (GOOD - DEFAULT)")
            elif options:
                self.video_quality_value.set(options[0])
            else:
                self.video_quality_value.set("")

    # Audio Tab
    def _setup_audio_tab(self):
        # Configures the specific widgets for audio conversion options.
        tab_name = "Audio"
        tab = self.audio_tab

        # Create main frame for the tab content
        main_frame = ctk.CTkFrame(
            tab, fg_color=APP_CONFIG["THEME_COLORS"]["card_bg"], corner_radius=10
        )
        main_frame.grid(row=0, column=0, padx=10, pady=5, sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)

        # Create common widgets first
        self._create_common_tab_widgets(tab_name, main_frame)

        # Reorder for audio: output below filters and above convert
        output_card = self.common_widgets[tab_name]["output_card"]
        output_card.grid_configure(row=4, pady=5)

        # --- Audio Settings Card ---
        # Note: We assign self.audio_options_frame to this card so dynamic updates work
        self.audio_options_frame, r = self._create_card(
            main_frame,
            row=2,
            column=0,
            title="HERE ARE THE SETTINGS FOR YOUR DESIRED AUDIO OUTPUT",
        )

        self.audio_options_frame.grid_columnconfigure(0, weight=1, uniform="audio")
        self.audio_options_frame.grid_columnconfigure(1, weight=1, uniform="audio")
        self.audio_options_frame.grid_columnconfigure(2, weight=1, uniform="audio")

        # Option menus for Format, MP3 Mode, and Audio Quality/Sample Rate.
        self.format_label = ctk.CTkLabel(
            self.audio_options_frame,
            text="OUTPUT FORMAT (CODEC):",
            text_color=APP_CONFIG["THEME_COLORS"]["text_primary"],
        )
        self.format_menu = ctk.CTkOptionMenu(
            self.audio_options_frame,
            values=AUDIO_FORMATS,
            variable=self.audio_format,
            command=self._update_audio_options,
        )
        self.common_widgets[tab_name]["format_label"] = self.format_label
        self.common_widgets[tab_name]["format_menu"] = self.format_menu

        self.mp3_mode_label = ctk.CTkLabel(
            self.audio_options_frame,
            text="MP3 MODE (CBR/VBR):",
            text_color=APP_CONFIG["THEME_COLORS"]["text_primary"],
        )
        self.mp3_mode_menu = ctk.CTkOptionMenu(
            self.audio_options_frame,
            values=["CBR", "VBR"],
            variable=self.mp3_mode,
            command=self._update_audio_options,
        )
        self.common_widgets[tab_name]["mp3_mode_label"] = self.mp3_mode_label
        self.common_widgets[tab_name]["mp3_mode_menu"] = self.mp3_mode_menu

        self.audio_quality_label = ctk.CTkLabel(
            self.audio_options_frame,
            text="AUDIO QUALITY:",
            text_color=APP_CONFIG["THEME_COLORS"]["text_primary"],
        )
        self.audio_quality_menu = ctk.CTkOptionMenu(
            self.audio_options_frame,
            values=MP3_CBR_OPTIONS,
            variable=self.audio_quality,
        )
        self.common_widgets[tab_name]["audio_quality_label"] = self.audio_quality_label
        self.common_widgets[tab_name]["audio_quality_menu"] = self.audio_quality_menu

        # --- Filters Card ---
        filters_card, r_filt = self._create_card(
            main_frame,
            row=3,
            column=0,
            title="HERE ARE SOME ADVANCED FILTERS YOU CAN CHOOSE FROM",
        )

        filters_card.grid_columnconfigure(0, weight=1, uniform="audio")
        filters_card.grid_columnconfigure(1, weight=1, uniform="audio")
        filters_card.grid_columnconfigure(2, weight=1, uniform="audio")

        dithering_cb = self._create_toggle_button(
            filters_card, "APPLY DITHERING", self.audio_dithering
        )
        dithering_cb.grid(
            row=r_filt, column=0, padx=(15, 5), pady=(10, 15), sticky="ew"
        )
        self.common_widgets[tab_name]["dithering_cb"] = dithering_cb

        limiter_cb = self._create_toggle_button(
            filters_card, "APPLY PEAK LIMITER", self.audio_limiter
        )
        limiter_cb.grid(row=r_filt, column=1, padx=5, pady=(10, 15), sticky="ew")
        self.common_widgets[tab_name]["limiter_cb"] = limiter_cb

        sm_cb = self._create_toggle_button(
            filters_card, "STRIP METADATA", self.audio_strip_metadata
        )
        sm_cb.grid(row=r_filt, column=2, padx=(5, 15), pady=(10, 15), sticky="ew")
        self.common_widgets[tab_name]["sm_cb"] = sm_cb

        self._update_audio_options(self.audio_format.get())

        # Convert button and progress bar.
        # Convert button and progress bar.
        action_frame = ctk.CTkFrame(
            main_frame, fg_color=APP_CONFIG["THEME_COLORS"]["card_bg"], corner_radius=10
        )
        action_frame.grid(row=5, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
        action_frame.grid_columnconfigure(0, weight=1)

        self.audio_convert_btn = ctk.CTkButton(
            action_frame,
            text="CONVERT",
            command=lambda: self._start_conversion("Audio"),
            height=50,
            corner_radius=8,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color=APP_CONFIG["THEME_COLORS"]["btn_green"],
            hover_color=APP_CONFIG["THEME_COLORS"]["btn_green_hover"],
            text_color="white",
        )
        self.audio_convert_btn.grid(row=0, column=0, padx=15, pady=(10, 5), sticky="ew")

        self.audio_progress_bar = ctk.CTkProgressBar(
            action_frame, orientation="horizontal", height=15, corner_radius=8
        )
        self.audio_progress_bar.grid(
            row=1, column=0, padx=15, pady=(5, 10), sticky="ew"
        )
        self.audio_progress_bar.set(0)

    # Update Audio
    def _update_audio_options(self, *args):
        # Updates the quality options (Bitrate/Sample Rate, CBR/VBR) and layout based on selected format.
        selected_format = self.audio_format.get()
        selected_mode = self.mp3_mode.get()

        # Always show format label and menu in consistent 3-column layout
        self.format_label.configure(
            text="OUTPUT FORMAT (CODEC):",
            text_color=APP_CONFIG["THEME_COLORS"]["text_primary"],
        )
        self.format_label.grid(row=1, column=0, padx=15, pady=(5, 5), sticky="w")

        # Handle MP3 Mode widgets visibility
        if selected_format == "MP3":
            # Show MP3 mode widgets
            self.mp3_mode_label.grid(row=1, column=1, padx=5, pady=(5, 5), sticky="w")
            self.mp3_mode_menu.grid(row=2, column=1, padx=5, pady=(0, 15), sticky="ew")
            # Format menu spans only 1 column when MP3 mode is visible
            self.format_menu.grid(
                row=2, column=0, padx=(15, 5), pady=(0, 15), sticky="ew"
            )

            label_text = (
                "CONSTANT BITRATE (CBR):"
                if selected_mode == "CBR"
                else "VARIABLE QUALITY (VBR):"
            )
            options = MP3_CBR_OPTIONS if selected_mode == "CBR" else MP3_VBR_OPTIONS
        else:
            # Hide MP3 mode widgets
            self.mp3_mode_label.grid_forget()
            self.mp3_mode_menu.grid_forget()
            # Format menu spans 2 columns when MP3 mode is hidden
            self.format_menu.grid(
                row=2, column=0, columnspan=2, padx=(15, 5), pady=(0, 15), sticky="ew"
            )

            if selected_format in AUDIO_SETTINGS:
                settings = AUDIO_SETTINGS[selected_format]
                options = settings["options"]
                label_text = (
                    "SAMPLE RATE:"
                    if settings["type"] == "samplerate"
                    else "AUDIO BITRATE:"
                )
            else:
                options = ["320K", "192K", "128K", "64K"]
                label_text = "AUDIO BITRATE:"

        # Always show quality widgets in column 2
        self.audio_quality_label.configure(
            text=label_text, text_color=APP_CONFIG["THEME_COLORS"]["text_primary"]
        )
        self.audio_quality_label.grid(
            row=1, column=2, padx=(5, 15), pady=(5, 5), sticky="w"
        )
        self.audio_quality_menu.grid(
            row=2, column=2, padx=(5, 15), pady=(0, 15), sticky="ew"
        )

        self.audio_quality_menu.configure(values=options)
        if self.audio_quality.get() not in options:
            self.audio_quality.set(options[0])

    # Image Tab
    def _setup_image_tab(self):
        # Configures the specific widgets for image conversion options.
        # Creates main frame and defers content creation for lazy loading.
        tab_name = "Image"
        tab = self.image_tab

        main_frame = ctk.CTkFrame(
            tab, fg_color=APP_CONFIG["THEME_COLORS"]["card_bg"], corner_radius=10
        )
        main_frame.grid(row=0, column=0, padx=10, pady=5, sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)

        self._setup_image_tab_content(main_frame)

    def _setup_image_tab_content(self, main_frame):
        # Builds image tab content into existing main_frame (for lazy loading)
        tab_name = "Image"
        # main_frame already passed in from _change_tab lazy loading

        # Create common widgets first
        self._create_common_tab_widgets(tab_name, main_frame)

        # Swap output folder and conversion button for image
        output_card = self.common_widgets[tab_name]["output_card"]
        output_card.grid_configure(row=3, pady=5)

        # --- Image Settings Card ---
        settings_card, r = self._create_card(
            main_frame,
            row=1,
            column=0,
            title="HERE ARE THE SETTINGS FOR YOUR DESIRED IMAGE OUTPUT",
        )

        settings_card.grid_columnconfigure(0, weight=1, uniform="image")
        settings_card.grid_columnconfigure(1, weight=1, uniform="image")
        settings_card.grid_columnconfigure(2, weight=1, uniform="image")

        # Option menus for Format, Size, and Visual Filter.
        format_label = ctk.CTkLabel(
            settings_card,
            text="CONVERT TO:",
            text_color=APP_CONFIG["THEME_COLORS"]["text_primary"],
        )
        format_label.grid(row=r, column=0, padx=15, pady=(5, 5), sticky="w")

        size_label = ctk.CTkLabel(
            settings_card,
            text="RESIZE IMAGE:",
            text_color=APP_CONFIG["THEME_COLORS"]["text_primary"],
        )
        size_label.grid(row=r, column=1, padx=5, pady=(5, 5), sticky="w")

        vf_label = ctk.CTkLabel(
            settings_card,
            text="VISUAL FILTER:",
            text_color=APP_CONFIG["THEME_COLORS"]["text_primary"],
        )
        vf_label.grid(row=r, column=2, padx=5, pady=(5, 5), sticky="w")

        format_menu = ctk.CTkOptionMenu(
            settings_card, values=IMAGE_FORMATS, variable=self.image_format
        )
        format_menu.grid(row=r + 1, column=0, padx=(15, 5), pady=(0, 15), sticky="ew")

        self.image_size_menu = ctk.CTkOptionMenu(
            settings_card,
            values=IMAGE_SIZE_PRESETS,
            variable=self.image_size,
            command=self._handle_image_size_change,
        )
        self.image_size_menu.grid(
            row=r + 1, column=1, padx=5, pady=(0, 15), sticky="ew"
        )

        vf_menu = ctk.CTkOptionMenu(
            settings_card, values=IMAGE_FILTERS, variable=self.image_visual_filter
        )

        vf_menu.grid(row=r + 1, column=2, padx=(5, 15), pady=(0, 15), sticky="ew")

        # Store widgets for help bindings
        self.common_widgets[tab_name]["image_format_label"] = format_label
        self.common_widgets[tab_name]["image_format_menu"] = format_menu
        self.common_widgets[tab_name]["image_size_label"] = size_label
        self.common_widgets[tab_name]["image_size_menu"] = self.image_size_menu
        self.common_widgets[tab_name]["vf_label"] = vf_label
        self.common_widgets[tab_name]["vf_menu"] = vf_menu

        # --- Filters Card ---
        filters_card, r_filt = self._create_card(
            main_frame,
            row=2,
            column=0,
            title="HERE ARE SOME ADVANCED FILTERS YOU CAN CHOOSE FROM",
        )

        filters_card.grid_columnconfigure(0, weight=1, uniform="image_filter")
        filters_card.grid_columnconfigure(1, weight=1, uniform="image_filter")
        filters_card.grid_columnconfigure(2, weight=1, uniform="image_filter")

        ar_cb = self._create_toggle_button(
            filters_card, "KEEP ASPECT RATIO", self.image_keep_aspect_ratio
        )
        ar_cb.grid(row=r_filt, column=0, padx=(15, 5), pady=(10, 15), sticky="ew")

        compress_cb = self._create_toggle_button(
            filters_card, "COMPRESS (REDUCE SIZE)", self.image_compress
        )
        compress_cb.grid(row=r_filt, column=1, padx=5, pady=(10, 15), sticky="ew")

        sm_cb = self._create_toggle_button(
            filters_card, "STRIP METADATA", self.image_strip_metadata
        )
        sm_cb.grid(row=r_filt, column=2, padx=(5, 15), pady=(10, 15), sticky="ew")

        # Store toggle buttons for help bindings
        self.common_widgets[tab_name]["ar_cb"] = ar_cb
        self.common_widgets[tab_name]["compress_cb"] = compress_cb
        self.common_widgets[tab_name]["sm_cb"] = sm_cb

        # Convert button and progress bar.
        action_frame = ctk.CTkFrame(
            main_frame, fg_color=APP_CONFIG["THEME_COLORS"]["card_bg"], corner_radius=10
        )
        action_frame.grid(row=4, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
        action_frame.grid_columnconfigure(0, weight=1)

        self.image_convert_btn = ctk.CTkButton(
            action_frame,
            text="CONVERT",
            command=lambda: self._start_conversion("Image"),
            height=50,
            corner_radius=8,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color=APP_CONFIG["THEME_COLORS"]["btn_green"],
            hover_color=APP_CONFIG["THEME_COLORS"]["btn_green_hover"],
            text_color="white",
        )
        self.image_convert_btn.grid(row=0, column=0, padx=15, pady=(10, 5), sticky="ew")

        self.image_progress_bar = ctk.CTkProgressBar(
            action_frame, orientation="horizontal", height=15, corner_radius=8
        )
        self.image_progress_bar.grid(
            row=1, column=0, padx=15, pady=(5, 10), sticky="ew"
        )
        self.image_progress_bar.set(0)

    # Custom Size
    def _handle_image_size_change(self, selected_value: str):
        # Prompts the user for custom WxH dimensions if "Custom (WxH)" is selected.
        self.custom_image_dims = None

        if selected_value == "CUSTOM (WXH)":
            dialog = CustomSizeDialog(self.winfo_toplevel())
            custom_dims = dialog.show()

            if custom_dims:
                W, H = custom_dims
                self.custom_image_dims = (W, H)
                self.common_widgets["Image"]["help_text_label"].configure(
                    text=f"Status: Custom size set to {W}x{H}. Ready."
                )
            else:
                self.image_size.set("ORIGINAL (COPY)")
                self.common_widgets["Image"]["help_text_label"].configure(
                    text="Status: Custom size selection failed or cancelled. Size reset to Original (Copy)."
                )

    # Audio Filters
    def _construct_audio_filters(self) -> str:
        # Builds the complex filter string for FFmpeg audio processing (dithering, limiter).
        filters = []
        is_filtering_active = self.audio_limiter.get() or self.audio_dithering.get()

        if is_filtering_active:
            filters.append("aformat=sample_fmts=fltp")

            if self.audio_limiter.get():
                filters.append(
                    "alimiter=limit=1.0:level=disabled:attack=5:release=50,volume=-1dB"
                )

            if self.audio_dithering.get():
                filters.append("aresample=osf=s16:dither_method=shibata")

        return ",".join(filters)

    # Validate Files
    def _validate_files(
        self, file_paths: List[str], tab_name: str
    ) -> Tuple[List[str], List[str]]:
        # Validates file extensions against allowed formats for the given tab.
        # Returns (valid_files, rejected_files)

        if tab_name == "Video":
            allowed_formats = VIDEO_FORMATS
        elif tab_name == "Audio":
            allowed_formats = AUDIO_FORMATS
        elif tab_name == "Image":
            allowed_formats = IMAGE_FORMATS
        else:
            allowed_formats = VIDEO_FORMATS + AUDIO_FORMATS + IMAGE_FORMATS

        # Convert to lowercase for case-insensitive comparison
        allowed_extensions = {ext.lower() for ext in allowed_formats}

        valid_files = []
        rejected_files = []

        for file_path in file_paths:
            file_ext = Path(file_path).suffix.lower().lstrip(".")
            if file_ext in allowed_extensions:
                valid_files.append(file_path)
            else:
                rejected_files.append(file_path)

        return valid_files, rejected_files

    # File Filters
    def _get_file_dialog_filters(self, mode: str) -> List[Tuple[str, str]]:
        # Builds the list of file type tuples for the file dialog based on the current tab (mode).
        # The format is [('Description', '*.ext1 *.ext2'), ...]
        if mode == "Video":
            format_list = VIDEO_FORMATS
            description = "Video Files"
        elif mode == "Audio":
            format_list = AUDIO_FORMATS
            description = "Audio Files"
        elif mode == "Image":
            format_list = IMAGE_FORMATS
            description = "Image Files"
        else:
            # Fallback for unexpected mode, ensures *.* is present
            return [("All Files", "*.*")]

        filetypes = []

        # 1. "All Supported" Filter (Combined: e.g., "All Supported Video Files (*.mp4 *.mkv)")
        all_supported_extensions = "*." + " *.".join(
            [fmt.lower() for fmt in format_list]
        )
        filetypes.append(
            (
                f"All Supported {description} ({len(format_list)} types)",
                all_supported_extensions,
            )
        )

        # 2. Individual extensions (e.g., "MP4 Files (*.mp4)")
        for fmt in format_list:
            filetypes.append((f"{fmt} Files", f"*.{fmt.lower()}"))

        # 3. "All Files" (Fallback) - Ensures all files are visible if the user needs them
        filetypes.append(("All Files", "*.*"))

        return filetypes

    # Native File
    def _native_file_dialog(self, title, initial_dir, filetypes=None):
        """
        Opens a native OS file dialog using the system's native tools.
        Returns a list of selected file paths, or None if cancelled.
        Returns empty list only if dialog was shown but no files matched.
        """
        import subprocess as sp

        native_tool_used = False  # Track if we successfully launched a native tool

        if os.name == "nt":
            # Windows: Use PowerShell with Windows Forms
            try:
                ps_script = """
                Add-Type -AssemblyName System.Windows.Forms
                $ofd = New-Object System.Windows.Forms.OpenFileDialog
                $ofd.Title = "{title}"
                $ofd.InitialDirectory = "{initial_dir}"
                $ofd.Multiselect = $true
                $ofd.Filter = "{filter}"
                if ($ofd.ShowDialog() -eq "OK") {{
                    $ofd.FileNames -join "|"
                }}
                """.format(
                    title=title.replace('"', '`"'),
                    initial_dir=initial_dir.replace("\\", "\\\\").replace('"', '`"'),
                    filter="All Files (*.*)|*.*"
                    if not filetypes
                    else "|".join(
                        f"{desc} ({patterns})|{patterns}"
                        for desc, patterns in filetypes
                    ),
                )
                result = sp.run(
                    ["powershell", "-Command", ps_script],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                native_tool_used = True
                # If stdout has content, return the files; otherwise return None (cancelled)
                if result.stdout.strip():
                    return result.stdout.strip().split("|")
                return None  # Dialog was cancelled
            except:
                pass

        elif os.uname().sysname == "Darwin":
            # macOS: Use osascript with AppleScript
            try:
                # Build filter string for AppleScript
                filter_str = ""
                if filetypes:
                    extensions = []
                    for desc, patterns in filetypes:
                        for p in patterns.split():
                            ext = p.replace("*.", "")
                            if ext not in extensions:
                                extensions.append(ext)
                    if extensions:
                        ext_quoted = ','.join(f'"{ext}"' for ext in extensions)
                        filter_str = f"of type {{{ext_quoted}}}"

                script = f'''
                set theFiles to choose file with prompt "{title}" default location POSIX file "{initial_dir}" with multiple selections allowed {filter_str}
                set thePaths to {{}}
                repeat with f in theFiles
                    set end of thePaths to POSIX path of f
                end repeat
                return thePaths as string
                '''
                result = sp.run(
                    ["osascript", "-e", script],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                native_tool_used = True
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip().split(", ")
                return None  # Dialog was cancelled
            except:
                pass

        else:
            # Linux: Try zenity first, then kdialog, then qarma
            initial_dir_expanded = os.path.expanduser(initial_dir)

            # Build combined filter pattern from ALL filetypes for Linux dialogs
            combined_filter = ""
            if filetypes:
                extensions = set()
                for desc, patterns in filetypes:
                    for p in patterns.split():
                        ext = p.replace("*.", "").strip()
                        if ext and ext != "*":  # Skip empty or wildcard
                            extensions.add(ext)
                if extensions:
                    combined_filter = " ".join(f"*.{ext}" for ext in sorted(extensions))

            # Try zenity (GTK-based, works on GNOME, XFCE, etc.)
            try:
                cmd = ["zenity", "--file-selection", "--multiple", "--title", title]
                if combined_filter:
                    cmd.append(f"--file-filter={combined_filter}")
                if os.path.isdir(initial_dir_expanded):
                    cmd.append(f"--filename={initial_dir_expanded}/")

                result = sp.run(cmd, capture_output=True, text=True, timeout=300)
                native_tool_used = True
                if result.returncode == 0 and result.stdout.strip():
                    # Zenity returns paths separated by |
                    paths = result.stdout.strip().split("|")
                    return [p for p in paths if os.path.isfile(p)]
                return None  # Dialog was cancelled (returncode != 0)
            except (sp.TimeoutExpired, FileNotFoundError):
                pass

            # Try kdialog (KDE)
            try:
                cmd = [
                    "kdialog",
                    "--title",
                    title,
                    "--getopenfilename",
                    initial_dir_expanded,
                    "--multiple",
                ]
                if combined_filter:
                    cmd.extend(["--multiple", "--filter", combined_filter])
                result = sp.run(cmd, capture_output=True, text=True, timeout=300)
                native_tool_used = True
                if result.returncode == 0 and result.stdout.strip():
                    # Kdialog returns paths separated by newlines
                    paths = result.stdout.strip().split("\n")
                    return [p for p in paths if os.path.isfile(p)]
                return None  # Dialog was cancelled
            except (sp.TimeoutExpired, FileNotFoundError):
                pass

            # Try qarma (GTK zenity alternative)
            try:
                cmd = ["qarma", "--file-selection", "--multiple", "--title", title]
                if combined_filter:
                    cmd.append(f"--file-filter={combined_filter}")
                if os.path.isdir(initial_dir_expanded):
                    cmd.append(f"--filename={initial_dir_expanded}/")
                result = sp.run(cmd, capture_output=True, text=True, timeout=300)
                native_tool_used = True
                if result.returncode == 0 and result.stdout.strip():
                    paths = result.stdout.strip().split("|")
                    return [p for p in paths if os.path.isfile(p)]
                return None  # Dialog was cancelled
            except (sp.TimeoutExpired, FileNotFoundError):
                pass

        # Only fall back to tkinter's built-in dialog if NO native tool was available/launched
        if not native_tool_used:
            return list(
                filedialog.askopenfilenames(
                    parent=self.winfo_toplevel(),
                    title=title,
                    filetypes=filetypes if filetypes else [("All Files", "*.*")],
                    initialdir=initial_dir,
                )
            )

        # If a native tool was used but cancelled, return None
        return None

    # Select Files
    def _select_input_file(self):
        # Opens native OS file dialog to select one or more files, filtered by the active tab's format.
        current_tab = self.current_tab_name

        filetypes = self._get_file_dialog_filters(current_tab)

        # Determine title based on tab
        if current_tab == "Video":
            title = "Select Video Files to Convert"
        elif current_tab == "Audio":
            title = "Select Audio Files to Convert"
        elif current_tab == "Image":
            title = "Select Image Files to Convert"
        else:
            title = "Select Files to Convert"

        file_paths = self._native_file_dialog(
            title=title,
            initial_dir=self.output_dir.get(),
            filetypes=filetypes,
        )

        if file_paths:
            valid_files, rejected_files = self._validate_files(file_paths, current_tab)

            if valid_files:
                # Store actual file paths for conversion
                if current_tab == "Video":
                    self.selected_video_files = valid_files
                elif current_tab == "Audio":
                    self.selected_audio_files = valid_files
                elif current_tab == "Image":
                    self.selected_image_files = valid_files

                # Display only file names (not full paths) with count, single line only
                file_names = [Path(f).name for f in valid_files]
                if len(valid_files) == 1:
                    display_text = f"Selected: {file_names[0]}"
                else:
                    display_text = (
                        f"Selected {len(valid_files)} files: {file_names[0]}..."
                    )

                # Truncate to ensure single line display (max ~80 chars)
                max_len = 80
                if len(display_text) > max_len:
                    display_text = display_text[: max_len - 3] + "..."

                if current_tab == "Video":
                    self.video_input_path.set(display_text)
                elif current_tab == "Audio":
                    self.audio_input_path.set(display_text)
                elif current_tab == "Image":
                    self.image_input_path.set(display_text)

                status_msg = (
                    f"Status: {len(valid_files)} file(s) selected for {current_tab}."
                )
                if rejected_files:
                    rejected_names = [Path(f).name for f in rejected_files]
                    status_msg += f" Rejected {len(rejected_files)} invalid file(s): {', '.join(rejected_names[:3])}{'...' if len(rejected_names) > 3 else ''}."
                status_msg += " Ready."

                self.common_widgets[current_tab]["help_text_label"].configure(
                    text=status_msg
                )
            else:
                rejected_names = [Path(f).name for f in rejected_files]
                status_msg = f"Status: All {len(rejected_files)} selected file(s) are invalid for {current_tab} tab: {', '.join(rejected_names[:3])}{'...' if len(rejected_names) > 3 else ''}."
                self.common_widgets[current_tab]["help_text_label"].configure(
                    text=status_msg
                )
        else:
            self.common_widgets[current_tab]["help_text_label"].configure(
                text="Status: File selection cancelled. Ready."
            )

    # Native Dir
    def _native_directory_dialog(self, title, initial_dir):
        """
        Opens a native OS directory/folder selection dialog using the system's native tools.
        Returns the selected directory path, or None if cancelled.
        """
        import subprocess as sp

        native_tool_used = False

        if os.name == "nt":
            # Windows: Use PowerShell with Windows Forms FolderBrowserDialog
            try:
                ps_script = """
                Add-Type -AssemblyName System.Windows.Forms
                $fbd = New-Object System.Windows.Forms.FolderBrowserDialog
                $fbd.Description = "{title}"
                $fbd.SelectedPath = "{initial_dir}"
                $fbd.ShowNewFolderButton = $true
                if ($fbd.ShowDialog() -eq "OK") {{
                    $fbd.SelectedPath
                }}
                """.format(
                    title=title.replace('"', '`"'),
                    initial_dir=initial_dir.replace("\\", "\\\\").replace('"', '`"'),
                )
                result = sp.run(
                    ["powershell", "-Command", ps_script],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                native_tool_used = True
                if result.stdout.strip():
                    return result.stdout.strip()
                return None
            except:
                pass

        elif os.uname().sysname == "Darwin":
            # macOS: Use osascript with AppleScript
            try:
                script = f'''
                set theFolder to choose folder with prompt "{title}" default location POSIX file "{initial_dir}"
                return POSIX path of theFolder
                '''
                result = sp.run(
                    ["osascript", "-e", script],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                native_tool_used = True
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip()
                return None
            except:
                pass

        else:
            # Linux: Use the same full file manager as file selection, but for directories
            initial_dir_expanded = os.path.expanduser(initial_dir)

            # Try zenity (GTK-based) - use file selection but only accept directories
            try:
                cmd = ["zenity", "--file-selection", "--directory", "--title", title]
                if os.path.isdir(initial_dir_expanded):
                    cmd.append(f"--filename={initial_dir_expanded}/")
                result = sp.run(cmd, capture_output=True, text=True, timeout=300)
                native_tool_used = True
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip()
                return None
            except (sp.TimeoutExpired, FileNotFoundError):
                pass

            # Try kdialog (KDE)
            try:
                cmd = [
                    "kdialog",
                    "--title",
                    title,
                    "--getexistingdirectory",
                    initial_dir_expanded,
                ]
                result = sp.run(cmd, capture_output=True, text=True, timeout=300)
                native_tool_used = True
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip()
                return None
            except (sp.TimeoutExpired, FileNotFoundError):
                pass

            # Try qarma
            try:
                cmd = ["qarma", "--file-selection", "--directory", "--title", title]
                if os.path.isdir(initial_dir_expanded):
                    cmd.append(f"--filename={initial_dir_expanded}/")
                result = sp.run(cmd, capture_output=True, text=True, timeout=300)
                native_tool_used = True
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip()
                return None
            except (sp.TimeoutExpired, FileNotFoundError):
                pass

            # Fallback: Use the same file dialog but filter for directories only
            # This gives the full file manager experience
            try:
                cmd = ["zenity", "--file-selection", "--title", title]
                if os.path.isdir(initial_dir_expanded):
                    cmd.append(f"--filename={initial_dir_expanded}/")
                result = sp.run(cmd, capture_output=True, text=True, timeout=300)
                native_tool_used = True
                if result.returncode == 0 and result.stdout.strip():
                    selected = result.stdout.strip()
                    # Only accept if it's a directory
                    if os.path.isdir(selected):
                        return selected
                    else:
                        # Show error and try again
                        sp.run(
                            [
                                "zenity",
                                "--error",
                                "--text",
                                "Please select a directory, not a file.",
                            ],
                            timeout=10,
                        )
                        return None
                return None
            except (sp.TimeoutExpired, FileNotFoundError):
                pass

        # Only fall back to tkinter if no native tool was available
        if not native_tool_used:
            return filedialog.askdirectory(
                parent=self.winfo_toplevel(),
                title=title,
                initialdir=initial_dir,
            )

        return None

    # Select Output
    def _select_output_directory(self):
        # Opens native OS directory dialog to choose the output folder.
        folder_path = self._native_directory_dialog(
            title="Select Output Folder",
            initial_dir=self.output_dir.get(),
        )
        if folder_path:
            self.output_dir.set(folder_path)
            self.common_widgets[self.current_tab_name]["help_text_label"].configure(
                text=f"Status: Output folder set to '{Path(folder_path).name}'. Ready."
            )
        else:
            self.common_widgets[self.current_tab_name]["help_text_label"].configure(
                text="Status: Output folder selection cancelled. Ready."
            )

    # Open Output
    def _open_output_directory(self):
        # Opens the selected output directory using the OS's default file explorer.
        path = self.output_dir.get()
        if not Path(path).exists():
            try:
                Path(path).mkdir(parents=True, exist_ok=True)
                self.common_widgets[self.current_tab_name]["help_text_label"].configure(
                    text=f"Status: Created missing directory: {path}"
                )
            except Exception as e:
                self.common_widgets[self.current_tab_name]["help_text_label"].configure(
                    text=f"Status: ERROR! Could not create directory: {e}"
                )
                return

        try:
            if os.name == "nt":
                os.startfile(path)
            elif os.uname().sysname == "Darwin":
                subprocess.Popen(["open", path])
            else:
                # Linux: Try xdg-open first, then fallbacks for common file managers
                try:
                    subprocess.Popen(["xdg-open", path])
                except FileNotFoundError:
                    # Fallback if xdg-open is missing (unlikely but possible)
                    file_managers = [
                        "nautilus",
                        "dolphin",
                        "nemo",
                        "thunar",
                        "pcmanfm",
                        "caja",
                    ]
                    found = False
                    for fm in file_managers:
                        try:
                            subprocess.Popen([fm, path])
                            found = True
                            break
                        except FileNotFoundError:
                            continue
                    if not found:
                        self.common_widgets[self.current_tab_name][
                            "help_text_label"
                        ].configure(
                            text=f"Status: ERROR! No file manager found to open {path}"
                        )
                        return
            self.common_widgets[self.current_tab_name]["help_text_label"].configure(
                text=f"Status: Opened output folder: {Path(path).name}"
            )
        except Exception as e:
            self.common_widgets[self.current_tab_name]["help_text_label"].configure(
                text=f"Status: ERROR! Could not open directory: {e}"
            )

    # Video Args
    def _build_video_args(self, cmd: List[str]) -> str:
        # Builds FFmpeg command arguments for video conversion.
        output_format = self.video_format.get()
        quality_mode = self.video_quality_mode.get()
        quality_value_setting = self.video_quality_value.get()

        if self.video_remove_audio.get():
            cmd.append("-an")
        elif self.video_remove_video.get():
            cmd.append("-vn")
            output_format = "wav"
            cmd.extend(["-c:a", "pcm_f32le"])

        video_codec_map = {
            "WEBM": "libvpx-vp9",
            "WMV": "wmv2",
            "ASF": "wmv2",
            "WTV": "wmv3",
            "FLV": "flv",
            "SWF": "flv",
            "MPG": "mpeg1video",
            "MPEG": "mpeg1video",
            "VOB": "mpeg2video",
            "MXF": "mpeg2video",
            "GXF": "mpeg2video",
            "DV": "dvvideo",
            "APNG": "apng",
            "OGG": "libtheora",
            "OGV": "libtheora",
            "IVF": "libvpx",
            "H264": "libx264",
            "H265": "libx265",
            "HEVC": "libx265",
        }

        default_codec = "libx264"
        video_codec = video_codec_map.get(output_format, default_codec)

        if quality_mode == "ORIGINAL (COPY)":
            cmd.extend(["-c:v", "copy"])
            if not self.video_remove_audio.get() and not self.video_remove_video.get():
                cmd.extend(["-c:a", "copy"])
        else:
            cmd.extend(["-c:v", video_codec])

            if quality_mode == "CRF (CONSTANT QUALITY)":
                crf_match = re.search(r"(\d+)", quality_value_setting)
                if crf_match:
                    crf_value = crf_match.group(1)
                    cmd.extend(["-crf", crf_value, "-preset", "medium"])

            elif quality_mode == "BITRATE (CBR/VBR AVG)":
                bitrate_match = re.search(r"\((\d+M)\)", quality_value_setting)
                if bitrate_match:
                    bitrate = bitrate_match.group(1)
                    cmd.extend(["-b:v", bitrate])
                    cmd.extend(["-maxrate", bitrate, "-bufsize", bitrate])

        video_filters = []
        if self.video_deinterlace.get():
            video_filters.append("yadif")

        if self.video_frame_rate.get() != "ORIGINAL (COPY)":
            cmd.extend(["-r", self.video_frame_rate.get()])

        if video_filters:
            if "-c:v" not in cmd or cmd[-1] != "copy":
                cmd.extend(["-vf", ",".join(video_filters)])

        return output_format

    # Audio Args
    def _build_audio_args(self, cmd: List[str]) -> str:
        # Builds FFmpeg command arguments for audio conversion.
        output_format = self.audio_format.get()
        audio_filters = self._construct_audio_filters()

        codec_map = {
            "AAC": "aac",
            "M4A": "aac",
            "OGG": "libvorbis",
            "WMA": "wmav2",
            "OPUS": "libopus",
            "AC3": "ac3",
            "DTS": "dts",
            "EAC3": "eac3",
            "AMR": "libopencore_amrnb",
            "MP2": "mp2",
            "FLAC": "flac",
            "WAV": "pcm_s16le",
            "AIFF": "pcm_s16be",
            "ALAC": "alac",
            "WV": "wavpack",
            "AU": "pcm_s16le",
            "TTA": "trueaudio",
        }

        if audio_filters:
            cmd.extend(["-af", audio_filters])

        if output_format == "MP3":
            cmd.extend(["-c:a", "libmp3lame"])
            if self.mp3_mode.get() == "VBR":
                vbr_setting = self.audio_quality.get().split(" ")[0].replace("V", "")
                cmd.extend(["-q:a", vbr_setting])
            else:
                cmd.extend(["-b:a", self.audio_quality.get()])

        elif output_format in codec_map:
            codec = codec_map[output_format]

            if audio_filters and output_format in ["wav", "flac", "aiff", "alac"]:
                cmd.extend(["-c:a", codec])

            elif "bitrate" in AUDIO_SETTINGS.get(output_format, {}).get(
                "type", "bitrate"
            ):
                cmd.extend(["-c:a", codec])
                cmd.extend(["-b:a", self.audio_quality.get()])

            elif not audio_filters and "samplerate" in AUDIO_SETTINGS.get(
                output_format, {}
            ).get("type", "samplerate"):
                cmd.extend(["-c:a", codec])
                samplerate = self.audio_quality.get().split(" ")[0]
                cmd.extend(["-ar", samplerate])

            elif AUDIO_SETTINGS.get(output_format, {}).get("type") == "compression":
                cmd.extend(["-c:a", codec])
                comp = self.audio_quality.get().split(" ")[0]
                cmd.extend(["-compression_level", comp])

        if audio_filters and "-c:a" not in cmd:
            cmd.extend(["-c:a", "aac"])

        return output_format

    # Image Args
    def _build_image_args(self, cmd: List[str]) -> str:
        # Builds FFmpeg command arguments for image conversion.
        output_format = self.image_format.get()
        image_filters = []

        if self.image_size.get() == "ORIGINAL (COPY)":
            pass

        elif self.image_size.get() == "CUSTOM (WXH)" and self.custom_image_dims:
            W, H = self.custom_image_dims

            if self.image_keep_aspect_ratio.get():
                scale_filter = f"scale={W}:-1"
            else:
                scale_filter = f"scale={W}:{H}"

            image_filters.append(scale_filter)
        elif self.image_size.get() != "ORIGINAL (COPY)":
            size_match = re.match(r"(\d+X\d+)", self.image_size.get())
            if size_match:
                W, H = size_match.group(1).split("X")
                scale_filter = (
                    f"scale={W}:-1"
                    if self.image_keep_aspect_ratio.get()
                    else f"scale={W}:{H}"
                )
                image_filters.append(scale_filter)

        visual_filter = self.image_visual_filter.get()
        if visual_filter == "GRAYSCALE (BLACK & WHITE)":
            image_filters.append("format=gray")
        elif visual_filter == "SHARPEN (BASIC)":
            image_filters.append("unsharp=5:5:0.8:5:5:0.0")
        elif visual_filter == "INVERT COLORS":
            image_filters.append("negate")

        if image_filters:
            cmd.extend(["-vf", ",".join(image_filters)])

        if self.image_compress.get():
            if output_format in ["jpg", "jpeg", "webp", "heic", "heif"]:
                cmd.extend(["-qscale:v", "3"])
            elif output_format == "png":
                cmd.extend(["-compression_level", "9"])
            elif output_format in ["pcx", "sgi", "xwd", "sun"]:
                cmd.extend(["-compression_level", "9"])
            elif output_format == "qoi":
                cmd.extend(["-compression_level", "1"])

        return output_format

    # Start Convert
    def _start_conversion(self, mode: str):
        # Main method to prepare FFmpeg command arguments and launch the conversion process in a thread.

        # Defer FFmpeg check to first conversion attempt (only once)
        if not self.ffmpeg_checked:
            self.ffmpeg_checked = True
            if not (FFMPEG_PATH and Path(FFMPEG_PATH).exists()):
                messagebox.showwarning(
                    "FFmpeg Not Found",
                    "FFmpeg was not found on your system. Conversion features will not work. Please install FFmpeg and restart the application.",
                )
                # Disable convert buttons
                if hasattr(self, 'video_convert_btn') and self.video_convert_btn:
                    self.video_convert_btn.configure(state="disabled")
                if hasattr(self, 'audio_convert_btn') and self.audio_convert_btn:
                    self.audio_convert_btn.configure(state="disabled")
                if hasattr(self, 'image_convert_btn') and self.image_convert_btn:
                    self.image_convert_btn.configure(state="disabled")
                return
            else:
                print(f"FFmpeg found: {FFMPEG_PATH}")

        if (
            self.active_conversion_process
            and self.active_conversion_process.poll() is None
        ):
            self.common_widgets[self.current_tab_name]["help_text_label"].configure(
                text="Status: WARNING! A conversion is already in progress. Please cancel it first."
            )
            return

        # Get actual file paths from stored lists (not from display text)
        if mode == "Video":
            input_paths = self.selected_video_files
        elif mode == "Audio":
            input_paths = self.selected_audio_files
        elif mode == "Image":
            input_paths = self.selected_image_files
        else:
            self.common_widgets[self.current_tab_name]["help_text_label"].configure(
                text="Status: ERROR! Unknown conversion mode."
            )
            return

        output_dir = Path(self.output_dir.get())

        if not input_paths:
            self.common_widgets[self.current_tab_name]["help_text_label"].configure(
                text="Status: ERROR! Please select a valid input file."
            )
            return

        for input_path in input_paths:
            if not os.path.exists(input_path):
                self.common_widgets[self.current_tab_name]["help_text_label"].configure(
                    text=f"Status: ERROR! Input file {Path(input_path).name} not found."
                )
                return

        output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize per-file progress tracking
        self.total_files_to_convert = len(input_paths)
        self.converted_files_count = 0
        self.current_file_index = 0

        for idx, input_path in enumerate(input_paths):
            self.current_file_index = idx
            file_progress_pct = int(((idx + 1) / self.total_files_to_convert) * 100)

            # Get file duration for progress calculation
            total_duration = self._get_file_duration(input_path)

            cmd = [FFMPEG_PATH, "-i", input_path, "-y"]
            output_format = None

            strip_metadata = False
            if mode == "Video" and self.video_strip_metadata.get():
                strip_metadata = True
            elif mode == "Audio" and self.audio_strip_metadata.get():
                strip_metadata = True
            elif mode == "Image" and self.image_strip_metadata.get():
                strip_metadata = True

            if strip_metadata:
                cmd.extend(["-map_metadata", "-1"])

            try:
                if mode == "Video":
                    output_format = self._build_video_args(cmd)
                elif mode == "Audio":
                    output_format = self._build_audio_args(cmd)
                elif mode == "Image":
                    output_format = self._build_image_args(cmd)

                if not output_format:
                    self.common_widgets[self.current_tab_name][
                        "help_text_label"
                    ].configure(
                        text="Status: ERROR! Please select a valid output format."
                    )
                    return

                base_name = Path(input_path).stem
                output_file = output_dir / f"{base_name}_converted.{output_format}"
                cmd.append(str(output_file))

                self._toggle_progress_bar(True)

                # Submit conversion task to executor with file index info
                self.current_future = self.executor.submit(
                    self._execute_ffmpeg,
                    cmd,
                    mode,
                    output_format,
                    output_file,
                    total_duration,
                    idx,
                    self.total_files_to_convert,
                )
                # Start checking the future for completion
                self._check_future_completion()

            except Exception as e:
                self._toggle_progress_bar(False)
                self.active_conversion_process = None
                self.common_widgets[self.current_tab_name]["help_text_label"].configure(
                    text=f"Status: CONVERSION ERROR! {str(e)}"
                )

    # Cancel
    def _cancel_conversion(self):
        # Terminates the running FFmpeg process and updates the UI state.

        if self.current_future and not self.current_future.done():
            self.current_future.cancel()
            self.common_widgets[self.current_tab_name]["help_text_label"].configure(
                text="Status: Cancellation requested..."
            )

        if (
            self.active_conversion_process
            and self.active_conversion_process.poll() is None
        ):
            try:
                self.active_conversion_process.terminate()
            except Exception as e:
                print(f"Error terminating process: {e}")

        # Reset per-file progress counters
        self.converted_files_count = 0
        self.total_files_to_convert = 0

        self._toggle_progress_bar(False)
        self._conversion_complete()
        self.common_widgets[self.current_tab_name]["help_text_label"].configure(
            text="Status: Conversion Cancelled by user."
        )

    # Check Future
    def _check_future_completion(self):
        # Periodically checks if the current Future is done and handles completion.
        if self.current_future and self.current_future.done():
            try:
                # Check for any exceptions that occurred in the worker thread
                self.current_future.result()
            except Exception as e:
                # Handle any unhandled exceptions from the worker thread
                print(f"Conversion error: {e}")
                self.common_widgets[self.current_tab_name]["help_text_label"].configure(
                    text=f"Status: CONVERSION ERROR! {str(e)}"
                )
                self._toggle_progress_bar(False)

            self._conversion_complete()
            self.current_future = None
        else:
            # Schedule next check
            self.after(100, self._check_future_completion)

    # Complete
    def _conversion_complete(self):
        # Resets the active conversion process variable to None upon completion.
        self.active_conversion_process = None

    # Duration
    def _get_file_duration(self, input_path: str) -> Optional[float]:
        # Uses ffprobe to get the duration of the input file in seconds.
        try:
            probe_cmd = [
                FFMPEG_PATH.replace("ffmpeg", "ffprobe")
                if "ffmpeg" in FFMPEG_PATH
                else "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                input_path,
            ]

            result = subprocess.run(
                probe_cmd,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )

            if result.returncode == 0 and result.stdout.strip():
                return float(result.stdout.strip())
            else:
                # For images or files without duration, return None
                return None

        except (subprocess.SubprocessError, ValueError, FileNotFoundError):
            # ffprobe not available or failed
            return None

    # Run FFmpeg
    def _execute_ffmpeg(
        self,
        cmd: List[str],
        mode: str,
        output_format: str,
        output_file: Path,
        total_duration: Optional[float] = None,
        file_index: int = 0,
        total_files: int = 1,
    ):
        # Executes the FFmpeg command with real-time progress monitoring using non-blocking I/O.
        # Calculate progress percentage for this file
        file_start_pct = int((file_index / total_files) * 100)
        file_target_pct = int(((file_index + 1) / total_files) * 100)

        self.after(
            0,
            lambda: self.common_widgets[self.current_tab_name][
                "help_text_label"
            ].configure(
                text=f"Status: Converting file {file_index + 1} of {total_files} ({file_start_pct}%)..."
            ),
        )

        self.active_conversion_process = None

        try:
            process = subprocess.Popen(
                cmd,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except OSError as e:
            error_msg = str(e)
            self.after(
                0,
                lambda: self.common_widgets[self.current_tab_name][
                    "help_text_label"
                ].configure(
                    text=f"Status: ERROR! Failed to start FFmpeg process: {error_msg}"
                ),
            )
            self.after(0, lambda: self._toggle_progress_bar(False))
            self.active_conversion_process = None
            return

        self.active_conversion_process = process

        try:
            # Start progress monitoring in a separate executor task
            progress_future = self.executor.submit(
                self._monitor_conversion_progress, process.stderr, total_duration
            )

            # Wait for the process to complete
            return_code = process.wait()
            self.active_conversion_process = None

            # Cancel progress monitoring if still running
            if not progress_future.done():
                progress_future.cancel()

            self.after(0, lambda: self._toggle_progress_bar(False))

            if return_code == 0:
                # Increment completed files counter
                self.converted_files_count += 1
                completed_pct = int((self.converted_files_count / total_files) * 100)

                # Update progress to milestone
                self.after(
                    0,
                    lambda: self._update_progress_milestone(completed_pct)
                )
                self.after(
                    0,
                    lambda: self.common_widgets[self.current_tab_name][
                        "help_text_label"
                    ].configure(
                        text=f"Status: Completed {self.converted_files_count} of {total_files} files ({completed_pct}%). Output: {output_file.name}"
                    ),
                )
            else:
                # Read any remaining stderr output for error details
                remaining_stderr = process.stderr.read()
                error_message = (
                    remaining_stderr.decode("utf-8", errors="ignore")
                    if remaining_stderr
                    else f"Unknown error (code: {return_code})"
                )

                if return_code in (-15, 1):
                    self.after(
                        0,
                        lambda: self.common_widgets[self.current_tab_name][
                            "help_text_label"
                        ].configure(text="Status: Conversion Cancelled by user."),
                    )
                else:
                    short_error = error_message.replace("\n", " ").strip()
                    display_error = (
                        f"{short_error[:150]}..."
                        if len(short_error) > 150
                        else short_error
                    )
                    self.after(
                        0,
                        lambda: self.common_widgets[self.current_tab_name][
                            "help_text_label"
                        ].configure(text=f"Status: FFmpeg ERROR! {display_error}"),
                    )

        except Exception as e:
            error_msg = str(e)
            self.after(0, lambda: self._toggle_progress_bar(False))
            self.after(
                0,
                lambda: self.common_widgets[self.current_tab_name][
                    "help_text_label"
                ].configure(text=f"Status: UNEXPECTED ERROR! {error_msg}"),
            )
            self.active_conversion_process = None

    # Monitor
    def _monitor_conversion_progress(
        self, stderr_pipe, total_duration: Optional[float] = None
    ):
        # Dedicated method to monitor FFmpeg conversion progress output in real-time
        import re

        try:
            while True:
                line = stderr_pipe.readline()
                if not line:  # EOF reached
                    break

                line_str = line.decode("utf-8", errors="ignore").strip()
                if not line_str:
                    continue

                # Use regex to find and extract the current conversion time
                time_match = re.search(r"time=(\d{2}:\d{2}:\d{2}\.\d{2})", line_str)
                if time_match:
                    time_str = time_match.group(1)
                    print(f"Current conversion time: {time_str}")

                # Also update UI with real-time progress information
                self.after(
                    0,
                    lambda l=line_str, d=total_duration: self._update_progress_status(
                        l, d
                    ),
                )

        except Exception as e:
            print(f"[PROGRESS MONITOR ERROR] {e}")

    def _update_progress_100(self):
        # Helper to force bar to full when done
        if self.current_tab_name == "Video":
            self.video_progress_bar.set(1.0)
        elif self.current_tab_name == "Audio":
            self.audio_progress_bar.set(1.0)
        elif self.current_tab_name == "Image":
            self.image_progress_bar.set(1.0)

    def _update_progress_milestone(self, percentage: int):
        # Helper to set progress bar to a specific milestone percentage (0-100)
        progress = percentage / 100.0
        if self.current_tab_name == "Video":
            self.video_progress_bar.set(progress)
        elif self.current_tab_name == "Audio":
            self.audio_progress_bar.set(progress)
        elif self.current_tab_name == "Image":
            self.image_progress_bar.set(progress)

    # Parse
    def _parse_progress_line(
        self, line: str, total_duration: Optional[float] = None
    ) -> Optional[str]:
        # Parse FFmpeg output line for progress information using regex
        import re

        # Look for time information (e.g., time=00:00:15.50)
        time_match = re.search(r"time=(\d{2}:\d{2}:\d{2}\.\d{2})", line)
        if time_match:
            time_str = time_match.group(1)
            if total_duration:
                # Convert time to seconds and calculate percentage
                h, m, s = time_str.split(":")
                current_seconds = int(h) * 3600 + int(m) * 60 + float(s)
                percentage = min(current_seconds / total_duration, 1.0) * 100
                return f"Time: {time_str} ({percentage:.1f}% complete)"
            else:
                return f"Time: {time_str}"

        # Look for frame information (e.g., frame=1234)
        frame_match = re.search(r"frame=\s*(\d+)", line)
        if frame_match:
            frame_num = frame_match.group(1)
            return f"Frame: {frame_num}"

        # Look for fps information
        fps_match = re.search(r"fps=\s*([\d.]+)", line)
        if fps_match:
            fps = fps_match.group(1)
            return f"FPS: {fps}"

        # Look for bitrate information
        bitrate_match = re.search(r"bitrate=\s*([^s]+)", line)
        if bitrate_match:
            bitrate = bitrate_match.group(1).strip()
            return f"Bitrate: {bitrate}"

        return None

    def _update_progress_status(
        self, progress_line: str, total_duration: Optional[float] = None
    ):
        # Updates the UI with real-time FFmpeg progress information and progress bar.
        # Parse basic progress info from FFmpeg output
        if "time=" in progress_line and total_duration:
            # Extract time information and calculate progress percentage
            time_match = re.search(r"time=(\d{2}:\d{2}:\d{2}\.\d{2})", progress_line)
            if time_match:
                time_str = time_match.group(1)
                # Convert HH:MM:SS.ms to seconds
                h, m, s = time_str.split(":")
                current_seconds = int(h) * 3600 + int(m) * 60 + float(s)

                # Calculate progress percentage
                if total_duration > 0:
                    progress_percentage = min(current_seconds / total_duration, 1.0)
                    # Update progress bar
                    current_tab = self.current_tab_name
                    if current_tab == "Video":
                        self.video_progress_bar.set(progress_percentage)
                    elif current_tab == "Audio":
                        self.audio_progress_bar.set(progress_percentage)
                    elif current_tab == "Image":
                        self.image_progress_bar.set(progress_percentage)

                    # Update status text with percentage
                    percent = int(progress_percentage * 100)
                    self.common_widgets[self.current_tab_name][
                        "help_text_label"
                    ].configure(
                        text=f"Status: Converting... {percent}% complete (Time: {time_str})"
                    )
                else:
                    self.common_widgets[self.current_tab_name][
                        "help_text_label"
                    ].configure(text=f"Status: Converting... Current time: {time_str}")
        elif progress_line.startswith("frame=") or "fps=" in progress_line:
            # Show general progress line when duration is not available
            if not total_duration:
                short_progress = (
                    progress_line[:100] + "..."
                    if len(progress_line) > 100
                    else progress_line
                )
                self.common_widgets[self.current_tab_name]["help_text_label"].configure(
                    text=f"Status: {short_progress}"
                )

    # Button State
    def _update_convert_button_state(
        self, is_converting: bool, convert_btn: ctk.CTkButton, mode: str
    ):
        # Changes the button text, color, and command between CONVERT and CANCEL.
        if is_converting:
            convert_btn.configure(
                text="CANCEL",
                command=self._cancel_conversion,
                fg_color=APP_CONFIG["THEME_COLORS"]["btn_cancel"],
                hover_color=APP_CONFIG["THEME_COLORS"]["btn_cancel_hover"],
                state="normal",
            )
        else:
            convert_btn.configure(
                text="CONVERT",
                command=lambda: self._start_conversion(mode),
                fg_color=APP_CONFIG["THEME_COLORS"]["btn_green"],
                hover_color=APP_CONFIG["THEME_COLORS"]["btn_green_hover"],
                state="normal",
            )

    # Progress Bar
    def _toggle_progress_bar(self, start: bool):
        # Starts/stops the progress bar animation and updates the CONVERT/CANCEL button.
        current_tab = self.current_tab_name
        progress_bar = None
        convert_btn = None

        if current_tab == "Video":
            progress_bar = self.video_progress_bar
            convert_btn = self.video_convert_btn
        elif current_tab == "Audio":
            progress_bar = self.audio_progress_bar
            convert_btn = self.audio_convert_btn
        elif current_tab == "Image":
            progress_bar = self.image_progress_bar
            convert_btn = self.image_convert_btn

        if progress_bar and convert_btn:
            if start:
                self.conversion_counter += 1
                if self.conversion_counter == 1:
                    progress_bar.start()
                    progress_bar.set(0.2)
                    self._update_convert_button_state(True, convert_btn, current_tab)
            else:
                self.conversion_counter -= 1
                if self.conversion_counter == 0:
                    progress_bar.stop()
                    progress_bar.set(0)
                    self._update_convert_button_state(False, convert_btn, current_tab)

    # Bind Help
    def _bind_help_text_for_tab(self, tab_name: str):
        # Binds help text for a specific tab (called on tab initialization)
        # This replaces the old _bind_help_text() which bound all tabs at once

        def set_help_text(tab_key, key):
            self.common_widgets[tab_key]["help_text_label"].configure(
                text=HELP_MESSAGES.get(key, HELP_MESSAGES["default"])
            )

        def bind_widget(tab_key, widget, key):
            try:
                widget.unbind("<Enter>")
                widget.unbind("<Leave>")
            except:
                pass
            widget.bind("<Enter>", lambda _: set_help_text(tab_key, key))
            widget.bind("<Leave>", lambda _: set_help_text(tab_key, "default"))

        if tab_name not in self.common_widgets:
            return

        tab_widgets = self.common_widgets[tab_name]

        # Common widgets for all tabs
        bind_widget(tab_name, tab_widgets["browse_button"], "browse_files")
        bind_widget(tab_name, tab_widgets["input_label"], "browse_files")
        bind_widget(tab_name, tab_widgets["output_entry"], "output_folder")
        bind_widget(tab_name, tab_widgets["change_btn"], "change_folder")
        bind_widget(tab_name, tab_widgets["open_btn"], "open_folder")

        if tab_name == "Video":
            # Convert button
            bind_widget(tab_name, self.video_convert_btn, "convert_btn")
            
            # Format dropdowns
            if "format_label" in tab_widgets:
                bind_widget(tab_name, tab_widgets["format_label"], "video_format")
                bind_widget(tab_name, tab_widgets["format_menu"], "video_format")
            
            # Quality mode
            if "quality_mode_label" in tab_widgets:
                bind_widget(tab_name, tab_widgets["quality_mode_label"], "video_quality_mode")
                bind_widget(tab_name, tab_widgets["quality_mode_menu"], "video_quality_mode")
            
            # Quality value (bitrate/CRF)
            if "quality_value_label" in tab_widgets:
                bind_widget(tab_name, tab_widgets["quality_value_label"], "video_quality_value")
            if hasattr(self, 'video_quality_value_menu'):
                bind_widget(tab_name, self.video_quality_value_menu, "video_quality_value")
            
            # Framerate
            if "framerate_label" in tab_widgets:
                bind_widget(tab_name, tab_widgets["framerate_label"], "video_framerate")
                bind_widget(tab_name, tab_widgets["framerate_menu"], "video_framerate")
            
            # Toggle buttons
            if "ar_cb" in tab_widgets:
                bind_widget(tab_name, tab_widgets["ar_cb"], "keep_aspect_ratio")
            if "di_cb" in tab_widgets:
                bind_widget(tab_name, tab_widgets["di_cb"], "apply_deinterlace")
            if "sm_cb" in tab_widgets:
                bind_widget(tab_name, tab_widgets["sm_cb"], "strip_metadata")
            if "ra_cb" in tab_widgets:
                bind_widget(tab_name, tab_widgets["ra_cb"], "remove_audio")
            if "rv_cb" in tab_widgets:
                bind_widget(tab_name, tab_widgets["rv_cb"], "remove_video")
                
        elif tab_name == "Audio":
            # Convert button
            bind_widget(tab_name, self.audio_convert_btn, "convert_btn")
            
            # Format
            if "format_label" in tab_widgets:
                bind_widget(tab_name, tab_widgets["format_label"], "audio_format")
                bind_widget(tab_name, tab_widgets["format_menu"], "audio_format")
            
            # MP3 Mode (for MP3 format)
            if hasattr(self, 'mp3_mode_label'):
                bind_widget(tab_name, self.mp3_mode_label, "mp3_mode")
            if hasattr(self, 'mp3_mode_menu'):
                bind_widget(tab_name, self.mp3_mode_menu, "mp3_mode")
            
            # Audio Quality
            if hasattr(self, 'audio_quality_label'):
                bind_widget(tab_name, self.audio_quality_label, "audio_quality")
            if hasattr(self, 'audio_quality_menu'):
                bind_widget(tab_name, self.audio_quality_menu, "audio_quality")
            
            # Toggles
            if "dithering_cb" in tab_widgets:
                bind_widget(tab_name, tab_widgets["dithering_cb"], "apply_dithering")
            if "limiter_cb" in tab_widgets:
                bind_widget(tab_name, tab_widgets["limiter_cb"], "apply_limiter")
            if "sm_cb" in tab_widgets:
                bind_widget(tab_name, tab_widgets["sm_cb"], "strip_metadata")
                
        elif tab_name == "Image":
            # Convert button
            bind_widget(tab_name, self.image_convert_btn, "convert_btn")
            
            # Format
            if "image_format_label" in tab_widgets:
                bind_widget(tab_name, tab_widgets["image_format_label"], "image_format")
                bind_widget(tab_name, tab_widgets["image_format_menu"], "image_format")
            
            # Size
            if "image_size_label" in tab_widgets:
                bind_widget(tab_name, tab_widgets["image_size_label"], "image_size")
                bind_widget(tab_name, tab_widgets["image_size_menu"], "image_size")
            
            # Visual filter
            if "vf_label" in tab_widgets:
                bind_widget(tab_name, tab_widgets["vf_label"], "visual_filter")
                bind_widget(tab_name, tab_widgets["vf_menu"], "visual_filter")
            
            # Toggles
            if "ar_cb" in tab_widgets:
                bind_widget(tab_name, tab_widgets["ar_cb"], "image_keep_aspect_ratio")
            if "compress_cb" in tab_widgets:
                bind_widget(tab_name, tab_widgets["compress_cb"], "image_compress")
            if "sm_cb" in tab_widgets:
                bind_widget(tab_name, tab_widgets["sm_cb"], "image_strip_metadata")

        # Add dynamic traces for Video quality mode
        if tab_name == "Video":
            self.video_quality_mode.trace_add(
                "write", lambda *args: self.after(10, self._bind_video_dynamic_options)
            )
            self.after(10, self._bind_video_dynamic_options)
        elif tab_name == "Audio":
            self.audio_format.trace_add(
                "write", lambda *args: self.after(10, self._bind_audio_dynamic_options)
            )
            self.mp3_mode.trace_add(
                "write", lambda *args: self.after(10, self._bind_audio_dynamic_options)
            )
            self.after(10, self._bind_audio_dynamic_options)

    # DnD
    def _setup_drag_and_drop(self):
        """
        Registers drop targets on the entire tab area for all relevant tabs.
        This provides a larger, more intuitive drag-and-drop experience.
        """
        if not TKINTERDND_AVAILABLE:
            return

        for tab_name in ["Audio", "Video", "Image"]:
            # Use the main tab frame as the drop target
            tab_frame = getattr(self, f"{tab_name.lower()}_tab")

            if tab_frame:
                # 1. Register the widget (the entire tab) as a drop target for files
                tab_frame.drop_target_register(DND_FILES)

                # 2. Bind the '<<Drop>>' event to the handler method
                tab_frame.dnd_bind(
                    "<<Drop>>",
                    lambda e, tab=tab_name, widget=tab_frame: [
                        self._handle_drop(e, tab),
                        self._reset_drop_visual(widget),
                    ],
                )

                # 3. Add visual feedback for drag over/enter/leave
                tab_frame.dnd_bind(
                    "<<DragEnter>>",
                    lambda e, widget=tab_frame: self._set_drop_visual(widget),
                )
                tab_frame.dnd_bind(
                    "<<DragLeave>>",
                    lambda e, widget=tab_frame: self._reset_drop_visual(widget),
                )

    def _set_drop_visual(self, widget):
        """Sets a border to visually indicate the widget is a valid drop target."""
        widget.configure(
            border_color=APP_CONFIG["THEME_COLORS"]["green"], border_width=3
        )

    def _reset_drop_visual(self, widget):
        """Removes the border after a drop or drag leave event."""
        # Note: You might need to check your CTkFrame/CTkTabview defaults.
        # Assuming default border_width is 0 or 1. If it's 0, use 0.
        widget.configure(border_color="transparent", border_width=0)

    def _handle_drop(self, event, tab_name: str):
        """
        Handles the '<<Drop>>' event.
        Parses files, validates, and updates the path variable.
        """
        dropped_data = event.data

        # Robustly handle paths, which can be space-separated or enclosed in {}.
        # This regex split is more robust than simple split() for files with spaces in their names.
        if dropped_data.startswith("{") and dropped_data.endswith("}"):
            # This is common for single files with spaces or complex paths
            file_paths = [dropped_data.strip("{}")]
        else:
            # Handle multiple files or simple paths without spaces
            # Use re.findall to handle space separation, possibly enclosed by braces (common TkinterDnD format)
            file_paths = [
                path.strip().strip("{}")
                for path in re.findall(r"\{[^}]+\}|\S+", dropped_data)
            ]

        file_paths = [p for p in file_paths if p]  # Filter out empty strings

        # 1. Validate files
        valid_files, rejected_files = self._validate_files(file_paths, tab_name)

        if not valid_files:
            # Update status if no files were valid
            if file_paths and rejected_files:
                self._update_status(
                    tab_name,
                    f"Status: Dropped file(s) rejected. Only {self.tab_variables[tab_name]['extensions']} supported.",
                    is_error=True,
                )
            else:
                self._update_status(
                    tab_name, "Status: No valid files were dropped.", is_error=True
                )
            return

        # 2. Set files into the appropriate variable
        file_path_str = "; ".join(valid_files)
        input_var = self.tab_variables[tab_name]["input"]
        input_var.set(file_path_str)

        # 3. Update status with success message
        status_msg = f"Status: {len(valid_files)} file(s) dropped successfully. Ready for conversion."
        if rejected_files:
            # Inform user about rejected files
            status_msg += f" ({len(rejected_files)} file(s) rejected due to format.)"

        self._update_status(tab_name, status_msg)

    def _update_status(self, tab_name: str, message: str, is_error: bool = False):
        """
        Updates the status label for the given tab.
        """
        if "help_text_label" in self.common_widgets.get(tab_name, {}):
            self.common_widgets[tab_name]["help_text_label"].configure(text=message)

    # Bind Video
    def _bind_video_dynamic_options(self, *args):
        # Binds help text to the changing Video Quality Value label and menu.

        def unbind_widget(widget):
            try:
                widget.unbind("<Enter>")
                widget.unbind("<Leave>")
            except:
                pass

        def bind_widget(widget, key):
            widget.bind("<Enter>", lambda _: self._update_help_text("Video", key))
            widget.bind("<Leave>", lambda _: self._update_help_text("Video", "default"))

        unbind_widget(self.quality_value_label)
        unbind_widget(self.video_quality_value_menu)

        selected_mode = self.video_quality_mode.get()
        if selected_mode == "BITRATE (CBR/VBR AVG)":
            bind_widget(self.quality_value_label, "video_bitrate")
            bind_widget(self.video_quality_value_menu, "video_bitrate")
        elif selected_mode == "CRF (CONSTANT QUALITY)":
            bind_widget(self.quality_value_label, "video_crf_value")
            bind_widget(self.video_quality_value_menu, "video_crf_value")

    # Bind Audio
    def _bind_audio_dynamic_options(self, *args):
        # Binds help text to the Audio Quality/MP3 Mode options, which change dynamically.

        def unbind_widget(widget):
            try:
                widget.unbind("<Enter>")
                widget.unbind("<Leave>")
            except:
                pass

        def bind_widget(widget, key):
            widget.bind("<Enter>", lambda _: self._update_help_text("Audio", key))
            widget.bind("<Leave>", lambda _: self._update_help_text("Audio", "default"))

        unbind_widget(self.mp3_mode_label)
        unbind_widget(self.mp3_mode_menu)
        unbind_widget(self.audio_quality_label)
        unbind_widget(self.audio_quality_menu)

        if self.audio_format.get() == "MP3":
            bind_widget(self.mp3_mode_label, "mp3_mode")
            bind_widget(self.mp3_mode_menu, "mp3_mode")
            bind_widget(self.audio_quality_label, "audio_quality")
            bind_widget(self.audio_quality_menu, "audio_quality")
        else:
            bind_widget(self.audio_quality_label, "audio_quality")
            bind_widget(self.audio_quality_menu, "audio_quality")

    # Theme
    def _setup_theme_toggler(self):
        # Creates the Light/Dark mode toggler buttons centered in the top header
        self.theme_toggler_frame = ctk.CTkFrame(
            self.top_header, fg_color=APP_CONFIG["THEME_COLORS"]["transparent"]
        )
        # Center the frame within the top header
        self.theme_toggler_frame.grid(row=0, column=0, padx=0, pady=0)

        self.btn_light = ctk.CTkButton(
            self.theme_toggler_frame,
            text="LIGHT",
            command=lambda: self._set_theme("Light"),
            width=80,
            height=28,
            fg_color=APP_CONFIG["THEME_COLORS"]["transparent"],
            text_color="white",
            hover_color=APP_CONFIG["THEME_COLORS"]["btn_inactive"],
            font=ctk.CTkFont(size=12, weight="bold"),
        )

        self.btn_dark = ctk.CTkButton(
            self.theme_toggler_frame,
            text="DARK",
            command=lambda: self._set_theme("Dark"),
            width=80,
            height=28,
            fg_color=APP_CONFIG["THEME_COLORS"][
                "transparent"
            ],  # Initially transparent or active depending on default
            text_color=APP_CONFIG["THEME_COLORS"]["text_primary"],
            hover_color=APP_CONFIG["THEME_COLORS"]["btn_inactive"],
            font=ctk.CTkFont(size=12, weight="bold"),
        )

        self.btn_dark.grid(row=0, column=0, padx=2, pady=(10, 0))
        self.btn_light.grid(row=0, column=1, padx=2, pady=(10, 0))

        # Set default state (Dark)
        self._set_theme("Dark", initial=True)

        # Bind help text to theme buttons
        self.btn_light.bind(
            "<Enter>",
            lambda _: self._update_help_text(self.current_tab_name, "light_theme"),
        )
        self.btn_light.bind(
            "<Leave>",
            lambda _: self._update_help_text(self.current_tab_name, "default"),
        )
        self.btn_dark.bind(
            "<Enter>",
            lambda _: self._update_help_text(self.current_tab_name, "dark_theme"),
        )
        self.btn_dark.bind(
            "<Leave>",
            lambda _: self._update_help_text(self.current_tab_name, "default"),
        )

    def _set_theme(self, mode: str, initial: bool = False):
        # Switches the interface theme and updates toggler button states
        ctk.set_appearance_mode(mode)

        if mode == "Light":
            self.btn_light.configure(
                text_color=APP_CONFIG["THEME_COLORS"]["text_primary"],
                fg_color=APP_CONFIG["THEME_COLORS"]["btn_inactive"],
            )
            self.btn_dark.configure(
                text_color=APP_CONFIG["THEME_COLORS"]["text_secondary"],
                fg_color=APP_CONFIG["THEME_COLORS"]["transparent"],
            )
        else:
            self.btn_light.configure(
                text_color=APP_CONFIG["THEME_COLORS"]["text_secondary"],
                fg_color=APP_CONFIG["THEME_COLORS"]["transparent"],
            )
            self.btn_dark.configure(
                text_color=APP_CONFIG["THEME_COLORS"]["text_primary"],
                fg_color=APP_CONFIG["THEME_COLORS"]["btn_inactive"],
            )

    # Exit
    def _on_closing(self):
        # Safely terminates any active FFmpeg conversion process before closing the application.
        if (
            self.active_conversion_process
            and self.active_conversion_process.poll() is None
        ):
            try:
                self.active_conversion_process.kill()
                self.active_conversion_process = None
            except Exception:
                pass

        # Shutdown the ThreadPoolExecutor
        if hasattr(self, "executor"):
            self.executor.shutdown(wait=False)

        # Destroy the root window to close the application
        self.winfo_toplevel().destroy()

    def _setup_tray_icon(self):
        """Setup system tray icon using subprocess to avoid signal issues."""
        try:
            import subprocess
            import os
            import sys
            
            # Find icon - check multiple locations
            possible_paths = [
                "/usr/share/ffconverter/ffconverter.png",
                "/usr/share/icons/hicolor/256x256/apps/ffconverter.png",
                str(CURRENT_DIR / "ffconverter.png"),
                str(CURRENT_DIR / "resources" / "images" / "LOGO_256.png"),
            ]
            
            icon_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    icon_path = path
                    break
            
            if not icon_path:
                print("Warning: Could not find icon file for tray")
                return
            
            # Create a separate script for tray icon
            tray_script = f'''#!/usr/bin/env python3
import sys
import os
from PIL import Image
import pystray
import threading

def show_window(icon, item):
    # Signal parent to show window
    with open("/tmp/ffconverter_tray_show", "w") as f:
        f.write("1")

def quit_app(icon, item):
    # Signal parent to quit
    with open("/tmp/ffconverter_tray_quit", "w") as f:
        f.write("1")
    icon.stop()

icon_path = "{icon_path}"
icon_image = Image.open(icon_path)
icon_image = icon_image.resize((64, 64), Image.LANCZOS)

menu = pystray.Menu(
    pystray.MenuItem("Show", show_window, default=True),
    pystray.MenuItem("Quit", quit_app)
)

tray = pystray.Icon("FFConverter", icon_image, "FFConverter", menu)
tray.run()
'''
            
            # Write tray script to temp file
            script_path = "/tmp/ffconverter_tray.py"
            with open(script_path, "w") as f:
                f.write(tray_script)
            
            # Start tray in subprocess
            self.tray_process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            
            # Start monitoring thread
            self.tray_monitor_thread = threading.Thread(target=self._monitor_tray, daemon=True)
            self.tray_monitor_thread.start()
            
            print("System tray icon initialized (subprocess)")
        except Exception as e:
            print(f"Warning: Failed to setup tray icon: {e}")

    def _monitor_tray(self):
        """Monitor tray icon for show/quit signals."""
        import time
        import os
        
        while True:
            time.sleep(0.5)
            if os.path.exists("/tmp/ffconverter_tray_show"):
                os.remove("/tmp/ffconverter_tray_show")
                self.after(0, self.deiconify)
                self.after(0, self.lift)
            if os.path.exists("/tmp/ffconverter_tray_quit"):
                os.remove("/tmp/ffconverter_tray_quit")
                self._quit_from_tray()
                break

    def _show_from_tray(self, icon=None, item=None):
        """Show the main window from tray."""
        self.after(0, self.deiconify)
        self.after(0, self.lift)
        # Stop the tray icon when showing
        if hasattr(self, 'tray_icon'):
            try:
                self.tray_icon.stop()
            except Exception:
                pass

    def _quit_from_tray(self, icon=None, item=None):
        """Quit the application from tray."""
        if hasattr(self, 'tray_icon'):
            try:
                self.tray_icon.stop()
            except Exception:
                pass
        self._on_closing()

    def _on_closing(self):
        """Handle window close - minimize to tray instead of quitting."""
        if hasattr(self, 'tray_icon'):
            self.withdraw()  # Hide the window instead of closing
        else:
            # Fallback to original behavior if tray not available
            self._cleanup_and_exit()


if __name__ == "__main__":
    # Creates the main window and starts the event loop.
    app = FFConverterApp()

    # Bind the cleanup method to the window closing protocol
    app.protocol("WM_DELETE_WINDOW", app._on_closing)

    app.mainloop()
