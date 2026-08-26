---
name: macos-hig-layout
description: "Guidelines and assistance for creating macOS applications compliant with Apple's Human Interface Guidelines regarding Layout, Window Management, and Displays."
license: Apache-2.0
metadata:
  version: "1.0.0"
---

# macOS HIG: Layout & Window Management

This skill provides expert guidance for macOS app design and development focusing on displays, ergonomics, and window behavior.

## Core Principles
1. **Displays**: macOS apps run on large, high-resolution displays. Connect multiple displays seamlessly.
2. **Ergonomics**: Viewers sit 1 to 3 feet away. Maintain a comfortable information density. Avoid straining the user's eyes.
3. **App Interactions**: Users frequently have multiple apps open. Ensure smooth transitions between active and inactive states.

## Best Practices
- **Leverage Large Displays**: Present more content in fewer nested levels with less need for modality.
- **Window Management**: Let people resize, hide, show, and move your windows to fit their work style and device configuration.
- **Full-Screen Mode**: Support full-screen mode to offer a distraction-free context.
- **Personalization**: Let people customize toolbars and configure windows to display the views they use most.

## Instructions
When assisting a user with macOS UI/UX:
- ALWAYS check if the proposed layout forces unnecessary modality instead of using available screen space.
- Review window resize constraints: verify that minimum and maximum window sizes are reasonable.
- Ensure the application properly handles active vs. inactive window states visually (e.g., dimming inactive elements).
