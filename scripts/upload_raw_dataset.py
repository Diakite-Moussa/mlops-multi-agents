from sklearn.datasets import fetch_openml

from core.storage import upload_bytes, sha256_bytes

frame = fetch_openml("adult", version=2, as_frame=True).frame
for col in frame.columns:
    if str(frame[col].dtype) == "category":
        frame[col] = frame[col].astype(object)

data = frame.to_csv(index=False, lineterminator="\n").encode("utf-8")
uri = upload_bytes("datasets", "raw/adult.csv", data, content_type="text/csv")
print(f"{len(frame)} lignes déposées : {uri} ({sha256_bytes(data)[:20]}...)")
