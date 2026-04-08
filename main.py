from pathlib import Path

import pandas as pd


def _load_bonds(path: Path) -> pd.DataFrame:
    bonds = pd.read_csv(path)
    bonds = bonds.loc[:, ~bonds.columns.str.startswith("Unnamed")]
    return bonds[["BondID", "Coupon", "Frequency", "MonthsSinceCoupon"]].copy()


def build_combo_pv_pnl(events_path: Path, bonds_path: Path) -> pd.DataFrame:
    events = pd.read_csv(events_path)
    bonds = _load_bonds(bonds_path)

    df = events.merge(bonds, on="BondID", how="left")
    if df[["Coupon", "Frequency", "MonthsSinceCoupon"]].isna().any().any():
        raise ValueError("Missing bond metadata for one or more events.")

    # Accrued interest in price points (per 100 notional), added to clean price.
    coupon_period_months = 12 / df["Frequency"]
    df["accrued_interest"] = (
        (df["Coupon"] / df["Frequency"])
        * (df["MonthsSinceCoupon"] / coupon_period_months)
        * 100
    )
    df["trade_dirty_price"] = df["CleanPrice"] + df["accrued_interest"]

    signed_qty = df["Quantity"].where(df["BuySell"].eq("BUY"), -df["Quantity"])
    df["signed_qty"] = signed_qty

    latest_clean = (
        df.sort_values("EventID")
        .groupby("BondID", as_index=False)
        .tail(1)[["BondID", "CleanPrice", "accrued_interest"]]
        .rename(columns={"CleanPrice": "current_clean_price"})
    )
    latest_clean["current_dirty_price"] = (
        latest_clean["current_clean_price"] + latest_clean["accrued_interest"]
    )

    df = df.merge(latest_clean[["BondID", "current_dirty_price"]], on="BondID", how="left")

    df["present_pv"] = df["signed_qty"] * df["current_dirty_price"]
    df["event_trade_value"] = df["signed_qty"] * df["trade_dirty_price"]
    df["event_pnl"] = df["present_pv"] - df["event_trade_value"]

    combo_df = (
        df.groupby(["Desk", "Trader", "BondID"], as_index=False)
        .agg(
            present_pv=("present_pv", "sum"),
            total_pnl=("event_pnl", "sum"),
        )
        .rename(columns={"Desk": "desk", "Trader": "trader", "BondID": "bondID"})
        .sort_values(["desk", "trader", "bondID"])
    )

    return combo_df


def main():
    root = Path(__file__).resolve().parent
    combo_df = build_combo_pv_pnl(root / "events.csv", root / "bonds.csv")
    print(combo_df.to_string(index=False))


if __name__ == "__main__":
    main()
