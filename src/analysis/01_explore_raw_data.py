import pandas as pd
from pathlib import Path

RAW_PATH = Path("data/raw")

#loading data
datasets = {}

for file in RAW_PATH.glob("*.csv"):
    name = file.stem
    print(f"\nLoading {name}...")
    datasets[name] = pd.read_csv(file)

#explore function
def explore(name, df):

    print("\n" + "="*60)
    print(f"DATASET: {name}")
    print("="*60)

    print("\nShape:")
    print(df.shape)

    print("\nColumns:")
    print(df.columns.tolist())

    print("\nData Types:")
    print(df.dtypes)

    print("\nMissing Values:")
    print(df.isnull().sum().sort_values(ascending=False))

    print("\nDuplicate Rows:")
    print(df.duplicated().sum())

    print("\nSample:")
    print(df.head(3))


#explore each dataset
for name, df in datasets.items():
    explore(name, df)
