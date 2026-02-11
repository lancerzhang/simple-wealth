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
理财链接在 `python/data/wealth_links.txt`，基金链接在 `python/data/fund_links.txt`，按行放 URL。

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
python3 python/scripts/wealth_scraper.py --wealth-links python/data/wealth_links.txt --wealth-output frontend/public/data/wealth.json --fund-links python/data/fund_links.txt --fund-output frontend/public/data/fund.json
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

最小用法（全部硬编码，region/bucket/prefix 已写死，默认跳过 pip）：
```
./python/deploy_lambda.sh
```

说明：
- region: `ap-southeast-1`，函数名 `wealth-scraper`，bucket `simple-wealth-cn`，前缀 `data`，每日 08:00 SGT 触发。
- 角色：脚本自动创建/复用 `wealth-scraper-role` 并附加基本执行 + S3 写权限。
- 若需强制安装依赖再打包，运行 `SKIP_PIP_INSTALL=0 ./python/deploy_lambda.sh`。
- 前端：脚本每次 `npm ci && npm run build`，上传 `frontend/dist` 到 S3 根目录（先清空远端 `assets/`，再 `sync --delete`），保证 `index.html` 与静态资源一起更新。

### Lambda 环境变量
- `WEALTH_LINKS_PATH`（默认：`data/wealth_links.txt`）
- `FUND_LINKS_PATH`（默认：`data/fund_links.txt`）
- `WEALTH_OUTPUT_PATH`（默认：`/tmp/wealth.json`）

### Lambda 手动触发（单行命令）
```
aws lambda invoke --function-name wealth-scraper --region ap-southeast-1 --cli-binary-format raw-in-base64-out --payload '{}' /tmp/wealth-scraper-lambda.json && cat /tmp/wealth-scraper-lambda.json
```

### 阿里云 FC 部署
脚本：`python/deploy_aliyun.sh`

最小用法（需已登录 aliyun CLI，Service 绑定有 OSS 读写权限的 RAM 角色，默认 bucket `simple-wealth-cn`，region `cn-shenzhen`）：
```
export ALI_FC_ROLE=acs:ram::1234567890:role/your-fc-role-with-oss
./python/deploy_aliyun.sh
```

可选参数：
```
export ALI_REGION=cn-shenzhen
export ALI_FC_SERVICE=simple-wealth
export ALI_FC_FUNCTION=wealth-scraper
export ALI_FC_CRON="0 0 0 * * *"     # 08:00 CST
export ALI_OSS_BUCKET=simple-wealth-cn
export ALI_OSS_PREFIX=data
```

环境变量（FC）：
- `WEALTH_LINKS_PATH`（默认：`data/wealth_links.txt`）
- `FUND_LINKS_PATH`（默认：`data/fund_links.txt`）
- `WEALTH_OUTPUT_PATH`（默认：`/tmp/wealth.json`）
- `FUND_OUTPUT_PATH`（默认：`/tmp/fund.json`）
- `OSS_BUCKET` / `OSS_PREFIX` / `OSS_REGION`
静态站点同步：会清空远端 `assets/` 后，将本地 `frontend/dist` 递归上传至 OSS 根目录。

阿里云脚本现已硬编码：region `cn-shenzhen`，Service `simple-wealth`，Function `wealth-scraper`，bucket `simple-wealth-cn`，前缀 `data`，每日 08:00 CST 触发。无需额外参数，直接运行 `./python/deploy_aliyun.sh`。

### FC 手动触发（单行命令）
```
aliyun fc-open POST "/2021-04-06/services/simple-wealth/functions/wealth-scraper/invocations" --body '{}' --region cn-shenzhen
```

### 同时触发 Lambda + FC（单行命令）
```
aws lambda invoke --function-name wealth-scraper --region ap-southeast-1 --cli-binary-format raw-in-base64-out --payload '{}' /tmp/wealth-scraper-lambda.json && aliyun fc-open POST "/2021-04-06/services/simple-wealth/functions/wealth-scraper/invocations" --body '{}' --region cn-shenzhen && cat /tmp/wealth-scraper-lambda.json
```

## CLI 登录速查

- AWS CLI（v2）  
  1. 安装 awscli v2。  
  2. 配置凭证：`aws configure`（Access Key/Secret/region 默认 `ap-southeast-1`），或使用 SSO：`aws configure sso`。  
  3. 如果用 profile，运行脚本前设置 `AWS_PROFILE=your-profile`（或在 `~/.aws/config` 里设默认）。  

- 阿里云 CLI（aliyun）  
  1. 安装 aliyun CLI。  
  2. 配置访问密钥：`aliyun configure set --access-key-id <AK> --access-key-secret <SK> --region cn-shenzhen`，或使用临时 STS：`aliyun configure set --mode StsToken --access-key-id <AK> --access-key-secret <SK> --sts-token <TOKEN> --region cn-shenzhen`。  
  3. 若使用多个账户，可加 `--profile myprof` 并在脚本前导出 `ALICLOUD_PROFILE=myprof`。  
