---
name: macos-hig-interaction
description: "Guidelines and assistance for creating macOS applications compliant with Apple's Human Interface Guidelines regarding Input, Interaction, and System Features."
license: Apache-2.0
metadata:
  version: "1.0.0"
---

# macOS HIG: Interaction & System Features

This skill provides expert guidance for macOS app design and development focusing on user inputs (keyboard, pointer) and integrating with core system features like the Menu Bar and Dock.

## Core Principles
1. **Inputs**: Users expect to enter data and control the interface using any combination of input modes (Physical Keyboards, Pointing devices, Game controls, Siri).
2. **High-Precision Input**: Help people take advantage of high-precision input modes to perform pixel-perfect selections and edits.
3. **Keyboard Centricity**: Handle keyboard shortcuts to help people accelerate actions and use keyboard-only work styles.

## System Features
macOS provides features that help people interact with the system in familiar ways:
- **The Menu Bar**: Give people easy access to all the commands they need to do things in your app. It should be comprehensive.
- **File Management**: Use standard file dialogs and management paradigms.
- **Dock Menus**: Provide a contextual menu in the Dock for quick access to key app actions.

## Instructions
When assisting a user with macOS inputs and interactions:
- Verify that all major application features are accessible via the Menu Bar.
- Ensure keyboard shortcuts (`Cmd`, `Option`, `Shift`, `Ctrl`) follow standard macOS conventions (e.g., `Cmd+C` to copy, `Cmd+Preferences` mapping to `Cmd+,`).
- Review interactions to ensure they do not rely solely on hover states, as touch or keyboard-only navigation must also be supported.
