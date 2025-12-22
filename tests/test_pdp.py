import pandas as pd
import math
import pytest
from src.planner.engine import calculate_weekly_pdp

def test_pdp_satisfaction_logic():
    # Setup dummy data
    df_demand = pd.DataFrame([
        {"semaine": 1, "parfum": "Parfum A", "format_g": 35, "quantite_caisses": 1000},
        {"semaine": 1, "parfum": "Parfum B", "format_g": 35, "quantite_caisses": 500}
    ])
    
    # Capacity: machine WOLF for format 35
    # Weekly capacity = shift * capacite_shift * 7
    # If shift=3, capacity_shift=100 -> 3 * 100 * 7 = 2100 units/week
    df_cap = pd.DataFrame([
        {"machine": "WOLF", "format_g": 35, "shift": 3, "capacite_shift": 100}
    ])
    
    df_prices = pd.DataFrame([
        {"parfum": "Parfum A", "format_g": 35, "prix_caisse_dt": 10},
        {"parfum": "Parfum B", "format_g": 35, "prix_caisse_dt": 12}
    ])
    
    # Run PDP
    results = calculate_weekly_pdp(df_demand, df_cap, df_prices, start_week=1, horizon=1)
    
    # Check if satisfaction is calculated correctly
    # Total demand = 1500, Total capacity = 2100. Should satisfy all.
    assert not results.empty
    assert results['Satisfaction'].mean() == 100.0
    assert results['Produit'].sum() == 1500

def test_pdp_limited_capacity():
    # Setup dummy data where demand exceeds capacity
    df_demand = pd.DataFrame([
        {"semaine": 1, "parfum": "Parfum A", "format_g": 35, "quantite_caisses": 3000}
    ])
    
    # Weekly capacity = 3 * 100 * 7 = 2100
    df_cap = pd.DataFrame([
        {"machine": "WOLF", "format_g": 35, "shift": 3, "capacite_shift": 100}
    ])
    
    df_prices = pd.DataFrame([
        {"parfum": "Parfum A", "format_g": 35, "prix_caisse_dt": 10}
    ])
    
    results = calculate_weekly_pdp(df_demand, df_cap, df_prices, start_week=1, horizon=1)
    
    # Produced should be limited to capacity (multiple of shift capacity)
    # 2100 is a multiple of 100.
    assert results.iloc[0]['Produit'] == 2100
    assert results.iloc[0]['Satisfaction'] == (2100 / 3000) * 100

def test_pdp_cip_logic():
    # Setup dummy data with different perfumes to trigger CIP
    df_demand = pd.DataFrame([
        {"semaine": 1, "parfum": "Parfum A", "format_g": 35, "quantite_caisses": 100},
        {"semaine": 1, "parfum": "Parfum B", "format_g": 35, "quantite_caisses": 100}
    ])
    
    # Capacity = 3 * 100 * 7 = 2100 units
    # Each shift is 100 units.
    df_cap = pd.DataFrame([
        {"machine": "WOLF", "format_g": 35, "shift": 3, "capacite_shift": 100}
    ])
    
    df_prices = pd.DataFrame([
        {"parfum": "Parfum A", "format_g": 35, "prix_caisse_dt": 12}, # High priority
        {"parfum": "Parfum B", "format_g": 35, "prix_caisse_dt": 10}
    ])
    
    results = calculate_weekly_pdp(df_demand, df_cap, df_prices, start_week=1, horizon=1)
    
    # First perfume (A) should have CIP=0 if it's the first one
    # Second perfume (B) should have CIP=8 if it triggers cleaning
    # Note: the code logic uses last_perfume_per_machine which is initialized to None.
    # The first perfume won't trigger CIP. The second will.
    assert results.iloc[1]['CIP'] == 8
