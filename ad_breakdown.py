import streamlit as st
import pandas as pd
import numpy as np

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Ad Revenue Breakdown",
    page_icon="📊",
    layout="wide",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;700&family=DM+Sans:wght@400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #0C0D16;
    color: #E2E4F0;
}
.stApp { background-color: #0C0D16; }

/* Hide streamlit branding */
#MainMenu, footer, header { visibility: hidden; }

/* Metric cards */
[data-testid="metric-container"] {
    background: #12131C;
    border: 1px solid #1E2030;
    border-radius: 12px;
    padding: 18px 20px;
}
[data-testid="stMetricLabel"] {
    color: #4E5270 !important;
    font-size: 10px !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    font-family: 'DM Sans', sans-serif !important;
}
[data-testid="stMetricValue"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-weight: 700 !important;
    font-size: 22px !important;
}
[data-testid="stMetricDelta"] { font-size: 11px !important; }

/* Dataframe */
[data-testid="stDataFrame"] {
    background: #12131C;
    border: 1px solid #1E2030;
    border-radius: 12px;
    overflow: hidden;
}

/* File uploader */
[data-testid="stFileUploader"] {
    background: #12131C;
    border: 1.5px dashed #252836;
    border-radius: 12px;
    padding: 12px;
}
[data-testid="stFileUploader"]:hover { border-color: #4A9EFF55; }

/* Section headers */
.section-label {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;
    margin-top: 6px;
}
.section-bar {
    width: 3px;
    height: 14px;
    background: #F5A623;
    border-radius: 2px;
    display: inline-block;
}
.section-text {
    color: #4E5270;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    font-family: 'DM Sans', sans-serif;
}

/* Hero card */
.hero-card {
    background: linear-gradient(130deg, #13141F 0%, #161824 100%);
    border: 1px solid #1E2030;
    border-radius: 16px;
    padding: 28px 32px;
    margin-bottom: 16px;
}
.roas-number {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 64px;
    font-weight: 700;
    line-height: 1;
    letter-spacing: -0.02em;
}
.roas-label {
    color: #4E5270;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    margin-bottom: 10px;
}
.badge {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 10px;
}
.pl-row {
    display: flex;
    justify-content: space-between;
    padding: 12px 20px;
    border-bottom: 1px solid #141520;
}
.pl-row-bold {
    display: flex;
    justify-content: space-between;
    padding: 16px 20px;
    background: #1A1C2C;
    border-top: 1px solid #1E2030;
    border-radius: 0 0 12px 12px;
}
.pl-label { color: #8084A8; font-size: 13px; }
.pl-label-bold { color: #E2E4F0; font-size: 15px; font-weight: 700; font-family: 'DM Sans', sans-serif; }
.pl-value { font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 700; }
.pl-value-bold { font-family: 'IBM Plex Mono', monospace; font-size: 16px; font-weight: 700; }
.pl-container {
    background: #12131C;
    border: 1px solid #1E2030;
    border-radius: 12px;
    overflow: hidden;
}
.kpi-sub { color: #3a3e55; font-size: 11px; margin-top: 4px; }
.dot { width:7px; height:7px; border-radius:50%; display:inline-block; margin-right:6px; vertical-align:middle; }
.info-bar {
    background: #12131C;
    border: 1px solid #1A1C2C;
    border-radius: 10px;
    padding: 14px 20px;
    margin-top: 20px;
    display: flex;
    gap: 28px;
}
.stButton > button {
    background: #F5A623 !important;
    color: #0C0D16 !important;
    font-weight: 700 !important;
    font-family: 'DM Sans', sans-serif !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 12px 0 !important;
    font-size: 15px !important;
    width: 100%;
    transition: all 0.18s ease;
}
.stButton > button:hover { background: #FFBA45 !important; transform: translateY(-1px); }
h1 { font-family: 'DM Sans', sans-serif !important; }
h2, h3 { font-family: 'DM Sans', sans-serif !important; color: #E2E4F0 !important; }
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
FUNNEL_PRICES = [37, 74, 77]
RETAINER = 1600.0
PRICE_LABELS = {37: "Base Offer ($37)", 74: "Base + Bump ($74)", 77: "Upsell ($77)"}

# ── Helpers ───────────────────────────────────────────────────────────────────

def find_col(df, candidates):
    cols_lower = {c.lower(): c for c in df.columns}
    for cand in candidates:
        for key, orig in cols_lower.items():
            if cand.lower() in key:
                return orig
    return None

def parse_num_series(series):
    return pd.to_numeric(series.astype(str).str.replace(r'[$,%\s,]', '', regex=True), errors='coerce').fillna(0)

def section(label):
    st.markdown(f"""
    <div class="section-label">
        <span class="section-bar"></span>
        <span class="section-text">{label}</span>
    </div>""", unsafe_allow_html=True)

def fmt_usd(n):
    return f"${n:,.2f}"

def fmt_n(n):
    return f"{int(n):,}"

def fmt_pct(n):
    return f"{n:.2f}%"

def roas_color(roas):
    if roas >= 3: return "#F5A623"
    if roas >= 2: return "#FFD166"
    if roas >= 1: return "#FFD166"
    return "#FF4757"

def roas_badge(roas):
    if roas >= 3: return "🔥 Strong", "#F5A62318", "#F5A623"
    if roas >= 2: return "✓ Profitable", "#FFD16618", "#FFD166"
    if roas >= 1: return "⚠ Marginal", "#FFD16618", "#FFD166"
    return "✗ Losing Money", "#FF475718", "#FF4757"

def net_color(net):
    return "#00D97E" if net >= 0 else "#FF4757"

# ── Analysis ──────────────────────────────────────────────────────────────────

def analyze(stripe_df, fb_df):
    # ── Stripe ──
    amt_col    = find_col(stripe_df, ["amount"])
    fee_col    = find_col(stripe_df, ["fee"])
    status_col = find_col(stripe_df, ["status"])

    df = stripe_df.copy()
    if status_col:
        df = df[df[status_col].str.lower().str.contains("paid|succeeded|complete|captured", na=False)]

    df["_amount"] = parse_num_series(df[amt_col]) if amt_col else 0
    df["_fee"]    = parse_num_series(df[fee_col]) if fee_col else 0
    df = df[df["_amount"] > 0]

    # Filter to funnel prices only
    def nearest_price(val):
        for p in FUNNEL_PRICES:
            if abs(val - p) < 1:
                return p
        return None
    df["_price_tier"] = df["_amount"].apply(nearest_price)
    df = df[df["_price_tier"].notna()]

    gross_revenue = df["_amount"].sum()
    total_fees    = df["_fee"].sum()
    tx_count      = len(df)

    price_groups = {}
    for p in FUNNEL_PRICES:
        sub = df[df["_price_tier"] == p]
        if len(sub) > 0:
            price_groups[p] = {
                "count":   len(sub),
                "revenue": sub["_amount"].sum(),
                "fees":    sub["_fee"].sum(),
            }

    # ── Facebook ──
    spend_col    = find_col(fb_df, ["amount spent", "spend", "cost"])
    impress_col  = find_col(fb_df, ["impressions"])
    reach_col    = find_col(fb_df, ["reach"])
    clicks_col   = find_col(fb_df, ["link click", "clicks (link)", "outbound click", "clicks (all)", "clicks"])
    purch_col    = find_col(fb_df, ["purchases", "results", "purchase"])
    campaign_col = find_col(fb_df, ["campaign name", "campaign"])

    ad_spend    = parse_num_series(fb_df[spend_col]).sum()   if spend_col   else 0
    impressions = parse_num_series(fb_df[impress_col]).sum() if impress_col else 0
    reach       = parse_num_series(fb_df[reach_col]).sum()   if reach_col   else 0
    clicks      = parse_num_series(fb_df[clicks_col]).sum()  if clicks_col  else 0
    fb_purch    = parse_num_series(fb_df[purch_col]).sum()   if purch_col   else 0

    purchases = fb_purch if fb_purch > 0 else tx_count
    ctr = (clicks / impressions * 100) if impressions > 0 else 0
    cpc = (ad_spend / clicks)           if clicks > 0      else 0
    cpp = (ad_spend / purchases)        if purchases > 0   else 0
    roas = (gross_revenue / ad_spend)   if ad_spend > 0    else 0
    net_revenue = gross_revenue - total_fees - ad_spend - RETAINER

    # Campaigns
    campaigns = []
    if campaign_col:
        for name, grp in fb_df.groupby(campaign_col):
            s = parse_num_series(grp[spend_col]).sum()   if spend_col   else 0
            i = parse_num_series(grp[impress_col]).sum() if impress_col else 0
            r = parse_num_series(grp[reach_col]).sum()   if reach_col   else 0
            cl = parse_num_series(grp[clicks_col]).sum() if clicks_col  else 0
            p = parse_num_series(grp[purch_col]).sum()   if purch_col   else 0
            campaigns.append({
                "Campaign": str(name),
                "Spend": s,
                "Impressions": int(i),
                "Reach": int(r),
                "Clicks": int(cl),
                "CTR %": round((cl/i*100) if i > 0 else 0, 2),
                "CPC": round((s/cl) if cl > 0 else 0, 2),
                "Purchases": int(p),
                "CPP": round((s/p) if p > 0 else 0, 2),
            })

    return {
        "gross_revenue": gross_revenue,
        "net_revenue":   net_revenue,
        "total_fees":    total_fees,
        "ad_spend":      ad_spend,
        "roas":          roas,
        "cpp":           cpp,
        "ctr":           ctr,
        "cpc":           cpc,
        "impressions":   impressions,
        "reach":         reach,
        "clicks":        clicks,
        "purchases":     purchases,
        "tx_count":      tx_count,
        "price_groups":  price_groups,
        "campaigns":     campaigns,
    }

# ── UI ────────────────────────────────────────────────────────────────────────

# Header
st.markdown("""
<div style="margin-bottom:32px">
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px">
    <span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:#F5A623"></span>
    <span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:#4A9EFF;opacity:0.75"></span>
    <span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:#00D97E;opacity:0.5"></span>
    <span style="color:#2E3048;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.14em;font-family:'DM Sans',sans-serif;margin-left:4px">Performance Intelligence</span>
  </div>
  <h1 style="font-family:'DM Sans',sans-serif;font-size:32px;font-weight:700;color:#E2E4F0;letter-spacing:-0.01em;line-height:1.15;margin:0">Ad Revenue Breakdown</h1>
  <p style="color:#35384E;font-family:'DM Sans',sans-serif;font-size:13px;margin-top:8px">Front-end funnel · $37 base · $74 w/ bump · $77 upsell · $1,600/mo retainer deducted</p>
</div>
""", unsafe_allow_html=True)

# Upload
col1, col2 = st.columns(2)
with col1:
    stripe_file = st.file_uploader("💳  Stripe Export", type="csv", help="Transactions CSV — needs Amount and Fee columns")
with col2:
    fb_file = st.file_uploader("📊  Facebook Ads Export", type="csv", help="Ads CSV — needs Spend, Impressions, Clicks, Purchases columns")

st.markdown("")

if stripe_file and fb_file:
    run = st.button("→  Run Analysis")
else:
    st.button("Upload both files to continue", disabled=True)
    run = False

# Info bar
st.markdown("""
<div class="info-bar">
  <div><span class="dot" style="background:#F5A623"></span><strong style="color:#8084A8;font-size:12px">Gross Revenue</strong><br>
    <span style="color:#35384E;font-size:11px">All funnel transactions from Stripe</span></div>
  <div><span class="dot" style="background:#FF6B6B"></span><strong style="color:#8084A8;font-size:12px">Net Revenue</strong><br>
    <span style="color:#35384E;font-size:11px">After fees, ad spend & $1,600 retainer</span></div>
  <div><span class="dot" style="background:#4A9EFF"></span><strong style="color:#8084A8;font-size:12px">ROAS</strong><br>
    <span style="color:#35384E;font-size:11px">Gross revenue ÷ total ad spend</span></div>
</div>
""", unsafe_allow_html=True)

# ── Results ───────────────────────────────────────────────────────────────────
if run or (stripe_file and fb_file and st.session_state.get("results")):
    if run:
        try:
            stripe_df = pd.read_csv(stripe_file)
            fb_df     = pd.read_csv(fb_file)
            r = analyze(stripe_df, fb_df)
            st.session_state["results"] = r
        except Exception as e:
            st.error(f"Error parsing files: {e}")
            st.stop()

    r = st.session_state.get("results")
    if not r:
        st.stop()

    st.markdown("---")

    # ── ROAS Hero ──
    roas_val = r["roas"]
    rc = roas_color(roas_val)
    badge_text, badge_bg, badge_fg = roas_badge(roas_val)
    nc = net_color(r["net_revenue"])

    hero_l, hero_div, hero_r = st.columns([2, 0.05, 5])
    with hero_l:
        st.markdown(f"""
        <div style="padding:8px 0">
          <div class="roas-label">Return on Ad Spend</div>
          <div class="roas-number" style="color:{rc}">{roas_val:.2f}<span style="font-size:28px;opacity:0.7">x</span></div>
          <div style="color:#35384E;font-size:11px;font-family:'DM Sans',sans-serif;margin-top:8px">Every $1 in ads → ${roas_val:.2f} gross</div>
          <div class="badge" style="background:{badge_bg};color:{badge_fg}">{badge_text}</div>
        </div>
        """, unsafe_allow_html=True)

    with hero_div:
        st.markdown('<div style="width:1px;height:100%;background:#1E2030;min-height:120px"></div>', unsafe_allow_html=True)

    with hero_r:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Gross Revenue",  fmt_usd(r["gross_revenue"]))
        c2.metric("Net Revenue",    fmt_usd(r["net_revenue"]))
        c3.metric("Ad Spend",       fmt_usd(r["ad_spend"]))
        c4.metric("Transactions",   fmt_n(r["tx_count"]))

    st.markdown("")

    # ── KPI Row 1 ──
    section("Cost & Efficiency")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Stripe Fees",          fmt_usd(r["total_fees"]),  delta="Deducted from net", delta_color="inverse")
    k2.metric("Ads Manager Retainer", "−$1,600.00",              delta="Fixed monthly",     delta_color="inverse")
    k3.metric("Cost Per Purchase",    fmt_usd(r["cpp"]),         delta=f"{fmt_n(r['purchases'])} purchases")
    net_margin = (r["net_revenue"] / r["gross_revenue"] * 100) if r["gross_revenue"] > 0 else 0
    k4.metric("Net Margin",           fmt_pct(net_margin),       delta="After all deductions")

    st.markdown("")

    # ── KPI Row 2 ──
    section("Ad Metrics")
    a1, a2, a3, a4 = st.columns(4)
    a1.metric("Impressions",     fmt_n(r["impressions"]))
    a2.metric("Reach",           fmt_n(r["reach"]))
    ctr_delta = "Above average" if r["ctr"] >= 2 else ("Average" if r["ctr"] >= 1 else "Below average")
    a3.metric("CTR",             fmt_pct(r["ctr"]),    delta=ctr_delta)
    a4.metric("Cost Per Click",  fmt_usd(r["cpc"]))

    st.markdown("")

    # ── Revenue by Product ──
    section("Revenue Breakdown by Product")
    rev_rows = []
    for p in FUNNEL_PRICES:
        g = r["price_groups"].get(p)
        if g:
            rev_rows.append({
                "Product":       PRICE_LABELS[p],
                "Transactions":  g["count"],
                "Gross Revenue": round(g["revenue"], 2),
                "Stripe Fees":   round(g["fees"], 2),
                "Net Revenue":   round(g["revenue"] - g["fees"], 2),
            })

    if rev_rows:
        rev_df = pd.DataFrame(rev_rows)
        # Totals row
        totals = {
            "Product": "TOTAL",
            "Transactions":  rev_df["Transactions"].sum(),
            "Gross Revenue": round(rev_df["Gross Revenue"].sum(), 2),
            "Stripe Fees":   round(rev_df["Stripe Fees"].sum(), 2),
            "Net Revenue":   round(rev_df["Net Revenue"].sum(), 2),
        }
        rev_df = pd.concat([rev_df, pd.DataFrame([totals])], ignore_index=True)
        st.dataframe(
            rev_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Gross Revenue": st.column_config.NumberColumn(format="$%.2f"),
                "Stripe Fees":   st.column_config.NumberColumn(format="$%.2f"),
                "Net Revenue":   st.column_config.NumberColumn(format="$%.2f"),
            }
        )

    st.markdown("")

    # ── P&L ──
    section("Profit & Loss Summary")
    st.markdown(f"""
    <div class="pl-container">
      <div class="pl-row">
        <span class="pl-label">Gross Revenue (funnel transactions)</span>
        <span class="pl-value" style="color:#F5A623">{fmt_usd(r['gross_revenue'])}</span>
      </div>
      <div class="pl-row">
        <span class="pl-label">− Stripe Processing Fees (auto-calculated)</span>
        <span class="pl-value" style="color:#FF6B6B">−{fmt_usd(r['total_fees'])}</span>
      </div>
      <div class="pl-row">
        <span class="pl-label">− Facebook Ad Spend</span>
        <span class="pl-value" style="color:#FF6B6B">−{fmt_usd(r['ad_spend'])}</span>
      </div>
      <div class="pl-row">
        <span class="pl-label">− Ads Manager Retainer ($1,600/mo)</span>
        <span class="pl-value" style="color:#FF6B6B">−$1,600.00</span>
      </div>
      <div class="pl-row-bold">
        <span class="pl-label-bold">Net Revenue</span>
        <span class="pl-value-bold" style="color:{nc}">{fmt_usd(r['net_revenue'])}</span>
      </div>
    </div>
    <div style="color:#25273A;font-size:10px;font-family:'IBM Plex Mono',monospace;margin-top:8px;text-align:right">
      Net = Gross − Stripe Fees − Ad Spend − $1,600 Retainer &nbsp;·&nbsp; ROAS = Gross ÷ Ad Spend
    </div>
    """, unsafe_allow_html=True)

    st.markdown("")

    # ── Campaigns ──
    if r["campaigns"]:
        section("Campaign Performance")
        camp_df = pd.DataFrame(r["campaigns"])
        # Totals
        if len(camp_df) > 1:
            tot = {
                "Campaign": "TOTALS",
                "Spend": round(camp_df["Spend"].sum(), 2),
                "Impressions": int(camp_df["Impressions"].sum()),
                "Reach": int(camp_df["Reach"].sum()),
                "Clicks": int(camp_df["Clicks"].sum()),
                "CTR %": round((camp_df["Clicks"].sum() / camp_df["Impressions"].sum() * 100) if camp_df["Impressions"].sum() > 0 else 0, 2),
                "CPC": round((camp_df["Spend"].sum() / camp_df["Clicks"].sum()) if camp_df["Clicks"].sum() > 0 else 0, 2),
                "Purchases": int(camp_df["Purchases"].sum()),
                "CPP": round((camp_df["Spend"].sum() / camp_df["Purchases"].sum()) if camp_df["Purchases"].sum() > 0 else 0, 2),
            }
            camp_df = pd.concat([camp_df, pd.DataFrame([tot])], ignore_index=True)

        st.dataframe(
            camp_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Spend": st.column_config.NumberColumn(format="$%.2f"),
                "CPC":   st.column_config.NumberColumn(format="$%.2f"),
                "CPP":   st.column_config.NumberColumn(format="$%.2f"),
                "CTR %": st.column_config.NumberColumn(format="%.2f%%"),
            }
        )
