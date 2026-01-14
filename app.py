import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from scipy.interpolate import griddata
import numpy as np

# Title
st.title("PhilOCA Ocean Acidification Data Portal")

# Google Sheets URL
sheet_url = "https://docs.google.com/spreadsheets/d/1pKbEDdcXGnvBspq_ILwkg6D6N-N56GwvRwdX6I_A9f0/export?format=csv"

# Load data
@st.cache_data
def load_data():
    data = pd.read_csv(sheet_url)
    return data

data = load_data()

# Show data table
st.subheader("Data Preview")
st.dataframe(data.head(10))

# Select parameter to visualize
st.subheader("Create Map")
parameter = st.selectbox(
    "Select parameter to visualize:",
    ["o2conc", "pco2", "temp_ctd", "temp_o2"]
)

# Filter data
map_data = data[['latitude', 'longitude', parameter]].dropna()

if len(map_data) > 3:
    # Extract coordinates and values
    lats = map_data['latitude'].values
    lons = map_data['longitude'].values
    values = map_data[parameter].values
    
    # Create grid for interpolation
    grid_lon = np.linspace(lons.min(), lons.max(), 100)
    grid_lat = np.linspace(lats.min(), lats.max(), 100)
    grid_lon, grid_lat = np.meshgrid(grid_lon, grid_lat)
    
    # Interpolate
    grid_values = griddata(
        (lons, lats), 
        values, 
        (grid_lon, grid_lat), 
        method='cubic'
    )
    
    # Create Plotly contour map
    fig = go.Figure(data=go.Contour(
        z=grid_values,
        x=grid_lon[0],
        y=grid_lat[:,0],
        colorscale='YlOrRd',
        contours=dict(
            showlabels=True,
            labelfont=dict(size=12, color='white')
        ),
        colorbar=dict(title=parameter)
    ))
    
    # Update layout
    fig.update_layout(
        title=f'{parameter} Distribution',
        xaxis_title='Longitude',
        yaxis_title='Latitude',
        width=800,
        height=600
    )
    
    # Display
    st.plotly_chart(fig)
else:
    st.error("Not enough data to create map. Need at least 4 data points.")