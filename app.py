import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ERS Fund of Funds Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #f4f6fb; }
    [data-testid="stMain"] { background-color: #f4f6fb; }
    .metric-card {
        background: #ffffff;
        border: 1px solid #dde3f0;
        border-radius: 12px;
        padding: 20px 24px;
        text-align: center;
        box-shadow: 0 1px 4px rgba(0,0,0,0.07);
    }
    .metric-label { color: #64748b; font-size: 13px; font-weight: 500; letter-spacing: 0.5px; }
    .metric-value { color: #1e293b; font-size: 28px; font-weight: 700; margin-top: 4px; }
    .metric-sub   { color: #6366f1; font-size: 12px; margin-top: 2px; }
    .section-title {
        color: #1e293b;
        font-size: 18px;
        font-weight: 600;
        margin: 20px 0 12px 0;
        padding-bottom: 6px;
        border-bottom: 2px solid #c7d2e8;
    }
    div[data-testid="stSidebarContent"] { background: #eef2f9; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background: #dde3f0;
        border-radius: 8px;
        color: #475569;
        padding: 8px 20px;
    }
    .stTabs [aria-selected="true"] {
        background: #6366f1 !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# ── Theme constants ────────────────────────────────────────────────────────────
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#1e293b", family="Inter, sans-serif", size=12),
    margin=dict(t=50, b=40, l=40, r=40),
    colorway=[
        "#6366f1","#22d3ee","#f59e0b","#10b981","#f43f5e",
        "#a78bfa","#fb923c","#34d399","#38bdf8","#e879f9",
        "#fbbf24","#4ade80","#f87171","#60a5fa","#c084fc",
        "#2dd4bf","#fb7185","#facc15","#86efac","#818cf8",
    ],
)

SECTOR_COLORS = {
    "Bank": "#6366f1", "IT": "#22d3ee", "Finance": "#f59e0b",
    "Healthcare": "#10b981", "FMCG": "#f43f5e",
    "Automobile & Ancillaries": "#a78bfa", "Capital Goods": "#fb923c",
    "Chemicals": "#34d399", "Crude Oil": "#38bdf8",
    "Construction Materials": "#e879f9", "Power": "#fbbf24",
    "Insurance": "#4ade80", "Telecom": "#f87171",
    "Iron & Steel": "#60a5fa", "Realty": "#c084fc",
    "Infrastructure": "#818cf8", "Logistics": "#2dd4bf",
    "Retailing": "#fb7185", "Consumer Durables": "#facc15",
    "Diamond  &  Jewellery": "#a3e635", "Diversified": "#94a3b8",
    "Non - Ferrous Metals": "#67e8f9", "Agri": "#86efac",
    "Trading": "#fcd34d", "Others": "#64748b",
}

# ── Data loading ───────────────────────────────────────────────────────────────
DATA_PATH = os.path.join(os.path.dirname(__file__), "ERS Historical Holdings Clean.csv")

def safe_max(series, default=1.0):
    """Return float max of series, falling back to default if NaN/empty."""
    v = series.max()
    return float(v) if pd.notna(v) and v > 0 else default

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH)
    df = df.dropna(subset=["Date", "Fund Name"])
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True)
    df["Security Weight"] = pd.to_numeric(df["Security Weight"], errors="coerce").fillna(0)
    df["Fund Weight"] = pd.to_numeric(df["Fund Weight"], errors="coerce").fillna(0)
    # Compute weight of each security inside its fund (for within-fund views)
    fund_totals = df.groupby(["Date", "Fund Name"])["Security Weight"].transform("sum")
    df["Weight In Fund"] = df["Security Weight"] / fund_totals.replace(0, 1)
    return df

df_all = load_data()

# ── Sidebar ────────────────────────────────────────────────────────────────────
st.sidebar.title("📊 ERS Portfolio")
st.sidebar.markdown("---")

# Date selector (radio buttons)
all_dates = sorted(df_all["Date"].unique())
date_labels = [pd.Timestamp(d).strftime("%b %Y") for d in all_dates]
date_label_to_ts = {lbl: ts for lbl, ts in zip(date_labels, all_dates)}

selected_label = st.sidebar.radio(
    "📅 Snapshot Month",
    options=date_labels[::-1],   # most recent first
    index=0,
)
selected_date = date_label_to_ts[selected_label]

st.sidebar.markdown("---")

# Fund filter
all_funds = sorted(df_all["Fund Name"].unique())
selected_funds = st.sidebar.multiselect(
    "💼 Funds (filter)",
    all_funds,
    default=all_funds,
    help="Select which funds to include",
)
if not selected_funds:
    selected_funds = all_funds

# Asset type filter
asset_types = sorted(df_all["Security Asset type"].dropna().unique())
selected_asset_types = st.sidebar.multiselect(
    "🏷 Asset Types",
    asset_types,
    default=["Domestic Equities"],
    help="Filter securities by asset type",
)
if not selected_asset_types:
    selected_asset_types = ["Domestic Equities"]

st.sidebar.markdown("---")
st.sidebar.caption("ERS Historical Holdings · Built with Streamlit & Plotly")

# ── Filtered datasets ──────────────────────────────────────────────────────────
# Snapshot for selected date
snap = df_all[df_all["Date"] == selected_date].copy()
snap_funds = snap[snap["Fund Name"].isin(selected_funds)]
snap_eq = snap_funds[snap_funds["Security Asset type"].isin(selected_asset_types)]

# Historical (all dates) filtered by funds + asset types
hist = df_all[
    (df_all["Fund Name"].isin(selected_funds)) &
    (df_all["Security Asset type"].isin(selected_asset_types))
].copy()

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("## 📊 ERS Fund of Funds — Portfolio Dashboard")
st.markdown("---")

# ── KPI Cards ──────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)

fund_wt_snap = snap[snap["Fund Name"].isin(selected_funds)].groupby("Fund Name")["Fund Weight"].first()
total_wt = fund_wt_snap.sum()
num_funds = snap_funds["Fund Name"].nunique()           # funds active on selected date only
num_securities = snap_funds["Security Name"].nunique()  # securities active on selected date only
num_sectors = snap_eq["Security Sector"].dropna().nunique()

top_sector = "—"
if not snap_eq.empty:
    s = snap_eq.groupby("Security Sector")["Security Weight"].sum()
    if not s.empty:
        top_sector = s.idxmax()

top_fund = fund_wt_snap.idxmax() if not fund_wt_snap.empty else "—"
top_fund_short = " ".join(top_fund.split()[:3]) if top_fund != "—" else "—"
top_fund_wt = fund_wt_snap.max() if not fund_wt_snap.empty else 0

cash_pct = max(0.0, 1.0 - total_wt)
k1.markdown(f"""
<div class="metric-card">
    <div class="metric-label">Portfolio Coverage</div>
    <div class="metric-value">{total_wt:.1%}</div>
    <div class="metric-sub">Sum of fund weights</div>
    <div style="font-size:11px; color:#94a3b8; margin-top:4px;">{cash_pct:.1%} in cash / unallocated</div>
</div>""", unsafe_allow_html=True)

for col, label, value, sub in [
    (k2, "Active Funds", str(num_funds), f"as of {selected_label}"),
    (k3, "Securities", str(num_securities), "unique holdings"),
    (k4, "Sectors", str(num_sectors), "unique sectors"),
    (k5, "Top Fund", top_fund_short[:16], f"wt: {top_fund_wt:.1%}"),
]:
    col.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-sub">{sub}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("")

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab_fund, tab_stock, tab_sector, tab_history, tab_drilldown, tab_overlap, tab_concentration, tab_compare = st.tabs([
    "🏦 Fund Composition",
    "📈 Stock Composition",
    "🗂 Sector Composition",
    "📅 Historical Trends",
    "🔍 Fund Deep-Dive",
    "🔗 Overlap Analysis",
    "📐 Concentration",
    "⚖️ Fund Comparison",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — FUND COMPOSITION
# ══════════════════════════════════════════════════════════════════════════════
with tab_fund:
    st.markdown('<div class="section-title">Fund Weight Distribution</div>', unsafe_allow_html=True)

    fund_df = (
        snap[snap["Fund Name"].isin(selected_funds)]
        .groupby("Fund Name")["Fund Weight"].first()
        .reset_index()
        .sort_values("Fund Weight", ascending=False)
    )
    fund_df["Short Name"] = fund_df["Fund Name"].apply(lambda x: " ".join(x.split()[:4]))

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("**Fund Weights in ERS Portfolio**")
        fig = px.bar(
            fund_df.sort_values("Fund Weight"),
            x="Fund Weight", y="Short Name",
            orientation="h",
            title=f"Fund Weights — {selected_label}",
            color="Fund Weight",
            color_continuous_scale="Teal",
            text=fund_df.sort_values("Fund Weight")["Fund Weight"].apply(lambda x: f"{x:.1%}"),
        )
        fig.update_layout(**PLOTLY_LAYOUT, height=420, showlegend=False,
            coloraxis_showscale=False)
        fig.update_traces(textposition="outside")
        fig.update_xaxes(tickformat=".0%", title="Fund Weight", showgrid=True, gridcolor="#e2e8f0")
        fig.update_yaxes(title="")
        st.plotly_chart(fig, width="stretch")

    with col2:
        st.markdown("**Fund Allocation — Stock Composition**")
        alloc_fund = st.selectbox(
            "Select a fund to view stock allocation",
            fund_df["Fund Name"].tolist(),
            key="fund_alloc_select",
        )
        alloc_data = snap_eq[snap_eq["Fund Name"] == alloc_fund].copy()
        alloc_data["Within-Fund Weight"] = alloc_data["Weight In Fund"].fillna(0)
        # Top 15 stocks + group the rest as "Others"
        alloc_sorted = alloc_data.sort_values("Within-Fund Weight", ascending=False)
        top15 = alloc_sorted.head(15).copy()
        others_wt = alloc_sorted.iloc[15:]["Within-Fund Weight"].sum()
        if others_wt > 0:
            others_row = pd.DataFrame([{
                "Security Name": "Others",
                "Security Sector": "Others",
                "Within-Fund Weight": others_wt,
            }])
            alloc_pie = pd.concat([top15[["Security Name", "Security Sector", "Within-Fund Weight"]], others_row], ignore_index=True)
        else:
            alloc_pie = top15[["Security Name", "Security Sector", "Within-Fund Weight"]]

        if not alloc_pie.empty:
            fig2 = px.pie(
                alloc_pie, names="Security Name", values="Within-Fund Weight",
                title=f"Stock Allocation — {alloc_fund.split('(')[0].strip()}",
                hole=0.4,
                color="Security Sector",
                color_discrete_map=SECTOR_COLORS,
            )
            fig2.update_layout(**PLOTLY_LAYOUT, height=420,
                legend=dict(font=dict(size=9), orientation="v", x=1.02))
            fig2.update_traces(
                textposition="inside", textinfo="percent",
                hovertemplate="<b>%{label}</b><br>Within-fund: %{value:.2%}<br>Sector: %{color}<extra></extra>",
            )
            st.plotly_chart(fig2, width="stretch")
        else:
            st.info("No equity data available for this fund at the selected date.")

    # Fund weight history
    st.markdown('<div class="section-title">Fund Weights Over Time</div>', unsafe_allow_html=True)

    fund_hist = (
        df_all[df_all["Fund Name"].isin(selected_funds)]
        .groupby(["Date", "Fund Name"])["Fund Weight"].first()
        .reset_index()
        .sort_values("Date")
    )
    fund_hist["Short Name"] = fund_hist["Fund Name"].apply(lambda x: " ".join(x.split()[:4]))

    fig3 = px.line(
        fund_hist, x="Date", y="Fund Weight", color="Short Name",
        title="Fund Weight Evolution",
        markers=True,
        color_discrete_sequence=PLOTLY_LAYOUT["colorway"],
    )
    fig3.update_layout(**PLOTLY_LAYOUT, height=380,
        legend=dict(font=dict(size=10), orientation="h", y=-0.25))
    fig3.update_xaxes(showgrid=True, gridcolor="#e2e8f0", title="")
    fig3.update_yaxes(showgrid=True, gridcolor="#e2e8f0", title="Fund Weight", tickformat=".0%")
    st.plotly_chart(fig3, width="stretch")

    # Fund details table
    st.markdown('<div class="section-title">Fund Summary Table</div>', unsafe_allow_html=True)
    fund_summary = fund_df.copy()
    fund_summary["# Securities"] = fund_df["Fund Name"].map(
        snap_eq.groupby("Fund Name")["Security Name"].nunique()
    ).fillna(0).astype(int)
    fund_summary["# Sectors"] = fund_df["Fund Name"].map(
        snap_eq.groupby("Fund Name")["Security Sector"].nunique()
    ).fillna(0).astype(int)
    fund_summary["Fund Weight %"] = (fund_summary["Fund Weight"] * 100).round(2)
    display_cols = ["Fund Name", "Fund Weight %", "# Securities", "# Sectors"]
    st.dataframe(
        fund_summary[display_cols].reset_index(drop=True),
        width="stretch",
        height=300,
        column_config={
            "Fund Weight %": st.column_config.ProgressColumn(
                "Fund Weight %", format="%.2f%%", min_value=0, max_value=100
            )
        },
    )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — STOCK COMPOSITION
# ══════════════════════════════════════════════════════════════════════════════
with tab_stock:
    st.markdown('<div class="section-title">Top Holdings (Portfolio Level)</div>', unsafe_allow_html=True)

    top_n = st.slider("Number of top holdings to show", 10, 50, 25, key="top_n_slider")

    # Aggregate by security (same stock can appear in multiple funds)
    top_holdings = (
        snap_eq.groupby(["Security Name", "Security Sector"])["Security Weight"]
        .sum().reset_index()
        .sort_values("Security Weight", ascending=False)
        .head(top_n)
    )

    if not top_holdings.empty:
        col1, col2 = st.columns([3, 2])

        with col1:
            # Sort ascending so Plotly renders heaviest bar at the top (horizontal bar behaviour)
            bar_data = top_holdings.sort_values("Security Weight", ascending=True)
            fig = px.bar(
                bar_data,
                x="Security Weight", y="Security Name",
                orientation="h",
                color="Security Sector",
                title=f"Top {top_n} Holdings — {selected_label}",
                color_discrete_map=SECTOR_COLORS,
                text=bar_data["Security Weight"].apply(lambda x: f"{x:.2%}"),
            )
            fig.update_layout(**PLOTLY_LAYOUT, height=max(400, top_n * 22),
                showlegend=True,
                legend=dict(font=dict(size=9), orientation="v", x=1.01))
            # Force y-axis to sort by bar length: highest weight at the top
            fig.update_yaxes(categoryorder="total ascending")
            fig.update_traces(textposition="outside")
            fig.update_xaxes(tickformat=".1%", title="Portfolio Weight", showgrid=True, gridcolor="#e2e8f0")
            fig.update_yaxes(title="", tickfont=dict(size=10))
            st.plotly_chart(fig, width="stretch")

        with col2:
            # Treemap
            fig2 = px.treemap(
                top_holdings,
                path=["Security Sector", "Security Name"],
                values="Security Weight",
                title=f"Treemap — Top {top_n} Holdings",
                color="Security Sector",
                color_discrete_map=SECTOR_COLORS,
            )
            fig2.update_layout(**PLOTLY_LAYOUT, height=max(400, top_n * 22))
            fig2.update_traces(
                hovertemplate="<b>%{label}</b><br>Weight: %{value:.2%}<extra></extra>"
            )
            st.plotly_chart(fig2, width="stretch")

    # Full holdings table
    st.markdown('<div class="section-title">Full Holdings Table</div>', unsafe_allow_html=True)

    full_holdings = (
        snap_eq.groupby(["Security Name", "Security Sector", "Security Asset type"])["Security Weight"]
        .sum().reset_index()
        .sort_values("Security Weight", ascending=False)  # heaviest holding = row 0
        .reset_index(drop=True)
    )
    full_holdings["Security Weight %"] = (full_holdings["Security Weight"] * 100).fillna(0).round(3)
    full_holdings["Rank"] = range(1, len(full_holdings) + 1)  # Rank 1 = highest weight
    full_holdings["In # Funds"] = full_holdings["Security Name"].map(
        snap_eq.groupby("Security Name")["Fund Name"].nunique()
    ).fillna(1).astype(int)

    st.dataframe(
        full_holdings[["Rank", "Security Name", "Security Sector", "Security Weight %", "In # Funds"]],
        width="stretch",
        height=400,
        column_config={
            "Security Weight %": st.column_config.ProgressColumn(
                "Portfolio Weight %", format="%.3f%%", min_value=0,
                max_value=safe_max(full_holdings["Security Weight %"])
            ),
            "In # Funds": st.column_config.NumberColumn("In # Funds", format="%d"),
        },
    )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — SECTOR COMPOSITION
# ══════════════════════════════════════════════════════════════════════════════
with tab_sector:
    st.markdown('<div class="section-title">Sector Allocation Overview</div>', unsafe_allow_html=True)

    sector_df = (
        snap_eq.groupby("Security Sector")["Security Weight"]
        .sum().reset_index()
        .sort_values("Security Weight", ascending=False)
    )
    sector_df["color"] = sector_df["Security Sector"].map(SECTOR_COLORS).fillna("#64748b")

    col1, col2 = st.columns([3, 2])

    with col1:
        fig = px.bar(
            sector_df,
            x="Security Weight", y="Security Sector",
            orientation="h",
            title=f"Sector Allocation — {selected_label}",
            color="Security Sector",
            color_discrete_map=SECTOR_COLORS,
            text=sector_df["Security Weight"].apply(lambda x: f"{x:.2%}"),
        )
        fig.update_layout(**PLOTLY_LAYOUT, height=500, showlegend=False)
        fig.update_traces(textposition="outside")
        fig.update_xaxes(tickformat=".1%", title="Portfolio Weight", showgrid=True, gridcolor="#e2e8f0")
        fig.update_yaxes(title="")
        st.plotly_chart(fig, width="stretch")

    with col2:
        fig2 = px.pie(
            sector_df.head(12), names="Security Sector", values="Security Weight",
            title="Sector Weight Pie (Top 12)",
            hole=0.4,
            color="Security Sector",
            color_discrete_map=SECTOR_COLORS,
        )
        fig2.update_layout(**PLOTLY_LAYOUT, height=500,
            legend=dict(font=dict(size=10), orientation="v", x=1.02))
        fig2.update_traces(
            textposition="inside", textinfo="percent",
            hovertemplate="<b>%{label}</b><br>Weight: %{value:.2%}<extra></extra>",
        )
        st.plotly_chart(fig2, width="stretch")

    # Fund × Sector heatmap
    st.markdown('<div class="section-title">Fund × Sector Heatmap</div>', unsafe_allow_html=True)

    hm_df = (
        snap_eq.groupby(["Fund Name", "Security Sector"])["Security Weight"]
        .sum().reset_index()
    )
    pivot = hm_df.pivot(index="Fund Name", columns="Security Sector", values="Security Weight").fillna(0)
    pivot.index = [" ".join(n.split()[:4]) for n in pivot.index]
    # Sort columns by total weight
    col_order = pivot.sum(axis=0).sort_values(ascending=False).index
    pivot = pivot[col_order]

    if not pivot.empty:
        # Format values as percentages for display
        pivot_pct = (pivot * 100).round(2)
        fig3 = px.imshow(
            pivot_pct,
            color_continuous_scale="Blues",
            title=f"Fund × Sector Weight (%) — {selected_label}",
            aspect="auto",
            text_auto=".1f",
        )
        fig3.update_layout(**PLOTLY_LAYOUT, height=500,
            coloraxis_colorbar=dict(title="Weight %", tickfont=dict(size=10)))
        fig3.update_xaxes(tickangle=-40, tickfont=dict(size=10), title="")
        fig3.update_yaxes(tickfont=dict(size=10), title="")
        st.plotly_chart(fig3, width="stretch")

    # Sector summary table
    st.markdown('<div class="section-title">Sector Summary</div>', unsafe_allow_html=True)
    sec_summary = sector_df.copy()
    sec_summary["# Stocks"] = sec_summary["Security Sector"].map(
        snap_eq.groupby("Security Sector")["Security Name"].nunique()
    ).fillna(0).astype(int)
    sec_summary["# Funds"] = sec_summary["Security Sector"].map(
        snap_eq.groupby("Security Sector")["Fund Name"].nunique()
    ).fillna(0).astype(int)
    sec_summary["Weight %"] = (sec_summary["Security Weight"] * 100).round(2)
    st.dataframe(
        sec_summary[["Security Sector", "Weight %", "# Stocks", "# Funds"]].reset_index(drop=True),
        width="stretch",
        height=350,
        column_config={
            "Weight %": st.column_config.ProgressColumn(
                "Portfolio Weight %", format="%.2f%%", min_value=0,
                max_value=safe_max(sec_summary["Weight %"])
            )
        },
    )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — HISTORICAL TRENDS
# ══════════════════════════════════════════════════════════════════════════════
with tab_history:
    st.markdown('<div class="section-title">Sector Weight Trends Over Time</div>', unsafe_allow_html=True)

    # Top sectors globally for dropdown
    top_sectors_global = (
        hist.groupby("Security Sector")["Security Weight"]
        .sum().nlargest(15).index.tolist()
    )
    default_sectors = top_sectors_global[:6]

    selected_sectors = st.multiselect(
        "Select sectors to track", top_sectors_global, default=default_sectors,
        key="sector_multiselect"
    )

    if selected_sectors:
        trend_df = (
            hist[hist["Security Sector"].isin(selected_sectors)]
            .groupby(["Date", "Security Sector"])["Security Weight"]
            .sum().reset_index()
            .sort_values("Date")
        )
        fig = px.area(
            trend_df, x="Date", y="Security Weight", color="Security Sector",
            title="Sector Weight Evolution (Stacked Area)",
            color_discrete_map=SECTOR_COLORS,
        )
        fig.update_layout(**PLOTLY_LAYOUT, height=420,
            legend=dict(font=dict(size=11), orientation="h", y=-0.28))
        fig.update_xaxes(showgrid=True, gridcolor="#e2e8f0", title="")
        fig.update_yaxes(showgrid=True, gridcolor="#e2e8f0", title="Portfolio Weight", tickformat=".0%")
        st.plotly_chart(fig, width="stretch")

    # Fund weight evolution (stacked area)
    st.markdown('<div class="section-title">Fund Weight Stacked Area</div>', unsafe_allow_html=True)

    fund_hist_all = (
        df_all[df_all["Fund Name"].isin(selected_funds)]
        .groupby(["Date", "Fund Name"])["Fund Weight"].first()
        .reset_index()
        .sort_values("Date")
    )
    fund_hist_all["Short Name"] = fund_hist_all["Fund Name"].apply(lambda x: " ".join(x.split()[:4]))

    fig2 = px.area(
        fund_hist_all, x="Date", y="Fund Weight", color="Short Name",
        title="Fund Weight Stacked Area",
        color_discrete_sequence=PLOTLY_LAYOUT["colorway"],
    )
    fig2.update_layout(**PLOTLY_LAYOUT, height=380,
        legend=dict(font=dict(size=10), orientation="h", y=-0.25))
    fig2.update_xaxes(showgrid=True, gridcolor="#e2e8f0", title="")
    fig2.update_yaxes(showgrid=True, gridcolor="#e2e8f0", title="Fund Weight", tickformat=".0%")
    st.plotly_chart(fig2, width="stretch")

    # Top stock evolution
    st.markdown('<div class="section-title">Top Stock Weight Over Time</div>', unsafe_allow_html=True)

    # Pick top 15 stocks by total historical weight for the selector
    top_stocks_global = (
        hist.groupby("Security Name")["Security Weight"]
        .sum().nlargest(20).index.tolist()
    )
    default_stocks = top_stocks_global[:5]
    selected_stocks = st.multiselect(
        "Select stocks to track", top_stocks_global, default=default_stocks,
        key="stock_multiselect"
    )

    if selected_stocks:
        stock_trend = (
            hist[hist["Security Name"].isin(selected_stocks)]
            .groupby(["Date", "Security Name"])["Security Weight"]
            .sum().reset_index()
            .sort_values("Date")
        )
        fig3 = px.line(
            stock_trend, x="Date", y="Security Weight", color="Security Name",
            title="Stock Weight Evolution",
            markers=True,
            color_discrete_sequence=PLOTLY_LAYOUT["colorway"],
        )
        fig3.update_layout(**PLOTLY_LAYOUT, height=380,
            legend=dict(font=dict(size=10), orientation="h", y=-0.25))
        fig3.update_xaxes(showgrid=True, gridcolor="#e2e8f0", title="")
        fig3.update_yaxes(showgrid=True, gridcolor="#e2e8f0", title="Portfolio Weight", tickformat=".2%")
        st.plotly_chart(fig3, width="stretch")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — FUND DEEP-DIVE
# ══════════════════════════════════════════════════════════════════════════════
with tab_drilldown:
    st.markdown('<div class="section-title">Fund-Level Exploration</div>', unsafe_allow_html=True)

    # Only show funds that actually appear in the snapshot for the selected date
    active_funds_on_date = sorted(snap_eq["Fund Name"].unique())
    fund_choice = st.selectbox(
        "Select a fund to drill into",
        active_funds_on_date,
        key="fund_drilldown_select"
    )

    fund_data = snap_eq[snap_eq["Fund Name"] == fund_choice].copy()
    fund_wt = snap[snap["Fund Name"] == fund_choice]["Fund Weight"].iloc[0] if not snap[snap["Fund Name"] == fund_choice].empty else 0

    st.markdown(
        f"**{fund_choice}** · Fund Weight in portfolio: **{fund_wt:.2%}** · "
        f"Securities: **{fund_data['Security Name'].nunique()}** · "
        f"Sectors: **{fund_data['Security Sector'].nunique()}**"
    )
    st.markdown("")

    col1, col2 = st.columns([1, 1])

    with col1:
        fund_sector = (
            fund_data.groupby("Security Sector")["Security Weight"]
            .sum().reset_index().sort_values("Security Weight", ascending=False)
        )
        fig = px.bar(
            fund_sector,
            x="Security Weight", y="Security Sector",
            orientation="h",
            title="Sector Mix (portfolio weight)",
            color="Security Sector",
            color_discrete_map=SECTOR_COLORS,
            text=fund_sector["Security Weight"].apply(lambda x: f"{x:.2%}"),
        )
        fig.update_layout(**PLOTLY_LAYOUT, showlegend=False, height=400)
        fig.update_traces(textposition="outside")
        fig.update_xaxes(tickformat=".1%", title="Portfolio Weight", showgrid=True, gridcolor="#e2e8f0")
        fig.update_yaxes(title="")
        st.plotly_chart(fig, width="stretch")

    with col2:
        # Within-fund weight view
        fund_data_wt = fund_data.copy()
        fund_data_wt["Within-Fund Weight"] = fund_data_wt["Weight In Fund"]
        fund_sector_wf = (
            fund_data_wt.groupby("Security Sector")["Within-Fund Weight"]
            .sum().reset_index().sort_values("Within-Fund Weight", ascending=False)
        )
        fig2 = px.pie(
            fund_sector_wf, names="Security Sector", values="Within-Fund Weight",
            title="Sector Mix (within-fund weight)",
            hole=0.4,
            color="Security Sector",
            color_discrete_map=SECTOR_COLORS,
        )
        fig2.update_layout(**PLOTLY_LAYOUT, height=400,
            legend=dict(font=dict(size=10), orientation="v", x=1.02))
        fig2.update_traces(
            textposition="inside", textinfo="percent",
            hovertemplate="<b>%{label}</b><br>Within-fund wt: %{value:.2%}<extra></extra>",
        )
        st.plotly_chart(fig2, width="stretch")

    # Top holdings table for this fund
    st.markdown(f'<div class="section-title">Top Holdings — {fund_choice.split("(")[0].strip()}</div>', unsafe_allow_html=True)

    top_fund_holdings = fund_data.sort_values("Security Weight", ascending=False).head(30).copy()
    top_fund_holdings["Portfolio Weight %"] = (top_fund_holdings["Security Weight"] * 100).fillna(0).round(3)
    top_fund_holdings["Within-Fund Weight %"] = (top_fund_holdings["Weight In Fund"] * 100).fillna(0).round(2)
    top_fund_holdings["Rank"] = range(1, len(top_fund_holdings) + 1)
    top_fund_holdings["Security ISIN"] = top_fund_holdings["Security ISIN"].fillna("—")
    top_fund_holdings["Security Bloomberg Ticker"] = top_fund_holdings["Security Bloomberg Ticker"].fillna("—")

    st.dataframe(
        top_fund_holdings[["Rank", "Security Name", "Security Sector",
                            "Portfolio Weight %", "Within-Fund Weight %",
                            "Security ISIN", "Security Bloomberg Ticker"]].reset_index(drop=True),
        width="stretch",
        height=450,
        column_config={
            "Portfolio Weight %": st.column_config.ProgressColumn(
                "Portfolio Wt %", format="%.3f%%", min_value=0,
                max_value=safe_max(top_fund_holdings["Portfolio Weight %"])
            ),
            "Within-Fund Weight %": st.column_config.ProgressColumn(
                "Within-Fund Wt %", format="%.2f%%", min_value=0,
                max_value=safe_max(top_fund_holdings["Within-Fund Weight %"])
            ),
        },
    )

    # Fund's historical weight trend
    st.markdown(f'<div class="section-title">Historical Weight — {fund_choice.split("(")[0].strip()}</div>', unsafe_allow_html=True)

    fund_hist_single = (
        df_all[df_all["Fund Name"] == fund_choice]
        .groupby("Date")["Fund Weight"].first()
        .reset_index()
        .sort_values("Date")
    )
    fig3 = px.line(
        fund_hist_single, x="Date", y="Fund Weight",
        title=f"{fund_choice.split('(')[0].strip()} — Fund Weight Over Time",
        markers=True,
        color_discrete_sequence=["#6366f1"],
    )
    fig3.update_layout(**PLOTLY_LAYOUT, height=280)
    fig3.update_xaxes(showgrid=True, gridcolor="#e2e8f0", title="")
    fig3.update_yaxes(showgrid=True, gridcolor="#e2e8f0", title="Fund Weight", tickformat=".1%")
    st.plotly_chart(fig3, width="stretch")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — OVERLAP ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
with tab_overlap:
    st.markdown('<div class="section-title">Stock Overlap Across Funds</div>', unsafe_allow_html=True)
    st.caption("How many funds in the selected snapshot hold each stock — higher overlap = higher concentration risk.")

    # Count how many funds hold each stock on the selected date
    overlap_df = (
        snap_eq.groupby("Security Name")
        .agg(
            num_funds=("Fund Name", "nunique"),
            funds_list=("Fund Name", lambda x: ", ".join(sorted(x.unique()))),
            sector=("Security Sector", "first"),
            total_portfolio_weight=("Security Weight", "sum"),
        )
        .reset_index()
        .sort_values(["num_funds", "total_portfolio_weight"], ascending=[False, False])
    )
    overlap_df["Portfolio Weight %"] = (overlap_df["total_portfolio_weight"] * 100).round(3)
    multi_fund = overlap_df[overlap_df["num_funds"] > 1]

    # KPI row
    ov1, ov2, ov3 = st.columns(3)
    ov1.markdown(f"""<div class="metric-card">
        <div class="metric-label">Stocks in 2+ Funds</div>
        <div class="metric-value">{len(multi_fund)}</div>
        <div class="metric-sub">of {len(overlap_df)} total holdings</div>
    </div>""", unsafe_allow_html=True)
    ov2.markdown(f"""<div class="metric-card">
        <div class="metric-label">Max Fund Overlap</div>
        <div class="metric-value">{int(overlap_df["num_funds"].max())}</div>
        <div class="metric-sub">funds holding same stock</div>
    </div>""", unsafe_allow_html=True)
    overlap_weight = multi_fund["total_portfolio_weight"].sum()
    ov3.markdown(f"""<div class="metric-card">
        <div class="metric-label">Overlap Portfolio Weight</div>
        <div class="metric-value">{overlap_weight:.1%}</div>
        <div class="metric-sub">weight of cross-fund stocks</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("")

    col1, col2 = st.columns([3, 2])

    with col1:
        # Bar chart of top overlapping stocks
        top_overlap = multi_fund.head(20).sort_values("num_funds")
        fig_ov = px.bar(
            top_overlap,
            x="num_funds", y="Security Name",
            orientation="h",
            color="num_funds",
            color_continuous_scale="Reds",
            title=f"Top Cross-Fund Holdings — {selected_label}",
            text="num_funds",
        )
        fig_ov.update_layout(**PLOTLY_LAYOUT, height=500, showlegend=False, coloraxis_showscale=False)
        fig_ov.update_traces(textposition="outside")
        fig_ov.update_xaxes(title="# Funds Holding Stock", dtick=1, showgrid=True, gridcolor="#e2e8f0")
        fig_ov.update_yaxes(title="")
        fig_ov.update_yaxes(categoryorder="total ascending")
        st.plotly_chart(fig_ov, width="stretch")

    with col2:
        # Fund overlap heatmap: how many stocks are shared between each pair of funds
        fund_stock_sets = snap_eq.groupby("Fund Name")["Security Name"].apply(set)
        fund_names_short = {f: " ".join(f.split()[:3]) for f in fund_stock_sets.index}
        fund_list = list(fund_stock_sets.index)
        matrix_data = []
        for fa in fund_list:
            row = []
            for fb in fund_list:
                shared = len(fund_stock_sets[fa] & fund_stock_sets[fb])
                row.append(shared)
            matrix_data.append(row)
        import numpy as np
        short_names = [fund_names_short[f] for f in fund_list]
        heatmap_fig = go.Figure(data=go.Heatmap(
            z=matrix_data,
            x=short_names,
            y=short_names,
            colorscale="Blues",
            text=[[str(v) for v in row] for row in matrix_data],
            texttemplate="%{text}",
            showscale=True,
        ))
        heatmap_fig.update_layout(
            **PLOTLY_LAYOUT,
            title="Fund-Pair Stock Overlap (# shared stocks)",
            height=500,
        )
        heatmap_fig.update_xaxes(tickangle=-40, tickfont=dict(size=9))
        heatmap_fig.update_yaxes(tickfont=dict(size=9))
        st.plotly_chart(heatmap_fig, width="stretch")

    # Detail table of overlapping stocks
    st.markdown('<div class="section-title">Cross-Fund Holdings Detail</div>', unsafe_allow_html=True)
    st.dataframe(
        multi_fund[["Security Name", "sector", "num_funds", "Portfolio Weight %", "funds_list"]]
        .rename(columns={"sector": "Sector", "num_funds": "# Funds", "funds_list": "Held By"})
        .reset_index(drop=True),
        width="stretch",
        height=380,
        column_config={
            "Portfolio Weight %": st.column_config.ProgressColumn(
                "Portfolio Wt %", format="%.3f%%", min_value=0,
                max_value=safe_max(multi_fund["Portfolio Weight %"])
            ),
            "# Funds": st.column_config.NumberColumn("# Funds", format="%d"),
        },
    )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 7 — CONCENTRATION METRICS
# ══════════════════════════════════════════════════════════════════════════════
with tab_concentration:
    st.markdown('<div class="section-title">Portfolio Concentration Metrics</div>', unsafe_allow_html=True)
    st.caption("Lower HHI = more diversified. Higher top-10 weight = more concentrated in a few stocks.")

    # ── Snapshot metrics ───────────────────────────────────────────────────────
    stock_weights = snap_eq.groupby("Security Name")["Security Weight"].sum()
    hhi_snap = (stock_weights ** 2).sum()
    top10_wt = stock_weights.nlargest(10).sum()
    top5_wt  = stock_weights.nlargest(5).sum()
    eff_n    = 1 / hhi_snap if hhi_snap > 0 else 0   # effective number of stocks

    c1, c2, c3, c4 = st.columns(4)
    for col, label, value, sub in [
        (c1, "HHI (Stock Level)", f"{hhi_snap:.4f}", "Lower = more diversified"),
        (c2, "Effective # Stocks", f"{eff_n:.0f}", "1/HHI — equivalent equal-weight portfolio"),
        (c3, "Top-10 Weight", f"{top10_wt:.1%}", "Concentration in top 10 holdings"),
        (c4, "Top-5 Weight",  f"{top5_wt:.1%}",  "Concentration in top 5 holdings"),
    ]:
        col.markdown(f"""<div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-sub">{sub}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("")

    # ── Historical concentration trends ────────────────────────────────────────
    st.markdown('<div class="section-title">Concentration Over Time</div>', unsafe_allow_html=True)

    conc_rows = []
    for dt in sorted(df_all["Date"].unique()):
        dt_eq = df_all[
            (df_all["Date"] == dt) &
            (df_all["Fund Name"].isin(selected_funds)) &
            (df_all["Security Asset type"].isin(selected_asset_types))
        ]
        sw = dt_eq.groupby("Security Name")["Security Weight"].sum()
        hhi_val = (sw ** 2).sum()
        conc_rows.append({
            "Date": dt,
            "HHI": round(hhi_val, 5),
            "Top-10 Weight": sw.nlargest(10).sum(),
            "Top-5 Weight":  sw.nlargest(5).sum(),
            "# Holdings":    len(sw),
            "Effective N":   round(1 / hhi_val, 1) if hhi_val > 0 else 0,
        })
    conc_hist = pd.DataFrame(conc_rows)

    col1, col2 = st.columns(2)
    with col1:
        fig_hhi = px.line(
            conc_hist, x="Date", y="HHI",
            title="HHI (Herfindahl Index) Over Time",
            markers=True,
            color_discrete_sequence=["#6366f1"],
        )
        fig_hhi.update_layout(**PLOTLY_LAYOUT, height=320)
        fig_hhi.update_xaxes(showgrid=True, gridcolor="#e2e8f0", title="")
        fig_hhi.update_yaxes(showgrid=True, gridcolor="#e2e8f0", title="HHI")
        st.plotly_chart(fig_hhi, width="stretch")

    with col2:
        fig_topn = px.line(
            conc_hist, x="Date", y=["Top-10 Weight", "Top-5 Weight"],
            title="Top-N Concentration Over Time",
            markers=True,
            color_discrete_sequence=["#f59e0b", "#f43f5e"],
        )
        fig_topn.update_layout(**PLOTLY_LAYOUT, height=320,
            legend=dict(orientation="h", y=-0.25, font=dict(size=11)))
        fig_topn.update_xaxes(showgrid=True, gridcolor="#e2e8f0", title="")
        fig_topn.update_yaxes(showgrid=True, gridcolor="#e2e8f0", title="Weight", tickformat=".1%")
        st.plotly_chart(fig_topn, width="stretch")

    col3, col4 = st.columns(2)
    with col3:
        fig_eff = px.line(
            conc_hist, x="Date", y="Effective N",
            title="Effective Number of Stocks (1/HHI)",
            markers=True,
            color_discrete_sequence=["#10b981"],
        )
        fig_eff.update_layout(**PLOTLY_LAYOUT, height=300)
        fig_eff.update_xaxes(showgrid=True, gridcolor="#e2e8f0", title="")
        fig_eff.update_yaxes(showgrid=True, gridcolor="#e2e8f0", title="Effective N")
        st.plotly_chart(fig_eff, width="stretch")

    with col4:
        fig_nh = px.line(
            conc_hist, x="Date", y="# Holdings",
            title="Total Unique Holdings Over Time",
            markers=True,
            color_discrete_sequence=["#22d3ee"],
        )
        fig_nh.update_layout(**PLOTLY_LAYOUT, height=300)
        fig_nh.update_xaxes(showgrid=True, gridcolor="#e2e8f0", title="")
        fig_nh.update_yaxes(showgrid=True, gridcolor="#e2e8f0", title="# Stocks")
        st.plotly_chart(fig_nh, width="stretch")

    # Summary table
    st.markdown('<div class="section-title">Concentration History Table</div>', unsafe_allow_html=True)
    conc_display = conc_hist.copy()
    conc_display["Date"] = pd.to_datetime(conc_display["Date"]).dt.strftime("%b %Y")
    conc_display["Top-10 Weight"] = (conc_display["Top-10 Weight"] * 100).round(2)
    conc_display["Top-5 Weight"]  = (conc_display["Top-5 Weight"]  * 100).round(2)
    st.dataframe(conc_display[::-1].reset_index(drop=True), width="stretch", height=350,
        column_config={
            "Top-10 Weight": st.column_config.ProgressColumn("Top-10 Wt %", format="%.2f%%", min_value=0, max_value=100),
            "Top-5 Weight":  st.column_config.ProgressColumn("Top-5 Wt %",  format="%.2f%%", min_value=0, max_value=100),
        },
    )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 8 — FUND COMPARISON
# ══════════════════════════════════════════════════════════════════════════════
with tab_compare:
    st.markdown('<div class="section-title">Fund Comparison</div>', unsafe_allow_html=True)
    st.caption("Pick two funds from the current snapshot and compare them side by side.")

    cmp_funds = sorted(snap_eq["Fund Name"].unique())
    cc1, cc2 = st.columns(2)
    with cc1:
        fund_a = st.selectbox("Fund A", cmp_funds, index=0, key="cmp_fund_a")
    with cc2:
        default_b = 1 if len(cmp_funds) > 1 else 0
        fund_b = st.selectbox("Fund B", cmp_funds, index=default_b, key="cmp_fund_b")

    data_a = snap_eq[snap_eq["Fund Name"] == fund_a]
    data_b = snap_eq[snap_eq["Fund Name"] == fund_b]
    wt_a = snap[snap["Fund Name"] == fund_a]["Fund Weight"].iloc[0] if not snap[snap["Fund Name"] == fund_a].empty else 0
    wt_b = snap[snap["Fund Name"] == fund_b]["Fund Weight"].iloc[0] if not snap[snap["Fund Name"] == fund_b].empty else 0

    # Summary KPIs
    km1, km2, km3, km4 = st.columns(4)
    for col, label, va, vb in [
        (km1, "Fund Weight", f"{wt_a:.1%}", f"{wt_b:.1%}"),
        (km2, "# Securities", str(data_a["Security Name"].nunique()), str(data_b["Security Name"].nunique())),
        (km3, "# Sectors",    str(data_a["Security Sector"].nunique()), str(data_b["Security Sector"].nunique())),
        (km4, "Shared Stocks", str(len(set(data_a["Security Name"]) & set(data_b["Security Name"]))), "in common"),
    ]:
        col.markdown(f"""<div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value" style="font-size:20px;">{va}</div>
            <div class="metric-sub">{vb}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("")

    # ── Sector mix side by side ────────────────────────────────────────────────
    st.markdown('<div class="section-title">Sector Mix Comparison</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    for col, data, fund_name in [(col1, data_a, fund_a), (col2, data_b, fund_b)]:
        with col:
            sec = (
                data.groupby("Security Sector")["Weight In Fund"]
                .sum().reset_index()
                .sort_values("Weight In Fund", ascending=True)
            )
            fig = px.bar(
                sec, x="Weight In Fund", y="Security Sector",
                orientation="h",
                color="Security Sector",
                color_discrete_map=SECTOR_COLORS,
                title=f"{' '.join(fund_name.split()[:4])}",
                text=sec["Weight In Fund"].apply(lambda x: f"{x:.1%}"),
            )
            fig.update_layout(**PLOTLY_LAYOUT, height=420, showlegend=False)
            fig.update_traces(textposition="outside")
            fig.update_xaxes(tickformat=".0%", title="Within-Fund Weight", showgrid=True, gridcolor="#e2e8f0")
            fig.update_yaxes(title="")
            st.plotly_chart(fig, width="stretch")

    # ── Top holdings side by side ──────────────────────────────────────────────
    st.markdown('<div class="section-title">Top Holdings Comparison</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    for col, data, fund_name in [(col1, data_a, fund_a), (col2, data_b, fund_b)]:
        with col:
            top = (
                data.sort_values("Weight In Fund", ascending=False)
                .head(15)[["Security Name", "Security Sector", "Weight In Fund"]]
                .copy()
            )
            top["Rank"] = range(1, len(top) + 1)
            top["Within-Fund Wt %"] = (top["Weight In Fund"] * 100).round(2)
            st.markdown(f"**{' '.join(fund_name.split()[:4])}** — top 15")
            st.dataframe(
                top[["Rank", "Security Name", "Security Sector", "Within-Fund Wt %"]].reset_index(drop=True),
                width="stretch", height=420,
                column_config={
                    "Within-Fund Wt %": st.column_config.ProgressColumn(
                        "Within-Fund Wt %", format="%.2f%%", min_value=0,
                        max_value=safe_max(top["Within-Fund Wt %"])
                    )
                },
            )

    # ── Weight history side by side ────────────────────────────────────────────
    st.markdown('<div class="section-title">Fund Weight History</div>', unsafe_allow_html=True)

    hist_a = (
        df_all[df_all["Fund Name"] == fund_a]
        .groupby("Date")["Fund Weight"].first().reset_index()
        .assign(Fund=fund_a)
    )
    hist_b = (
        df_all[df_all["Fund Name"] == fund_b]
        .groupby("Date")["Fund Weight"].first().reset_index()
        .assign(Fund=fund_b)
    )
    hist_cmp = pd.concat([hist_a, hist_b]).sort_values("Date")
    hist_cmp["Short"] = hist_cmp["Fund"].apply(lambda x: " ".join(x.split()[:4]))

    fig_h = px.line(
        hist_cmp, x="Date", y="Fund Weight", color="Short",
        title="Fund Weight Over Time",
        markers=True,
        color_discrete_sequence=["#6366f1", "#f59e0b"],
    )
    fig_h.update_layout(**PLOTLY_LAYOUT, height=320,
        legend=dict(orientation="h", y=-0.25, font=dict(size=11)))
    fig_h.update_xaxes(showgrid=True, gridcolor="#e2e8f0", title="")
    fig_h.update_yaxes(showgrid=True, gridcolor="#e2e8f0", title="Fund Weight", tickformat=".1%")
    st.plotly_chart(fig_h, width="stretch")

# ── Raw data expander ──────────────────────────────────────────────────────────
with st.expander("📋 Raw Holdings (filtered snapshot)", expanded=False):
    display_df = snap_eq[["Date", "Fund Name", "Security Name", "Security Sector",
                           "Security Asset type", "Security Weight",
                           "Security ISIN", "Security Bloomberg Ticker"]].copy()
    display_df["Date"] = display_df["Date"].dt.strftime("%d %b %Y")
    display_df["Security Weight"] = display_df["Security Weight"].round(4)
    st.dataframe(display_df.reset_index(drop=True), width="stretch", height=400)

st.markdown("---")
st.caption("ERS Fund of Funds Dashboard · Streamlit & Plotly")
