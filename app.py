import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from scipy.interpolate import griddata
import numpy as np

# Page config
st.set_page_config(
    page_title="PhilOCA Data Portal",
    page_icon="🌊",
    layout="wide"
)

# Title
st.title("PhilOCA Ocean Acidification Data Portal")
st.markdown("### Philippine Ocean and Coastal Acidification Monitoring")
st.markdown("---")

# Google Sheets URL
sheet_url = "https://docs.google.com/spreadsheets/d/1pKbEDdcXGnvBspq_ILwkg6D6N-N56GwvRwdX6I_A9f0/export?format=csv"

# Thresholds for each parameter
THRESHOLDS = {
    "pco2": None,  # Set if needed (ppm)
    "o2conc": None,  # Set if needed
    "temp_ctd": None,  # Set if needed
    "temp_o2": None  # Set if needed
}

# Load data
@st.cache_data
def load_data():
    data = pd.read_csv(sheet_url)
    return data

data = load_data()

# Sidebar
st.sidebar.header("Controls")
parameter = st.sidebar.selectbox(
    "Select Parameter:",
    ["pco2", "o2conc", "temp_ctd", "temp_o2"],
    format_func=lambda x: {
        "o2conc": "O₂ Concentration",
        "pco2": "pCO₂",
        "temp_ctd": "Temperature (CTD)",
        "temp_o2": "Temperature (O₂)"
    }[x]
)

# Threshold input
threshold = THRESHOLDS.get(parameter)
if threshold:
    threshold = st.sidebar.number_input(
        f"Threshold for {parameter}:",
        value=float(threshold),
        step=1.0,
        help="Values above threshold = red (bad), below = green (good)"
    )
else:
    threshold = st.sidebar.number_input(
        f"Set threshold for {parameter}:",
        value=0.0,
        step=1.0,
        help="Values above threshold = red (bad), below = green (good)"
    )

show_data = st.sidebar.checkbox("Show Raw Data", value=False)

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Total Records:** {len(data)}")
if threshold:
    st.sidebar.markdown(f"**Threshold:** {threshold}")

# Main layout
st.subheader(f"{parameter.upper()} Distribution Map")

# Filter data
map_data = data[['latitude', 'longitude', parameter]].dropna()

if len(map_data) > 3:
    lats = map_data['latitude'].values
    lons = map_data['longitude'].values
    values = map_data[parameter].values
    
    # Classify points as above/below threshold
    above_threshold = values > threshold
    below_threshold = values <= threshold
    
    # Create figure
    fig = go.Figure()
    
    # Add heatmap layer for ALL data
    fig.add_trace(go.Densitymapbox(
        lat=lats,
        lon=lons,
        z=values,
        radius=15,
        colorscale=[
            [0, 'green'],      # Low values = good (green)
            [0.5, 'yellow'],   # Mid values
            [1, 'red']         # High values = bad (red)
        ],
        showscale=True,
        zmin=values.min(),
        zmax=values.max(),
        colorbar=dict(
            title=parameter,
            x=1.02
        ),
        hovertemplate='<b>%{z:.2f}</b><br>Lat: %{lat:.4f}<br>Lon: %{lon:.4f}<extra></extra>',
        name='Distribution'
    ))
    
    # Add points ABOVE threshold (red - bad)
    if above_threshold.any():
        fig.add_trace(go.Scattermapbox(
            lat=lats[above_threshold],
            lon=lons[above_threshold],
            mode='markers',
            marker=dict(
                size=10,
                color='red',
                opacity=0.9,
                symbol='circle'
            ),
            text=[f"⚠️ {v:.2f}" for v in values[above_threshold]],
            hovertemplate='<b>ABOVE THRESHOLD</b><br>Value: %{text}<br>Lat: %{lat:.4f}<br>Lon: %{lon:.4f}<extra></extra>',
            name=f'> {threshold} (Above Threshold)'
        ))
    
    # Add points BELOW threshold (green - good)
    if below_threshold.any():
        fig.add_trace(go.Scattermapbox(
            lat=lats[below_threshold],
            lon=lons[below_threshold],
            mode='markers',
            marker=dict(
                size=10,
                color='green',
                opacity=0.9,
                symbol='circle'
            ),
            text=[f"✓ {v:.2f}" for v in values[below_threshold]],
            hovertemplate='<b>BELOW THRESHOLD</b><br>Value: %{text}<br>Lat: %{lat:.4f}<br>Lon: %{lon:.4f}<extra></extra>',
            name=f'< {threshold} (Below Threshold)'
        ))
    
    # Calculate center and zoom
    center_lat = (lats.min() + lats.max()) / 2
    center_lon = (lons.min() + lons.max()) / 2
    
    # Update layout
    fig.update_layout(
        mapbox=dict(
            style='open-street-map',
            center=dict(lat=center_lat, lon=center_lon),
            zoom=10
        ),
        height=700,
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(255,255,255,0.8)"
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Statistics at bottom
    st.markdown("---")
    st.subheader("Statistics")
    
    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    
    stats = map_data[parameter]
    
    with col1:
        st.metric("Mean", f"{stats.mean():.2f}")
    with col2:
        st.metric("Median", f"{stats.median():.2f}")
    with col3:
        st.metric("Std Dev", f"{stats.std():.2f}")
    with col4:
        st.metric("Min", f"{stats.min():.2f}")
    with col5:
        st.metric("Max", f"{stats.max():.2f}")
    with col6:
        above_count = above_threshold.sum()
        st.metric("Above Threshold", above_count, delta=f"{(above_count/len(values)*100):.1f}%", delta_color="inverse")
    with col7:
        below_count = below_threshold.sum()
        st.metric("Below Threshold", below_count, delta=f"{(below_count/len(values)*100):.1f}%", delta_color="normal")
        
else:
    st.error("❌ Not enough data points.")

if show_data:
    st.markdown("---")
    st.subheader("Raw Data")
    st.dataframe(data, use_container_width=True)

st.markdown("---")
st.markdown("<div style='text-align: center; color: gray;'>PhilOCA/HOLCIM | MSI, UP Diliman</div>", unsafe_allow_html=True)