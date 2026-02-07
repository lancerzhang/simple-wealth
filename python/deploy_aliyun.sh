#!/usr/bin/env bash
set -euo pipefail

# Deploy wealth scraper to Aliyun Function Compute (FC)
# Requirements: ali/aliyun CLI logged in with permissions for FC + RAM + OSS

REGION="cn-shenzhen"
FC_ENDPOINT=""
SERVICE_NAME="simple-wealth"
FUNCTION_NAME="wealth-scraper"
SCHEDULE_NAME="wealth-scraper-daily"  # timer trigger name
# FC cron is UTC; 08:00 CST == 00:00 UTC
CRON_EXPR="0 0 0 * * *"

WEALTH_LINKS_PATH="data/wealth_links.txt"
FUND_LINKS_PATH="data/fund_links.txt"
WEALTH_OUTPUT_PATH="/tmp/wealth.json"
FUND_OUTPUT_PATH="/tmp/fund.json"

OSS_BUCKET="simple-wealth-cn"
OSS_PREFIX="data"
FRONTEND_DIR="$(cd "$(dirname "$0")/.." && pwd)/frontend"

PYTHON_BIN="${PYTHON_BIN:-python3}"
ZIP_DIR="$(cd "$(dirname "$0")" && pwd)/../dist"
BUILD_DIR="${ZIP_DIR}/aliyun_build"
ZIP_PATH="${ZIP_DIR}/wealth-scraper-aliyun.zip"

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON_DIR="${ROOT_DIR}/python"

rm -rf "$BUILD_DIR" "$ZIP_PATH"
mkdir -p "$BUILD_DIR/data" "$BUILD_DIR/scripts"

# Install deps if any
if [[ -s "${PYTHON_DIR}/requirements.txt" ]]; then
  ${PYTHON_BIN} -m pip install -r "${PYTHON_DIR}/requirements.txt" -t "$BUILD_DIR" >/dev/null
fi

cp -R "${PYTHON_DIR}/wealth_scraper" "$BUILD_DIR/"
cp "${PYTHON_DIR}/data/wealth_links.txt" "$BUILD_DIR/data/wealth_links.txt"
cp "${PYTHON_DIR}/data/fund_links.txt" "$BUILD_DIR/data/fund_links.txt"
cp "${PYTHON_DIR}/scripts/wealth_scraper.py" "$BUILD_DIR/scripts/wealth_scraper.py"
cp "${PYTHON_DIR}/requirements.txt" "$BUILD_DIR/requirements.txt"

cd "$BUILD_DIR"
zip -r "$ZIP_PATH" . -x "**/__pycache__/*" "**/*.pyc" "**/.DS_Store" >/dev/null
cd "$ROOT_DIR"

# Build frontend (always rebuild)
cd "$FRONTEND_DIR"
if [[ -f package-lock.json ]]; then
  npm ci >/dev/null
else
  npm install >/dev/null
fi
npm run build >/dev/null
cd "$ROOT_DIR"

# Upload code package to OSS (required before create/update)
aliyun oss cp "$ZIP_PATH" "oss://${OSS_BUCKET}/${OSS_PREFIX}/fc/${FUNCTION_NAME}.zip" --region "$REGION"

# Clean remote assets and sync static site
aliyun oss rm "oss://${OSS_BUCKET}/assets/" --recursive --force --region "$REGION" || true
aliyun oss cp "${FRONTEND_DIR}/dist/" "oss://${OSS_BUCKET}/" --recursive --force --region "$REGION" --exclude ".DS_Store"

# Create service if missing
if ! aliyun fc list-functions --service-name "$SERVICE_NAME" --region "$REGION" >/dev/null 2>&1; then
  aliyun fc create-service --service-name "$SERVICE_NAME" --role "${ALI_FC_ROLE:-}" --region "$REGION"
fi

# Create or update function
if aliyun fc get-function --service-name "$SERVICE_NAME" --function-name "$FUNCTION_NAME" --region "$REGION" >/dev/null 2>&1; then
  aliyun fc update-function \
    --service-name "$SERVICE_NAME" \
    --function-name "$FUNCTION_NAME" \
    --region "$REGION" \
    --handler "scripts/wealth_scraper.handler" \
    --runtime "python3" \
    --memory-size 256 \
    --timeout 60 \
    --code-bucket "$OSS_BUCKET" \
    --code-object "${OSS_PREFIX}/fc/${FUNCTION_NAME}.zip" \
    --environment-variables "WEALTH_LINKS_PATH=${WEALTH_LINKS_PATH},FUND_LINKS_PATH=${FUND_LINKS_PATH},WEALTH_OUTPUT_PATH=${WEALTH_OUTPUT_PATH},FUND_OUTPUT_PATH=${FUND_OUTPUT_PATH},OSS_BUCKET=${OSS_BUCKET},OSS_PREFIX=${OSS_PREFIX},OSS_REGION=${REGION}" \
    >/dev/null
else
  aliyun fc create-function \
    --service-name "$SERVICE_NAME" \
    --function-name "$FUNCTION_NAME" \
    --region "$REGION" \
    --handler "scripts/wealth_scraper.handler" \
    --runtime "python3" \
    --memory-size 256 \
    --timeout 60 \
    --code-bucket "$OSS_BUCKET" \
    --code-object "${OSS_PREFIX}/fc/${FUNCTION_NAME}.zip" \
    --environment-variables "WEALTH_LINKS_PATH=${WEALTH_LINKS_PATH},FUND_LINKS_PATH=${FUND_LINKS_PATH},WEALTH_OUTPUT_PATH=${WEALTH_OUTPUT_PATH},FUND_OUTPUT_PATH=${FUND_OUTPUT_PATH},OSS_BUCKET=${OSS_BUCKET},OSS_PREFIX=${OSS_PREFIX},OSS_REGION=${REGION}" \
    >/dev/null
fi

# Create/Update timed trigger (CRON uses UTC in FC; set via env)
aliyun fc put-trigger \
  --service-name "$SERVICE_NAME" \
  --function-name "$FUNCTION_NAME" \
  --trigger-name "$SCHEDULE_NAME" \
  --trigger-type timer \
  --trigger-config "{\"payload\":\"{}\",\"cronExpression\":\"${CRON_EXPR}\",\"enable\":true}" \
  --region "$REGION"

echo "Aliyun FC deployed: ${SERVICE_NAME}/${FUNCTION_NAME} (region ${REGION}), cron=${CRON_EXPR}"
