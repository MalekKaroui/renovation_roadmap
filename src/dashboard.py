"""
dashboard.py
Interactive Streamlit Dashboard for The Renovation Roadmap
Run with: streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import numpy as np

# Page config
st.set_page_config(
    page_title="The Renovation Roadmap",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .finding-box {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Data paths
DATA_DIR = Path("data")
FIGURES_DIR = Path("outputs/figures")

# Load data functions
@st.cache_data
def load_grid_stats():
    """Load grid-level statistics"""
    try:
        return pd.read_csv(DATA_DIR / "grid_stats.csv")
    except:
        return None

@st.cache_data
def load_iar_results():
    """Load IAR analysis results"""
    try:
        return pd.read_csv(DATA_DIR / "assessment_integration.csv")
    except:
        return None

@st.cache_data
def load_temporal_data():
    """Load temporal analysis"""
    try:
        return pd.read_csv(DATA_DIR / "temporal_analysis.csv")
    except:
        return None

@st.cache_data
def load_getis_ord():
    """Load hotspot analysis"""
    try:
        return pd.read_csv(DATA_DIR / "getis_ord_results.csv")
    except:
        return None

@st.cache_data
def load_permits_data():
    """Load cleaned permits"""
    try:
        return pd.read_csv(DATA_DIR / "permits_cleaned.csv", parse_dates=["BPISDT"])
    except:
        return None

# Header
st.markdown('<div class="main-header">🏙️ The Renovation Roadmap</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Predicting Urban Gentrification in Saint John, NB</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://via.placeholder.com/300x100/1f77b4/ffffff?text=UNB+CS+4403", use_container_width=True)
    st.markdown("### Project Info")
    st.info("""
    **Author:** Malek Karoui (3751935)  
    **Course:** CS 4403 Data Mining  
    **Institution:** University of New Brunswick
    """)
    
    st.markdown("### Navigation")
    page = st.radio(
        "Select View:",
        ["📊 Executive Summary", "🗺️ Spatial Analysis", "📈 Temporal Trends", 
         "🔥 Hotspot Detection", "💰 IAR Analysis", "📉 Raw Data Explorer"]
    )
    
    st.markdown("---")
    st.markdown("### Quick Stats")
    permits_df = load_permits_data()
    if permits_df is not None:
        st.metric("Total Permits", f"{len(permits_df):,}")
        st.metric("Total Investment", f"${permits_df['BPEVAL'].sum():,.0f}")
        st.metric("Mean Value", f"${permits_df['BPEVAL'].mean():,.0f}")

# Load all data
grid_stats = load_grid_stats()
iar_results = load_iar_results()
temporal_data = load_temporal_data()
getis_ord = load_getis_ord()
permits_df = load_permits_data()

# ============================================================================
# PAGE 1: EXECUTIVE SUMMARY
# ============================================================================
if page == "📊 Executive Summary":
    st.header("Executive Summary")
    
    # Key Findings
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>15</h3>
            <p>Pre-Gentrification Zones</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>1</h3>
            <p>Statistical Hotspot</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>71%</h3>
            <p>Max Annual Growth</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h3>21.1</h3>
            <p>Highest IAR Ratio</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # The Problem
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🎯 The Problem")
        st.markdown("""
        <div class="finding-box">
        Cities typically react to gentrification <b>after</b> it happens:
        <ul>
            <li>Property values have already spiked</li>
            <li>Residents are being displaced</li>
            <li>Infrastructure is overwhelmed</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.subheader("💡 The Solution")
        st.markdown("""
        <div class="finding-box">
        Detect gentrification <b>2-3 years early</b> using:
        <ul>
            <li><b>Building permits</b> as leading indicators</li>
            <li><b>Investment-Assessment Ratio (IAR)</b> metric</li>
            <li><b>Spatial statistics</b> (Getis-Ord G*ᵢ)</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.subheader("📊 Dashboard Preview")
        if (FIGURES_DIR / "08_dashboard.png").exists():
            st.image(str(FIGURES_DIR / "08_dashboard.png"), use_container_width=True)
    
    st.markdown("---")
    
    # Top Findings
    st.subheader("🔍 Key Findings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 🚀 Explosive Growth Cell")
        st.info("""
        **GRID_10_10** shows 71% annual growth:
        - 2015-16 mean: $12,000
        - 2023-25 mean: $585,420
        - **48× increase** over 10 years
        
        ➡️ *Classic pre-gentrification trajectory*
        """)
    
    with col2:
        st.markdown("##### ⚠️ Highest IAR Signal")
        st.warning("""
        **GRID_03_16** has IAR = 21.1:
        - Mean permit value: $2,215,000
        - Mean assessment: $104,893
        - **21× gap** between investment and official value
        
        ➡️ *Severe investment-value decoupling*
        """)
    
    # Methodology
    st.markdown("---")
    st.subheader("🛠️ Methodology")
    
    method_col1, method_col2, method_col3 = st.columns(3)
    
    with method_col1:
        st.markdown("**1. Data Processing**")
        st.text("""
        • 30,287 raw permits
        • ↓ Cleaning & deduplication
        • 1,098 high-quality records
        • Grid-based aggregation
        """)
    
    with method_col2:
        st.markdown("**2. Clustering**")
        st.text("""
        • K-Means (k=6)
        • DBSCAN (density-based)
        • Feature engineering
        • Cross-validation
        """)
    
    with method_col3:
        st.markdown("**3. Statistical Testing**")
        st.text("""
        • Getis-Ord G*ᵢ
        • Monte Carlo permutations
        • IAR calculation
        • Temporal CAGR
        """)

# ============================================================================
# PAGE 2: SPATIAL ANALYSIS
# ============================================================================
elif page == "🗺️ Spatial Analysis":
    st.header("Spatial Distribution Analysis")
    
    if grid_stats is not None:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Permit Density Heatmap")
            if (FIGURES_DIR / "02_permit_density_grid.png").exists():
                st.image(str(FIGURES_DIR / "02_permit_density_grid.png"), 
                        use_container_width=True,
                        caption="1km × 1km grid cells colored by permit count")
        
        with col2:
            st.subheader("Top 10 Cells")
            top_10 = grid_stats.nlargest(10, 'permit_count')[['GRID_ID', 'permit_count', 'mean_value']]
            st.dataframe(top_10, use_container_width=True, hide_index=True)
            
            st.metric("Most Active Cell", "GRID_10_10")
            st.metric("Permits", "75")
            st.metric("Mean Value", "$585,420")
        
        st.markdown("---")
        
        # Interactive scatter plot
        st.subheader("Interactive Permit Value Distribution")
        
        fig = px.scatter(
            grid_stats,
            x='permit_count',
            y='mean_value',
            size='total_value',
            hover_data=['GRID_ID'],
            labels={
                'permit_count': 'Number of Permits',
                'mean_value': 'Mean Permit Value (CAD)',
                'total_value': 'Total Investment'
            },
            title='Grid Cell Activity: Count vs Value',
            color='mean_value',
            color_continuous_scale='Viridis'
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Grid statistics not found. Run the analysis pipeline first.")

# ============================================================================
# PAGE 3: TEMPORAL TRENDS
# ============================================================================
elif page == "📈 Temporal Trends":
    st.header("Temporal Evolution (2015-2025)")
    
    if permits_df is not None:
        # Permits per year
        st.subheader("Permit Activity Over Time")
        
        permits_per_year = permits_df.groupby('YEAR').size().reset_index(name='count')
        
        fig = px.bar(
            permits_per_year,
            x='YEAR',
            y='count',
            title='Building Permits Issued Per Year',
            labels={'count': 'Number of Permits', 'YEAR': 'Year'},
            color='count',
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("Temporal Heatmap")
            if (FIGURES_DIR / "06_grid_heatmap.png").exists():
                st.image(str(FIGURES_DIR / "06_grid_heatmap.png"), 
                        use_container_width=True,
                        caption="Top 15 cells: value evolution over time windows")
        
        with col2:
            st.subheader("City-Wide Trend")
            if (FIGURES_DIR / "06_city_trend.png").exists():
                st.image(str(FIGURES_DIR / "06_city_trend.png"), 
                        use_container_width=True,
                        caption="Mean permit value per time window")
        
        # CAGR distribution
        if temporal_data is not None:
            st.markdown("---")
            st.subheader("Growth Rate Distribution")
            
            cagr_clean = temporal_data['CAGR'].dropna() * 100
            
            fig = px.histogram(
                cagr_clean,
                nbins=30,
                title='Compound Annual Growth Rate (CAGR) Distribution',
                labels={'value': 'CAGR (%)', 'count': 'Number of Grid Cells'},
                color_discrete_sequence=['#43A047']
            )
            fig.add_vline(x=0, line_dash="dash", line_color="black")
            st.plotly_chart(fig, use_container_width=True)
            
            # Highlight emerging cell
            st.success("""
            **🚀 EMERGING CELL DETECTED:**  
            GRID_10_10 has CAGR = 71% — the highest growth rate in the city.
            """)

# ============================================================================
# PAGE 4: HOTSPOT DETECTION
# ============================================================================
elif page == "🔥 Hotspot Detection":
    st.header("Getis-Ord G*ᵢ Hotspot Analysis")
    
    st.info("""
    **What is Getis-Ord G*ᵢ?**  
    A spatial statistic that identifies areas where high (or low) values cluster 
    significantly beyond what random chance would produce. A z-score > 1.96 (p<0.05) 
    indicates a statistically significant hotspot.
    """)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Hotspot Map")
        if (FIGURES_DIR / "05_hotspot_map.png").exists():
            st.image(str(FIGURES_DIR / "05_hotspot_map.png"), 
                    use_container_width=True,
                    caption="Red outline = significant hotspot (p<0.05)")
    
    with col2:
        st.subheader("Classification Results")
        if getis_ord is not None:
            counts = getis_ord['hotspot'].value_counts()
            st.dataframe(counts.reset_index(), 
                        column_config={
                            "index": "Classification",
                            "hotspot": "Count"
                        },
                        hide_index=True)
            
            # Show the significant hotspot
            hot = getis_ord[getis_ord['hotspot'].str.startswith('Hot', na=False)]
            if len(hot) > 0:
                st.success(f"""
                **Significant Hotspot Found:**  
                {hot.iloc[0]['GRID_ID']}  
                z-score: {hot.iloc[0]['Gi_star']:.2f}  
                p-value: {hot.iloc[0]['p_value']:.3f}
                """)
    
    # Distribution
    if getis_ord is not None:
        st.markdown("---")
        st.subheader("G*ᵢ Z-Score Distribution")
        
        fig = px.histogram(
            getis_ord,
            x='Gi_star',
            nbins=30,
            title='Distribution of Getis-Ord Z-Scores',
            labels={'Gi_star': 'G*ᵢ Z-Score', 'count': 'Number of Cells'},
            color_discrete_sequence=['#78909C']
        )
        fig.add_vline(x=1.96, line_dash="dash", line_color="red", 
                     annotation_text="p<0.05 threshold")
        fig.add_vline(x=-1.96, line_dash="dash", line_color="blue")
        st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# PAGE 5: IAR ANALYSIS
# ============================================================================
elif page == "💰 IAR Analysis":
    st.header("Investment-Assessment Ratio (IAR)")
    
    st.markdown("""
    ### The Core Metric
    
    $$
    \\text{IAR} = \\frac{\\text{Mean Permit Value}}{\\text{Mean Assessed Property Value}}
    $$
    
    **Why it matters:**  
    High IAR in low-assessment areas indicates capital flowing into undervalued neighborhoods 
    *before* property tax assessments adjust — a 2-3 year leading indicator of gentrification.
    """)
    
    if iar_results is not None:
        # Scatter plot
        st.subheader("Investment vs Assessment Scatter")
        if (FIGURES_DIR / "07_investment_vs_assessment.png").exists():
            st.image(str(FIGURES_DIR / "07_investment_vs_assessment.png"), 
                    use_container_width=True,
                    caption="Red dots = pre-gentrification signals (high IAR + low assessment)")
        
        st.markdown("---")
        
        # Top IAR cells
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("Top 10 High-IAR Cells")
            top_iar = iar_results.nlargest(10, 'IAR')[
                ['GRID_ID', 'IAR', 'mean_value', 'mean_assessment']
            ]
            st.dataframe(
                top_iar.style.format({
                    'IAR': '{:.2f}',
                    'mean_value': '${:,.0f}',
                    'mean_assessment': '${:,.0f}'
                }),
                use_container_width=True,
                hide_index=True
            )
        
        with col2:
            st.subheader("Pre-Gentrification Signals")
            pregen = iar_results[iar_results['signal'] == '⚠️ Pre-Gentrification Signal']
            st.metric("Cells Flagged", len(pregen))
            
            st.warning(f"""
            **Highest Risk Cell:**  
            {pregen.iloc[0]['GRID_ID']}  
            IAR: {pregen.iloc[0]['IAR']:.1f}  
            Permit avg: ${pregen.iloc[0]['mean_value']:,.0f}  
            Assessment avg: ${pregen.iloc[0]['mean_assessment']:,.0f}
            """)
        
        # IAR distribution
        st.markdown("---")
        st.subheader("IAR Distribution")
        
        fig = px.histogram(
            iar_results,
            x='IAR',
            nbins=40,
            title='Investment-Assessment Ratio Distribution',
            labels={'IAR': 'IAR Value', 'count': 'Number of Cells'},
            color_discrete_sequence=['#E53935']
        )
        fig.add_vline(x=1, line_dash="dash", line_color="black",
                     annotation_text="IAR = 1 (balanced)")
        st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# PAGE 6: RAW DATA EXPLORER
# ============================================================================
elif page == "📉 Raw Data Explorer":
    st.header("Raw Data Explorer")
    
    st.markdown("Explore the underlying datasets used in this analysis.")
    
    dataset = st.selectbox(
        "Select Dataset:",
        ["Cleaned Permits", "Grid Statistics", "IAR Results", 
         "Temporal Analysis", "Getis-Ord Results"]
    )
    
    if dataset == "Cleaned Permits" and permits_df is not None:
        st.subheader(f"Cleaned Permits ({len(permits_df):,} records)")
        st.dataframe(permits_df.head(100), use_container_width=True)
        
        # Download button
        csv = permits_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "Download Full Dataset",
            csv,
            "permits_cleaned.csv",
            "text/csv",
            key='download-permits'
        )
    
    elif dataset == "Grid Statistics" and grid_stats is not None:
        st.subheader(f"Grid Cell Statistics ({len(grid_stats):,} cells)")
        st.dataframe(grid_stats, use_container_width=True)
    
    elif dataset == "IAR Results" and iar_results is not None:
        st.subheader(f"IAR Analysis ({len(iar_results):,} cells)")
        st.dataframe(iar_results, use_container_width=True)
    
    elif dataset == "Temporal Analysis" and temporal_data is not None:
        st.subheader("Temporal Analysis Results")
        st.dataframe(temporal_data, use_container_width=True)
    
    elif dataset == "Getis-Ord Results" and getis_ord is not None:
        st.subheader(f"Hotspot Analysis ({len(getis_ord):,} cells)")
        st.dataframe(getis_ord, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9rem;'>
    <b>The Renovation Roadmap</b> | Malek Karoui (3751935) | CS 4403 Data Mining | UNB 2026<br>
    📧 malek.karoui@unb.ca | 🔗 <a href='https://github.com/MalekKaroui/renovation-roadmap'>GitHub Repository</a>
</div>
""", unsafe_allow_html=True)
"""
dashboard.py

Interactive Streamlit dashboard for The Renovation Roadmap.
This dashboard presents the main project findings, figures,
and processed datasets in a simple browser interface.

Run with:
    streamlit run src/dashboard.py
"""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


DATA_DIR = Path("data")
FIGURES_DIR = Path("outputs/figures")

PRE_GENTRIFICATION_LABEL = "Pre-Gentrification Signal"
EMERGING_LABEL = "Emerging"


# -----------------------------------------------------------------------------
# Page setup
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="The Renovation Roadmap",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# -----------------------------------------------------------------------------
# Styling
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
        .main-header {
            font-size: 3rem;
            font-weight: bold;
            color: #1f77b4;
            text-align: center;
            margin-bottom: 0.5rem;
        }
        .sub-header {
            font-size: 1.2rem;
            color: #666;
            text-align: center;
            margin-bottom: 2rem;
        }
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1.5rem;
            border-radius: 10px;
            color: white;
            text-align: center;
        }
        .finding-box {
            background: #f0f2f6;
            padding: 1rem;
            border-radius: 5px;
            border-left: 4px solid #1f77b4;
            margin: 1rem 0;
        }
    </style>
    """,
    unsafe_allow_html=True
)


# -----------------------------------------------------------------------------
# Data loading
# -----------------------------------------------------------------------------
@st.cache_data
def load_csv(filename, parse_dates=None):
    """
    Load a CSV file from the data folder.
    Returns None if the file does not exist or cannot be read.
    """
    file_path = DATA_DIR / filename

    try:
        return pd.read_csv(file_path, parse_dates=parse_dates)
    except Exception:
        return None


@st.cache_data
def load_grid_stats():
    return load_csv("grid_stats.csv")


@st.cache_data
def load_iar_results():
    return load_csv("assessment_integration.csv")


@st.cache_data
def load_temporal_results():
    return load_csv("temporal_analysis.csv")


@st.cache_data
def load_hotspot_results():
    return load_csv("getis_ord_results.csv")


@st.cache_data
def load_cleaned_permits():
    return load_csv("permits_cleaned.csv", parse_dates=["BPISDT"])


# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------
def image_exists(filename):
    return (FIGURES_DIR / filename).exists()


def show_figure(filename, caption=None):
    """
    Display a figure if it exists.
    """
    figure_path = FIGURES_DIR / filename
    if figure_path.exists():
        st.image(str(figure_path), use_container_width=True, caption=caption)


def build_sidebar(permits_df):
    """
    Render the sidebar and return the selected page.
    """
    with st.sidebar:
        st.markdown("### Project Info")
        st.info(
            """
            **Author:** Malek Karoui (3751935)  
            **Course:** CS 4403 Data Mining  
            **Institution:** University of New Brunswick
            """
        )

        st.markdown("### Navigation")
        selected_page = st.radio(
            "Select View:",
            [
                "Executive Summary",
                "Spatial Analysis",
                "Temporal Trends",
                "Hotspot Detection",
                "IAR Analysis",
                "Raw Data Explorer",
            ]
        )

        st.markdown("---")
        st.markdown("### Quick Stats")

        if permits_df is not None:
            st.metric("Total Permits", f"{len(permits_df):,}")
            st.metric("Total Investment", f"${permits_df['BPEVAL'].sum():,.0f}")
            st.metric("Mean Value", f"${permits_df['BPEVAL'].mean():,.0f}")

    return selected_page


# -----------------------------------------------------------------------------
# Page sections
# -----------------------------------------------------------------------------
def show_header():
    st.markdown(
        '<div class="main-header">The Renovation Roadmap</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="sub-header">Predicting Urban Gentrification in Saint John, NB</div>',
        unsafe_allow_html=True
    )


def show_executive_summary():
    st.header("Executive Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            """
            <div class="metric-card">
                <h3>15</h3>
                <p>Pre-Gentrification Zones</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            """
            <div class="metric-card">
                <h3>1</h3>
                <p>Statistical Hotspot</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            """
            <div class="metric-card">
                <h3>71%</h3>
                <p>Max Annual Growth</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col4:
        st.markdown(
            """
            <div class="metric-card">
                <h3>21.1</h3>
                <p>Highest IAR Ratio</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("The Problem")
        st.markdown(
            """
            <div class="finding-box">
            Cities usually respond to gentrification after it is already visible:
            <ul>
                <li>Property values have already increased</li>
                <li>Residents may already be under pressure</li>
                <li>Infrastructure demand is already changing</li>
            </ul>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.subheader("The Project Idea")
        st.markdown(
            """
            <div class="finding-box">
            This project uses:
            <ul>
                <li><b>Building permits</b> as an early signal of change</li>
                <li><b>Investment-Assessment Ratio (IAR)</b> to identify mismatches</li>
                <li><b>Spatial statistics</b> to test hotspot patterns</li>
            </ul>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.subheader("Dashboard Preview")
        show_figure("08_dashboard.png")

    st.markdown("---")
    st.subheader("Key Findings")

    col1, col2 = st.columns(2)

    with col1:
        st.info(
            """
            **Explosive Growth Cell: GRID_10_10**

            - CAGR: 71%
            - 2015--16 mean: $12,000
            - 2023--25 mean: $585,420
            - About 48× growth over 10 years
            """
        )

    with col2:
        st.warning(
            """
            **Highest IAR Signal: GRID_03_16**

            - IAR: 21.1
            - Mean permit value: $2,215,000
            - Mean assessed value: $104,893
            - Very large gap between investment and official value
            """
        )

    st.markdown("---")
    st.subheader("Method Overview")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**1. Data Preparation**")
        st.text(
            "30,287 raw permits\n"
            "↓ Cleaning and deduplication\n"
            "1,098 usable records\n"
            "Grid-based aggregation"
        )

    with col2:
        st.markdown("**2. Pattern Detection**")
        st.text(
            "K-Means (k=6)\n"
            "DBSCAN\n"
            "Feature engineering\n"
            "Cross-method comparison"
        )

    with col3:
        st.markdown("**3. Statistical Analysis**")
        st.text(
            "Getis-Ord Gi*\n"
            "Monte Carlo testing\n"
            "IAR calculation\n"
            "Temporal growth analysis"
        )


def show_spatial_analysis(grid_stats_df):
    st.header("Spatial Analysis")

    if grid_stats_df is None:
        st.error("Grid statistics not found. Run the pipeline first.")
        return

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Permit Density Map")
        show_figure(
            "02_permit_density_grid.png",
            caption="1 km grid cells colored by permit count"
        )

    with col2:
        st.subheader("Top 10 Cells")
        top_10 = grid_stats_df.nlargest(10, "permit_count")[
            ["GRID_ID", "permit_count", "mean_value"]
        ]
        st.dataframe(top_10, use_container_width=True, hide_index=True)

        st.metric("Most Active Cell", "GRID_10_10")
        st.metric("Permits", "75")
        st.metric("Mean Value", "$585,420")

    st.markdown("---")
    st.subheader("Permit Count vs Mean Value")

    fig = px.scatter(
        grid_stats_df,
        x="permit_count",
        y="mean_value",
        size="total_value",
        hover_data=["GRID_ID"],
        labels={
            "permit_count": "Number of Permits",
            "mean_value": "Mean Permit Value (CAD)",
            "total_value": "Total Investment",
        },
        title="Grid Cell Activity",
        color="mean_value",
        color_continuous_scale="Viridis"
    )
    fig.update_layout(height=500)

    st.plotly_chart(fig, use_container_width=True)


def show_temporal_trends(permits_df, temporal_df):
    st.header("Temporal Trends (2015–2025)")

    if permits_df is not None:
        st.subheader("Permit Activity Over Time")

        permits_per_year = permits_df.groupby("YEAR").size().reset_index(name="count")

        fig = px.bar(
            permits_per_year,
            x="YEAR",
            y="count",
            title="Building Permits Issued Per Year",
            labels={"count": "Number of Permits", "YEAR": "Year"},
            color="count",
            color_continuous_scale="Blues"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Temporal Heatmap")
        show_figure(
            "06_grid_heatmap.png",
            caption="Top grid cells across multiple time windows"
        )

    with col2:
        st.subheader("City-Wide Trend")
        show_figure(
            "06_city_trend.png",
            caption="Average permit value over time"
        )

    if temporal_df is not None and "CAGR" in temporal_df.columns:
        st.markdown("---")
        st.subheader("CAGR Distribution")

        cagr_values = temporal_df["CAGR"].dropna() * 100

        fig = px.histogram(
            cagr_values,
            nbins=30,
            title="Compound Annual Growth Rate Distribution",
            labels={"value": "CAGR (%)", "count": "Number of Grid Cells"},
            color_discrete_sequence=["#43A047"]
        )
        fig.add_vline(x=0, line_dash="dash", line_color="black")

        st.plotly_chart(fig, use_container_width=True)

        st.success(
            "Emerging cell detected: GRID_10_10 has the highest growth rate in the city (about 71%)."
        )


def show_hotspot_analysis(hotspot_df):
    st.header("Getis-Ord Hotspot Analysis")

    st.info(
        """
        **What is Getis-Ord Gi\*?**

        It is a spatial statistic that tests whether high or low values are clustered
        more than we would expect by chance. A z-score above about 1.96 corresponds
        to statistical significance at the 5\% level.
        """
    )

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Hotspot Map")
        show_figure(
            "05_hotspot_map.png",
            caption="Red outline marks the significant hotspot"
        )

    with col2:
        st.subheader("Classification Results")

        if hotspot_df is not None:
            counts = hotspot_df["hotspot"].value_counts()
            st.dataframe(counts.reset_index(), use_container_width=True, hide_index=True)

            hot_spots = hotspot_df[hotspot_df["hotspot"].str.startswith("Hot", na=False)]
            if len(hot_spots) > 0:
                st.success(
                    f"""
                    **Significant Hotspot**

                    Grid cell: {hot_spots.iloc[0]['GRID_ID']}

                    z-score: {hot_spots.iloc[0]['Gi_star']:.2f}

                    p-value: {hot_spots.iloc[0]['p_value']:.3f}
                    """
                )

    if hotspot_df is not None:
        st.markdown("---")
        st.subheader("Gi* Z-Score Distribution")

        fig = px.histogram(
            hotspot_df,
            x="Gi_star",
            nbins=30,
            title="Distribution of Gi* Z-Scores",
            labels={"Gi_star": "Gi* Z-Score", "count": "Number of Cells"},
            color_discrete_sequence=["#78909C"]
        )
        fig.add_vline(
            x=1.96,
            line_dash="dash",
            line_color="red",
            annotation_text="p < 0.05"
        )
        fig.add_vline(x=-1.96, line_dash="dash", line_color="blue")

        st.plotly_chart(fig, use_container_width=True)


def show_iar_analysis(iar_df):
    st.header("Investment-Assessment Ratio (IAR)")

    st.markdown(
        r"""
        ### Core Metric

        $$
        \text{IAR} = \frac{\text{Mean Permit Value}}{\text{Mean Assessed Property Value}}
        $$

        High IAR in a low-assessment area suggests that investment may be arriving
        before official property values have fully adjusted.
        """
    )

    if iar_df is None:
        st.error("IAR results not found. Run the pipeline first.")
        return

    st.subheader("Investment vs Assessment")
    show_figure(
        "07_investment_vs_assessment.png",
        caption="Cells with strong investment and low assessment stand out clearly"
    )

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top 10 IAR Cells")
        top_iar = iar_df.nlargest(10, "IAR")[
            ["GRID_ID", "IAR", "mean_value", "mean_assessment"]
        ]
        st.dataframe(
            top_iar.style.format({
                "IAR": "{:.2f}",
                "mean_value": "${:,.0f}",
                "mean_assessment": "${:,.0f}"
            }),
            use_container_width=True,
            hide_index=True
        )

    with col2:
        st.subheader("Pre-Gentrification Signals")
        pregen_df = iar_df[iar_df["signal"] == PRE_GENTRIFICATION_LABEL]
        st.metric("Cells Flagged", len(pregen_df))

        if len(pregen_df) > 0:
            strongest = pregen_df.sort_values("IAR", ascending=False).iloc[0]
            st.warning(
                f"""
                **Highest-Risk Cell**

                Grid cell: {strongest['GRID_ID']}

                IAR: {strongest['IAR']:.1f}

                Mean permit value: ${strongest['mean_value']:,.0f}

                Mean assessed value: ${strongest['mean_assessment']:,.0f}
                """
            )

    st.markdown("---")
    st.subheader("IAR Distribution")

    fig = px.histogram(
        iar_df,
        x="IAR",
        nbins=40,
        title="Investment-Assessment Ratio Distribution",
        labels={"IAR": "IAR Value", "count": "Number of Cells"},
        color_discrete_sequence=["#E53935"]
    )
    fig.add_vline(
        x=1,
        line_dash="dash",
        line_color="black",
        annotation_text="IAR = 1"
    )

    st.plotly_chart(fig, use_container_width=True)


def show_raw_data_explorer(permits_df, grid_stats_df, iar_df, temporal_df, hotspot_df):
    st.header("Raw Data Explorer")
    st.markdown("Browse the processed datasets used in the project.")

    dataset_name = st.selectbox(
        "Select Dataset:",
        [
            "Cleaned Permits",
            "Grid Statistics",
            "IAR Results",
            "Temporal Analysis",
            "Getis-Ord Results",
        ]
    )

    if dataset_name == "Cleaned Permits" and permits_df is not None:
        st.subheader(f"Cleaned Permits ({len(permits_df):,} records)")
        st.dataframe(permits_df.head(100), use_container_width=True)

        csv_data = permits_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download Full Dataset",
            csv_data,
            "permits_cleaned.csv",
            "text/csv"
        )

    elif dataset_name == "Grid Statistics" and grid_stats_df is not None:
        st.subheader(f"Grid Statistics ({len(grid_stats_df):,} cells)")
        st.dataframe(grid_stats_df, use_container_width=True)

    elif dataset_name == "IAR Results" and iar_df is not None:
        st.subheader(f"IAR Results ({len(iar_df):,} cells)")
        st.dataframe(iar_df, use_container_width=True)

    elif dataset_name == "Temporal Analysis" and temporal_df is not None:
        st.subheader("Temporal Analysis Results")
        st.dataframe(temporal_df, use_container_width=True)

    elif dataset_name == "Getis-Ord Results" and hotspot_df is not None:
        st.subheader(f"Getis-Ord Results ({len(hotspot_df):,} cells)")
        st.dataframe(hotspot_df, use_container_width=True)


def show_footer():
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; font-size: 0.9rem;'>
            <b>The Renovation Roadmap</b> | Malek Karoui (3751935) | CS 4403 Data Mining | UNB 2026<br>
            <a href='https://github.com/MalekKaroui/renovation-roadmap'>GitHub Repository</a>
        </div>
        """,
        unsafe_allow_html=True
    )


# -----------------------------------------------------------------------------
# App execution
# -----------------------------------------------------------------------------
show_header()

permits_df = load_cleaned_permits()
grid_stats_df = load_grid_stats()
iar_df = load_iar_results()
temporal_df = load_temporal_results()
hotspot_df = load_hotspot_results()

selected_page = build_sidebar(permits_df)

if selected_page == "Executive Summary":
    show_executive_summary()
elif selected_page == "Spatial Analysis":
    show_spatial_analysis(grid_stats_df)
elif selected_page == "Temporal Trends":
    show_temporal_trends(permits_df, temporal_df)
elif selected_page == "Hotspot Detection":
    show_hotspot_analysis(hotspot_df)
elif selected_page == "IAR Analysis":
    show_iar_analysis(iar_df)
elif selected_page == "Raw Data Explorer":
    show_raw_data_explorer(permits_df, grid_stats_df, iar_df, temporal_df, hotspot_df)

show_footer()