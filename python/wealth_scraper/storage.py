from __future__ import annotations

import os
from pathlib import Path
from typing import Dict


def _read_file(path: Path) -> bytes:
    return path.read_bytes()


def _upload_oss(file_path: Path, bucket: str, key: str, endpoint: str | None = None) -> None:
    try:
        import oss2  # type: ignore
    except Exception as exc:
        raise RuntimeError("oss2 not installed; cannot upload to OSS") from exc

    ak = os.environ.get("OSS_ACCESS_KEY_ID") or os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_ID")
    sk = os.environ.get("OSS_ACCESS_KEY_SECRET") or os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_SECRET")
    sts_token = os.environ.get("ALIBABA_CLOUD_SECURITY_TOKEN")

    if not (ak and sk):
        raise RuntimeError("OSS credentials not provided in env (OSS_ACCESS_KEY_ID/SECRET or ALIBABA_CLOUD_ACCESS_KEY_ID/SECRET)")

    ep = endpoint or os.environ.get("OSS_ENDPOINT")
    if not ep:
        region = os.environ.get("OSS_REGION", "ap-southeast-1")
        ep = f"https://oss-{region}.aliyuncs.com"

    auth = oss2.StsAuth(ak, sk, sts_token) if sts_token else oss2.Auth(ak, sk)
    bucket_client = oss2.Bucket(auth, ep, bucket)
    bucket_client.put_object(key, _read_file(file_path))


def _upload_s3(file_path: Path, bucket: str, key: str, region: str | None = None) -> None:
    try:
        import boto3  # type: ignore
    except Exception as exc:
        raise RuntimeError("boto3 not available; cannot upload to S3") from exc

    session = boto3.session.Session(region_name=region)
    s3 = session.client("s3")
    s3.upload_file(str(file_path), bucket, key)


def publish_outputs(paths: Dict) -> None:
    """Publish generated JSONs to OSS or S3 if env variables are present."""

    wealth_path: Path = paths["wealth_output"]
    fund_path: Path = paths["fund_output"]

    # OSS
    oss_bucket = os.environ.get("OSS_BUCKET")
    if oss_bucket:
        prefix = os.environ.get("OSS_PREFIX", "data")
        region = os.environ.get("OSS_REGION")  # optional
        wealth_key = f"{prefix}/wealth.json"
        fund_key = f"{prefix}/fund.json"
        _upload_oss(wealth_path, oss_bucket, wealth_key, os.environ.get("OSS_ENDPOINT"))
        _upload_oss(fund_path, oss_bucket, fund_key, os.environ.get("OSS_ENDPOINT"))

    # S3
    s3_bucket = os.environ.get("S3_BUCKET")
    if s3_bucket:
        prefix = os.environ.get("S3_PREFIX", "data")
        region = os.environ.get("S3_REGION")  # optional
        wealth_key = f"{prefix}/wealth.json"
        fund_key = f"{prefix}/fund.json"
        _upload_s3(wealth_path, s3_bucket, wealth_key, region)
        _upload_s3(fund_path, s3_bucket, fund_key, region)

