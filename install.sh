#!/usr/bin/env bash
# Backstage Essentials Toolkit installer for macOS and Linux.
#
# Run directly:
#   curl -fsSL https://raw.githubusercontent.com/backstageessentials/backstage-essentials-toolkit/main/install.sh | bash
#
# Or after cloning:
#   bash install.sh
#
# The script is idempotent. Running it again on a configured machine updates
# the toolkit and re-verifies prerequisites without breaking anything.

set -u
set -o pipefail

REPO_URL="https://github.com/backstageessentials/backstage-essentials-toolkit.git"
INSTALL_PARENT="${BES_INSTALL_PARENT:-$HOME/Code}"
INSTALL_DIR="$INSTALL_PARENT/backstage-essentials-toolkit"
MIN_PY_MAJOR=3
MIN_PY_MINOR=10

# ---- output helpers --------------------------------------------------------

if [ -t 1 ]; then
  C_BOLD=$(printf '\033[1m')
  C_DIM=$(printf '\033[2m')
  C_RED=$(printf '\033[31m')
  C_GREEN=$(printf '\033[32m')
  C_YELLOW=$(printf '\033[33m')
  C_BLUE=$(printf '\033[34m')
  C_RESET=$(printf '\033[0m')
else
  C_BOLD="" C_DIM="" C_RED="" C_GREEN="" C_YELLOW="" C_BLUE="" C_RESET=""
fi

step()    { printf "\n${C_BOLD}${C_BLUE}==>${C_RESET} ${C_BOLD}%s${C_RESET}\n" "$1"; }
ok()      { printf "    ${C_GREEN}OK${C_RESET}     %s\n" "$1"; }
info()    { printf "    ${C_DIM}info${C_RESET}   %s\n" "$1"; }
warn()    { printf "    ${C_YELLOW}warn${C_RESET}   %s\n" "$1"; }
fail()    { printf "    ${C_RED}error${C_RESET}  %s\n" "$1"; }
abort()   { fail "$1"; printf "\n${C_RED}Installation stopped.${C_RESET} Fix the issue above and re-run.\n" >&2; exit 1; }

# ---- OS detection ----------------------------------------------------------

detect_os() {
  case "$(uname -s)" in
    Darwin)
      OS="macos"
      case "$(uname -m)" in
        arm64) ARCH="apple-silicon" ;;
        x86_64) ARCH="intel" ;;
        *) ARCH="unknown" ;;
      esac
      ;;
    Linux)
      OS="linux"
      ARCH="$(uname -m)"
      ;;
    *)
      abort "Unsupported OS: $(uname -s). This installer supports macOS and Linux. For Windows, use install.ps1."
      ;;
  esac
}

# ---- prerequisite checks ---------------------------------------------------

# Returns 0 if "$1" >= MIN_PY_*, 1 otherwise. "$1" is a python executable.
python_version_ok() {
  local py="$1"
  "$py" - "$MIN_PY_MAJOR" "$MIN_PY_MINOR" <<'PY' >/dev/null 2>&1
import sys
major = int(sys.argv[1]); minor = int(sys.argv[2])
sys.exit(0 if sys.version_info >= (major, minor) else 1)
PY
}

find_python() {
  for candidate in python3.13 python3.12 python3.11 python3.10 python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then
      if python_version_ok "$candidate"; then
        PYTHON_BIN="$(command -v "$candidate")"
        return 0
      fi
    fi
  done
  return 1
}

require_python() {
  if find_python; then
    local v
    v=$("$PYTHON_BIN" -c 'import sys; print("{}.{}.{}".format(*sys.version_info[:3]))')
    ok "Python $v at $PYTHON_BIN"
    return 0
  fi
  fail "Python ${MIN_PY_MAJOR}.${MIN_PY_MINOR}+ not found."
  if [ "$OS" = "macos" ]; then
    info "Install Python 3.12 with Homebrew:  brew install python@3.12"
    info "Or download the official installer:  https://www.python.org/downloads/macos/"
  else
    info "On Debian/Ubuntu:                  sudo apt install python3 python3-pip python3-venv"
    info "On Fedora/RHEL:                    sudo dnf install python3 python3-pip"
    info "Or download from:                  https://www.python.org/downloads/"
  fi
  abort "Install Python and re-run this script."
}

require_command() {
  local cmd="$1" hint_macos="$2" hint_linux="$3"
  if command -v "$cmd" >/dev/null 2>&1; then
    ok "$cmd at $(command -v "$cmd")"
    return 0
  fi
  fail "$cmd not found."
  if [ "$OS" = "macos" ]; then
    info "$hint_macos"
  else
    info "$hint_linux"
  fi
  abort "Install $cmd and re-run this script."
}

require_claude_code() {
  if command -v claude >/dev/null 2>&1; then
    local v
    v=$(claude --version 2>/dev/null | head -1)
    ok "Claude Code: $v"
    return 0
  fi
  fail "Claude Code (the 'claude' CLI) is not installed."
  info "The toolkit drives Claude Code to author lessons, quizzes, and diagrams."
  info "Install it before continuing:"
  info "  npm install -g @anthropic-ai/claude-code"
  info "Or follow Anthropic's instructions:  https://docs.anthropic.com/en/docs/claude-code"
  abort "Install Claude Code and re-run this script."
}

# ---- pip install (PEP 668 aware) ------------------------------------------

run_pip_install() {
  local target="$1"
  cd "$target" || abort "Could not cd into $target"

  if "$PYTHON_BIN" -m pip install -e . 2>&1 | tee /tmp/bes_pip.log; then
    return 0
  fi

  if grep -q "externally-managed-environment" /tmp/bes_pip.log 2>/dev/null; then
    warn "Python flagged this environment as externally-managed (PEP 668)."
    info "Retrying with --user (does not require sudo, isolates from system Python)..."
    if "$PYTHON_BIN" -m pip install --user -e . 2>&1 | tee /tmp/bes_pip.log; then
      USED_USER_INSTALL=1
      return 0
    fi
    warn "User install also failed. Retrying with --break-system-packages as a last resort..."
    if "$PYTHON_BIN" -m pip install --break-system-packages -e . 2>&1 | tee /tmp/bes_pip.log; then
      return 0
    fi
  fi
  return 1
}

# ---- main ------------------------------------------------------------------

main() {
  printf "${C_BOLD}Backstage Essentials Toolkit installer${C_RESET}\n"
  printf "${C_DIM}https://github.com/backstageessentials/backstage-essentials-toolkit${C_RESET}\n"

  step "1/6  Detecting OS"
  detect_os
  ok "$OS ($ARCH)"

  step "2/6  Checking prerequisites"
  require_python
  require_command git \
    "brew install git  (or use the Xcode Command Line Tools: xcode-select --install)" \
    "sudo apt install git   # Debian/Ubuntu     |   sudo dnf install git   # Fedora/RHEL"
  require_command curl \
    "Already part of macOS. If missing, run: brew install curl" \
    "sudo apt install curl   |   sudo dnf install curl"
  require_command npm \
    "Install Node.js: brew install node   (or download: https://nodejs.org)" \
    "sudo apt install nodejs npm   |   https://nodejs.org/en/download/package-manager"
  require_claude_code

  step "3/6  Preparing install directory"
  if [ ! -d "$INSTALL_PARENT" ]; then
    mkdir -p "$INSTALL_PARENT" || abort "Could not create $INSTALL_PARENT"
    ok "Created $INSTALL_PARENT"
  else
    ok "$INSTALL_PARENT exists"
  fi

  step "4/6  Cloning or updating toolkit"
  if [ -d "$INSTALL_DIR/.git" ]; then
    info "Existing checkout found at $INSTALL_DIR. Pulling latest..."
    if git -C "$INSTALL_DIR" pull --ff-only 2>&1 | sed 's/^/        /'; then
      ok "Updated $INSTALL_DIR"
    else
      warn "git pull did not fast-forward. Leaving the checkout as-is."
      info "If you have local changes, commit or stash them and re-run this script."
    fi
  elif [ -d "$INSTALL_DIR" ]; then
    abort "$INSTALL_DIR exists but is not a git checkout. Move or remove it and re-run."
  else
    if git clone "$REPO_URL" "$INSTALL_DIR" 2>&1 | sed 's/^/        /'; then
      ok "Cloned to $INSTALL_DIR"
    else
      abort "git clone failed. Check your network connection and that $REPO_URL is reachable."
    fi
  fi

  step "5/6  Installing the bes CLI (pip install -e .)"
  USED_USER_INSTALL=0
  if run_pip_install "$INSTALL_DIR"; then
    ok "Installed editable package"
  else
    fail "pip install failed. Last 20 lines of output:"
    tail -20 /tmp/bes_pip.log 2>/dev/null | sed 's/^/        /' || true
    info "Common fixes:"
    info "  - Re-run with: $PYTHON_BIN -m pip install --upgrade pip   then re-run this script."
    info "  - On Linux, install python3-venv and python3-pip system packages."
    info "  - Check /tmp/bes_pip.log for the full error."
    abort "Could not install the bes CLI."
  fi

  step "6/6  Verifying installation"
  if command -v bes >/dev/null 2>&1; then
    ok "$(bes --version)"
  elif [ "$USED_USER_INSTALL" = "1" ]; then
    local user_base
    user_base=$("$PYTHON_BIN" -m site --user-base 2>/dev/null)
    fail "bes installed but is not on your PATH."
    info "Add this to your shell profile (~/.zshrc, ~/.bash_profile, or ~/.profile):"
    info "  export PATH=\"$user_base/bin:\$PATH\""
    info "Then open a new terminal window."
    exit 2
  else
    fail "bes installed but the shell cannot find it. Open a new terminal window and run: bes --version"
    exit 2
  fi

  printf "\n${C_GREEN}${C_BOLD}Done.${C_RESET} Toolkit is ready at ${C_BOLD}%s${C_RESET}\n\n" "$INSTALL_DIR"
  printf "${C_BOLD}Next step — start your first course:${C_RESET}\n\n"
  printf "    cd %s\n" "$INSTALL_PARENT"
  printf "    bes new-course\n\n"
  printf "${C_DIM}Then open the new course folder in Claude Code and follow the prompts.${C_RESET}\n"
}

main "$@"
