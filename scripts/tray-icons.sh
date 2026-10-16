#!/bin/sh
# Rasterise the tray glyphs written by scripts/logo.py: the tray takes PNG.
# 44 px is the macOS menu bar's 22 pt at 2x; 64 px leaves Windows and Linux
# room to scale down. Needs ImageMagick with librsvg. Run from the root.
set -eu
cd launcher/src-tauri/tray
magick -background none -density 600 tray-black.svg -resize 44x44 PNG32:tray-template.png
magick -background none -density 600 tray-white.svg -resize 64x64 PNG32:tray-white.png
magick -background none -density 600 tray-black.svg -resize 64x64 PNG32:tray-black.png
