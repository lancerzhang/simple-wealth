#!/usr/bin/env bash
set -euo pipefail

PYTHON_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${PYTHON_DIR}/.." && pwd)"
FUNCTION_NAME="${LAMBDA_FUNCTION_NAME:-wealth-scraper}"
REGION="${AWS_REGION:-ap-southeast-1}"
RUNTIME="${LAMBDA_RUNTIME:-python3.11}"
HANDLER="${LAMBDA_HANDLER:-scripts/wealth_scraper.lambda_handler}"
TIMEOUT="${LAMBDA_TIMEOUT:-60}"
MEMORY="${LAMBDA_MEMORY:-256}"
RULE_NAME="${SCHEDULE_RULE_NAME:-${FUNCTION_NAME}-daily}"
# 08:00 SGT (UTC+8) == 00:00 UTC
SCHEDULE_EXPRESSION="${SCHEDULE_EXPRESSION:-cron(0 0 * * ? *)}"
ROLE_NAME="${LAMBDA_ROLE_NAME:-wealth-scraper-role}"
ROLE_POLICY_NAME="${LAMBDA_ROLE_POLICY_NAME:-wealth-scraper-s3}"

ZIP_DIR="${ROOT_DIR}/dist"
ZIP_PATH="${ZIP_DIR}/wealth-scraper.zip"
BUILD_DIR="${ZIP_DIR}/lambda_build"
PYTHON_BIN="${PYTHON_BIN:-python3}"
SKIP_PIP_INSTALL="${SKIP_PIP_INSTALL:-0}"
mkdir -p "$ZIP_DIR"

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

# Resolve or create IAM role
if [[ -z "${LAMBDA_ROLE_ARN:-}" ]]; then
  if aws iam get-role --role-name "$ROLE_NAME" >/dev/null 2>&1; then
    LAMBDA_ROLE_ARN=$(aws iam get-role --role-name "$ROLE_NAME" --query 'Role.Arn' --output text)
  else
    TRUST_DOC='{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}'
    LAMBDA_ROLE_ARN=$(aws iam create-role --role-name "$ROLE_NAME" --assume-role-policy-document "$TRUST_DOC" --query 'Role.Arn' --output text)
    aws iam attach-role-policy --role-name "$ROLE_NAME" --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole >/dev/null
    # S3 write access to target bucket/prefix
    BUCKET="${S3_BUCKET:-simple-wealth-cn}"
    PREFIX="${S3_PREFIX:-data}"
    POLICY_DOC=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:PutObjectAcl"],
      "Resource": [
        "arn:aws:s3:::$BUCKET/$PREFIX/*",
        "arn:aws:s3:::$BUCKET/$PREFIX"
      ]
    }
  ]
}
EOF
)
    aws iam put-role-policy --role-name "$ROLE_NAME" --policy-name "$ROLE_POLICY_NAME" --policy-document "$POLICY_DOC" >/dev/null
    echo "Created IAM role $ROLE_NAME with S3 write to s3://$BUCKET/$PREFIX/*"
    # IAM propagation pause
    sleep 5
  fi
fi

if aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" >/dev/null 2>&1; then
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
    --environment "Variables={WEALTH_LINKS_PATH=data/wealth_links.txt,WEALTH_OUTPUT_PATH=/tmp/wealth.json,FUND_LINKS_PATH=data/fund_links.txt,FUND_OUTPUT_PATH=/tmp/fund.json,S3_BUCKET=${S3_BUCKET:-simple-wealth-cn},S3_PREFIX=${S3_PREFIX:-data},S3_REGION=${S3_REGION:-$REGION}}" \
    --region "$REGION" >/dev/null
else
  aws lambda create-function \
    --function-name "$FUNCTION_NAME" \
    --runtime "$RUNTIME" \
    --handler "$HANDLER" \
    --role "$LAMBDA_ROLE_ARN" \
    --zip-file "fileb://${ZIP_PATH}" \
    --timeout "$TIMEOUT" \
    --memory-size "$MEMORY" \
    --environment "Variables={WEALTH_LINKS_PATH=data/wealth_links.txt,WEALTH_OUTPUT_PATH=/tmp/wealth.json,FUND_LINKS_PATH=data/fund_links.txt,FUND_OUTPUT_PATH=/tmp/fund.json,S3_BUCKET=${S3_BUCKET:-simple-wealth-cn},S3_PREFIX=${S3_PREFIX:-data},S3_REGION=${S3_REGION:-$REGION}}" \
    --region "$REGION" >/dev/null
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

echo "Deployed $FUNCTION_NAME to $REGION and scheduled $RULE_NAME ($SCHEDULE_EXPRESSION)."
