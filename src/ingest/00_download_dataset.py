import os
import zipfile
from pathlib import Path

RAW_PATH = Path("data/raw")
RAW_PATH.mkdir(parents=True, exist_ok=True)

DATASET = "olistbr/brazilian-ecommerce"

def download_dataset():
    print("Downloading dataset...")

    os.system(f"kaggle datasets download -d {DATASET} -p {RAW_PATH}")

    for file in RAW_PATH.glob("*.zip"):
        with zipfile.ZipFile(file, "r") as zip_ref:
            zip_ref.extractall(RAW_PATH)
        file.unlink()

    print("Dataset downloaded and extracted.")

if __name__ == "__main__":
    download_dataset()
