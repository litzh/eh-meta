#!/bin/bash
# 构建两个 calibre 插件 zip（zip 根目录必须直接包含 __init__.py）
set -euo pipefail
cd "$(dirname "$0")"

mkdir -p dist

for plugin in EHentaiComicInfo EHentaiImport; do
    out="dist/${plugin}.zip"
    rm -f "$out"
    (cd "$plugin" && zip -r -X "../$out" . \
        -x '__pycache__/*' -x '*.pyc' -x '.DS_Store')
    echo "built: $out"
done
