import streamlit as st
import pandas as pd
import numpy as np

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Ad Revenue Breakdown", page_icon="📊", layout="wide")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;700&family=DM+Sans:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; background-color: #0C0D16; color: #E2E4F0; }
.stApp { background-color: #0C0D16; }
#MainMenu, footer, header { visibility: hidden; }
[data-testid="metric-container"] { background: #12131C; border: 1px solid #1E2030; border-radius: 12px; padding: 18px 20px; }
[data-testid="stMetricLabel"] { color: #4E5270 !important; font-size: 10px !important; font-weight: 700 !important; text-transform: uppercase; letter-spacing: 0.12em; font-family: 'DM Sans', sans-serif !important; }
[data-testid="stMetricValue"] { font-family: 'IBM Plex Mono', monospace !important; font-weight: 700 !important; font-size: 22px !important; }
[data-testid="stMetricDelta"] { font-size: 11px !important; }
[data-testid="stDataFrame"] { background: #12131C; border: 1px solid #1E2030; border-radius: 12px; overflow: hidden; }
[data-testid="stFileUploader"] { background: #12131C; border: 1.5px dashed #252836; border-radius: 12px; padding: 12px; }
.section-label { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; margin-top: 6px; }
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
.date-range-box { background: #12131C; border: 1px solid #1E2030; border-radius: 12px; padding: 16px 20px; margin-bottom: 18px; }
.date-range-title { color: #4E5270; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.12em; margin-bottom: 10px; }
.date-chip { display: inline-block; padding: 4px 12px; border-radius: 6px; font-family: 'IBM Plex Mono', monospace; font-size: 11px; font-weight: 700; margin-right: 8px; }
.stButton > button { background: #F5A623 !important; color: #0C0D16 !important; font-weight: 700 !important; font-family: 'DM Sans', sans-serif !important; border: none !important; border-radius: 10px !important; padding: 12px 0 !important; font-size: 15px !important; width: 100%; transition: all 0.18s ease; }
.stButton > button:hover { background: #FFBA45 !important; }
.stButton > button:disabled { background: #14151E !important; color: #2E3048 !important; border: 1px solid #1E2030 !important; }
.dot { width:7px; height:7px; border-radius:50%; display:inline-block; margin-right:6px; vertical-align:middle; }
.info-bar { background: #12131C; border: 1px solid #1A1C2C; border-radius: 10px; padding: 14px 20px; margin-top: 20px; display: flex; gap: 28px; }
h1 { font-family: 'DM Sans', sans-serif !important; }
hr { border-color: #1E2030 !important; }
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
FUNNEL_PRICES   = [37, 74, 77]
RETAINER        = 1600.0
WEEKLY_RETAINER = RETAINER / 4   # ~$400/week
PRICE_LABELS    = {37: "Base Offer ($37)", 74: "Base + Bump ($74)", 77: "Upsell ($77)"}

# ── Helpers ───────────────────────────────────────────────────────────────────

def find_col(df, candidates):
    """Case-insensitive partial match on column names."""
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
    st.markdown(f'<div class="section-label"><span class="section-bar"></span>'
                f'<span class="section-text">{label}</span></div>', unsafe_allow_html=True)

def fmt_usd(n):  return f"${n:,.2f}"
def fmt_n(n):    return f"{int(round(n)):,}"
def fmt_pct(n):  return f"{n:.2f}%"

def roas_color(v):
    return "#F5A623" if v >= 3 else "#FFD166" if v >= 1 else "#FF4757"

def roas_badge(v):
    if v >= 3: return "🔥 Strong",     "#F5A62318", "#F5A623"
    if v >= 2: return "✓ Profitable",  "#FFD16618", "#FFD166"
    if v >= 1: return "⚠ Marginal",    "#FFD16618", "#FFD166"
    return          "✗ Losing Money",  "#FF475718", "#FF4757"

def net_color(n): return "#00D97E" if n >= 0 else "#FF4757"

def week_label(dt): return dt.strftime("Week of %b %-d")

# ── Stripe Loader ─────────────────────────────────────────────────────────────

def load_stripe(df):
    amt_col    = find_col(df, ["amount"])
    fee_col    = find_col(df, ["fee"])
    status_col = find_col(df, ["status"])
    date_col   = find_col(df, ["created", "date"])

    if not amt_col:  raise ValueError("Stripe CSV: can't find 'Amount' column.")
    if not date_col: raise ValueError("Stripe CSV: can't find 'Created' or 'Date' column.")

    df = df.copy()
    if status_col:
        df = df[df[status_col].astype(str).str.lower().str.contains(
            "paid|succeeded|complete|captured", na=False)]

    df["_amount"] = parse_num_series(df[amt_col])
    df["_fee"]    = parse_num_series(df[fee_col]) if fee_col else 0.0
    df["_date"]   = parse_date_series(df[date_col])
    df = df[(df["_amount"] > 0) & (df["_date"].notna())]

    def nearest(val):
        for p in FUNNEL_PRICES:
            if abs(val - p) < 1: return p
        return None

    df["_price_tier"] = df["_amount"].apply(nearest)
    return df[df["_price_tier"].notna()].copy()

# ── Facebook Loader ───────────────────────────────────────────────────────────
# Handles two export formats:
#   • Daily breakdown  — one row per day, single date column ("Day")
#   • Aggregated       — one row per ad/adset, "Reporting starts" + "Reporting ends"
#
# Aggregated detection: if unique start dates << total date-range days,
# the file is aggregated and we prorate ad metrics by day count per week.

def load_facebook(df):
    spend_col    = find_col(df, ["amount spent", "spend", "cost"])
    impress_col  = find_col(df, ["impressions"])
    reach_col    = find_col(df, ["reach"])
    clicks_col   = find_col(df, ["link click", "clicks (link)", "outbound click",
                                  "clicks (all)", "clicks"])
    purch_col    = find_col(df, ["purchases", "results", "purchase"])

    # Prefer "Ad set name" over "Ad name" over "Campaign name" for grouping
    group_col    = (find_col(df, ["ad set name"])
                    or find_col(df, ["campaign name", "campaign"])
                    or find_col(df, ["ad name"]))

    start_col    = find_col(df, ["reporting starts", "date start", "day", "date", "week"])
    end_col      = find_col(df, ["reporting ends", "date stop", "end date", "date end"])

    if not spend_col:  raise ValueError("Facebook CSV: can't find 'Amount Spent' / 'Spend' column.")
    if not start_col:  raise ValueError("Facebook CSV: can't find a date column "
                                        "(expected: 'Day', 'Reporting Starts', etc.).")

    df = df.copy()
    df["_spend"]      = parse_num_series(df[spend_col])
    df["_impress"]    = parse_num_series(df[impress_col])   if impress_col else 0.0
    df["_reach"]      = parse_num_series(df[reach_col])     if reach_col   else 0.0
    df["_clicks"]     = parse_num_series(df[clicks_col])    if clicks_col  else 0.0
    # Purchases may be NaN for rows with no conversions — fill with 0
    df["_purchases"]  = parse_num_series(df[purch_col])     if purch_col   else 0.0
    df["_group"]      = df[group_col].astype(str)           if group_col   else "All Campaigns"
    df["_date_start"] = parse_date_series(df[start_col])
    df["_date_end"]   = (parse_date_series(df[end_col])
                         if end_col else df["_date_start"])
    df["_date_end"]   = df["_date_end"].fillna(df["_date_start"])
    df["_date"]       = df["_date_start"]
    df = df[df["_date"].notna()].copy()

    # Detect aggregated export:
    # If nearly all rows share the same start date (or unique start dates are
    # far fewer than the days spanned), the export is per-ad/adset, not per-day.
    total_days   = max((df["_date_end"].max() - df["_date_start"].min()).days + 1, 1)
    unique_starts = df["_date_start"].nunique()
    is_aggregated = unique_starts < max(total_days * 0.5, 2)

    df.attrs["is_aggregated"] = is_aggregated
    df.attrs["group_col_name"] = group_col or "Ad Set / Group"
    return df

# ── Date Alignment ────────────────────────────────────────────────────────────

def align_dates(stripe_df, fb_df):
    s_min = stripe_df["_date"].min()
    s_max = stripe_df["_date"].max()
    f_min = fb_df["_date_start"].min()
    f_max = fb_df["_date_end"].max()

    overlap_start = max(s_min, f_min)
    overlap_end   = min(s_max, f_max)

    if overlap_start > overlap_end:
        raise ValueError(
            f"No overlapping dates between files.\n"
            f"Stripe:   {s_min.date()} → {s_max.date()}\n"
            f"Facebook: {f_min.date()} → {f_max.date()}"
        )

    s_f = stripe_df[
        (stripe_df["_date"] >= overlap_start) &
        (stripe_df["_date"] <= overlap_end)
    ].copy()

    f_f = fb_df[
        (fb_df["_date_start"] <= overlap_end) &
        (fb_df["_date_end"]   >= overlap_start)
    ].copy()

    return s_f, f_f, {
        "stripe_original":  (s_min.date(), s_max.date()),
        "fb_original":      (f_min.date(), f_max.date()),
        "overlap_start":    overlap_start.date(),
        "overlap_end":      overlap_end.date(),
        "stripe_trimmed":   s_min.date() != overlap_start.date() or s_max.date() != overlap_end.date(),
        "fb_trimmed":       f_min.date() != overlap_start.date() or f_max.date() != overlap_end.date(),
        "fb_is_aggregated": fb_df.attrs.get("is_aggregated", False),
        "fb_group_label":   fb_df.attrs.get("group_col_name", "Ad Set / Group"),
    }

# ── Core Metrics ──────────────────────────────────────────────────────────────

def compute_metrics(stripe_df, fb_df, retainer=RETAINER):
    gross   = stripe_df["_amount"].sum()
    fees    = stripe_df["_fee"].sum()
    tx      = len(stripe_df)
    spend   = fb_df["_spend"].sum()
    impress = fb_df["_impress"].sum()
    reach   = fb_df["_reach"].sum()
    clicks  = fb_df["_clicks"].sum()
    purch   = fb_df["_purchases"].sum()

    price_groups = {}
    for p in FUNNEL_PRICES:
        sub = stripe_df[stripe_df["_price_tier"] == p]
        if len(sub):
            price_groups[p] = {"count": len(sub),
                                "revenue": sub["_amount"].sum(),
                                "fees":    sub["_fee"].sum()}

    purchases = purch if purch > 0 else tx
    ctr  = clicks / impress * 100 if impress > 0 else 0
    cpc  = spend  / clicks        if clicks  > 0 else 0
    cpp  = spend  / purchases     if purchases > 0 else 0
    roas = gross  / spend         if spend   > 0 else 0
    net  = gross  - fees - spend  - retainer

    return dict(gross_revenue=gross, net_revenue=net, total_fees=fees,
                ad_spend=spend, roas=roas, cpp=cpp, ctr=ctr, cpc=cpc,
                impressions=impress, reach=reach, clicks=clicks,
                purchases=purchases, tx_count=tx, price_groups=price_groups)

# ── Weekly Breakdown ──────────────────────────────────────────────────────────
# Aggregated FB exports (one row per ad covering the whole period):
#   → prorate each metric proportionally by days-in-week / total-days
# Daily FB exports (one row per day):
#   → filter rows to each week directly

def weekly_breakdown(stripe_df, fb_df, date_info):
    is_agg        = date_info["fb_is_aggregated"]
    overlap_start = pd.Timestamp(date_info["overlap_start"])
    overlap_end   = pd.Timestamp(date_info["overlap_end"])
    total_days    = max((overlap_end - overlap_start).days + 1, 1)

    s = stripe_df.copy()
    s["_week"] = s["_date"].dt.to_period("W").apply(lambda p: p.start_time)

    # Build week-start index (all Mondays in range)
    first_monday = overlap_start - pd.Timedelta(days=overlap_start.weekday())
    all_weeks    = pd.date_range(start=first_monday, end=overlap_end, freq="W-MON")
    if len(all_weeks) == 0:
        all_weeks = pd.DatetimeIndex([first_monday])

    # FB totals for proportional distribution (aggregated mode)
    fb_totals = dict(
        spend     = fb_df["_spend"].sum(),
        impress   = fb_df["_impress"].sum(),
        reach     = fb_df["_reach"].sum(),
        clicks    = fb_df["_clicks"].sum(),
        purchases = fb_df["_purchases"].sum(),
    )

    # Precompute daily FB for non-aggregated mode
    if not is_agg:
        f = fb_df.copy()
        f["_week"] = f["_date"].dt.to_period("W").apply(lambda p: p.start_time)

    rows = []
    for wk in all_weeks:
        wk_end = wk + pd.Timedelta(days=6)
        s_w    = s[s["_week"] == wk]

        if is_agg:
            eff_start  = max(wk, overlap_start)
            eff_end    = min(wk_end, overlap_end)
            days_in_wk = max((eff_end - eff_start).days + 1, 0)
            ratio      = days_in_wk / total_days
            fw_spend   = fb_totals["spend"]     * ratio
            fw_impress = fb_totals["impress"]   * ratio
            fw_reach   = fb_totals["reach"]     * ratio
            fw_clicks  = fb_totals["clicks"]    * ratio
            fw_purch   = fb_totals["purchases"] * ratio
        else:
            f_w        = f[f["_week"] == wk]
            fw_spend   = f_w["_spend"].sum()
            fw_impress = f_w["_impress"].sum()
            fw_reach   = f_w["_reach"].sum()
            fw_clicks  = f_w["_clicks"].sum()
            fw_purch   = f_w["_purchases"].sum()

        gross = s_w["_amount"].sum()
        if gross == 0 and fw_spend == 0:
            continue

        fees      = s_w["_fee"].sum()
        purchases = fw_purch if fw_purch > 0 else len(s_w)
        ctr  = fw_clicks / fw_impress * 100 if fw_impress > 0 else 0
        cpc  = fw_spend  / fw_clicks        if fw_clicks  > 0 else 0
        cpp  = fw_spend  / purchases        if purchases  > 0 else 0
        roas = gross     / fw_spend         if fw_spend   > 0 else 0
        net  = gross - fees - fw_spend - WEEKLY_RETAINER

        rows.append({
            "Week":           week_label(wk),
            "Transactions":   len(s_w),
            "Gross Revenue":  round(gross, 2),
            "Stripe Fees":    round(fees, 2),
            "Ad Spend":       round(fw_spend, 2),
            "Retainer (wk)":  round(WEEKLY_RETAINER, 2),
            "Net Revenue":    round(net, 2),
            "ROAS":           round(roas, 2),
            "Impressions":    int(round(fw_impress)),
            "Reach":          int(round(fw_reach)),
            "Clicks":         int(round(fw_clicks)),
            "CTR %":          round(ctr, 2),
            "CPC":            round(cpc, 2),
            "Purchases":      int(round(purchases)),
            "CPP":            round(cpp, 2),
        })

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    # Totals row
    ts = df["Ad Spend"].sum(); ti = df["Impressions"].sum()
    tc = df["Clicks"].sum();   tg = df["Gross Revenue"].sum()
    tp = df["Purchases"].sum()
    df = pd.concat([df, pd.DataFrame([{
        "Week":           "TOTALS",
        "Transactions":   int(df["Transactions"].sum()),
        "Gross Revenue":  round(tg, 2),
        "Stripe Fees":    round(df["Stripe Fees"].sum(), 2),
        "Ad Spend":       round(ts, 2),
        "Retainer (wk)":  round(df["Retainer (wk)"].sum(), 2),
        "Net Revenue":    round(df["Net Revenue"].sum(), 2),
        "ROAS":           round(tg / ts, 2) if ts > 0 else 0,
        "Impressions":    int(ti),
        "Reach":          int(df["Reach"].sum()),
        "Clicks":         int(tc),
        "CTR %":          round(tc / ti * 100, 2) if ti > 0 else 0,
        "CPC":            round(ts / tc, 2) if tc > 0 else 0,
        "Purchases":      int(tp),
        "CPP":            round(ts / tp, 2) if tp > 0 else 0,
    }])], ignore_index=True)
    return df

# ── Ad Set / Group Breakdown ──────────────────────────────────────────────────

def group_breakdown(fb_df, group_label="Ad Set"):
    rows = []
    for name, grp in fb_df.groupby("_group"):
        s  = grp["_spend"].sum()
        i  = grp["_impress"].sum()
        r  = grp["_reach"].sum()
        cl = grp["_clicks"].sum()
        p  = grp["_purchases"].sum()
        rows.append({
            group_label: str(name),
            "Spend":       round(s, 2),
            "Impressions": int(i),
            "Reach":       int(r),
            "Clicks":      int(cl),
            "CTR %":       round(cl/i*100  if i  > 0 else 0, 2),
            "CPC":         round(s/cl      if cl > 0 else 0, 2),
            "Purchases":   int(p),
            "CPP":         round(s/p       if p  > 0 else 0, 2),
        })
    rows.sort(key=lambda x: x["Spend"], reverse=True)
    if len(rows) > 1:
        d = pd.DataFrame(rows)
        rows.append({
            group_label:   "TOTALS",
            "Spend":       round(d["Spend"].sum(), 2),
            "Impressions": int(d["Impressions"].sum()),
            "Reach":       int(d["Reach"].sum()),
            "Clicks":      int(d["Clicks"].sum()),
            "CTR %":       round(d["Clicks"].sum()/d["Impressions"].sum()*100
                                 if d["Impressions"].sum()>0 else 0, 2),
            "CPC":         round(d["Spend"].sum()/d["Clicks"].sum()
                                 if d["Clicks"].sum()>0 else 0, 2),
            "Purchases":   int(d["Purchases"].sum()),
            "CPP":         round(d["Spend"].sum()/d["Purchases"].sum()
                                 if d["Purchases"].sum()>0 else 0, 2),
        })
    return rows

# ═══════════════════════════════════════════════════════════════════════════════
# UI
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div style="margin-bottom:32px">
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px">
    <span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:#F5A623"></span>
    <span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:#4A9EFF;opacity:0.75"></span>
    <span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:#00D97E;opacity:0.5"></span>
    <span style="color:#2E3048;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.14em;margin-left:4px">Performance Intelligence</span>
  </div>
  <h1 style="font-family:'DM Sans',sans-serif;font-size:32px;font-weight:700;color:#E2E4F0;letter-spacing:-0.01em;line-height:1.15;margin:0">Ad Revenue Breakdown</h1>
  <p style="color:#35384E;font-family:'DM Sans',sans-serif;font-size:13px;margin-top:8px">
    Front-end funnel · $37 base · $74 w/ bump · $77 upsell · $1,600/mo retainer · Date-aligned · Week-by-week
  </p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    stripe_file = st.file_uploader("💳  Stripe Export", type="csv",
        help="Needs Amount, Fee, Created/Date columns. Any date range — trimmed to match Facebook.")
with col2:
    fb_file = st.file_uploader("📊  Facebook Ads Export", type="csv",
        help="Works with aggregated (per-ad) AND daily exports. Needs Amount Spent + date columns.")

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
    <span style="color:#35384E;font-size:11px">Overlapping period only — mismatches trimmed automatically</span>
  </div>
  <div>
    <span class="dot" style="background:#4A9EFF"></span>
    <strong style="color:#8084A8;font-size:12px">Aggregated or Daily FB</strong><br>
    <span style="color:#35384E;font-size:11px">Handles both Facebook export types automatically</span>
  </div>
  <div>
    <span class="dot" style="background:#00D97E"></span>
    <strong style="color:#8084A8;font-size:12px">Retainer Prorated</strong><br>
    <span style="color:#35384E;font-size:11px">$1,600/mo ÷ 4 = ~$400/week in weekly table</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Run & Cache ───────────────────────────────────────────────────────────────
if run:
    try:
        stripe_df = load_stripe(pd.read_csv(stripe_file))
        fb_df     = load_facebook(pd.read_csv(fb_file))
        stripe_df, fb_df, date_info = align_dates(stripe_df, fb_df)
        st.session_state.update(stripe_df=stripe_df, fb_df=fb_df, date_info=date_info)
    except Exception as e:
        st.error(f"⚠ {e}")
        st.stop()

if "stripe_df" not in st.session_state:
    st.stop()

stripe_df = st.session_state["stripe_df"]
fb_df     = st.session_state["fb_df"]
date_info = st.session_state["date_info"]

st.markdown("---")

# ── Date Range Banner ─────────────────────────────────────────────────────────
trimmed      = date_info["stripe_trimmed"] or date_info["fb_trimmed"]
is_agg       = date_info["fb_is_aggregated"]
group_label  = date_info["fb_group_label"] or "Ad Set / Group"
banner_color = "#F5A623" if trimmed else "#00D97E"
trim_note    = ("<div style='color:#F5A623;font-size:11px;margin-top:8px'>"
                "⚠ Date ranges didn't match — trimmed to overlapping period only.</div>") if trimmed else ""
agg_note     = ("<div style='color:#4A9EFF;font-size:11px;margin-top:6px'>"
                "ℹ Facebook export is aggregated (per-ad rows, not daily). "
                "Ad metrics prorated proportionally by day count per week.</div>") if is_agg else ""

st.markdown(f"""
<div class="date-range-box">
  <div class="date-range-title">{'⚠' if trimmed else '✓'} Analyzed Date Range</div>
  <div style="margin-bottom:6px">
    <span class="date-chip" style="background:{banner_color}22;color:{banner_color}">
      {date_info['overlap_start']} → {date_info['overlap_end']}
    </span>
  </div>
  <div style="color:#4E5270;font-size:11px;font-family:'DM Sans',sans-serif">
    Stripe: <strong style="color:#6B6F8E">{date_info['stripe_original'][0]} → {date_info['stripe_original'][1]}</strong>
    &nbsp;|&nbsp;
    Facebook: <strong style="color:#6B6F8E">{date_info['fb_original'][0]} → {date_info['fb_original'][1]}</strong>
  </div>
  {trim_note}{agg_note}
</div>
""", unsafe_allow_html=True)

# ── Overall Summary ───────────────────────────────────────────────────────────
r  = compute_metrics(stripe_df, fb_df)
rc = roas_color(r["roas"])
bt, bb, bf = roas_badge(r["roas"])
nc = net_color(r["net_revenue"])

section("Overall Summary — Full Aligned Period")
hl, hd, hr = st.columns([2, 0.05, 5])
with hl:
    st.markdown(f"""
    <div style="padding:8px 0">
      <div class="roas-label">Return on Ad Spend</div>
      <div class="roas-number" style="color:{rc}">{r['roas']:.2f}<span style="font-size:26px;opacity:0.7">x</span></div>
      <div style="color:#35384E;font-size:11px;margin-top:8px">Every $1 in ads → ${r['roas']:.2f} gross</div>
      <div class="badge" style="background:{bb};color:{bf}">{bt}</div>
    </div>""", unsafe_allow_html=True)
with hd:
    st.markdown('<div style="width:1px;min-height:140px;background:#1E2030"></div>', unsafe_allow_html=True)
with hr:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Gross Revenue", fmt_usd(r["gross_revenue"]))
    c2.metric("Net Revenue",   fmt_usd(r["net_revenue"]))
    c3.metric("Ad Spend",      fmt_usd(r["ad_spend"]))
    c4.metric("Transactions",  fmt_n(r["tx_count"]))

st.markdown("")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Stripe Fees",          fmt_usd(r["total_fees"]), delta="Auto-calculated", delta_color="inverse")
k2.metric("Ads Manager Retainer", "−$1,600.00",             delta="Fixed monthly",   delta_color="inverse")
k3.metric("Cost Per Purchase",    fmt_usd(r["cpp"]))
nm = (r["net_revenue"] / r["gross_revenue"] * 100) if r["gross_revenue"] > 0 else 0
k4.metric("Net Margin", fmt_pct(nm))

st.markdown("")
a1, a2, a3, a4 = st.columns(4)
a1.metric("Impressions",    fmt_n(r["impressions"]))
a2.metric("Reach",          fmt_n(r["reach"]))
ctr_d = "Above avg" if r["ctr"] >= 2 else ("Average" if r["ctr"] >= 1 else "Below avg")
a3.metric("CTR",            fmt_pct(r["ctr"]), delta=ctr_d)
a4.metric("Cost Per Click", fmt_usd(r["cpc"]))

st.markdown("")

# ── P&L ──────────────────────────────────────────────────────────────────────
section("Profit & Loss Summary")
st.markdown(f"""
<div class="pl-container">
  <div class="pl-row"><span class="pl-label">Gross Revenue (funnel transactions)</span>
    <span class="pl-value" style="color:#F5A623">{fmt_usd(r['gross_revenue'])}</span></div>
  <div class="pl-row"><span class="pl-label">− Stripe Processing Fees (auto-calculated)</span>
    <span class="pl-value" style="color:#FF6B6B">−{fmt_usd(r['total_fees'])}</span></div>
  <div class="pl-row"><span class="pl-label">− Facebook Ad Spend</span>
    <span class="pl-value" style="color:#FF6B6B">−{fmt_usd(r['ad_spend'])}</span></div>
  <div class="pl-row"><span class="pl-label">− Ads Manager Retainer ($1,600/mo)</span>
    <span class="pl-value" style="color:#FF6B6B">−$1,600.00</span></div>
  <div class="pl-row-bold"><span class="pl-label-bold">Net Revenue</span>
    <span class="pl-value-bold" style="color:{nc}">{fmt_usd(r['net_revenue'])}</span></div>
</div>
<div style="color:#25273A;font-size:10px;font-family:'IBM Plex Mono',monospace;margin-top:8px;text-align:right">
  Net = Gross − Stripe Fees − Ad Spend − $1,600 Retainer &nbsp;·&nbsp; ROAS = Gross ÷ Ad Spend
</div>""", unsafe_allow_html=True)

st.markdown("")

# ── Week-by-Week ─────────────────────────────────────────────────────────────
section("Week-by-Week Breakdown")
st.markdown("""<div style="color:#4E5270;font-size:11px;margin-bottom:12px">
  Mon–Sun weeks. Retainer ~$400/week. Facebook spend prorated by day count when using aggregated export.
</div>""", unsafe_allow_html=True)

wdf = weekly_breakdown(stripe_df, fb_df, date_info)
if not wdf.empty:
    st.dataframe(wdf, use_container_width=True, hide_index=True, column_config={
        "Gross Revenue": st.column_config.NumberColumn(format="$%.2f"),
        "Stripe Fees":   st.column_config.NumberColumn(format="$%.2f"),
        "Ad Spend":      st.column_config.NumberColumn(format="$%.2f"),
        "Retainer (wk)": st.column_config.NumberColumn(format="$%.2f"),
        "Net Revenue":   st.column_config.NumberColumn(format="$%.2f"),
        "ROAS":          st.column_config.NumberColumn(format="%.2fx"),
        "CTR %":         st.column_config.NumberColumn(format="%.2f%%"),
        "CPC":           st.column_config.NumberColumn(format="$%.2f"),
        "CPP":           st.column_config.NumberColumn(format="$%.2f"),
    })

st.markdown("")

# ── Revenue by Product ────────────────────────────────────────────────────────
section("Revenue Breakdown by Product")
rev_rows = []
for p in FUNNEL_PRICES:
    g = r["price_groups"].get(p)
    if g:
        rev_rows.append({"Product": PRICE_LABELS[p], "Transactions": g["count"],
                         "Gross Revenue": round(g["revenue"], 2),
                         "Stripe Fees":   round(g["fees"], 2),
                         "Net Revenue":   round(g["revenue"] - g["fees"], 2)})
if rev_rows:
    rdf = pd.DataFrame(rev_rows)
    rdf = pd.concat([rdf, pd.DataFrame([{
        "Product": "TOTAL", "Transactions": rdf["Transactions"].sum(),
        "Gross Revenue": round(rdf["Gross Revenue"].sum(), 2),
        "Stripe Fees":   round(rdf["Stripe Fees"].sum(), 2),
        "Net Revenue":   round(rdf["Net Revenue"].sum(), 2),
    }])], ignore_index=True)
    st.dataframe(rdf, use_container_width=True, hide_index=True, column_config={
        "Gross Revenue": st.column_config.NumberColumn(format="$%.2f"),
        "Stripe Fees":   st.column_config.NumberColumn(format="$%.2f"),
        "Net Revenue":   st.column_config.NumberColumn(format="$%.2f"),
    })

st.markdown("")

# ── Ad Set Breakdown ──────────────────────────────────────────────────────────
groups = group_breakdown(fb_df, group_label=group_label)
if groups:
    section(f"Performance by {group_label}")
    gdf = pd.DataFrame(groups)
    st.dataframe(gdf, use_container_width=True, hide_index=True, column_config={
        "Spend": st.column_config.NumberColumn(format="$%.2f"),
        "CPC":   st.column_config.NumberColumn(format="$%.2f"),
        "CPP":   st.column_config.NumberColumn(format="$%.2f"),
        "CTR %": st.column_config.NumberColumn(format="%.2f%%"),
    })
