#!/bin/bash
# check_menubar.sh
# A simple script to verify if a SwiftUI macOS app has defined Menu Bar commands.
# Apple HIG strongly recommends that all major actions are available in the Menu Bar.

TARGET_DIR=${1:-.}

echo "Scanning $TARGET_DIR for Menu Bar configurations..."

# Check for .commands { ... } modifier
COMMANDS_FOUND=$(grep -rnw "$TARGET_DIR" -e "\.commands")
COMMAND_MENU_FOUND=$(grep -rnw "$TARGET_DIR" -e "CommandMenu")

if [ -z "$COMMANDS_FOUND" ] && [ -z "$COMMAND_MENU_FOUND" ]; then
    echo "[FAIL] No .commands or CommandMenu found. macOS apps should provide comprehensive Menu Bar items."
    exit 1
else
    echo "[PASS] Menu Bar configurations found."
    exit 0
fi
