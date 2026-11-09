import os
import mlflow
from dotenv import load_dotenv

load_dotenv()
os.environ["MLFLOW_S3_ENDPOINT_URL"] = "http://localhost:9000"
os.environ["AWS_ACCESS_KEY_ID"] = os.environ["MINIO_ROOT_USER"]
os.environ["AWS_SECRET_ACCESS_KEY"] = os.environ["MINIO_ROOT_PASSWORD"]

mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("check")
with mlflow.start_run():
    mlflow.log_metric("ok", 1)
    with open("hello.txt", "w") as f:
        f.write("hello")
    mlflow.log_artifact("hello.txt")
print("MLflow + MinIO OK")
