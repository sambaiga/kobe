#!/usr/bin/env bash
# Link every skill in this folder into ~/.claude/skills, so edits here are live everywhere.
# A skill that already exists there as a real folder is left alone: move it away first.
set -euo pipefail

source_dir="$(cd "$(dirname "$0")" && pwd)"
target_dir="${HOME}/.claude/skills"
mkdir -p "${target_dir}"

for skill in "${source_dir}"/*/; do
  name="$(basename "${skill}")"
  link="${target_dir}/${name}"
  if [ -L "${link}" ]; then
    ln -sfn "${skill%/}" "${link}"
    echo "relinked ${name}"
  elif [ -e "${link}" ]; then
    echo "skipped ${name}: ${link} exists and is not a link (move it, then run this again)" >&2
  else
    ln -s "${skill%/}" "${link}"
    echo "linked ${name}"
  fi
done
