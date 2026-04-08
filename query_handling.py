def query_bond_state(df, event_id, bond_id, ai_dict):
    bond_idx = int(bond_id.replace("BOND", ""))
    s = f"stock{bond_idx}"
    
    if event_id not in df.index:
        raise ValueError(f"Event {event_id} not found")
    
    row = df.loc[event_id]
    if isinstance(row, pd.DataFrame):
        row = row.iloc[-1]
    
    dirty_price = float(row[f"{s}dirtyprice"])
    clean_price = dirty_price - ai_dict[bond_id]  # subtract accrued interest
    
    return {
        "position": float(row[f"{s}position"]),
        "dirty_price": dirty_price,
        "clean_price": clean_price,
        "pv": float(row[f"{s}PV"])
    }

def query_bond_pnl(df, event_id, bond_id):
    bond_idx = int(bond_id.replace("BOND", ""))
    s = f"stock{bond_idx}"
    if event_id not in df.index:
        raise ValueError(f"Event {event_id} not found")
    return float(df.loc[event_id, f"{s}P&L"])

def get_trader_total_pnl(combo_df, trader):
    return combo_df[combo_df["trader"] == trader]["total_pnl"].sum()