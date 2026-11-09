import hashlib
import io
import os

from dotenv import load_dotenv
from minio import Minio
from minio.error import S3Error

load_dotenv()


def get_client() -> Minio:
    return Minio(
        os.getenv("MINIO_ENDPOINT", "localhost:9000"),
        access_key=os.environ["MINIO_ROOT_USER"],
        secret_key=os.environ["MINIO_ROOT_PASSWORD"],
        secure=False,
    )


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def make_uri(bucket: str, key: str) -> str:
    return f"s3://{bucket}/{key}"


def parse_uri(uri: str) -> tuple[str, str]:
    assert uri.startswith("s3://"), f"URI invalide : {uri}"
    bucket, _, key = uri[5:].partition("/")
    return bucket, key


def upload_bytes(bucket, key, data: bytes, content_type="application/octet-stream", client=None) -> str:
    client = client or get_client()
    client.put_object(bucket, key, io.BytesIO(data), length=len(data), content_type=content_type)
    return make_uri(bucket, key)


def download_bytes(bucket, key, client=None) -> bytes:
    client = client or get_client()
    resp = client.get_object(bucket, key)
    try:
        return resp.read()
    finally:
        resp.close()
        resp.release_conn()


def exists(bucket, key, client=None) -> bool:
    client = client or get_client()
    try:
        client.stat_object(bucket, key)
        return True
    except S3Error as e:
        if e.code in ("NoSuchKey", "NoSuchObject", "NoSuchBucket"):
            return False
        raise


def list_keys(bucket, prefix="", client=None) -> list[str]:
    client = client or get_client()
    return [o.object_name for o in client.list_objects(bucket, prefix=prefix, recursive=True)]
