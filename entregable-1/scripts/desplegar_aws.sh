#!/usr/bin/env bash
# Despliega MiRitmo en la nube con un solo comando:
#   Cloudant (bases) -> IAM (rol) -> S3 (bucket privado) -> CloudFront (HTTPS) -> Lambda (API) -> interfaz.
# Se puede correr varias veces: crea lo que falte y actualiza lo demás.
#
# Requisitos: AWS CLI v2 con sesión iniciada (`aws login` o `aws configure`)
#             y el archivo ../despliegue.env con las credenciales de Cloudant.
# Uso:        scripts/desplegar_aws.sh
set -euo pipefail
cd "$(dirname "$0")/.."

CONFIG="$(cd .. && pwd)/despliegue.env"
if [ ! -f "$CONFIG" ]; then
  echo "Falta $CONFIG. Copia despliegue.env.ejemplo como despliegue.env y llénalo." >&2
  exit 1
fi
set -a
# shellcheck disable=SC1090
source "$CONFIG"
set +a
: "${CLOUDANT_URL:?Falta CLOUDANT_URL en despliegue.env}"
: "${CLOUDANT_APIKEY:?Falta CLOUDANT_APIKEY en despliegue.env}"

export AWS_REGION="${AWS_REGION:-us-east-2}" AWS_PAGER=""
FUNCION="${FUNCION:-miritmo-api}"
ROL="${ROL:-miritmo-lambda-rol}"
CUENTA=$(aws sts get-caller-identity --query Account --output text)
BUCKET="${BUCKET:-miritmo-web-$CUENTA}"
mkdir -p build

# Secreto de los tokens: se genera una vez y se guarda en despliegue.env (no cambia entre despliegues).
if [ -z "${TOKEN_SECRET:-}" ]; then
  TOKEN_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(48))")
  printf '\nTOKEN_SECRET=%s\n' "$TOKEN_SECRET" >> "$CONFIG"
fi
export TOKEN_SECRET

echo "== Cuenta AWS $CUENTA, región $AWS_REGION"

# ------------------------------------------------------------------ Cloudant
echo "== IBM Cloudant"
python3 scripts/crear_bases_cloudant.py

# ----------------------------------------------------------------------- IAM
echo "== Rol IAM"
if [ -n "${LAMBDA_ROLE_ARN:-}" ]; then
  ROL_ARN="$LAMBDA_ROLE_ARN"
  echo "  Usando rol existente $ROL_ARN"
elif ROL_ARN=$(aws iam get-role --role-name "$ROL" --query Role.Arn --output text 2>/dev/null); then
  echo "  Rol $ROL ya existía."
else
  ROL_ARN=$(aws iam create-role --role-name "$ROL" --query Role.Arn --output text \
    --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}')
  # Permisos mínimos: solo escribir logs en CloudWatch.
  aws iam attach-role-policy --role-name "$ROL" \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
  echo "  Rol $ROL creado."
fi

# ------------------------------------------------------------------------ S3
echo "== Bucket S3 $BUCKET"
if aws s3api head-bucket --bucket "$BUCKET" 2>/dev/null; then
  echo "  Ya existía."
else
  if [ "$AWS_REGION" = "us-east-1" ]; then
    aws s3api create-bucket --bucket "$BUCKET" >/dev/null
  else
    aws s3api create-bucket --bucket "$BUCKET" --create-bucket-configuration LocationConstraint="$AWS_REGION" >/dev/null
  fi
  echo "  Creado."
fi
aws s3api put-public-access-block --bucket "$BUCKET" --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

# ---------------------------------------------------------------- CloudFront
echo "== CloudFront"
COMENTARIO="MiRitmo $BUCKET"
DIST_ID=$(aws cloudfront list-distributions --query "DistributionList.Items[?Comment=='$COMENTARIO'].Id | [0]" --output text)
if [ -z "$DIST_ID" ] || [ "$DIST_ID" = "None" ]; then
  OAC_NOMBRE="miritmo-oac-$CUENTA"
  OAC_ID=$(aws cloudfront list-origin-access-controls --query "OriginAccessControlList.Items[?Name=='$OAC_NOMBRE'].Id | [0]" --output text)
  if [ -z "$OAC_ID" ] || [ "$OAC_ID" = "None" ]; then
    OAC_ID=$(aws cloudfront create-origin-access-control --query OriginAccessControl.Id --output text \
      --origin-access-control-config "Name=$OAC_NOMBRE,SigningProtocol=sigv4,SigningBehavior=always,OriginAccessControlOriginType=s3")
  fi
  cat > build/cloudfront.json <<EOF
{
  "CallerReference": "miritmo-$(date +%s)",
  "Comment": "$COMENTARIO",
  "Enabled": true,
  "DefaultRootObject": "index.html",
  "PriceClass": "PriceClass_100",
  "HttpVersion": "http2and3",
  "Origins": {
    "Quantity": 1,
    "Items": [{
      "Id": "s3-miritmo",
      "DomainName": "$BUCKET.s3.$AWS_REGION.amazonaws.com",
      "OriginAccessControlId": "$OAC_ID",
      "S3OriginConfig": { "OriginAccessIdentity": "" }
    }]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "s3-miritmo",
    "ViewerProtocolPolicy": "redirect-to-https",
    "CachePolicyId": "658327ea-f89d-4fab-a63d-7e88639e58f6",
    "Compress": true,
    "AllowedMethods": {
      "Quantity": 2, "Items": ["GET", "HEAD"],
      "CachedMethods": { "Quantity": 2, "Items": ["GET", "HEAD"] }
    }
  }
}
EOF
  DIST_ID=$(aws cloudfront create-distribution --distribution-config file://build/cloudfront.json --query Distribution.Id --output text)
  echo "  Distribución $DIST_ID creada (tarda unos minutos en activarse)."
else
  echo "  Distribución $DIST_ID ya existía."
fi
DOMINIO=$(aws cloudfront get-distribution --id "$DIST_ID" --query Distribution.DomainName --output text)

# Solo CloudFront (esta distribución) puede leer el bucket.
cat > build/politica-bucket.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "SoloCloudFront",
    "Effect": "Allow",
    "Principal": { "Service": "cloudfront.amazonaws.com" },
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::$BUCKET/*",
    "Condition": { "StringEquals": { "AWS:SourceArn": "arn:aws:cloudfront::$CUENTA:distribution/$DIST_ID" } }
  }]
}
EOF
aws s3api put-bucket-policy --bucket "$BUCKET" --policy file://build/politica-bucket.json

# -------------------------------------------------------------------- Lambda
echo "== Lambda $FUNCION"
scripts/empaquetar_lambda.sh
export ALLOWED_ORIGIN="https://$DOMINIO"
# Variables de entorno en un archivo temporal (no en la línea de comandos).
umask 077
python3 -c 'import json, os; print(json.dumps({"Variables": {k: os.environ[k] for k in ("CLOUDANT_URL", "CLOUDANT_APIKEY", "TOKEN_SECRET", "ALLOWED_ORIGIN")}}))' > build/entorno.json
umask 022

if aws lambda get-function --function-name "$FUNCION" >/dev/null 2>&1; then
  aws lambda update-function-code --function-name "$FUNCION" --zip-file fileb://build/miritmo-lambda.zip >/dev/null
  aws lambda wait function-updated-v2 --function-name "$FUNCION"
  aws lambda update-function-configuration --function-name "$FUNCION" --environment file://build/entorno.json \
    --timeout 10 --memory-size 256 >/dev/null
  aws lambda wait function-updated-v2 --function-name "$FUNCION"
  echo "  Código y configuración actualizados."
else
  # Un rol recién creado tarda unos segundos en estar disponible para Lambda.
  for intento in 1 2 3 4 5 6; do
    if aws lambda create-function --function-name "$FUNCION" --runtime python3.12 --architectures x86_64 \
        --handler lambda_function.lambda_handler --role "$ROL_ARN" --timeout 10 --memory-size 256 \
        --zip-file fileb://build/miritmo-lambda.zip --environment file://build/entorno.json >/dev/null 2>build/error-lambda.txt; then
      break
    fi
    if [ "$intento" = 6 ]; then cat build/error-lambda.txt >&2; exit 1; fi
    echo "  Esperando a que el rol esté listo..."
    sleep 10
  done
  aws lambda wait function-active-v2 --function-name "$FUNCION"
  echo "  Función creada."
fi
rm -f build/entorno.json build/error-lambda.txt

# URL de función pública (la seguridad la da el token; CORS lo maneja el código).
if ! API_URL=$(aws lambda get-function-url-config --function-name "$FUNCION" --query FunctionUrl --output text 2>/dev/null); then
  API_URL=$(aws lambda create-function-url-config --function-name "$FUNCION" --auth-type NONE --query FunctionUrl --output text)
fi
POLITICA=$(aws lambda get-policy --function-name "$FUNCION" --query Policy --output text 2>/dev/null || echo "")
if [[ "$POLITICA" != *'"Sid":"url-publica"'* ]]; then
  aws lambda add-permission --function-name "$FUNCION" --statement-id url-publica \
    --action lambda:InvokeFunctionUrl --principal "*" --function-url-auth-type NONE >/dev/null
fi
if [[ "$POLITICA" != *'"Sid":"url-publica-invocar"'* ]]; then
  aws lambda add-permission --function-name "$FUNCION" --statement-id url-publica-invocar \
    --action lambda:InvokeFunction --principal "*" --invoked-via-function-url >/dev/null
fi
API_URL="${API_URL%/}"

# ------------------------------------------------------------------- interfaz
echo "== Interfaz"
scripts/publicar_frontend.sh "$BUCKET" "$DIST_ID" "$API_URL"

cat <<EOF

Listo.
  Aplicación: https://$DOMINIO
  API:        $API_URL
  Logs:       CloudWatch -> /aws/lambda/$FUNCION
Si la distribución es nueva, espera de 5 a 10 minutos antes de abrir la aplicación.
EOF
