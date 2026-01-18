import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from scipy.interpolate import griddata
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from io import BytesIO
import base64

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
    "pco2": None,
    "o2conc": None,
    "temp_ctd": None,
    "temp_o2": None
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
        help="Reference value for comparison"
    )
else:
    threshold = st.sidebar.number_input(
        f"Set threshold for {parameter}:",
        value=0.0,
        step=1.0,
        help="Reference value for comparison"
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
    n_points = 200
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
    
    # Create matplotlib contour plot as PNG
    matplotlib.use('Agg')
    fig_mpl = plt.figure(figsize=(10, 10))
    ax_mpl = fig_mpl.add_axes([0, 0, 1, 1])
    
    # Create filled contours
    ax_mpl.contourf(
        grid_lon_mesh, 
        grid_lat_mesh, 
        grid_values,
        levels=15,
        cmap='coolwarm',
        alpha=1.0,
        vmin=np.nanmin(grid_values),
        vmax=np.nanmax(grid_values)
    )
    
    # Add contour lines
    contour_lines = ax_mpl.contour(
        grid_lon_mesh,
        grid_lat_mesh,
        grid_values,
        levels=10,
        colors='black',
        linewidths=1.0
    )
    
    ax_mpl.clabel(contour_lines, inline=True, fontsize=9, fmt='%.0f')
    ax_mpl.set_xlim(lon_min - lon_padding, lon_max + lon_padding)
    ax_mpl.set_ylim(lat_min - lat_padding, lat_max + lat_padding)
    ax_mpl.axis('off')
    
    # Save to bytes
    buf = BytesIO()
    fig_mpl.savefig(buf, format='png', bbox_inches='tight', pad_inches=0, transparent=True, dpi=200)
    buf.seek(0)
    plt.close(fig_mpl)
    
    # Calculate center
    center_lat = (lat_min + lat_max) / 2
    center_lon = (lon_min + lon_max) / 2
    
    # Create Folium map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=12,
        tiles='OpenStreetMap'
    )
    
    # Add image overlay
    folium.raster_layers.ImageOverlay(
        name='Contours',
        image=f'data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}',
        bounds=[[lat_min - lat_padding, lon_min - lon_padding], 
                [lat_max + lat_padding, lon_max + lon_padding]],
        opacity=0.6,
        interactive=True,
        cross_origin=False,
        zindex=1
    ).add_to(m)
    
    # Add sampling points if enabled
    if show_points:
        for i, (lat, lon, val) in enumerate(zip(lats, lons, values)):
            folium.CircleMarker(
                location=[lat, lon],
                radius=5,
                color='black',
                fill=True,
                fillColor='black',
                fillOpacity=1,
                popup=f'<b>Sample Point</b><br>Value: {val:.2f}<br>Lat: {lat:.4f}<br>Lon: {lon:.4f}',
                tooltip=f'{val:.2f}'
            ).add_to(m)
    
    # Display map in Streamlit
    st_folium(m, width=None, height=700)
    
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