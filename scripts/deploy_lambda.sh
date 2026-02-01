#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FUNCTION_NAME="${LAMBDA_FUNCTION_NAME:-wealth-scraper}"
REGION="${AWS_REGION:-ap-east-1}"
RUNTIME="${LAMBDA_RUNTIME:-python3.11}"
HANDLER="${LAMBDA_HANDLER:-wealth_scraper.handler.lambda_handler}"
TIMEOUT="${LAMBDA_TIMEOUT:-60}"
MEMORY="${LAMBDA_MEMORY:-256}"
RULE_NAME="${SCHEDULE_RULE_NAME:-${FUNCTION_NAME}-daily}"
SCHEDULE_EXPRESSION="${SCHEDULE_EXPRESSION:-cron(0 1 * * ? *)}"

ZIP_DIR="${ROOT_DIR}/dist"
ZIP_PATH="${ZIP_DIR}/wealth-scraper.zip"
mkdir -p "$ZIP_DIR"

if ! command -v aws >/dev/null 2>&1; then
  echo "aws CLI not found. Install AWS CLI v2 first." >&2
  exit 1
fi

if ! command -v zip >/dev/null 2>&1; then
  echo "zip not found. Install zip first." >&2
  exit 1
fi

cd "$ROOT_DIR"
rm -f "$ZIP_PATH"
zip -r "$ZIP_PATH" \
  wealth_scraper \
  data/product_links.txt \
  requirements.txt \
  scripts/wealth_scraper.py \
  -x "**/__pycache__/*" "**/*.pyc" "**/.DS_Store" >/dev/null

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
    --environment "Variables={WEALTH_LINKS_PATH=data/product_links.txt,WEALTH_OUTPUT_PATH=/tmp/wealth.json}" \
    --region "$REGION" >/dev/null
else
  if [[ -z "${LAMBDA_ROLE_ARN:-}" ]]; then
    echo "LAMBDA_ROLE_ARN is required to create the function." >&2
    exit 1
  fi

  aws lambda create-function \
    --function-name "$FUNCTION_NAME" \
    --runtime "$RUNTIME" \
    --handler "$HANDLER" \
    --role "$LAMBDA_ROLE_ARN" \
    --zip-file "fileb://${ZIP_PATH}" \
    --timeout "$TIMEOUT" \
    --memory-size "$MEMORY" \
    --environment "Variables={WEALTH_LINKS_PATH=data/product_links.txt,WEALTH_OUTPUT_PATH=/tmp/wealth.json}" \
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
