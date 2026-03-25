import os
import streamlit as st
import streamlit.components.v1 as components
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
    /* Expand button styling */
    div[data-testid="stButton"] > button[kind="secondary"] {
        font-size: 11px;
        padding: 2px 10px;
        color: #6366f1;
        border-color: #6366f1;
        background: transparent;
        margin-top: -4px;
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
    v = series.max()
    return float(v) if pd.notna(v) and v > 0 else default

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH)
    df = df.dropna(subset=["Date", "Fund Name"])
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True)
    df["Security Weight"] = pd.to_numeric(df["Security Weight"], errors="coerce").fillna(0)
    df["Fund Weight"] = pd.to_numeric(df["Fund Weight"], errors="coerce").fillna(0)
    fund_totals = df.groupby(["Date", "Fund Name"])["Security Weight"].transform("sum")
    df["Weight In Fund"] = df["Security Weight"] / fund_totals.replace(0, 1)
    return df

df_all = load_data()

# ── Chart renderer ────────────────────────────────────────────────────────────
def show_chart(fig, key, height=None):
    """Render a Plotly chart. JS (injected once globally) adds expand buttons."""
    if height is not None:
        fig.update_layout(height=height)
    st.plotly_chart(fig, use_container_width=True, key=f"c_{key}")

# ── Sidebar — date selector only ───────────────────────────────────────────────
st.sidebar.title("📊 ERS Portfolio")
st.sidebar.markdown("---")

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
st.sidebar.caption("ERS Historical Holdings · Built with Streamlit & Plotly")

# ── Filtered datasets ──────────────────────────────────────────────────────────
snap = df_all[df_all["Date"] == selected_date].copy()
snap_eq = snap[snap["Security Asset type"] == "Domestic Equities"].copy()
selected_funds = sorted(snap["Fund Name"].unique())
selected_asset_types = ["Domestic Equities"]

hist = df_all[df_all["Security Asset type"].isin(selected_asset_types)].copy()

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("## 📊 ERS Fund of Funds — Portfolio Dashboard")
st.markdown("---")

# ── KPI Cards ──────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)

fund_wt_snap = snap.groupby("Fund Name")["Fund Weight"].first()
total_wt     = fund_wt_snap.sum()
num_funds    = snap["Fund Name"].nunique()
num_securities = snap_eq["Security Name"].nunique()
num_sectors  = snap_eq["Security Sector"].dropna().nunique()

top_fund = fund_wt_snap.idxmax() if not fund_wt_snap.empty else "—"
top_fund_short = " ".join(top_fund.split()[:3]) if top_fund != "—" else "—"
top_fund_wt = fund_wt_snap.max() if not fund_wt_snap.empty else 0

cash_pct = max(0.0, 1.0 - total_wt)
k1.markdown(f"""
<div class="metric-card">
    <div class="metric-label">Portfolio Coverage</div>
    <div class="metric-value">{total_wt:.1%}</div>
    <div class="metric-sub">Sum of fund weights</div>
    <div style="font-size:11px; color:#94a3b8; margin-top:4px;">{cash_pct:.1%} in cash</div>
</div>""", unsafe_allow_html=True)

for col, label, value, sub in [
    (k2, "Active Funds",  str(num_funds),      f"as of {selected_label}"),
    (k3, "Securities",    str(num_securities),  "unique holdings"),
    (k4, "Sectors",       str(num_sectors),     "unique sectors"),
    (k5, "Top Fund",      top_fund_short[:16],  f"wt: {top_fund_wt:.1%}"),
]:
    col.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-sub">{sub}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("")

# ── Inject "Click to expand" buttons that trigger Streamlit's fullscreen ───────
components.html("""
<script>
(function () {
    var doc = window.parent.document;

    function attachButtons() {
        doc.querySelectorAll('[data-testid="stPlotlyChart"]').forEach(function (chart) {
            // Skip if we already added our button
            if (chart.parentNode.querySelector('.ers-expand-btn')) return;
            var fsBtn = chart.querySelector('button[data-testid="StyledFullScreenButton"]');
            if (!fsBtn) return;

            var btn = doc.createElement('button');
            btn.className = 'ers-expand-btn';
            btn.innerHTML = '&#x2197;&nbsp;Click to expand';
            btn.style.cssText = [
                'display:inline-block',
                'margin:3px 0 10px 0',
                'padding:3px 14px',
                'font-size:11px',
                'font-family:Inter,sans-serif',
                'color:#6366f1',
                'border:1px solid #6366f1',
                'border-radius:4px',
                'background:transparent',
                'cursor:pointer',
                'transition:background 0.15s'
            ].join(';');
            btn.onmouseover = function () { btn.style.background = '#ede9fe'; };
            btn.onmouseout  = function () { btn.style.background = 'transparent'; };
            btn.onclick     = function () { fsBtn.click(); };

            chart.parentNode.insertBefore(btn, chart.nextSibling);
        });
    }

    // Run immediately, then watch for any new charts rendered by Streamlit
    attachButtons();
    new MutationObserver(attachButtons).observe(doc.body, { childList: true, subtree: true });
})();
</script>
""", height=0)

# ── Tabs (Historical Trends removed) ───────────────────────────────────────────
tab_fund, tab_stock, tab_sector, tab_drilldown, tab_overlap, tab_concentration, tab_compare = st.tabs([
    "🏦 Fund Composition",
    "📈 Stock Composition",
    "🗂 Sector Composition",
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
        snap.groupby("Fund Name")["Fund Weight"].first()
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
            coloraxis_showscale=False, bargap=0.35)
        fig.update_layout(margin=dict(t=50, b=40, l=160, r=60))
        fig.update_traces(textposition="outside")
        fig.update_xaxes(tickformat=".0%", title="Fund Weight", showgrid=True, gridcolor="#e2e8f0")
        fig.update_yaxes(title="", tickfont=dict(size=9), automargin=True)
        show_chart(fig, "fund_weights")

    with col2:
        st.markdown("**Top Stock Holdings — Total Portfolio**")
        # Portfolio-wide top stocks pie (all funds combined)
        port_top = (
            snap_eq.groupby(["Security Name", "Security Sector"])["Security Weight"]
            .sum().reset_index()
            .sort_values("Security Weight", ascending=False)
        )
        top15_port = port_top.head(15).copy()
        others_wt = port_top.iloc[15:]["Security Weight"].sum()
        if others_wt > 0:
            others_row = pd.DataFrame([{
                "Security Name": "Others",
                "Security Sector": "Others",
                "Security Weight": others_wt,
            }])
            alloc_pie = pd.concat([top15_port, others_row], ignore_index=True)
        else:
            alloc_pie = top15_port.copy()

        if not alloc_pie.empty:
            fig2 = px.pie(
                alloc_pie, names="Security Name", values="Security Weight",
                title=f"Top Stock Holdings — {selected_label}",
                hole=0.4,
                color="Security Sector",
                color_discrete_map=SECTOR_COLORS,
            )
            fig2.update_layout(**PLOTLY_LAYOUT, height=420,
                legend=dict(font=dict(size=9), orientation="v", x=1.02))
            fig2.update_traces(
                textposition="inside", textinfo="percent",
                hovertemplate="<b>%{label}</b><br>Portfolio wt: %{value:.2%}<extra></extra>",
            )
            show_chart(fig2, "fund_alloc_pie")
        else:
            st.info("No equity data available for the selected date.")

    # Fund weight history — discrete / categorical x-axis
    st.markdown('<div class="section-title">Fund Weights Over Time</div>', unsafe_allow_html=True)

    fund_hist = (
        df_all.groupby(["Date", "Fund Name"])["Fund Weight"].first()
        .reset_index()
        .sort_values("Date")
    )
    fund_hist["Short Name"] = fund_hist["Fund Name"].apply(lambda x: " ".join(x.split()[:4]))
    fund_hist["DateStr"] = fund_hist["Date"].dt.strftime("%b %Y")
    # Preserve chronological order for the categorical axis
    ordered_date_strs = [pd.Timestamp(d).strftime("%b %Y") for d in sorted(df_all["Date"].unique())]

    fig3 = px.line(
        fund_hist, x="DateStr", y="Fund Weight", color="Short Name",
        title="Fund Weight Evolution (each snapshot)",
        markers=True,
        color_discrete_sequence=PLOTLY_LAYOUT["colorway"],
        category_orders={"DateStr": ordered_date_strs},
    )
    fig3.update_layout(**PLOTLY_LAYOUT, height=400,
        legend=dict(font=dict(size=10), orientation="h", y=-0.28))
    fig3.update_xaxes(showgrid=True, gridcolor="#e2e8f0", title="",
        tickangle=-30, tickfont=dict(size=10), type="category")
    fig3.update_yaxes(showgrid=True, gridcolor="#e2e8f0", title="Fund Weight", tickformat=".0%")
    show_chart(fig3, "fund_hist_line")

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
    st.dataframe(
        fund_summary[["Fund Name", "Fund Weight %", "# Securities", "# Sectors"]].reset_index(drop=True),
        use_container_width=True,
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

    top_holdings = (
        snap_eq.groupby(["Security Name", "Security Sector"])["Security Weight"]
        .sum().reset_index()
        .sort_values("Security Weight", ascending=False)
        .head(top_n)
    )

    if not top_holdings.empty:
        col1, col2 = st.columns([3, 2])

        with col1:
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
            fig.update_layout(
                **PLOTLY_LAYOUT,
                height=max(420, top_n * 22),
                showlegend=True,
                bargap=0.35,
                legend=dict(font=dict(size=9), orientation="v", x=1.01),
            )
            fig.update_layout(margin=dict(t=50, b=40, l=160, r=80))
            fig.update_yaxes(categoryorder="total ascending", tickfont=dict(size=8),
                             automargin=True, title="")
            fig.update_traces(textposition="outside")
            fig.update_xaxes(tickformat=".1%", title="Portfolio Weight",
                             showgrid=True, gridcolor="#e2e8f0")
            show_chart(fig, "top_holdings_bar", height=max(420, top_n * 22))

        with col2:
            fig2 = px.treemap(
                top_holdings,
                path=["Security Sector", "Security Name"],
                values="Security Weight",
                title=f"Treemap — Top {top_n} Holdings",
                color="Security Sector",
                color_discrete_map=SECTOR_COLORS,
            )
            fig2.update_layout(**PLOTLY_LAYOUT, height=max(420, top_n * 22))
            fig2.update_traces(
                hovertemplate="<b>%{label}</b><br>Weight: %{value:.2%}<extra></extra>"
            )
            show_chart(fig2, "top_holdings_treemap", height=max(420, top_n * 22))

    # Full holdings table — "In # Funds" column removed
    st.markdown('<div class="section-title">Full Holdings Table</div>', unsafe_allow_html=True)

    full_holdings = (
        snap_eq.groupby(["Security Name", "Security Sector", "Security Asset type"])["Security Weight"]
        .sum().reset_index()
        .sort_values("Security Weight", ascending=False)
        .reset_index(drop=True)
    )
    full_holdings["Security Weight %"] = (full_holdings["Security Weight"] * 100).fillna(0).round(3)
    full_holdings["Rank"] = range(1, len(full_holdings) + 1)

    st.dataframe(
        full_holdings[["Rank", "Security Name", "Security Sector", "Security Weight %"]],
        use_container_width=True,
        height=400,
        column_config={
            "Security Weight %": st.column_config.ProgressColumn(
                "Portfolio Weight %", format="%.3f%%", min_value=0,
                max_value=safe_max(full_holdings["Security Weight %"])
            ),
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
    # Count stocks per sector (for hover)
    sector_stock_count = snap_eq.groupby("Security Sector")["Security Name"].nunique().rename("num_stocks")
    sector_df = sector_df.join(sector_stock_count, on="Security Sector")

    col1, col2 = st.columns([3, 2])

    with col1:
        fig = px.bar(
            sector_df.sort_values("Security Weight"),
            x="Security Weight", y="Security Sector",
            orientation="h",
            title=f"Sector Allocation — {selected_label}",
            color="Security Sector",
            color_discrete_map=SECTOR_COLORS,
            text=sector_df.sort_values("Security Weight")["Security Weight"].apply(lambda x: f"{x:.2%}"),
        )
        fig.update_layout(**PLOTLY_LAYOUT, height=520, showlegend=False, bargap=0.35)
        fig.update_layout(margin=dict(t=50, b=40, l=160, r=80))
        fig.update_traces(textposition="outside")
        fig.update_xaxes(tickformat=".1%", title="Portfolio Weight",
                         showgrid=True, gridcolor="#e2e8f0")
        fig.update_yaxes(title="", tickfont=dict(size=9), automargin=True)
        show_chart(fig, "sector_bar")

    with col2:
        # Pie with # stocks in hover
        pie_data = sector_df.head(12).copy()
        fig2 = px.pie(
            pie_data, names="Security Sector", values="Security Weight",
            title="Sector Weight Pie (Top 12)",
            hole=0.4,
            color="Security Sector",
            color_discrete_map=SECTOR_COLORS,
            custom_data=["num_stocks"],
        )
        fig2.update_layout(**PLOTLY_LAYOUT, height=520,
            legend=dict(font=dict(size=10), orientation="v", x=1.02))
        fig2.update_traces(
            textposition="inside", textinfo="percent",
            hovertemplate="<b>%{label}</b><br>Weight: %{value:.2%}<br># Stocks: %{customdata[0]}<extra></extra>",
        )
        show_chart(fig2, "sector_pie")

    # Fund × Sector heatmap
    st.markdown('<div class="section-title">Fund × Sector Heatmap</div>', unsafe_allow_html=True)

    hm_df = snap_eq.groupby(["Fund Name", "Security Sector"])["Security Weight"].sum().reset_index()
    pivot = hm_df.pivot(index="Fund Name", columns="Security Sector",
                        values="Security Weight").fillna(0)
    pivot.index = [" ".join(n.split()[:4]) for n in pivot.index]
    col_order = pivot.sum(axis=0).sort_values(ascending=False).index
    pivot = pivot[col_order]

    if not pivot.empty:
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
        show_chart(fig3, "sector_heatmap")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — FUND DEEP-DIVE
# ══════════════════════════════════════════════════════════════════════════════
with tab_drilldown:
    st.markdown('<div class="section-title">Fund-Level Exploration</div>', unsafe_allow_html=True)

    # Only funds active on the selected date
    active_funds_on_date = sorted(snap_eq["Fund Name"].unique())
    fund_choice = st.selectbox(
        "Select a fund to drill into",
        active_funds_on_date,
        key="fund_drilldown_select",
    )

    fund_data = snap_eq[snap_eq["Fund Name"] == fund_choice].copy()
    fund_wt_row = snap[snap["Fund Name"] == fund_choice]["Fund Weight"]
    fund_wt = fund_wt_row.iloc[0] if not fund_wt_row.empty else 0

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
            .sum().reset_index().sort_values("Security Weight", ascending=True)
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
        fig.update_layout(**PLOTLY_LAYOUT, showlegend=False, height=400, bargap=0.35)
        fig.update_layout(margin=dict(t=50, b=40, l=160, r=80))
        fig.update_traces(textposition="outside")
        fig.update_xaxes(tickformat=".1%", title="Portfolio Weight",
                         showgrid=True, gridcolor="#e2e8f0")
        fig.update_yaxes(title="", tickfont=dict(size=9), automargin=True)
        show_chart(fig, "drill_sector_bar")

    with col2:
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
        show_chart(fig2, "drill_sector_pie")

    # Top holdings table
    st.markdown(f'<div class="section-title">Top Holdings — {fund_choice.split("(")[0].strip()}</div>',
                unsafe_allow_html=True)

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
        use_container_width=True,
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
    # Historical weight chart removed per request

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — OVERLAP ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
with tab_overlap:
    st.markdown('<div class="section-title">Stock Overlap Across Funds</div>', unsafe_allow_html=True)
    st.caption("How many funds in the selected snapshot hold each stock — higher overlap = higher concentration risk.")

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
        fig_ov.update_layout(**PLOTLY_LAYOUT, height=500, showlegend=False,
            coloraxis_showscale=False, bargap=0.35)
        fig_ov.update_layout(margin=dict(t=50, b=40, l=160, r=80))
        fig_ov.update_traces(textposition="outside")
        fig_ov.update_xaxes(title="# Funds Holding Stock", dtick=1,
                             showgrid=True, gridcolor="#e2e8f0")
        fig_ov.update_yaxes(title="", tickfont=dict(size=9), automargin=True)
        fig_ov.update_yaxes(categoryorder="total ascending")
        show_chart(fig_ov, "overlap_bar")

    with col2:
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
            z=matrix_data, x=short_names, y=short_names,
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
        show_chart(heatmap_fig, "overlap_heatmap")

    st.markdown('<div class="section-title">Cross-Fund Holdings Detail</div>', unsafe_allow_html=True)
    st.dataframe(
        multi_fund[["Security Name", "sector", "num_funds", "Portfolio Weight %", "funds_list"]]
        .rename(columns={"sector": "Sector", "num_funds": "# Funds", "funds_list": "Held By"})
        .reset_index(drop=True),
        use_container_width=True,
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
# TAB 6 — CONCENTRATION METRICS
# ══════════════════════════════════════════════════════════════════════════════
with tab_concentration:
    st.markdown('<div class="section-title">Portfolio Concentration Metrics</div>', unsafe_allow_html=True)
    st.caption("Lower HHI = more diversified. Higher top-10 weight = more concentrated in a few stocks.")

    stock_weights = snap_eq.groupby("Security Name")["Security Weight"].sum()
    hhi_snap = (stock_weights ** 2).sum()
    top10_wt = stock_weights.nlargest(10).sum()
    top5_wt  = stock_weights.nlargest(5).sum()
    eff_n    = 1 / hhi_snap if hhi_snap > 0 else 0

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
    st.markdown('<div class="section-title">Concentration Over Time</div>', unsafe_allow_html=True)

    conc_rows = []
    for dt in sorted(df_all["Date"].unique()):
        dt_eq = df_all[
            (df_all["Date"] == dt) &
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
        fig_hhi = px.line(conc_hist, x="Date", y="HHI",
            title="HHI (Herfindahl Index) Over Time", markers=True,
            color_discrete_sequence=["#6366f1"])
        fig_hhi.update_layout(**PLOTLY_LAYOUT, height=320)
        fig_hhi.update_xaxes(showgrid=True, gridcolor="#e2e8f0", title="")
        fig_hhi.update_yaxes(showgrid=True, gridcolor="#e2e8f0", title="HHI")
        show_chart(fig_hhi, "hhi_line")

    with col2:
        fig_topn = px.line(conc_hist, x="Date", y=["Top-10 Weight", "Top-5 Weight"],
            title="Top-N Concentration Over Time", markers=True,
            color_discrete_sequence=["#f59e0b", "#f43f5e"])
        fig_topn.update_layout(**PLOTLY_LAYOUT, height=320,
            legend=dict(orientation="h", y=-0.25, font=dict(size=11)))
        fig_topn.update_xaxes(showgrid=True, gridcolor="#e2e8f0", title="")
        fig_topn.update_yaxes(showgrid=True, gridcolor="#e2e8f0", title="Weight", tickformat=".1%")
        show_chart(fig_topn, "topn_line")

    col3, col4 = st.columns(2)
    with col3:
        fig_eff = px.line(conc_hist, x="Date", y="Effective N",
            title="Effective Number of Stocks (1/HHI)", markers=True,
            color_discrete_sequence=["#10b981"])
        fig_eff.update_layout(**PLOTLY_LAYOUT, height=300)
        fig_eff.update_xaxes(showgrid=True, gridcolor="#e2e8f0", title="")
        fig_eff.update_yaxes(showgrid=True, gridcolor="#e2e8f0", title="Effective N")
        show_chart(fig_eff, "effn_line")

    with col4:
        fig_nh = px.line(conc_hist, x="Date", y="# Holdings",
            title="Total Unique Holdings Over Time", markers=True,
            color_discrete_sequence=["#22d3ee"])
        fig_nh.update_layout(**PLOTLY_LAYOUT, height=300)
        fig_nh.update_xaxes(showgrid=True, gridcolor="#e2e8f0", title="")
        fig_nh.update_yaxes(showgrid=True, gridcolor="#e2e8f0", title="# Stocks")
        show_chart(fig_nh, "holdings_line")

    st.markdown('<div class="section-title">Concentration History Table</div>', unsafe_allow_html=True)
    conc_display = conc_hist.copy()
    conc_display["Date"] = pd.to_datetime(conc_display["Date"]).dt.strftime("%b %Y")
    conc_display["Top-10 Weight"] = (conc_display["Top-10 Weight"] * 100).round(2)
    conc_display["Top-5 Weight"]  = (conc_display["Top-5 Weight"]  * 100).round(2)
    st.dataframe(conc_display[::-1].reset_index(drop=True), use_container_width=True, height=350,
        column_config={
            "Top-10 Weight": st.column_config.ProgressColumn("Top-10 Wt %", format="%.2f%%", min_value=0, max_value=100),
            "Top-5 Weight":  st.column_config.ProgressColumn("Top-5 Wt %",  format="%.2f%%", min_value=0, max_value=100),
        },
    )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 7 — FUND COMPARISON
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
    shared_count = len(set(data_a["Security Name"]) & set(data_b["Security Name"]))

    short_a = " ".join(fund_a.split()[:4])
    short_b = " ".join(fund_b.split()[:4])

    # ── Fund A summary row ────────────────────────────────────────────────────
    st.markdown(f"**Fund A — {short_a}**")
    fa1, fa2, fa3 = st.columns(3)
    for col, label, value, sub in [
        (fa1, "Fund Weight",   f"{wt_a:.1%}",                           "in portfolio"),
        (fa2, "# Securities",  str(data_a["Security Name"].nunique()),   "unique stocks"),
        (fa3, "# Sectors",     str(data_a["Security Sector"].nunique()), "sectors covered"),
    ]:
        col.markdown(f"""<div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value" style="font-size:22px;">{value}</div>
            <div class="metric-sub">{sub}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("")

    # ── Fund B summary row ────────────────────────────────────────────────────
    st.markdown(f"**Fund B — {short_b}**")
    fb1, fb2, fb3 = st.columns(3)
    for col, label, value, sub in [
        (fb1, "Fund Weight",   f"{wt_b:.1%}",                           "in portfolio"),
        (fb2, "# Securities",  str(data_b["Security Name"].nunique()),   "unique stocks"),
        (fb3, "# Sectors",     str(data_b["Security Sector"].nunique()), "sectors covered"),
    ]:
        col.markdown(f"""<div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value" style="font-size:22px;">{value}</div>
            <div class="metric-sub">{sub}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("")

    # ── Shared stocks card ────────────────────────────────────────────────────
    sh1, sh2, sh3 = st.columns([1, 2, 1])
    sh1.markdown(f"""<div class="metric-card">
        <div class="metric-label">Shared Stocks</div>
        <div class="metric-value" style="font-size:22px;">{shared_count}</div>
        <div class="metric-sub">in both funds</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("")

    # ── Sector mix side by side ────────────────────────────────────────────────
    st.markdown('<div class="section-title">Sector Mix Comparison</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    for col, data, fund_name, key_sfx in [
        (col1, data_a, fund_a, "cmp_sec_a"),
        (col2, data_b, fund_b, "cmp_sec_b"),
    ]:
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
            fig.update_layout(**PLOTLY_LAYOUT, height=420, showlegend=False, bargap=0.35)
            fig.update_layout(margin=dict(t=50, b=40, l=160, r=80))
            fig.update_traces(textposition="outside")
            fig.update_xaxes(tickformat=".0%", title="Within-Fund Weight",
                             showgrid=True, gridcolor="#e2e8f0")
            fig.update_yaxes(title="", tickfont=dict(size=9), automargin=True)
            show_chart(fig, key_sfx)

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
                use_container_width=True, height=420,
                column_config={
                    "Within-Fund Wt %": st.column_config.ProgressColumn(
                        "Within-Fund Wt %", format="%.2f%%", min_value=0,
                        max_value=safe_max(top["Within-Fund Wt %"])
                    )
                },
            )

st.markdown("---")
st.caption("ERS Fund of Funds Dashboard · Streamlit & Plotly")
