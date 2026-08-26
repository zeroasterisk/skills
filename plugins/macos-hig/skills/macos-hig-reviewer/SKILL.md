---
name: macos-hig-reviewer
description: "A comprehensive macOS Human Interface Guidelines code and design reviewer. Analyzes macOS application code and design for HIG compliance."
license: Apache-2.0
metadata:
  version: "1.1.0"
---

# macOS HIG: Compliance Reviewer

This skill orchestrates a complete review of a macOS application (design, layout, and code) to ensure it strictly follows Apple's Human Interface Guidelines.

## Review Categories

### 1. Ergonomics & Density
- Is the information density appropriate for a user viewing the screen from 1-3 feet away?
- Does it avoid making users strain to read text or click targets?

### 2. Window Behavior
- Can the main application window be resized, maximized, and hidden appropriately?
- Is full-screen mode supported and implemented without visual glitches?
- Are multiple window states (active vs. inactive) handled gracefully?

### 3. System Integration
- Is there a comprehensive Menu Bar implementation? (Every action should be available in the menu bar).
- Does the app provide a Dock menu for quick contextual actions?
- Does it use standard file dialogs instead of custom ones?

### 4. Input & Accessibility
- Are high-precision pointer inputs utilized?
- Are keyboard shortcuts prevalent and idiomatic (e.g., `Cmd+W` to close window, `Cmd+Q` to quit)?
- Can the app be navigated entirely by keyboard?

## Tools & Linters

### SwiftLint
This skill can utilize SwiftLint to enforce macOS-specific coding guidelines. 
- **Obtaining SwiftLint:** If SwiftLint is not installed on the system, you can easily install it using Homebrew:
  ```bash
  brew install swiftlint
  ```
- **Configuration:** A customized `swiftlint.yml` tailored for macOS applications and idiomatic Swift is provided in the `assets/` directory.

## Instructions
When invoked to review a codebase or design:
1. Systematically analyze the provided code against the four categories above.
2. Flag any custom UI components that reinvent standard macOS controls (e.g., custom scrollbars or window control buttons) as violations unless explicitly justified by the app's nature (e.g., a game).
3. If SwiftLint is available (or after helping the user install it), run it using the provided `assets/swiftlint.yml` to catch stylistic or structural issues.
4. Run `scripts/check_menubar.sh` to quickly verify if the project has Menu Bar definitions.
5. Generate a structured report highlighting PASS, WARNING, and FAIL items.
6. Provide actionable code or design recommendations to fix any WARNING or FAIL items.
