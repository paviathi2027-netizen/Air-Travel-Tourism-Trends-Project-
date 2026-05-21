
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 2. Set Streamlit page configuration and title
st.set_page_config(layout="wide")
st.title("Flight Data Dashboard")

# 3. Define a function to encapsulate data loading and preprocessing
@st.cache_data
def load_data():
    air_df = pd.read_csv("cleaned_flight_data.csv")
    
    air_df['Date_of_Journey'] = pd.to_datetime(air_df['Date_of_Journey'], errors='coerce')
    air_df['Dep_Time'] = pd.to_datetime(air_df['Dep_Time'], errors='coerce')
    air_df['Departure_Hour'] = air_df['Dep_Time'].dt.hour
    air_df['Route_Label'] = air_df['Source'] + ' → ' + air_df['Destination']
    air_df['Journey_Month'] = air_df['Date_of_Journey'].dt.month

    def get_time_period(hour):
        if pd.isna(hour): return 'Unknown'
        if 5 <= hour < 12: return 'Morning'
        elif 12 <= hour < 17: return 'Afternoon'
        elif 17 <= hour < 21: return 'Evening'
        else: return 'Night'

    air_df['Time_Period'] = air_df['Departure_Hour'].apply(get_time_period)
    
    return air_df

# 4. Call the load_data() function
original_air_df = load_data()

# 5. Initialize session states for filters
filterable_columns = [
    'Airline',
    'Source',
    'Destination',
    'Total_Stops',
    'Time_Period',
    'Journey_Month'
]

if 'filter_selections' not in st.session_state:
    st.session_state.filter_selections = {}
    for col in filterable_columns:
        options = sorted(original_air_df[col].astype(str).unique().tolist())
        st.session_state.filter_selections[col] = options # Select all by default initially

if 'applied_filters' not in st.session_state:
    st.session_state.applied_filters = {}
    for col in filterable_columns:
        options = sorted(original_air_df[col].astype(str).unique().tolist())
        st.session_state.applied_filters[col] = options # Apply all by default initially

# 6. Create a sidebar for filter options
st.sidebar.header("Filter Options")

for col in filterable_columns:
    options = sorted(original_air_df[col].astype(str).unique().tolist())
    selected_options = st.sidebar.multiselect(
        f"Select {col}",
        options,
        default=st.session_state.filter_selections[col],
        key=f"multiselect_{col}"
    )
    st.session_state.filter_selections[col] = selected_options

# 7. Add 'Apply Filters' and 'Clear Filters' buttons
col1, col2 = st.sidebar.columns(2)
with col1:
    apply_button = st.button("Apply Filters", key="apply_filters_btn")
with col2:
    clear_button = st.button("Clear Filters", key="clear_filters_btn")

if apply_button:
    st.session_state.applied_filters = st.session_state.filter_selections.copy()
    st.experimental_rerun()

if clear_button:
    for col in filterable_columns:
        st.session_state.filter_selections[col] = []
    st.session_state.applied_filters = {}
    st.experimental_rerun()

# 8. Implement the filtering logic
filtered_df = original_air_df.copy()

# Check if st.session_state.applied_filters is empty, if so, use all original data
if not st.session_state.applied_filters:
    st.session_state.applied_filters = {
        col: sorted(original_air_df[col].astype(str).unique().tolist()) 
        for col in filterable_columns
    }

for col, selected_values in st.session_state.applied_filters.items():
    if selected_values: # Only apply filter if there are selections
        if col == 'Journey_Month':
            filtered_df = filtered_df[filtered_df[col].isin([int(val) for val in selected_values])]
        else:
            filtered_df = filtered_df[filtered_df[col].astype(str).isin(selected_values)]

# 9. Define a function to display dashboard content (KPIs and Charts)
def display_dashboard_content(df_to_display):
    if df_to_display.empty:
        st.warning("No data available for the selected filters.")
        cols = st.columns(5)
        for i, col in enumerate(cols):
            with col:
                st.markdown(f"""<div style='text-align: center; margin: 10px; padding: 10px; border: 1px solid #ccc; border-radius: 5px;'>
                    <h3 style='font-size: 1em; color: gray;'>No Data</h3>
                    <p style='font-size: 1.5em; font-weight: bold; color: #1f77b4;'>N/A</p>
                </div>""", unsafe_allow_html=True)
        return

    # --- KPI LOGIC ---
    alaska_df = df_to_display.groupby("Airline")["Price"].mean()
    top_airline_name = alaska_df.idxmax()
    top_airline_val = alaska_df.max()
    route_counts = df_to_display['Route_Label'].value_counts()
    top_route_name = route_counts.idxmax()
    top_route_val = route_counts.max()
    dest_counts = df_to_display['Destination'].value_counts()
    top_dest_name = dest_counts.idxmax()
    top_dest_val = dest_counts.max()
    stop_counts = df_to_display['Total_Stops'].value_counts()
    top_stop_name = stop_counts.idxmax()
    top_stop_val = stop_counts.max()
    time_counts = df_to_display['Time_Period'].value_counts()
    top_time_name = time_counts.idxmax()
    top_time_val = time_counts.max()

    kpi_configs = [
        ("Top Airline", top_airline_name, top_airline_val, "Avg Price"),
        ("Busiest Route", top_route_name, top_route_val, "Trips"),
        ("Top Destination", top_dest_name, top_dest_val, "Trips"),
        ("Top Travel Way", top_stop_name, top_stop_val, "Trips"),
        ("Peak Time", top_time_name, top_time_val, "Trips")
    ]

    st.markdown("## Key Performance Indicators")
    kpi_cols = st.columns(5)
    for i, (label, name, val, unit) in enumerate(kpi_configs):
        display_name = (str(name)[:18] + '..') if len(str(name)) > 20 else str(name)
        with kpi_cols[i]:
            if unit == "Trips":
                val_format = f"{val:,}"
            else:
                val_format = f"${val:,.0f}"

            st.markdown(f"""<div style='text-align: center; margin: 10px; padding: 10px; border: 1px solid #ccc; border-radius: 5px;'>
                <p style='font-size: 0.9em; color: gray;'>{label}</p>
                <h3 style='font-size: 1.5em; font-weight: bold; color: #1f77b4;'>{display_name}</h3>
                <p style='font-size: 0.8em; color: gray;'>{val_format} {unit}</p>
            </div>""", unsafe_allow_html=True)

    st.markdown("## Flight Data Visualizations")

    avg_price_airline = df_to_display.groupby("Airline", as_index=False)["Price"].mean().sort_values("Price", ascending=False)
    if not avg_price_airline.empty:
        fig1 = px.bar(avg_price_airline, x="Airline", y="Price", title="Average Ticket Price by Airline", color="Airline")
        fig1.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig1, width='stretch')
    else:
        st.warning("No data to display Average Ticket Price by Airline.")

    if not df_to_display.empty:
        median_prices = df_to_display.groupby('Airline')['Price'].median().sort_values(ascending=False)
        fig2 = px.box(df_to_display, x='Airline', y='Price', title='Airline by Price Distribution',
                      category_orders={"Airline": median_prices.index.tolist()}, color="Airline")
        fig2.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig2, width='stretch')
    else:
        st.warning("No data to display Airline by Price Distribution.")

    avg_price_stops = df_to_display.groupby("Total_Stops", as_index=False)["Price"].mean()
    if not avg_price_stops.empty:
        fig3 = px.pie(avg_price_stops, values='Price', names='Total_Stops', hole=0.4,
                     title='Average Price Distribution by Number of Stops (%)', color="Total_Stops")
        fig3.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig3, width='stretch')
    else:
        st.warning("No data to display Average Price Distribution by Number of Stops.")

    if not df_to_display.empty:
        median_prices_stops = df_to_display.groupby('Total_Stops')['Price'].median().sort_values(ascending=True)
        fig4 = px.box(df_to_display, x='Total_Stops', y='Price', title='Price Distribution by Number of Stops',
                      category_orders={"Total_Stops": median_prices_stops.index.tolist()}, color="Total_Stops")
        st.plotly_chart(fig4, width='stretch')
    else:
        st.warning("No data to display Price Distribution by Number of Stops.")

    average_prices_per_route = df_to_display.groupby(['Source', 'Destination'])['Price'].mean().reset_index()
    if not average_prices_per_route.empty:
        top_routes = average_prices_per_route.sort_values(by='Price', ascending=False).head(10)
        top_routes['Route'] = top_routes['Source'] + ' - ' + top_routes['Destination']
        fig5 = px.bar(top_routes, x='Route', y='Price', title='Top 10 Routes by Average Flight Price', color="Route")
        fig5.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig5, width='stretch')
    else:
        st.warning("No routes available for the selected filters to display Top 10 Routes by Average Flight Price.")

    price_volatility_per_route = df_to_display.groupby(['Source', 'Destination'])['Price'].std().reset_index()
    if not price_volatility_per_route.empty:
        top_volatility_routes = price_volatility_per_route.sort_values(by='Price', ascending=False).head(10)
        top_volatility_routes['Route'] = top_volatility_routes['Source'] + ' - ' + top_volatility_routes['Destination']
        fig6 = px.bar(top_volatility_routes, x='Route', y='Price', title='Top 10 Routes by Price Volatility', color="Route")
        fig6.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig6, width='stretch')
    else:
        st.warning("No routes available for the selected filters to display Top 10 Routes by Price Volatility.")

    average_price_by_hour = df_to_display.groupby('Departure_Hour')['Price'].mean().reset_index()
    if not average_price_by_hour.empty:
        fig7 = px.bar(average_price_by_hour, x='Departure_Hour', y='Price', title='Average Flight Price by Departure Hour', color="Departure_Hour")
        st.plotly_chart(fig7, width='stretch')
    else:
        st.warning("No data to display Average Flight Price by Departure Hour.")

    average_price_by_month = df_to_display.groupby('Journey_Month')['Price'].mean().reset_index()
    if not average_price_by_month.empty:
        fig8 = px.bar(average_price_by_month, x='Journey_Month', y='Price', title='Average Flight Price by Journey Month', color="Journey_Month")
        st.plotly_chart(fig8, width='stretch')
    else:
        st.warning("No data to display Average Flight Price by Journey Month.")

display_dashboard_content(filtered_df)
