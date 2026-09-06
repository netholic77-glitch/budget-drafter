#!/bin/bash
# Prepares the remote container for the `watch` skill (/watch), which needs
# yt-dlp for downloads + native captions and ffmpeg/ffprobe for frame extraction.
# Local machines get these from the skill's own installer, so this only runs in
# Claude Code on the web.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

need_apt=0
for bin in ffmpeg ffprobe; do
  command -v "$bin" >/dev/null 2>&1 || need_apt=1
done

if [ "$need_apt" = "1" ]; then
  export DEBIAN_FRONTEND=noninteractive
  # The base image ships a stale package index, so a plain install 404s on the
  # pinned .deb versions. Refresh first; third-party PPAs are blocked by the
  # egress policy and their failures are not fatal here.
  apt-get update -qq || true
  apt-get install -y -qq ffmpeg
fi

if ! command -v yt-dlp >/dev/null 2>&1; then
  pip3 install --quiet --upgrade yt-dlp
fi

# Scaffold the watch skill's config so its preflight passes without prompting.
# Whisper keys stay unset on purpose: native captions cover the common case, and
# no key should be baked into a repo-tracked script.
config_dir="${HOME}/.config/watch"
config_file="${config_dir}/.env"
if [ ! -f "$config_file" ]; then
  mkdir -p "$config_dir"
  {
    echo "# watch skill config - https://github.com/bradautomates/claude-video"
    echo "# Set one of these to enable the Whisper fallback for caption-less videos:"
    echo "# GROQ_API_KEY="
    echo "# OPENAI_API_KEY="
    echo "WATCH_DETAIL=balanced"
    echo "SETUP_COMPLETE=true"
  } > "$config_file"
  chmod 600 "$config_file"
fi

echo "watch skill deps ready: yt-dlp $(yt-dlp --version), $(ffmpeg -version | head -1 | cut -d' ' -f1-3)"
