#!/usr/bin/env bash
# Sube la interfaz al bucket S3 e invalida la caché de CloudFront (requiere AWS CLI configurado).
#
# Uso: scripts/publicar_frontend.sh <bucket> <id-distribucion-cloudfront> <url-funcion-lambda>
# Ej.: scripts/publicar_frontend.sh miritmo-web E1ABCDEF2GHIJ https://abc123.lambda-url.us-east-2.on.aws
set -euo pipefail
cd "$(dirname "$0")/.."

if [ $# -ne 3 ]; then
  echo "Uso: $0 <bucket> <id-distribucion-cloudfront> <url-funcion-lambda>" >&2
  exit 1
fi
BUCKET="$1"; DISTRIBUCION="$2"; API_URL="${3%/}"

rm -rf build/web
mkdir -p build/web
cp -r frontend/. build/web/
cat > build/web/js/config.js <<EOF
// Generado por scripts/publicar_frontend.sh
window.MIRITMO_CONFIG = {
  apiUrl: "${API_URL}",
};
EOF

aws s3 sync build/web "s3://${BUCKET}" --delete
aws cloudfront create-invalidation --distribution-id "${DISTRIBUCION}" --paths "/*" --query "Invalidation.Id" --output text
echo "Interfaz publicada. La invalidación de CloudFront tarda 1 a 2 minutos."
