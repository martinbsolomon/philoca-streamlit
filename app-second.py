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

show_points = st.sidebar.checkbox("Show Sampling Points", value=True)
show_data = st.sidebar.checkbox("Show Raw Data", value=False)

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Total Records:** {len(data)}")

# Main layout
st.subheader(f"{parameter.upper()} Distribution Map")

# Filter data
map_data = data[['latitude', 'longitude', parameter]].dropna()

if len(map_data) > 3:
    lats = map_data['latitude'].values
    lons = map_data['longitude'].values
    values = map_data[parameter].values
    
    # Create interpolation grid
    lat_min, lat_max = lats.min(), lats.max()
    lon_min, lon_max = lons.min(), lons.max()
    
    # Padding
    lat_padding = (lat_max - lat_min) * 0.05
    lon_padding = (lon_max - lon_min) * 0.05
    
    # Create grid
    n_points = 100
    grid_lat = np.linspace(lat_min - lat_padding, lat_max + lat_padding, n_points)
    grid_lon = np.linspace(lon_min - lon_padding, lon_max + lon_padding, n_points)
    grid_lon_mesh, grid_lat_mesh = np.meshgrid(grid_lon, grid_lat)
    
    # Interpolate
    grid_values = griddata(
        (lons, lats), 
        values, 
        (grid_lon_mesh, grid_lat_mesh), 
        method='cubic'
    )
    
    # Create figure
    fig = go.Figure()
    
    # Add filled contour
    fig.add_trace(go.Contour(
        x=grid_lon,
        y=grid_lat,
        z=grid_values,
        colorscale='RdBu_r',
        contours=dict(
            coloring='heatmap',
            showlabels=True,
            labelfont=dict(size=10, color='black'),
        ),
        colorbar=dict(
            title=dict(text=parameter, side='right'),
            thickness=20,
            len=0.9
        ),
        hovertemplate='Value: %{z:.2f}<br>Lat: %{y:.4f}<br>Lon: %{x:.4f}<extra></extra>'
    ))
    
    # Add contour lines
    fig.add_trace(go.Contour(
        x=grid_lon,
        y=grid_lat,
        z=grid_values,
        showscale=False,
        contours=dict(
            coloring='lines',
            showlabels=True,
            labelfont=dict(size=9, color='black'),
        ),
        line=dict(color='black', width=1),
        hoverinfo='skip'
    ))
    
    # Add sampling points if enabled
    if show_points:
        fig.add_trace(go.Scatter(
            x=lons,
            y=lats,
            mode='markers',
            marker=dict(
                size=8,
                color='black',
                symbol='circle'
            ),
            text=[f"{v:.2f}" for v in values],
            hovertemplate='<b>Sample Point</b><br>Value: %{text}<br>Lat: %{y:.4f}<br>Lon: %{x:.4f}<extra></extra>',
            name='Sampling Points'
        ))
    
    # Update layout - no map, just plot
    fig.update_layout(
        xaxis=dict(
            title='Longitude',
            showgrid=True,
            gridcolor='lightgray'
        ),
        yaxis=dict(
            title='Latitude',
            scaleanchor='x',
            showgrid=True,
            gridcolor='lightgray'
        ),
        height=700,
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(255,255,255,0.8)"
        ),
        plot_bgcolor='white'
    )

    fig.update_xaxes(fixedrange=False)
    fig.update_yaxes(fixedrange=False)
    
    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})
    
    # Statistics at bottom
    st.markdown("---")
    st.subheader("Statistics")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
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
        
else:
    st.error("❌ Not enough data points.")

if show_data:
    st.markdown("---")
    st.subheader("Raw Data")
    st.dataframe(data, use_container_width=True)

st.markdown("---")
st.markdown("<div style='text-align: center; color: gray;'>PhilOCA/HOLCIM | MSI, UP Diliman</div>", unsafe_allow_html=True)