#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

usage() {
  cat <<'EOF'
Usage:
  HF_TOKEN=xxx scripts/bash/upload_hf_qcow2.sh <repo_id> <qcow2_path> [path_in_repo]

Example:
  HF_TOKEN=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 scripts/bash/upload_hf_qcow2.sh \
    Wenkaiwang/ubuntu-qcow2 \
    docker_vm_data/new_env/Ubuntu.qcow2 \
    Ubuntu.qcow2

Notes:
  - The repo type defaults to model. Override with HF_REPO_TYPE=dataset if needed.
  - This script uploads the file directly with `hf upload` and does not split the file.
  - Requires `hf` CLI and `git-lfs` to be installed.
EOF
}

if [[ $# -lt 2 || $# -gt 3 ]]; then
  usage
  exit 1
fi

if ! command -v hf >/dev/null 2>&1; then
  echo "Error: \\`hf\\` CLI not found." >&2
  exit 1
fi

if ! command -v git-lfs >/dev/null 2>&1; then
  echo "Error: \\`git-lfs\\` not found." >&2
  exit 1
fi

REPO_ID="$1"
LOCAL_PATH="$2"
PATH_IN_REPO="${3:-$(basename "$LOCAL_PATH")}"
REPO_TYPE="${HF_REPO_TYPE:-model}"
HF_TOKEN_VALUE="${HF_TOKEN:-${HUGGINGFACE_HUB_TOKEN:-}}"
COMMIT_MESSAGE="${HF_COMMIT_MESSAGE:-Add $(basename "$PATH_IN_REPO")}"

if [[ -z "$HF_TOKEN_VALUE" ]]; then
  echo "Error: set HF_TOKEN or HUGGINGFACE_HUB_TOKEN first." >&2
  exit 1
fi

if [[ ! -f "$LOCAL_PATH" ]]; then
  echo "Error: file not found: $LOCAL_PATH" >&2
  exit 1
fi

FILE_SIZE_HUMAN="$(ls -lh "$LOCAL_PATH" | awk '{print $5}')"

echo "Repo: $REPO_ID"
echo "Repo type: $REPO_TYPE"
echo "Source file: $LOCAL_PATH"
echo "Target path: $PATH_IN_REPO"
echo "File size: $FILE_SIZE_HUMAN"

git lfs install >/dev/null

hf repo create "$REPO_ID" \
  --repo-type "$REPO_TYPE" \
  --exist-ok \
  --token "$HF_TOKEN_VALUE"

hf upload "$REPO_ID" "$LOCAL_PATH" "$PATH_IN_REPO" \
  --repo-type "$REPO_TYPE" \
  --token "$HF_TOKEN_VALUE" \
  --commit-message "$COMMIT_MESSAGE"

echo "Upload finished: https://huggingface.co/$REPO_ID"
