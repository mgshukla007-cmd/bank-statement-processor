import os
import pandas as pd


def export_data(transactions, account_info, output_dir="outputs", fmt="both"):
    """
    Exports transactions + account info to CSV and/or Excel.
    Returns the DataFrame and a dict of created file paths.
    """
    if not transactions:
        return None, {}

    os.makedirs(output_dir, exist_ok=True)

    df = pd.DataFrame(transactions)

    # Ensure consistent column order
    preferred_cols = ["date", "description", "debit", "credit", "balance", "category"]
    ordered_cols = [c for c in preferred_cols if c in df.columns]
    extra_cols = [c for c in df.columns if c not in ordered_cols]
    df = df[ordered_cols + extra_cols]

    # Add account info columns (same value on every row — useful for downstream systems)
    for key in ["account_holder", "account_number", "ifsc"]:
        df[key] = account_info.get(key)

    created_files = {}

    if fmt in ("csv", "both"):
        csv_path = os.path.join(output_dir, "transactions.csv")
        df.to_csv(csv_path, index=False)
        created_files["csv"] = csv_path

    if fmt in ("excel", "both"):
        xlsx_path = os.path.join(output_dir, "transactions.xlsx")
        df.to_excel(xlsx_path, index=False)
        created_files["excel"] = xlsx_path

    return df, created_files


def export_summary(transactions, output_dir="outputs"):
    """
    Optional: write a small category-summary CSV.
    """
    if not transactions:
        return None
    os.makedirs(output_dir, exist_ok=True)
    df = pd.DataFrame(transactions)
    if "category" not in df.columns:
        return None

    summary = (
        df.groupby("category")
        .agg(
            count=("category", "size"),
            total_debit=("debit", lambda x: pd.to_numeric(x, errors="coerce").sum()),
            total_credit=("credit", lambda x: pd.to_numeric(x, errors="coerce").sum()),
        )
        .reset_index()
    )
    path = os.path.join(output_dir, "category_summary.csv")
    summary.to_csv(path, index=False)
    return path