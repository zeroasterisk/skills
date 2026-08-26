#!/usr/bin/env bash
# ANSI Color Double-Border Banner Header Generator
# Wrapper around scripts/banner.py with fallback to standalone bash cases

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STEP="${1:-0}"

if [ -f "$DIR/banner.py" ]; then
  case "$STEP" in
    0)
      python3 "$DIR/banner.py" "DEMO TITLE • INTERACTIVE EXPLAINER WALKTHROUGH" "Sub-headline describing what this scenario or capability demonstrates" --align center --color cyan
      ;;
    1)
      python3 "$DIR/banner.py" --step 1 "Capability Discovery & Search" "Agent queries repository and registry for capabilities"
      ;;
    2)
      python3 "$DIR/banner.py" --step 2 "Installation & Setup" "Configures runtime environment and validates dependencies"
      ;;
    3)
      python3 "$DIR/banner.py" --step 3 "Execution & Verification" "Runs the autonomous task and verifies output correctness"
      ;;
    *)
      TITLE="${2:-Step Title}"
      SUBTITLE="${3:-Step subtitle explaining the action}"
      python3 "$DIR/banner.py" --step "$STEP" "$TITLE" "$SUBTITLE"
      ;;
  esac
  exit 0
fi

# Fallback bash implementation if python is unavailable
case "$STEP" in
  0)
    echo -e "\033[1;36m╔══════════════════════════════════════════════════════════════════════════════════════════════════════════════╗\033[0m"
    echo -e "\033[1;36m║\033[0m            \033[1;37mDEMO TITLE • INTERACTIVE EXPLAINER WALKTHROUGH\033[0m                                                    \033[1;36m║\033[0m"
    echo -e "\033[1;36m║\033[0m       \033[0;33mSub-headline describing what this scenario or capability demonstrates\033[0m                                 \033[1;36m║\033[0m"
    echo -e "\033[1;36m╚══════════════════════════════════════════════════════════════════════════════════════════════════════════════╝\033[0m"
    ;;
  1)
    echo -e "\033[1;32m╔══════════════════════════════════════════════════════════════════════════════════════════════════════════════╗\033[0m"
    echo -e "\033[1;32m║\033[0m  \033[1;37mSTEP 1: Capability Discovery & Search\033[0m                                                               \033[1;32m║\033[0m"
    echo -e "\033[1;32m║\033[0m  \033[0;33mAgent queries repository and registry for capabilities\033[0m                                                \033[1;32m║\033[0m"
    echo -e "\033[1;32m╚══════════════════════════════════════════════════════════════════════════════════════════════════════════════╝\033[0m"
    ;;
  2)
    echo -e "\033[1;34m╔══════════════════════════════════════════════════════════════════════════════════════════════════════════════╗\033[0m"
    echo -e "\033[1;34m║\033[0m  \033[1;37mSTEP 2: Installation & Setup\033[0m                                                                        \033[1;34m║\033[0m"
    echo -e "\033[1;34m║\033[0m  \033[0;33mConfigures runtime environment and validates dependencies\033[0m                                             \033[1;34m║\033[0m"
    echo -e "\033[1;34m╚══════════════════════════════════════════════════════════════════════════════════════════════════════════════╝\033[0m"
    ;;
  3)
    echo -e "\033[1;35m╔══════════════════════════════════════════════════════════════════════════════════════════════════════════════╗\033[0m"
    echo -e "\033[1;35m║\033[0m  \033[1;37mSTEP 3: Execution & Verification\033[0m                                                                    \033[1;35m║\033[0m"
    echo -e "\033[1;35m║\033[0m  \033[0;33mRuns the autonomous task and verifies output correctness\033[0m                                              \033[1;35m║\033[0m"
    echo -e "\033[1;35m╚══════════════════════════════════════════════════════════════════════════════════════════════════════════════╝\033[0m"
    ;;
esac
