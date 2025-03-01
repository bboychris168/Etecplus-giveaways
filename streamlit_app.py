import streamlit as st
import pandas as pd
import math

# Set page config FIRST
st.set_page_config(
    page_title="🏆 Location Giveaway",
    page_icon="📍",
    layout="wide"
)

# Dark mode CSS styling
st.markdown("""
<style>
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    h1, h2, h3 {
        color: #FFFFFF !important;
        font-family: 'Arial', sans-serif;
    }
    .card {
        background-color: #1A1C21;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #2E3035;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    .winner-banner {
        background: #2E7D32;
        color: white;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        margin: 20px 0;
        border: 2px solid #4CAF50;
    }
    .map-container {
        border: 2px solid #2E3035;
        border-radius: 15px;
        overflow: hidden;
        margin: 15px 0;
        background-color: #0E1117;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = 'upload'
if 'participants' not in st.session_state:
    st.session_state.participants = None
if 'winner' not in st.session_state:
    st.session_state.winner = None

# Constants
GIVEAWAY_LOCATION = (-33.867582661116245, 151.05560569089798)

@st.cache_data
def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance using Haversine formula (in km)"""
    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)
    
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return 6371 * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

# Page 1: Upload CSV
def upload_page():
    st.title("📤 Upload Participants")
    with st.expander("📋 CSV Format Help"):
        st.write("""
        **Required format:**
        ```
        name,coordinates
        John Doe,-33.867582661116245,151.05560569089798
        Jane Smith,40.7128,-74.0060
        ```
        """)
    
    uploaded_file = st.file_uploader("Upload Participant CSV", type=["csv"])
    
    if uploaded_file:
        try:
            participants = pd.read_csv(uploaded_file)
            
            if list(participants.columns) != ['name', 'coordinates']:
                st.error("Invalid columns. Must be: name, coordinates")
                return
                
            coord_split = participants['coordinates'].str.split(r'\s*,\s*', n=1, expand=True)
            if coord_split.shape[1] != 2:
                st.error("Invalid coordinates format")
                return
                
            participants['latitude'] = pd.to_numeric(coord_split[0])
            participants['longitude'] = pd.to_numeric(coord_split[1])
            
            participants['distance_km'] = participants.apply(
                lambda row: calculate_distance(
                    GIVEAWAY_LOCATION[0], GIVEAWAY_LOCATION[1],
                    row['latitude'], row['longitude']
                ), axis=1
            )
            
            st.session_state.participants = participants
            st.success("✅ File uploaded successfully!")
            st.session_state.page = 'map'
            st.rerun()
            
        except Exception as e:
            st.error(f"Error: {str(e)}")

# Page 2: Map View
def map_page():
    st.title("🗺️ Players Map")
    
    if st.session_state.participants is None:
        st.error("No data available. Please upload a CSV first.")
        return
    
    map_df = pd.concat([
        pd.DataFrame({
            'lat': [GIVEAWAY_LOCATION[0]],
            'lon': [GIVEAWAY_LOCATION[1]],
            'name': ['Giveaway Location'],
            'color': ['#FF0000'],
            'size': [100]
        }),
        pd.DataFrame({
            'lat': st.session_state.participants['latitude'],
            'lon': st.session_state.participants['longitude'],
            'name': st.session_state.participants['name'],
            'color': ['#2196F3']*len(st.session_state.participants),
            'size': [20]*len(st.session_state.participants)
        })
    ])
    
    with st.container():
        st.markdown("<div class='map-container'>", unsafe_allow_html=True)
        st.map(map_df,
              latitude='lat',
              longitude='lon',
              color='color',
              size='size',
              zoom=12)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Fixed Draw Winner button
    if st.button("🎲 Draw Winner", use_container_width=True):
        if st.session_state.participants is not None:
            st.session_state.winner = st.session_state.participants.loc[
                st.session_state.participants['distance_km'].idxmin()
            ].copy()
            st.session_state.page = 'winner'
            st.rerun()

# Page 3: Winner with Leaderboard
def winner_page():
    st.title("🏆 Winner Selection")
    
    if st.session_state.participants is None or st.session_state.winner is None:
        st.error("No winner data available. Please draw a winner first.")
        st.session_state.page = 'upload'
        st.rerun()
        return
    
    st.balloons()
    st.markdown(f"""
    <div class='winner-banner'>
        <h2>🏆 Winner: {st.session_state.winner['name'].upper()} 🏆</h2>
        <h3>{st.session_state.winner['distance_km']:.2f} km from prize</h3>
    </div>
    """, unsafe_allow_html=True)

    # Combined map with all participants and winner
    winner_map_df = pd.concat([
        pd.DataFrame({
            'lat': [GIVEAWAY_LOCATION[0]],
            'lon': [GIVEAWAY_LOCATION[1]],
            'name': ['Giveaway Location'],
            'color': ['#FF0000'],
            'size': [100]
        }),
        pd.DataFrame({
            'lat': st.session_state.participants['latitude'],
            'lon': st.session_state.participants['longitude'],
            'name': st.session_state.participants['name'],
            'color': ['#2196F3']*len(st.session_state.participants),
            'size': [20]*len(st.session_state.participants)
        }),
        pd.DataFrame({
            'lat': [st.session_state.winner['latitude']],
            'lon': [st.session_state.winner['longitude']],
            'name': [f"Winner: {st.session_state.winner['name']}"],
            'color': ['#4CAF50'],
            'size': [200]
        })
    ])

    with st.container():
        st.markdown("<div class='map-container'>", unsafe_allow_html=True)
        st.subheader("🗺️ All Participants with Winner")
        st.map(winner_map_df,
              latitude='lat',
              longitude='lon',
              color='color',
              size='size',
              zoom=12)
        st.markdown("</div>", unsafe_allow_html=True)

    # Leaderboard Section
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("🏅 Closest Participants Leaderboard")
        closest = st.session_state.participants.sort_values('distance_km').reset_index(drop=True)
        st.dataframe(
            closest[['name', 'distance_km']].head(10)
            .style.format({'distance_km': '{:.2f} km'}),
            use_container_width=True
        )
        st.markdown("</div>", unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.title("Navigation")
pages = {
    "📤Upload CSV": "upload",
    "🗺️View Map": "map",
    "🏆Winner": "winner"
}

# Get current page index for radio selection
page_names = list(pages.keys())
page_values = list(pages.values())
current_index = page_values.index(st.session_state.page) if st.session_state.page in page_values else 0

# Display radio and update page
selected_page = st.sidebar.radio("Go to", page_names, index=current_index)
st.session_state.page = pages[selected_page]

# Page routing
if st.session_state.page == 'upload':
    upload_page()
elif st.session_state.page == 'map':
    map_page()
elif st.session_state.page == 'winner':
    winner_page()