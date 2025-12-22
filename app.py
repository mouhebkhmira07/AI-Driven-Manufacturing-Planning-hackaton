import streamlit as st
import pandas as pd
from src.planner.utils import load_all_datasets
from src.planner.engine import calculate_weekly_pdp

# Page Configuration
st.set_page_config(
    layout="wide", 
    page_title="Ikel AI Planner - Grain d'Or",
    page_icon="🌾"
)

# Custom Styling
st.markdown("""
<style>
    .main {
        background-color: #f5f7f9;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

st.title("🌾 Ikel Manufacturing - Grain d'Or AI Planner")
st.markdown("---")

# Load Data
try:
    df_cap, df_demand, df_prices = load_all_datasets()
    data_loaded = True
except Exception as e:
    st.error(f"Error loading datasets: {e}")
    data_loaded = False

if data_loaded:
    # Sidebar Configuration
    st.sidebar.header("🛠️ Planning Configuration")
    wk_start = st.sidebar.number_input("Semaine Début", min_value=1, max_value=52, value=1)
    wk_horizon = st.sidebar.slider("Horizon (Semaines)", min_value=1, max_value=8, value=4)

    st.sidebar.markdown("---")
    st.sidebar.subheader("⚠️ Simulation de Panne")
    fail_m = st.sidebar.selectbox("Machine en panne", ["Aucune", "WOLF", "ROVEMA"])
    fail_d = st.sidebar.slider("Durée de panne (jours)", min_value=0, max_value=7, value=0)

    # Main Action Button
    if st.sidebar.button("Générer Plan de Production (PDP)", type="primary"):
        m_name = None if fail_m == "Aucune" else fail_m
        results = calculate_weekly_pdp(df_demand, df_cap, df_prices, wk_start, wk_horizon, m_name, fail_d)
        
        if not results.empty:
            # KPI Metrics
            avg_satisfaction = results['Satisfaction'].mean()
            total_revenue = results['Revenue'].sum()
            total_cip = results['CIP'].sum()
            
            c1, c2, c3 = st.columns(3)
            
            # Display average satisfaction with a color-coded delta or warning
            sat_color = "normal" if avg_satisfaction >= 98 else "inverse"
            c1.metric("Taux de Satisfaction Moyen", f"{avg_satisfaction:.1f}%", 
                      delta=f"{avg_satisfaction - 98:.1f}% (Seuil: 98%)", delta_color=sat_color)
            
            c2.metric("Chiffre d'Affaires Estimé", f"{total_revenue:,.0f} DT")
            c3.metric("Temps Total CIP (Nettoyage)", f"{total_cip}h")
            
            if avg_satisfaction < 98:
                st.warning(f"⚠️ **Attention:** Le taux de satisfaction moyen ({avg_satisfaction:.1f}%) est inférieur au seuil requis de 98%.")
            else:
                st.success(f"✅ Le plan de production respecte le seuil de satisfaction de 98%.")

            # Results Table
            st.subheader("📋 Détails du Plan de Production (Hebdomadaire)")
            
            # Format the display DataFrame
            display_df = results.copy()
            display_df['Satisfaction'] = display_df['Satisfaction'].map('{:.1f}%'.format)
            display_df['Revenue'] = display_df['Revenue'].map('{:,.0f} DT'.format)
            
            st.dataframe(display_df, use_container_width=True)
            
            # Additional Insights
            st.markdown("---")
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.subheader("📊 Satisfaction par Parfum")
                sat_by_parfum = results.groupby('Parfum')['Satisfaction'].mean().sort_values()
                st.bar_chart(sat_by_parfum)
                
            with col_b:
                st.subheader("💰 Revenue par Machine")
                rev_by_machine = results.groupby('Machine')['Revenue'].sum()
                st.pie_chart(rev_by_machine)
        else:
            st.info("Aucune donnée de demande trouvée pour les semaines sélectionnées.")
    else:
        st.info("Utilisez la barre latérale pour configurer le plan et cliquez sur 'Générer PDP'.")
else:
    st.warning("Veuillez vous assurer que les fichiers CSV sont présents dans le dossier 'data'.")
