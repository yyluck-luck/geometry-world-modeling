#!/bin/zsh
set -e
export PATH='/Users/rocket/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin':"$PATH"
export DSH_HOME='/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/tools/deepseek-harness/state'
cd '/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/tools/deepseek-harness/runtime'
exec npx @deepseek-ai/dsh web
