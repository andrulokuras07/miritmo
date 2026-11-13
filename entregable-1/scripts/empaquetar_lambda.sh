#!/usr/bin/env bash
# Genera build/miritmo-lambda.zip listo para subir a AWS Lambda (Python 3.12, x86_64).
set -euo pipefail
cd "$(dirname "$0")/.."

rm -rf build
mkdir -p build/paquete

# Dependencias para Linux (el sistema operativo de Lambda), aunque empaquetes desde Mac o Windows.
python3 -m pip install -r backend/requirements.txt -t build/paquete --quiet \
  --platform manylinux2014_x86_64 --implementation cp --python-version 3.12 --only-binary=:all:

cp backend/lambda_function.py build/paquete/
cp -r backend/miritmo build/paquete/
find build/paquete -name "__pycache__" -type d -prune -exec rm -rf {} +

(cd build/paquete && zip -qr ../miritmo-lambda.zip .)
echo "Listo: build/miritmo-lambda.zip ($(du -h build/miritmo-lambda.zip | cut -f1))"
