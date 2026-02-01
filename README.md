# simple-wealth

## 前端运行

**依赖：** Node.js

在 `frontend` 目录运行：
```
npm install
npm run dev
```

生产构建：
```
npm run build
```

## 数据抓取（理财产品）

### 链接配置
产品链接在 `python/data/product_links.txt`，按行放 URL。

### 本地运行
1) 安装依赖（用于 SSL 证书）：
```
python3 -m pip install -r python/requirements.txt
```

2) 运行抓取：
```
python3 python/scripts/wealth_scraper.py
```

默认会写入 `frontend/public/data/wealth.json`。
输出中每条产品会包含 `updatedAt`（UTC 时间）。

如需指定路径：
```
python3 python/scripts/wealth_scraper.py --links python/data/product_links.txt --output frontend/public/data/wealth.json
```

### SSL 证书问题（macOS 常见）
如果遇到 `CERTIFICATE_VERIFY_FAILED`：
```
/Applications/Python\ 3.12/Install\ Certificates.command
```

或者临时指定 CA：
```
WEALTH_CA_BUNDLE=/path/to/ca.pem python3 python/scripts/wealth_scraper.py
```

如果遇到 `UNSAFE_LEGACY_RENEGOTIATION_DISABLED`：
```
WEALTH_SSL_ALLOW_LEGACY=1 python3 python/scripts/wealth_scraper.py
```

如果遇到 404/5xx 间歇性错误，可增加重试次数与退避时间：
```
WEALTH_HTTP_RETRIES=5 WEALTH_HTTP_RETRY_BACKOFF=1.2 python3 python/scripts/wealth_scraper.py
```

开启调试日志：
```
WEALTH_DEBUG=1 python3 python/scripts/wealth_scraper.py
```
调试日志会输出收益率的获取/计算来源与区间明细。

单个链接失败会自动记录日志并继续，不会中断；脚本最后会输出成功/失败数量和失败 URL。

不推荐的临时绕过：
```
WEALTH_SSL_NO_VERIFY=1 python3 python/scripts/wealth_scraper.py
```

## AWS Lambda 部署

### 一键部署
脚本：`python/deploy_lambda.sh`

最小用法（首次创建函数需要角色 ARN）：
```
export AWS_REGION=ap-east-1
export LAMBDA_ROLE_ARN=arn:aws:iam::123456789012:role/your-lambda-role
./python/deploy_lambda.sh
```

可选参数：
```
export LAMBDA_FUNCTION_NAME=wealth-scraper
export LAMBDA_RUNTIME=python3.11
export LAMBDA_HANDLER=wealth_scraper.handler.lambda_handler
export LAMBDA_TIMEOUT=60
export LAMBDA_MEMORY=256
export SCHEDULE_EXPRESSION="cron(0 1 * * ? *)"  # 香港时间 09:00
```

脚本会自动：
- 安装 `python/requirements.txt` 到打包目录
- 打包并更新/创建 Lambda
- 创建 EventBridge 定时触发

### Lambda 环境变量
- `WEALTH_LINKS_PATH`（默认：`data/product_links.txt`）
- `WEALTH_OUTPUT_PATH`（默认：`/tmp/wealth.json`）
