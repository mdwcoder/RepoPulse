#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
REQ_FILE="$ROOT_DIR/requirements.txt"
APP_NAME="repopulse"

color() {
  local code="$1"
  shift
  printf "\033[%sm%s\033[0m\n" "$code" "$*"
}

info() {
  color "36" "[RepoPulse] $*"
}

success() {
  color "32" "[RepoPulse] $*"
}

warn() {
  color "33" "[RepoPulse] $*"
}

fail() {
  color "31" "[RepoPulse] $*"
  exit 1
}

detect_platform() {
  case "$(uname -s)" in
    Linux) echo "linux" ;;
    Darwin) echo "macos" ;;
    *)
      fail "Unsupported OS. RepoPulse supports macOS and Linux."
      ;;
  esac
}

find_python() {
  local candidates=("python3.12" "python3.11" "python3")
  for candidate in "${candidates[@]}"; do
    if command -v "$candidate" >/dev/null 2>&1; then
      echo "$candidate"
      return 0
    fi
  done
  return 1
}

check_python_version() {
  local python_bin="$1"
  "$python_bin" - <<'PY'
import sys
if sys.version_info < (3, 11):
    raise SystemExit(1)
PY
}

install_launcher() {
  local launcher_dir=""
  local target_dir="$HOME/.local/bin"

  mkdir -p "$target_dir"
  launcher_dir="$target_dir"

  if [[ ! -w "$launcher_dir" ]]; then
    target_dir="$HOME/bin"
    mkdir -p "$target_dir"
    launcher_dir="$target_dir"
  fi

  local launcher_path="$launcher_dir/$APP_NAME"
  cat >"$launcher_path" <<EOF
#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$ROOT_DIR"
VENV_PYTHON="\$ROOT_DIR/.venv/bin/python"
exec "\$VENV_PYTHON" "\$ROOT_DIR/main.py" "\$@"
EOF
  chmod +x "$launcher_path"
  success "Launcher installed at $launcher_path"

  case ":$PATH:" in
    *":$launcher_dir:"*) ;;
    *)
      warn "Your PATH does not include $launcher_dir"
      warn "Add it manually to run '$APP_NAME' from any terminal."
      ;;
  esac
}

main() {
  local platform
  local python_bin

  platform="$(detect_platform)"
  info "Platform detected: $platform"

  python_bin="$(find_python)" || fail "Python 3.11+ was not found."
  check_python_version "$python_bin" || fail "Python 3.11+ is required."
  info "Using Python: $("$python_bin" --version 2>&1)"

  if [[ ! -d "$VENV_DIR" ]]; then
    info "Creating virtual environment at $VENV_DIR"
    "$python_bin" -m venv "$VENV_DIR"
  else
    info "Reusing existing virtual environment at $VENV_DIR"
  fi

  # shellcheck disable=SC1091
  source "$VENV_DIR/bin/activate"

  info "Upgrading pip"
  python -m pip install --upgrade pip

  info "Installing dependencies from $REQ_FILE"
  python -m pip install -r "$REQ_FILE"

  install_launcher

  success "Initialization complete."
  info "Run the app with:"
  printf "  %s\n" "$APP_NAME"
  printf "  %s\n" "./run.sh"
}

main "$@"
