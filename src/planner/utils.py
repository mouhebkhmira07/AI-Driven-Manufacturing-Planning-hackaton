import pandas as pd
import os

def load_all_datasets(data_path="data"):
    """
    Loads all required CSV datasets from the data directory.
    
    Args:
        data_path: Path to the directory containing CSV files.
        
    Returns:
        tuple: (df_cap, df_demand, df_prices)
    """
    # Using ';' as separator based on user requirement
    df_cap = pd.read_csv(os.path.join(data_path, "capacite_machine.csv"), sep=';')
    df_demand = pd.read_csv(os.path.join(data_path, "demande_prevision.csv"), sep=';')
    df_hist = pd.read_csv(os.path.join(data_path, "planning_historique.csv"), sep=';')
    
    # Helper to get unique prices
    # Drop duplicates to have a clean reference for pricing per product/format
    df_prices = df_hist[['parfum', 'format_g', 'prix_caisse_dt']].drop_duplicates().sort_values('prix_caisse_dt', ascending=False)
    
    return df_cap, df_demand, df_prices
