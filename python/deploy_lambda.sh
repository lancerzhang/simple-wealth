#!/usr/bin/env bash
set -euo pipefail

PYTHON_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${PYTHON_DIR}/.." && pwd)"

# Hard-coded defaults for this project
REGION="ap-southeast-1"
FUNCTION_NAME="wealth-scraper"
RUNTIME="python3.11"
HANDLER="scripts/wealth_scraper.lambda_handler"
TIMEOUT="60"
MEMORY="256"
RULE_NAME="${FUNCTION_NAME}-daily"
# 08:00 SGT (UTC+8) == 00:00 UTC
SCHEDULE_EXPRESSION="cron(0 0 * * ? *)"
ROLE_NAME="wealth-scraper-role"
ROLE_POLICY_NAME="wealth-scraper-s3"
BUCKET="simple-wealth-cn"
PREFIX="data"
S3_REGION="$REGION"

ZIP_DIR="${ROOT_DIR}/dist"
ZIP_PATH="${ZIP_DIR}/wealth-scraper.zip"
BUILD_DIR="${ZIP_DIR}/lambda_build"
PYTHON_BIN="${PYTHON_BIN:-python3}"
# Default skip pip to avoid network dependency; set SKIP_PIP_INSTALL=0 if you want vendored deps
SKIP_PIP_INSTALL="${SKIP_PIP_INSTALL:-1}"
mkdir -p "$ZIP_DIR"

FRONTEND_DIR="${ROOT_DIR}/frontend"

if ! command -v aws >/dev/null 2>&1; then
  echo "aws CLI not found. Install AWS CLI v2 first." >&2
  exit 1
fi

if ! command -v zip >/dev/null 2>&1; then
  echo "zip not found. Install zip first." >&2
  exit 1
fi

cd "$PYTHON_DIR"
rm -f "$ZIP_PATH"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/data" "$BUILD_DIR/scripts"

if [[ "$SKIP_PIP_INSTALL" != "1" ]] && grep -Eqv '^\s*(#|$)' requirements.txt; then
  "$PYTHON_BIN" -m pip install -r requirements.txt -t "$BUILD_DIR" >/dev/null
fi

cp -R wealth_scraper "$BUILD_DIR/"
cp data/wealth_links.txt "$BUILD_DIR/data/wealth_links.txt"
cp data/fund_links.txt "$BUILD_DIR/data/fund_links.txt"
cp requirements.txt "$BUILD_DIR/requirements.txt"
cp scripts/wealth_scraper.py "$BUILD_DIR/scripts/wealth_scraper.py"

cd "$BUILD_DIR"
zip -r "$ZIP_PATH" . -x "**/__pycache__/*" "**/*.pyc" "**/.DS_Store" >/dev/null
cd "$PYTHON_DIR"

# Build frontend (always rebuild)
cd "$FRONTEND_DIR"
if [[ -f package-lock.json ]]; then
  npm ci >/dev/null
else
  npm install >/dev/null
fi
npm run build >/dev/null
cd "$PYTHON_DIR"

BUCKET="${S3_BUCKET:-simple-wealth-cn}"
PREFIX="${S3_PREFIX:-data}"

ensure_role() {
  local role_name="$1"
  if ! aws iam get-role --role-name "$role_name" >/dev/null 2>&1; then
    local TRUST_DOC='{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}'
    aws iam create-role --role-name "$role_name" --assume-role-policy-document "$TRUST_DOC" >/dev/null
    echo "Created IAM role $role_name"
  fi
}

attach_managed_basic() {
  if ! aws iam list-attached-role-policies --role-name "$ROLE_NAME" --query "AttachedPolicies[?PolicyArn=='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole']" --output text | grep -q AWSLambdaBasicExecutionRole; then
    aws iam attach-role-policy --role-name "$ROLE_NAME" --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole >/dev/null
  fi
}

ensure_inline_s3() {
  local policy_doc
  policy_doc=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:PutObjectAcl"],
      "Resource": [
        "arn:aws:s3:::$BUCKET/$PREFIX/*",
        "arn:aws:s3:::$BUCKET/*",
        "arn:aws:s3:::$BUCKET"
      ]
    }
  ]
}
EOF
)
  aws iam put-role-policy --role-name "$ROLE_NAME" --policy-name "$ROLE_POLICY_NAME" --policy-document "$policy_doc" >/dev/null
}

wait_ready() {
  local name="$1"
  aws lambda wait function-updated --function-name "$name" --region "$REGION" >/dev/null 2>&1 || true
}

# Resolve or create IAM role and ensure policies
if [[ -z "${LAMBDA_ROLE_ARN:-}" ]]; then
  ensure_role "$ROLE_NAME"
  attach_managed_basic
  ensure_inline_s3
  LAMBDA_ROLE_ARN=$(aws iam get-role --role-name "$ROLE_NAME" --query 'Role.Arn' --output text)
  # IAM propagation pause
  sleep 5
else
  # even if role ARN provided, ensure S3 inline policy attached to that role if name matches
  if [[ -n "${LAMBDA_ROLE_NAME:-}" ]]; then
    ROLE_NAME="$LAMBDA_ROLE_NAME"
    attach_managed_basic || true
    ensure_inline_s3 || true
  fi
fi

if aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" >/dev/null 2>&1; then
  wait_ready "$FUNCTION_NAME"
  aws lambda update-function-code \
    --function-name "$FUNCTION_NAME" \
    --zip-file "fileb://${ZIP_PATH}" \
    --region "$REGION" >/dev/null

  aws lambda update-function-configuration \
    --function-name "$FUNCTION_NAME" \
    --handler "$HANDLER" \
    --runtime "$RUNTIME" \
    --timeout "$TIMEOUT" \
    --memory-size "$MEMORY" \
    --role "$LAMBDA_ROLE_ARN" \
    --environment "Variables={WEALTH_LINKS_PATH=data/wealth_links.txt,WEALTH_OUTPUT_PATH=/tmp/wealth.json,FUND_LINKS_PATH=data/fund_links.txt,FUND_OUTPUT_PATH=/tmp/fund.json,S3_BUCKET=${BUCKET},S3_PREFIX=${PREFIX},S3_REGION=${S3_REGION}}" \
    --region "$REGION" >/dev/null
  wait_ready "$FUNCTION_NAME"
else
  aws lambda create-function \
    --function-name "$FUNCTION_NAME" \
    --runtime "$RUNTIME" \
    --handler "$HANDLER" \
    --role "$LAMBDA_ROLE_ARN" \
    --zip-file "fileb://${ZIP_PATH}" \
    --timeout "$TIMEOUT" \
    --memory-size "$MEMORY" \
    --environment "Variables={WEALTH_LINKS_PATH=data/wealth_links.txt,WEALTH_OUTPUT_PATH=/tmp/wealth.json,FUND_LINKS_PATH=data/fund_links.txt,FUND_OUTPUT_PATH=/tmp/fund.json,S3_BUCKET=${BUCKET},S3_PREFIX=${PREFIX},S3_REGION=${S3_REGION}}" \
    --region "$REGION" >/dev/null
  aws lambda wait function-exists --function-name "$FUNCTION_NAME" --region "$REGION" >/dev/null 2>&1 || true
fi

aws events put-rule \
  --name "$RULE_NAME" \
  --schedule-expression "$SCHEDULE_EXPRESSION" \
  --state ENABLED \
  --region "$REGION" >/dev/null

RULE_ARN=$(aws events describe-rule --name "$RULE_NAME" --query 'Arn' --output text --region "$REGION")
LAMBDA_ARN=$(aws lambda get-function-configuration --function-name "$FUNCTION_NAME" --query 'FunctionArn' --output text --region "$REGION")

set +e
aws lambda add-permission \
  --function-name "$FUNCTION_NAME" \
  --statement-id "${RULE_NAME}-invoke" \
  --action "lambda:InvokeFunction" \
  --principal events.amazonaws.com \
  --source-arn "$RULE_ARN" \
  --region "$REGION" >/dev/null 2>&1
set -e

aws events put-targets \
  --rule "$RULE_NAME" \
  --targets "Id"="1","Arn"="$LAMBDA_ARN" \
  --region "$REGION" >/dev/null

# Clean remote assets and sync full static site
echo "Cleaning s3://$BUCKET/assets/"
aws s3 rm "s3://$BUCKET/assets/" --recursive --region "$REGION" >/dev/null 2>&1 || true

echo "Syncing static site from ${FRONTEND_DIR}/dist to s3://$BUCKET/ (with delete)"
aws s3 sync "${FRONTEND_DIR}/dist" "s3://$BUCKET/" \
  --delete \
  --region "$REGION" \
  --exclude ".DS_Store"

echo "Deployed $FUNCTION_NAME to $REGION, scheduled $RULE_NAME ($SCHEDULE_EXPRESSION), and synced static site to s3://$BUCKET/."
