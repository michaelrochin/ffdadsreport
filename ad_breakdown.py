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
#MainMenu, footer, header { visibility: hidden; }

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

[data-testid="stDataFrame"] {
    background: #12131C;
    border: 1px solid #1E2030;
    border-radius: 12px;
    overflow: hidden;
}
[data-testid="stFileUploader"] {
    background: #12131C;
    border: 1.5px dashed #252836;
    border-radius: 12px;
    padding: 12px;
}

.section-label {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;
    margin-top: 6px;
}
.section-bar { width: 3px; height: 14px; background: #F5A623; border-radius: 2px; display: inline-block; }
.section-text { color: #4E5270; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.14em; }

.roas-number { font-family: 'IBM Plex Mono', monospace; font-size: 60px; font-weight: 700; line-height: 1; letter-spacing: -0.02em; }
.roas-label { color: #4E5270; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.14em; margin-bottom: 10px; }
.badge { display: inline-block; padding: 3px 12px; border-radius: 20px; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; margin-top: 10px; }

.pl-row { display: flex; justify-content: space-between; padding: 12px 20px; border-bottom: 1px solid #141520; }
.pl-row-bold { display: flex; justify-content: space-between; padding: 16px 20px; background: #1A1C2C; border-top: 1px solid #1E2030; border-radius: 0 0 12px 12px; }
.pl-label { color: #8084A8; font-size: 13px; }
.pl-label-bold { color: #E2E4F0; font-size: 15px; font-weight: 700; }
.pl-value { font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 700; }
.pl-value-bold { font-family: 'IBM Plex Mono', monospace; font-size: 16px; font-weight: 700; }
.pl-container { background: #12131C; border: 1px solid #1E2030; border-radius: 12px; overflow: hidden; }

.date-range-box {
    background: #12131C;
    border: 1px solid #1E2030;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 18px;
}
.date-range-title { color: #4E5270; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.12em; margin-bottom: 10px; }
.date-chip {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 6px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    font-weight: 700;
    margin-right: 8px;
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
.stButton > button:hover { background: #FFBA45 !important; }
.stButton > button:disabled { background: #14151E !important; color: #2E3048 !important; border: 1px solid #1E2030 !important; }

.dot { width:7px; height:7px; border-radius:50%; display:inline-block; margin-right:6px; vertical-align:middle; }
.info-bar { background: #12131C; border: 1px solid #1A1C2C; border-radius: 10px; padding: 14px 20px; margin-top: 20px; display: flex; gap: 28px; }
h1 { font-family: 'DM Sans', sans-serif !important; }
h2, h3 { font-family: 'DM Sans', sans-serif !important; color: #E2E4F0 !important; }
hr { border-color: #1E2030 !important; }
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
FUNNEL_PRICES  = [37, 74, 77]
RETAINER       = 1600.0
WEEKLY_RETAINER = RETAINER / 4  # ~$400/week
PRICE_LABELS   = {37: "Base Offer ($37)", 74: "Base + Bump ($74)", 77: "Upsell ($77)"}

# ── Helpers ───────────────────────────────────────────────────────────────────

def find_col(df, candidates):
    cols_lower = {c.lower(): c for c in df.columns}
    for cand in candidates:
        for key, orig in cols_lower.items():
            if cand.lower() in key:
                return orig
    return None

def parse_num_series(series):
    return pd.to_numeric(
        series.astype(str).str.replace(r'[$,%\s,]', '', regex=True),
        errors='coerce'
    ).fillna(0)

def parse_date_series(series):
    parsed = pd.to_datetime(series, infer_datetime_format=True, errors='coerce', utc=True)
    return parsed.dt.tz_localize(None)

def section(label):
    st.markdown(f"""
    <div class="section-label">
        <span class="section-bar"></span>
        <span class="section-text">{label}</span>
    </div>""", unsafe_allow_html=True)

def fmt_usd(n):  return f"${n:,.2f}"
def fmt_n(n):    return f"{int(round(n)):,}"
def fmt_pct(n):  return f"{n:.2f}%"

def roas_color(roas):
    if roas >= 3: return "#F5A623"
    if roas >= 2: return "#FFD166"
    if roas >= 1: return "#FFD166"
    return "#FF4757"

def roas_badge(roas):
    if roas >= 3: return "🔥 Strong",       "#F5A62318", "#F5A623"
    if roas >= 2: return "✓ Profitable",    "#FFD16618", "#FFD166"
    if roas >= 1: return "⚠ Marginal",      "#FFD16618", "#FFD166"
    return             "✗ Losing Money",    "#FF475718", "#FF4757"

def net_color(net): return "#00D97E" if net >= 0 else "#FF4757"

def week_label(dt):
    return dt.strftime("Week of %b %-d")

# ── Loaders ───────────────────────────────────────────────────────────────────

def load_stripe(df):
    amt_col    = find_col(df, ["amount"])
    fee_col    = find_col(df, ["fee"])
    status_col = find_col(df, ["status"])
    date_col   = find_col(df, ["created", "date"])

    if not amt_col:
        raise ValueError("Stripe CSV: could not find an 'Amount' column.")
    if not date_col:
        raise ValueError("Stripe CSV: could not find a 'Created' or 'Date' column.")

    df = df.copy()
    if status_col:
        df = df[df[status_col].astype(str).str.lower().str.contains(
            "paid|succeeded|complete|captured", na=False)]

    df["_amount"] = parse_num_series(df[amt_col])
    df["_fee"]    = parse_num_series(df[fee_col]) if fee_col else 0.0
    df["_date"]   = parse_date_series(df[date_col])
    df = df[(df["_amount"] > 0) & (df["_date"].notna())]

    def nearest_price(val):
        for p in FUNNEL_PRICES:
            if abs(val - p) < 1:
                return p
        return None

    df["_price_tier"] = df["_amount"].apply(nearest_price)
    df = df[df["_price_tier"].notna()]
    return df

def load_facebook(df):
    spend_col    = find_col(df, ["amount spent", "spend", "cost"])
    impress_col  = find_col(df, ["impressions"])
    reach_col    = find_col(df, ["reach"])
    clicks_col   = find_col(df, ["link click", "clicks (link)", "outbound click", "clicks (all)", "clicks"])
    purch_col    = find_col(df, ["purchases", "results", "purchase"])
    campaign_col = find_col(df, ["campaign name", "campaign"])
    date_col     = find_col(df, ["reporting starts", "date start", "day", "date", "week"])

    if not spend_col:
        raise ValueError("Facebook CSV: could not find a 'Spend' or 'Amount Spent' column.")
    if not date_col:
        raise ValueError("Facebook CSV: could not find a date column (tried: Day, Date, Reporting Starts, Week).")

    df = df.copy()
    df["_date"]      = parse_date_series(df[date_col])
    df["_spend"]     = parse_num_series(df[spend_col])
    df["_impress"]   = parse_num_series(df[impress_col])   if impress_col  else 0.0
    df["_reach"]     = parse_num_series(df[reach_col])     if reach_col    else 0.0
    df["_clicks"]    = parse_num_series(df[clicks_col])    if clicks_col   else 0.0
    df["_purchases"] = parse_num_series(df[purch_col])     if purch_col    else 0.0
    df["_campaign"]  = df[campaign_col].astype(str)        if campaign_col else "All Campaigns"
    df = df[df["_date"].notna()]
    return df

# ── Date Alignment ────────────────────────────────────────────────────────────

def align_dates(stripe_df, fb_df):
    s_min, s_max = stripe_df["_date"].min(), stripe_df["_date"].max()
    f_min, f_max = fb_df["_date"].min(),     fb_df["_date"].max()

    overlap_start = max(s_min, f_min)
    overlap_end   = min(s_max, f_max)

    if overlap_start > overlap_end:
        raise ValueError(
            f"No overlapping dates found.\n"
            f"Stripe range: {s_min.date()} → {s_max.date()}\n"
            f"Facebook range: {f_min.date()} → {f_max.date()}"
        )

    s_filtered = stripe_df[
        (stripe_df["_date"] >= overlap_start) &
        (stripe_df["_date"] <= overlap_end)
    ].copy()
    f_filtered = fb_df[
        (fb_df["_date"] >= overlap_start) &
        (fb_df["_date"] <= overlap_end)
    ].copy()

    date_info = {
        "stripe_original": (s_min.date(), s_max.date()),
        "fb_original":     (f_min.date(), f_max.date()),
        "overlap_start":   overlap_start.date(),
        "overlap_end":     overlap_end.date(),
        "stripe_trimmed":  (s_min.date() != overlap_start.date() or s_max.date() != overlap_end.date()),
        "fb_trimmed":      (f_min.date() != overlap_start.date() or f_max.date() != overlap_end.date()),
    }
    return s_filtered, f_filtered, date_info

# ── Core Metrics ──────────────────────────────────────────────────────────────

def compute_metrics(stripe_df, fb_df, retainer=RETAINER):
    gross_revenue = stripe_df["_amount"].sum()
    total_fees    = stripe_df["_fee"].sum()
    tx_count      = len(stripe_df)

    price_groups = {}
    for p in FUNNEL_PRICES:
        sub = stripe_df[stripe_df["_price_tier"] == p]
        if len(sub) > 0:
            price_groups[p] = {
                "count":   len(sub),
                "revenue": sub["_amount"].sum(),
                "fees":    sub["_fee"].sum(),
            }

    ad_spend    = fb_df["_spend"].sum()
    impressions = fb_df["_impress"].sum()
    reach       = fb_df["_reach"].sum()
    clicks      = fb_df["_clicks"].sum()
    fb_purch    = fb_df["_purchases"].sum()

    purchases   = fb_purch if fb_purch > 0 else tx_count
    ctr         = (clicks / impressions * 100) if impressions > 0 else 0
    cpc         = (ad_spend / clicks)           if clicks > 0      else 0
    cpp         = (ad_spend / purchases)        if purchases > 0   else 0
    roas        = (gross_revenue / ad_spend)    if ad_spend > 0    else 0
    net_revenue = gross_revenue - total_fees - ad_spend - retainer

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
    }

# ── Weekly Breakdown ──────────────────────────────────────────────────────────

def weekly_breakdown(stripe_df, fb_df):
    s = stripe_df.copy()
    f = fb_df.copy()

    # Assign ISO week-start (Monday) to each row
    s["_week"] = s["_date"].dt.to_period("W").apply(lambda p: p.start_time)
    f["_week"] = f["_date"].dt.to_period("W").apply(lambda p: p.start_time)

    all_weeks = sorted(set(s["_week"].unique()) | set(f["_week"].unique()))

    rows = []
    for week_start in all_weeks:
        s_w = s[s["_week"] == week_start]
        f_w = f[f["_week"] == week_start]
        m = compute_metrics(s_w, f_w, retainer=WEEKLY_RETAINER)
        rows.append({
            "Week":            week_label(week_start),
            "Transactions":    m["tx_count"],
            "Gross Revenue":   round(m["gross_revenue"], 2),
            "Stripe Fees":     round(m["total_fees"], 2),
            "Ad Spend":        round(m["ad_spend"], 2),
            "Retainer (wk)":   round(WEEKLY_RETAINER, 2),
            "Net Revenue":     round(m["net_revenue"], 2),
            "ROAS":            round(m["roas"], 2),
            "Impressions":     int(m["impressions"]),
            "Clicks":          int(m["clicks"]),
            "CTR %":           round(m["ctr"], 2),
            "CPC":             round(m["cpc"], 2),
            "Purchases":       int(m["purchases"]),
            "CPP":             round(m["cpp"], 2),
        })

    df = pd.DataFrame(rows)

    # Totals row
    total_spend   = df["Ad Spend"].sum()
    total_clicks  = df["Clicks"].sum()
    total_impress = df["Impressions"].sum()
    total_gross   = df["Gross Revenue"].sum()
    total_purch   = df["Purchases"].sum()

    totals = {
        "Week":           "TOTALS",
        "Transactions":   int(df["Transactions"].sum()),
        "Gross Revenue":  round(total_gross, 2),
        "Stripe Fees":    round(df["Stripe Fees"].sum(), 2),
        "Ad Spend":       round(total_spend, 2),
        "Retainer (wk)":  round(df["Retainer (wk)"].sum(), 2),
        "Net Revenue":    round(df["Net Revenue"].sum(), 2),
        "ROAS":           round(total_gross / total_spend, 2) if total_spend > 0 else 0,
        "Impressions":    int(total_impress),
        "Clicks":         int(total_clicks),
        "CTR %":          round(total_clicks / total_impress * 100, 2) if total_impress > 0 else 0,
        "CPC":            round(total_spend / total_clicks, 2) if total_clicks > 0 else 0,
        "Purchases":      int(total_purch),
        "CPP":            round(total_spend / total_purch, 2) if total_purch > 0 else 0,
    }

    df_display = pd.concat([df, pd.DataFrame([totals])], ignore_index=True)
    return df_display

# ── Campaign Breakdown ────────────────────────────────────────────────────────

def campaign_breakdown(fb_df):
    rows = []
    for name, grp in fb_df.groupby("_campaign"):
        s  = grp["_spend"].sum()
        i  = grp["_impress"].sum()
        r  = grp["_reach"].sum()
        cl = grp["_clicks"].sum()
        p  = grp["_purchases"].sum()
        rows.append({
            "Campaign":    str(name),
            "Spend":       round(s, 2),
            "Impressions": int(i),
            "Reach":       int(r),
            "Clicks":      int(cl),
            "CTR %":       round((cl/i*100) if i > 0 else 0, 2),
            "CPC":         round((s/cl) if cl > 0 else 0, 2),
            "Purchases":   int(p),
            "CPP":         round((s/p) if p > 0 else 0, 2),
        })
    rows.sort(key=lambda x: x["Spend"], reverse=True)

    if len(rows) > 1:
        df = pd.DataFrame(rows)
        rows.append({
            "Campaign":    "TOTALS",
            "Spend":       round(df["Spend"].sum(), 2),
            "Impressions": int(df["Impressions"].sum()),
            "Reach":       int(df["Reach"].sum()),
            "Clicks":      int(df["Clicks"].sum()),
            "CTR %":       round(df["Clicks"].sum()/df["Impressions"].sum()*100 if df["Impressions"].sum()>0 else 0, 2),
            "CPC":         round(df["Spend"].sum()/df["Clicks"].sum() if df["Clicks"].sum()>0 else 0, 2),
            "Purchases":   int(df["Purchases"].sum()),
            "CPP":         round(df["Spend"].sum()/df["Purchases"].sum() if df["Purchases"].sum()>0 else 0, 2),
        })
    return rows

# ═══════════════════════════════════════════════════════════════════════════════
# ── UI
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div style="margin-bottom:32px">
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px">
    <span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:#F5A623"></span>
    <span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:#4A9EFF;opacity:0.75"></span>
    <span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:#00D97E;opacity:0.5"></span>
    <span style="color:#2E3048;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.14em;margin-left:4px">Performance Intelligence</span>
  </div>
  <h1 style="font-family:'DM Sans',sans-serif;font-size:32px;font-weight:700;color:#E2E4F0;letter-spacing:-0.01em;line-height:1.15;margin:0">
    Ad Revenue Breakdown
  </h1>
  <p style="color:#35384E;font-family:'DM Sans',sans-serif;font-size:13px;margin-top:8px">
    Front-end funnel · $37 base · $74 w/ bump · $77 upsell · $1,600/mo retainer · Date-aligned · Week-by-week
  </p>
</div>
""", unsafe_allow_html=True)

# ── File Uploaders ──
col1, col2 = st.columns(2)
with col1:
    stripe_file = st.file_uploader(
        "💳  Stripe Export", type="csv",
        help="Needs: Amount, Fee, Created/Date columns. Any date range — will be trimmed to match Facebook."
    )
with col2:
    fb_file = st.file_uploader(
        "📊  Facebook Ads Export", type="csv",
        help="Needs: Amount Spent, Impressions, Clicks, Purchases, and a Day/Date column. Any date range — will be trimmed to match Stripe."
    )

st.markdown("")

if stripe_file and fb_file:
    run = st.button("→  Run Analysis")
else:
    st.button("Upload both files to continue", disabled=True)
    run = False

st.markdown("""
<div class="info-bar">
  <div>
    <span class="dot" style="background:#F5A623"></span>
    <strong style="color:#8084A8;font-size:12px">Date-Aligned</strong><br>
    <span style="color:#35384E;font-size:11px">Only overlapping days analyzed — mismatched ranges trimmed automatically</span>
  </div>
  <div>
    <span class="dot" style="background:#4A9EFF"></span>
    <strong style="color:#8084A8;font-size:12px">Week-by-Week</strong><br>
    <span style="color:#35384E;font-size:11px">Full breakdown per calendar week (Mon–Sun)</span>
  </div>
  <div>
    <span class="dot" style="background:#00D97E"></span>
    <strong style="color:#8084A8;font-size:12px">Retainer Prorated</strong><br>
    <span style="color:#35384E;font-size:11px">$1,600/mo ÷ 4 = ~$400/week in weekly table</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Run & Cache ──
if run:
    try:
        raw_stripe = pd.read_csv(stripe_file)
        raw_fb     = pd.read_csv(fb_file)
        stripe_df  = load_stripe(raw_stripe)
        fb_df      = load_facebook(raw_fb)
        stripe_df, fb_df, date_info = align_dates(stripe_df, fb_df)
        st.session_state["stripe_df"] = stripe_df
        st.session_state["fb_df"]     = fb_df
        st.session_state["date_info"] = date_info
    except Exception as e:
        st.error(f"⚠ {e}")
        st.stop()

if "stripe_df" not in st.session_state:
    st.stop()

stripe_df = st.session_state["stripe_df"]
fb_df     = st.session_state["fb_df"]
date_info = st.session_state["date_info"]

st.markdown("---")

# ── Date Range Banner ──
trimmed = date_info["stripe_trimmed"] or date_info["fb_trimmed"]
banner_color = "#F5A623" if trimmed else "#00D97E"
banner_icon  = "⚠" if trimmed else "✓"
trim_note    = (
    "<div style='color:#F5A623;font-size:11px;margin-top:8px'>"
    "⚠ Date ranges didn't match — analysis automatically trimmed to the overlapping period only."
    "</div>"
) if trimmed else ""

st.markdown(f"""
<div class="date-range-box">
  <div class="date-range-title">{banner_icon} Analyzed Date Range</div>
  <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:6px">
    <span class="date-chip" style="background:{banner_color}22;color:{banner_color}">
      {date_info['overlap_start']} → {date_info['overlap_end']}
    </span>
  </div>
  <div style="color:#4E5270;font-size:11px;font-family:'DM Sans',sans-serif">
    Stripe file: <strong style="color:#6B6F8E">{date_info['stripe_original'][0]} → {date_info['stripe_original'][1]}</strong>
    &nbsp;&nbsp;|&nbsp;&nbsp;
    Facebook file: <strong style="color:#6B6F8E">{date_info['fb_original'][0]} → {date_info['fb_original'][1]}</strong>
  </div>
  {trim_note}
</div>
""", unsafe_allow_html=True)

# ── Overall Metrics ──
r  = compute_metrics(stripe_df, fb_df)
rc = roas_color(r["roas"])
badge_text, badge_bg, badge_fg = roas_badge(r["roas"])
nc = net_color(r["net_revenue"])

section("Overall Summary — Full Aligned Period")

hero_l, hero_div, hero_r = st.columns([2, 0.05, 5])
with hero_l:
    st.markdown(f"""
    <div style="padding:8px 0">
      <div class="roas-label">Return on Ad Spend</div>
      <div class="roas-number" style="color:{rc}">{r['roas']:.2f}<span style="font-size:26px;opacity:0.7">x</span></div>
      <div style="color:#35384E;font-size:11px;font-family:'DM Sans',sans-serif;margin-top:8px">Every $1 in ads → ${r['roas']:.2f} gross</div>
      <div class="badge" style="background:{badge_bg};color:{badge_fg}">{badge_text}</div>
    </div>
    """, unsafe_allow_html=True)
with hero_div:
    st.markdown('<div style="width:1px;min-height:140px;background:#1E2030"></div>', unsafe_allow_html=True)
with hero_r:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Gross Revenue",  fmt_usd(r["gross_revenue"]))
    c2.metric("Net Revenue",    fmt_usd(r["net_revenue"]))
    c3.metric("Ad Spend",       fmt_usd(r["ad_spend"]))
    c4.metric("Transactions",   fmt_n(r["tx_count"]))

st.markdown("")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Stripe Fees",          fmt_usd(r["total_fees"]),  delta="Auto-calculated", delta_color="inverse")
k2.metric("Ads Manager Retainer", "−$1,600.00",              delta="Fixed monthly",   delta_color="inverse")
k3.metric("Cost Per Purchase",    fmt_usd(r["cpp"]))
net_margin = (r["net_revenue"] / r["gross_revenue"] * 100) if r["gross_revenue"] > 0 else 0
k4.metric("Net Margin", fmt_pct(net_margin))

st.markdown("")

a1, a2, a3, a4 = st.columns(4)
a1.metric("Impressions",    fmt_n(r["impressions"]))
a2.metric("Reach",          fmt_n(r["reach"]))
ctr_note = "Above avg" if r["ctr"] >= 2 else ("Average" if r["ctr"] >= 1 else "Below avg")
a3.metric("CTR",            fmt_pct(r["ctr"]), delta=ctr_note)
a4.metric("Cost Per Click", fmt_usd(r["cpc"]))

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

# ── Week-by-Week ──
section("Week-by-Week Breakdown")
st.markdown("""
<div style="color:#4E5270;font-size:11px;font-family:'DM Sans',sans-serif;margin-bottom:12px">
  Each week runs Mon–Sun. Retainer prorated at $400/week. Both Stripe and Facebook data filtered to the same days per week.
</div>
""", unsafe_allow_html=True)

weekly_df = weekly_breakdown(stripe_df, fb_df)

st.dataframe(
    weekly_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Gross Revenue":  st.column_config.NumberColumn(format="$%.2f"),
        "Stripe Fees":    st.column_config.NumberColumn(format="$%.2f"),
        "Ad Spend":       st.column_config.NumberColumn(format="$%.2f"),
        "Retainer (wk)":  st.column_config.NumberColumn(format="$%.2f"),
        "Net Revenue":    st.column_config.NumberColumn(format="$%.2f"),
        "ROAS":           st.column_config.NumberColumn(format="%.2fx"),
        "CTR %":          st.column_config.NumberColumn(format="%.2f%%"),
        "CPC":            st.column_config.NumberColumn(format="$%.2f"),
        "CPP":            st.column_config.NumberColumn(format="$%.2f"),
    }
)

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
    rev_df = pd.concat([rev_df, pd.DataFrame([{
        "Product":       "TOTAL",
        "Transactions":  rev_df["Transactions"].sum(),
        "Gross Revenue": round(rev_df["Gross Revenue"].sum(), 2),
        "Stripe Fees":   round(rev_df["Stripe Fees"].sum(), 2),
        "Net Revenue":   round(rev_df["Net Revenue"].sum(), 2),
    }])], ignore_index=True)
    st.dataframe(rev_df, use_container_width=True, hide_index=True,
        column_config={
            "Gross Revenue": st.column_config.NumberColumn(format="$%.2f"),
            "Stripe Fees":   st.column_config.NumberColumn(format="$%.2f"),
            "Net Revenue":   st.column_config.NumberColumn(format="$%.2f"),
        })

st.markdown("")

# ── Campaigns ──
camps = campaign_breakdown(fb_df)
if camps:
    section("Campaign Performance")
    st.dataframe(
        pd.DataFrame(camps),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Spend": st.column_config.NumberColumn(format="$%.2f"),
            "CPC":   st.column_config.NumberColumn(format="$%.2f"),
            "CPP":   st.column_config.NumberColumn(format="$%.2f"),
            "CTR %": st.column_config.NumberColumn(format="%.2f%%"),
        }
    )
