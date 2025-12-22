import pandas as pd
import math

def calculate_weekly_pdp(df_demand, df_cap, df_prices, start_week, horizon, breakdown_machine=None, breakdown_duration=0):
    """
    Calculates the weekly Production Distribution Plan (PDP).
    
    Args:
        df_demand: DataFrame with demand predictions.
        df_cap: DataFrame with machine capacities.
        df_prices: DataFrame with product prices.
        start_week: The starting week for the planning.
        horizon: The number of weeks to plan for.
        breakdown_machine: Optional name of the machine that has a breakdown.
        breakdown_duration: Duration of the breakdown in days.
        
    Returns:
        DataFrame with PDP results including Satisfaction rate.
    """
    pdp_results = []
    df_cap = df_cap.copy()
    
    # Pre-calculate Max Weekly Capacity
    # Each machine has a capacity per shift and a number of shifts.
    # We assume 3 shifts of 8 hours each = 24 hours per day.
    # The 'shift' column in df_cap might represent number of shifts per day.
    # Based on user logic: df_cap['capacite_shift'] * df_cap['shift'] * 7
    df_cap['cap_hebdo_max'] = df_cap['shift'] * df_cap['capacite_shift'] * 7
    
    last_perfume_per_machine = {"WOLF": None, "ROVEMA": None}

    for week in range(start_week, start_week + horizon):
        week_demand = df_demand[df_demand['semaine'] == week].copy()
        if week_demand.empty:
            continue
            
        week_demand = week_demand.merge(df_prices, on=['parfum', 'format_g'], how='left')
        
        # Priority: Satisfaction -> Revenue (CA)
        # We sort by price to prioritize higher revenue products if capacity is limited
        week_demand = week_demand.sort_values(by=['prix_caisse_dt'], ascending=False)
        current_cap = df_cap.set_index(['machine', 'format_g'])['cap_hebdo_max'].to_dict()
        
        # Apply Breakdown (Module 2 logic)
        if breakdown_machine and breakdown_duration > 0:
            for k in list(current_cap.keys()):
                if k[0] == breakdown_machine:
                    # Subtract hours/capacity based on breakdown
                    machine_rows = df_cap[df_cap['machine'] == breakdown_machine]
                    if not machine_rows.empty:
                        machine_row = machine_rows.iloc[0]
                        # Assuming 8 hours per shift as standard
                        capacity_per_hour = machine_row['capacite_shift'] / 8
                        # Loss calculation: days * 24h * capacity_per_hour
                        loss = breakdown_duration * 24 * capacity_per_hour
                        current_cap[k] = max(0, current_cap[k] - loss)

        for _, row in week_demand.iterrows():
            # Machine selection logic based on format
            machine = "WOLF" if row['format_g'] == 35 else "ROVEMA"
            cap_key = (machine, row['format_g'])
            if cap_key not in current_cap: 
                continue
                
            available_units = current_cap[cap_key]
            cap_per_shift_rows = df_cap[(df_cap['machine'] == machine) & (df_cap['format_g'] == row['format_g'])]
            if cap_per_shift_rows.empty:
                continue
            cap_per_shift = cap_per_shift_rows['capacite_shift'].values[0]
            
            # CIP (Cleaning in Place) Logic: If perfume changes, 1 shift (8h) is lost
            cip_time = 0
            if last_perfume_per_machine[machine] and row['parfum'] != last_perfume_per_machine[machine]:
                if available_units >= cap_per_shift:
                    available_units -= cap_per_shift
                    cip_time = 8
            
            # Production Rounding: Produce in shifts
            shifts_needed = math.ceil(row['quantite_caisses'] / cap_per_shift)
            max_shifts = math.floor(available_units / cap_per_shift)
            actual_shifts = min(shifts_needed, max_shifts)
            produced_qty = actual_shifts * cap_per_shift
            
            current_cap[cap_key] -= produced_qty
            last_perfume_per_machine[machine] = row['parfum']

            satisfaction = (produced_qty / row['quantite_caisses']) if row['quantite_caisses'] > 0 else 1.0
            
            pdp_results.append({
                "Semaine": week, 
                "Machine": machine, 
                "Parfum": row['parfum'],
                "Format": row['format_g'], 
                "Demande": row['quantite_caisses'],
                "Produit": produced_qty, 
                "Satisfaction": satisfaction * 100,
                "Revenue": produced_qty * row['prix_caisse_dt'], 
                "CIP": cip_time
            })
            
    results_df = pd.DataFrame(pdp_results)
    
    # Check satisfaction constraint (> 98%)
    if not results_df.empty:
        mean_satisfaction = results_df['Satisfaction'].mean()
        if mean_satisfaction < 98:
            # We could log a warning or flag it in the UI
            pass
            
    return results_df
