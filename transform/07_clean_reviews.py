import pandas as pd

df = pd.read_csv("data/raw/olist_order_reviews_dataset.csv")

#fill missing comments
df["review_comment_title"] = df["review_comment_title"].fillna("no_title")
df["review_comment_message"] = df["review_comment_message"].fillna("no_comment")

df["review_creation_date"] = pd.to_datetime(
    df["review_creation_date"], errors="coerce"
)

df["review_answer_timestamp"] = pd.to_datetime(
    df["review_answer_timestamp"], errors="coerce"
)

df = df.drop_duplicates()

df.to_csv("data/processed/reviews_clean.csv", index=False)

print("Saved reviews_clean")