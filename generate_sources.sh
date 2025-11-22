#!/bin/bash
echo "  - name: python-dependencies"
echo "    buildsystem: simple"
echo "    build-commands:"
echo "      - pip3 install --prefix=/app --no-cache-dir --no-build-isolation --no-index --find-links=\"file://\${PWD}\" -r requirements.txt"
echo "    sources:"
echo "      - type: file"
echo "        path: requirements.txt"
for wheel in packages/*.whl; do
  echo "      - type: file"
  echo "        path: $wheel"
done
