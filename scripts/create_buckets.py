import os
from dotenv import load_dotenv
from minio import Minio

load_dotenv()
client = Minio(
    os.getenv("MINIO_ENDPOINT", "localhost:9000"),
    access_key=os.getenv("MINIO_ROOT_USER"),
    secret_key=os.getenv("MINIO_ROOT_PASSWORD"),
    secure=False,
)
for bucket in ("datasets", "models", "mlflow"):
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
        print(f"créé : {bucket}")
    else:
        print(f"existe déjà : {bucket}")
