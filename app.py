import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import os
import textwrap

# --- Page Configuration ---
st.set_page_config(
    page_title="Claims Denial Analysis & Financial Impact Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

import plotly.io as pio
pio.templates["custom_mag"] = go.layout.Template(
    layout=go.Layout(
        font=dict(family="skala migalla, Sakkal Majalla, Arial, sans-serif", size=18, color="#000000"),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        colorway=["#1E3A8A", "#047857", "#B91C1C", "#D97706", "#4338CA"]
    )
)
pio.templates.default = "custom_mag"

# --- Custom CSS ---
def inject_custom_css():
    st.markdown("""
        <style>
            /* Global Font & Theme */
            * {
                font-family: 'skala migalla', 'Sakkal Majalla', Arial, sans-serif !important;
            }
            html, body, [class*="css"] {
                color: #000000 !important;
                font-size: 20px !important;
            }
            
            :root {
                --bg-color: #F8FAFC;
                --text-main: #000000;
                --primary-blue: #1E3A8A; /* Deep Navy */
                --paid-green: #047857;  /* Emerald */
                --denied-red: #B91C1C;  /* Ruby Red */
                --warning-orange: #D97706;
                --table-gray: #475569;
                --card-bg: #FFFFFF;
            }
            
            .stApp {
                background-color: var(--bg-color);
            }
            
            /* Hide Streamlit Header, Menu, and Footer */
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
            
            /* KPI Cards - Premium Glassmorphism / Shadow */
            .kpi-card {
                background-color: var(--card-bg);
                border-radius: 16px;
                padding: 24px;
                box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
                text-align: center;
                margin-bottom: 24px;
                border-top: 5px solid var(--primary-blue);
                transition: all 0.3s ease-in-out;
                display: flex;
                flex-direction: column;
                justify-content: center;
                min-height: 160px;
                height: 100%;
            }
            
            .kpi-card:hover {
                transform: translateY(-8px);
                box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
            }
            
            .kpi-card.red { border-top-color: var(--denied-red); }
            .kpi-card.green { border-top-color: var(--paid-green); }
            .kpi-card.orange { border-top-color: var(--warning-orange); }
            
            .kpi-title {
                color: var(--table-gray) !important;
                font-size: 1.1rem;
                font-weight: 700;
                margin-bottom: 12px;
                letter-spacing: 0.5px;
            }
            
            .kpi-value {
                color: var(--text-main) !important;
                font-size: 1.6rem;
                font-weight: 800;
                line-height: 1.2;
            }
            
            .kpi-value.text-small {
                font-size: 1.4rem;
                word-wrap: break-word;
            }
            
            .kpi-value.blue { color: var(--primary-blue) !important; }
            .kpi-value.green { color: var(--paid-green) !important; }
            .kpi-value.red { color: var(--denied-red) !important; }
            .kpi-value.orange { color: var(--warning-orange) !important; }
            
            .kpi-subtitle {
                color: var(--table-gray);
                font-size: 1.1rem;
                margin-top: 10px;
                font-weight: 600;
            }

            /* Headers */
            h1, h2, h3 {
                color: #000000 !important;
                font-weight: 800 !important;
            }
            
            h1 { font-size: 3rem !important; }
            h2 { font-size: 2.5rem !important; border-bottom: 2px solid #E2E8F0; padding-bottom: 10px; margin-top: 30px; }
            h3 { font-size: 2rem !important; }
            
            /* Sidebar */
            .css-1d391kg {
                background-color: #FFFFFF !important;
                border-right: 1px solid #E2E8F0;
            }
            
            /* Print Optimization */
            @media print {
                @page {
                    size: landscape;
                    margin: 10mm;
                }
                
                [data-testid="stSidebar"] { display: none !important; }
                [data-testid="stHeader"] { display: none !important; }
                footer { display: none !important; }
                .stDeployButton { display: none !important; }
                
                .stApp, .main { 
                    background-color: white !important; 
                    width: 100% !important;
                    max-width: 100% !important;
                }
                .block-container { 
                    padding: 0 !important; 
                    width: 100% !important;
                    max-width: 100% !important; 
                    min-width: 100% !important;
                }
                
                .kpi-card { 
                    page-break-inside: avoid !important; 
                    box-shadow: none !important; 
                    border: 1px solid #E2E8F0 !important;
                    border-top: 5px solid !important;
                    width: 100% !important;
                }
                .kpi-card.red { border-top-color: var(--denied-red) !important; }
                .kpi-card.green { border-top-color: var(--paid-green) !important; }
                .kpi-card.orange { border-top-color: var(--warning-orange) !important; }
                .kpi-card.blue { border-top-color: var(--primary-blue) !important; }
                
                .stPlotlyChart { 
                    page-break-inside: avoid !important; 
                    margin-bottom: 2rem !important; 
                    width: 100% !important;
                    max-width: 100% !important;
                }
                .stPlotlyChart iframe, .stPlotlyChart div, svg {
                    width: 100% !important;
                    max-width: 100% !important;
                    box-sizing: border-box !important;
                }
                
                h1, h2, h3 { page-break-after: avoid !important; }
            }
        </style>
    """, unsafe_allow_html=True)

# --- Data Processing Functions ---
@st.cache_data
def load_data(file):
    try:
        if file.name.endswith('.csv'):
            try:
                df = pd.read_csv(file, encoding='utf-8')
            except UnicodeDecodeError:
                file.seek(0)
                try:
                    df = pd.read_csv(file, encoding='cp1256')
                except UnicodeDecodeError:
                    file.seek(0)
                    df = pd.read_csv(file, encoding='latin1')
        else:
            df = pd.read_excel(file, engine='calamine')
        return df, None
    except Exception as e:
        return None, str(e)

def clean_data(df):
    df.columns = df.columns.str.strip()
    
    date_cols = [
        "Reception Date", "Encounter Start Date", "Encounter End Date",
        "Activity Service Date", "Due Date"
    ]
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
            
    num_cols = [
        "Requested AMT", "Activity Price", "Unit Price", "Factor Value",
        "Gross AMT", "Patient Share", "Net AMT", "Payment AMT",
        "Collected Patient Share", "Service QTY"
    ]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    text_cols = df.select_dtypes(include=['object', 'category']).columns
    df[text_cols] = df[text_cols].fillna("Unknown")
    
    if "Net AMT" in df.columns and "Payment AMT" in df.columns:
        df["Lost Payment AMT"] = df["Net AMT"] - df["Payment AMT"]
    else:
        df["Lost Payment AMT"] = 0
        
    if "Requested AMT" in df.columns and "Payment AMT" in df.columns:
        df["Denied Amount"] = (df["Requested AMT"] - df["Payment AMT"]).clip(lower=0)
    else:
        df["Denied Amount"] = 0
        
    if "Denial Description" in df.columns and "Net AMT" in df.columns and "Payment AMT" in df.columns:
        df["Is Denied"] = ((df["Denial Description"] != "") & 
                           (df["Denial Description"].str.lower() != "unknown")) | \
                          (df["Payment AMT"] < df["Net AMT"])
    else:
        df["Is Denied"] = False

    return df

# --- UI Helpers ---
def format_currency(val):
    return f"{val:,.2f} EGP"

def format_percentage(val):
    return f"{val:,.1f}%"

def get_delta_html(current, previous, invert_colors=False, is_currency=False, is_percent=False):
    if not previous or previous == 0:
        return ""
    diff = current - previous
    pct_change = (diff / previous) * 100
    
    if diff == 0:
        return "<span style='color: var(--table-gray);'>⏸ 0</span>"
        
    if diff > 0:
        arrow = "▲"
        color = "var(--denied-red)" if invert_colors else "var(--paid-green)"
    else:
        arrow = "▼"
        color = "var(--paid-green)" if invert_colors else "var(--denied-red)"
            
    if is_currency:
        val_str = f"{abs(diff):,.2f} EGP"
    elif is_percent:
        val_str = f"{abs(diff):.1f}%"
    else:
        val_str = f"{abs(diff):,.0f}"
            
    return f"<span style='color: {color}; font-weight: 600; font-size: 1rem;'>{arrow} {val_str} vs Prev Month</span>"

def kpi_card(title, value, color_class="blue", subtitle="", card_class=""):
    # If the value is a long string, append text-small to the color_class
    if isinstance(value, str) and len(value) > 15 and not any(char.isdigit() for char in value[:3]):
        color_class += " text-small"
        
    st.markdown(f"""
        <div class="kpi-card {card_class}">
            <div class="kpi-title">{title}</div>
            <div class="kpi-value {color_class}">{value}</div>
            {f'<div class="kpi-subtitle">{subtitle}</div>' if subtitle else ''}
        </div>
    """, unsafe_allow_html=True)

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Claims')
    return output.getvalue()

# --- Main App ---
def main():
    inject_custom_css()
    
    # --- Header ---
    col1, col2 = st.columns([1, 8])
    with col1:
        if os.path.exists("logo.png"):
            st.image("logo.png", use_container_width=True)
    with col2:
        st.title("Claims Denial Analysis & Financial Impact Dashboard")
        st.markdown("**Monitor denied claims, financial impact, top rejection reasons, and provider performance.**")
    st.markdown("---")
    
    # --- Sidebar Logo ---
    if os.path.exists("logo.png"):
        st.sidebar.image("logo.png", use_container_width=True)
        
    # --- File Upload ---
    uploaded_file = st.sidebar.file_uploader("📂 Upload Excel/CSV", type=['xlsx', 'xls', 'csv'])
    uploaded_file_prev = st.sidebar.file_uploader("📂 Upload Previous Month Excel/CSV (Optional)", type=['xlsx', 'xls', 'csv'])
    
    if not uploaded_file:
        st.info("👋 Please upload a Claims file from the sidebar to start analysis.")
        return
        
    with st.spinner("Processing data..."):
        raw_df, err = load_data(uploaded_file)
        
    if err:
        st.error(f"Failed to read file: {err}")
        return
        
    df = clean_data(raw_df)
    
    if df.empty:
        st.error("Dataset is empty after cleaning.")
        return
        
    prev_df = pd.DataFrame()
    if uploaded_file_prev:
        with st.spinner("Processing previous month data..."):
            raw_prev_df, err_prev = load_data(uploaded_file_prev)
            if not err_prev:
                prev_df = clean_data(raw_prev_df)
        
    # --- Global Filters ---
    st.sidebar.markdown("### Global Filters")
    
    filtered_df = df.copy()
    filtered_prev_df = prev_df.copy() if not prev_df.empty else pd.DataFrame()
    


    # Categorical Filters
    filter_cols = [
        "Provider Name", "Specialty Names", "Encounter Type", 
        "Service Type", "Benefit Description", "Source Flag", 
        "Resubmission Flag", "Denial Description"
    ]
    
    for col in filter_cols:
        if f"sel_{col}" not in st.session_state:
            st.session_state[f"sel_{col}"] = []
            
    active_filters = {col: st.session_state[f"sel_{col}"] for col in filter_cols if col in filtered_df.columns and st.session_state.get(f"sel_{col}")}

    for col in filter_cols:
        if col in filtered_df.columns:
            temp_df = filtered_df.copy()
            for other_col, selected_vals in active_filters.items():
                if other_col != col and selected_vals:
                    temp_df = temp_df[temp_df[other_col].isin(selected_vals)]
            
            valid_opts = temp_df[col].dropna().unique().tolist()
            current_sel = st.session_state.get(f"sel_{col}", [])
            opts = sorted(list(set(valid_opts + current_sel)), key=lambda x: str(x))
            
            st.sidebar.multiselect(col, options=opts, key=f"sel_{col}")
            
    for col, selected_vals in active_filters.items():
        if selected_vals:
            filtered_df = filtered_df[filtered_df[col].isin(selected_vals)]
            if not filtered_prev_df.empty and col in filtered_prev_df.columns:
                filtered_prev_df = filtered_prev_df[filtered_prev_df[col].isin(selected_vals)]
                
    if filtered_df.empty:
        st.warning("No data matches the selected filters.")
        return

    # --- Global KPIs Calculation ---
    total_claims = filtered_df["Encounter ID"].count() if "Encounter ID" in filtered_df.columns else len(filtered_df)
    total_req_amt = filtered_df["Requested AMT"].sum() if "Requested AMT" in filtered_df.columns else 0
    total_denied_amt = filtered_df["Denied Amount"].sum() if "Denied Amount" in filtered_df.columns else 0
    total_payment_amt = filtered_df["Payment AMT"].sum() if "Payment AMT" in filtered_df.columns else 0
    
    denied_rows = filtered_df[filtered_df["Is Denied"] == True]
    denied_claims_count = denied_rows["Encounter ID"].count() if "Encounter ID" in denied_rows.columns else len(denied_rows)
    revenue_gap_rate = ((total_req_amt - total_payment_amt) / total_req_amt * 100) if total_req_amt > 0 else 0
    
    unique_patients = filtered_df["Patient ID"].nunique() if "Patient ID" in filtered_df.columns else 1
    req_avg_per_claim = (total_req_amt / unique_patients) if unique_patients > 0 else 0
    pay_avg_per_claim = (total_payment_amt / unique_patients) if unique_patients > 0 else 0
    avg_claim_gap = req_avg_per_claim - pay_avg_per_claim
    avg_claim_gap_percent = (avg_claim_gap / req_avg_per_claim * 100) if req_avg_per_claim > 0 else 0
    
    top_provider = "N/A"
    if "Provider Name" in denied_rows.columns and "Denied Amount" in denied_rows.columns:
        prov_denial = denied_rows.groupby("Provider Name")["Denied Amount"].sum()
        if not prov_denial.empty:
            top_provider = prov_denial.idxmax()

    # Prev KPIs
    if not filtered_prev_df.empty:
        total_claims_prev = filtered_prev_df["Encounter ID"].count() if "Encounter ID" in filtered_prev_df.columns else len(filtered_prev_df)
        total_req_amt_prev = filtered_prev_df["Requested AMT"].sum() if "Requested AMT" in filtered_prev_df.columns else 0
        total_denied_amt_prev = filtered_prev_df["Denied Amount"].sum() if "Denied Amount" in filtered_prev_df.columns else 0
        total_payment_amt_prev = filtered_prev_df["Payment AMT"].sum() if "Payment AMT" in filtered_prev_df.columns else 0
        revenue_gap_rate_prev = ((total_req_amt_prev - total_payment_amt_prev) / total_req_amt_prev * 100) if total_req_amt_prev > 0 else 0
        
        unique_patients_prev = filtered_prev_df["Patient ID"].nunique() if "Patient ID" in filtered_prev_df.columns else 1
        req_avg_per_claim_prev = (total_req_amt_prev / unique_patients_prev) if unique_patients_prev > 0 else 0
        pay_avg_per_claim_prev = (total_payment_amt_prev / unique_patients_prev) if unique_patients_prev > 0 else 0
        avg_claim_gap_prev = req_avg_per_claim_prev - pay_avg_per_claim_prev
        avg_claim_gap_percent_prev = (avg_claim_gap_prev / req_avg_per_claim_prev * 100) if req_avg_per_claim_prev > 0 else 0
        
        top_provider_prev = "N/A"
        denied_rows_prev = filtered_prev_df[filtered_prev_df["Is Denied"] == True]
        if "Provider Name" in denied_rows_prev.columns and "Denied Amount" in denied_rows_prev.columns:
            prov_denial_prev = denied_rows_prev.groupby("Provider Name")["Denied Amount"].sum()
            if not prov_denial_prev.empty:
                top_provider_prev = prov_denial_prev.idxmax()
        top_provider_subtitle = f"<span style='color: var(--table-gray); font-size: 1rem; font-weight: 600;'>Prev Month: {top_provider_prev}</span>"
        
        tc_delta = get_delta_html(total_claims, total_claims_prev)
        req_delta = get_delta_html(total_req_amt, total_req_amt_prev, is_currency=True)
        den_delta = get_delta_html(total_denied_amt, total_denied_amt_prev, invert_colors=True, is_currency=True)
        pay_delta = get_delta_html(total_payment_amt, total_payment_amt_prev, is_currency=True)
        rev_gap_delta = get_delta_html(revenue_gap_rate, revenue_gap_rate_prev, invert_colors=True, is_percent=True)
        req_avg_delta = get_delta_html(req_avg_per_claim, req_avg_per_claim_prev, is_currency=True)
        pay_avg_delta = get_delta_html(pay_avg_per_claim, pay_avg_per_claim_prev, is_currency=True)
        avg_claim_gap_delta = get_delta_html(avg_claim_gap, avg_claim_gap_prev, invert_colors=True, is_currency=True)
        avg_claim_gap_percent_delta = get_delta_html(avg_claim_gap_percent, avg_claim_gap_percent_prev, invert_colors=True, is_percent=True)
    else:
        tc_delta = req_delta = den_delta = pay_delta = rev_gap_delta = req_avg_delta = pay_avg_delta = avg_claim_gap_delta = avg_claim_gap_percent_delta = top_provider_subtitle = ""

    # ==========================
    # SINGLE PAGE LAYOUT
    # ==========================
    
    # 1. KPIs
    st.markdown("### General Overview")
    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi_card("Total Claims", f"{total_claims:,}", "blue", subtitle=tc_delta, card_class="")
    with c2: kpi_card("Requested Amount", format_currency(total_req_amt), "blue", subtitle=req_delta, card_class="")
    with c3: kpi_card("Payment Amount", format_currency(total_payment_amt), "green", subtitle=pay_delta, card_class="green")
    with c4: kpi_card("Denied Amount", format_currency(total_denied_amt), "red", subtitle=den_delta, card_class="red")
    
    st.markdown("### Averages & Gaps Analysis")
    c5, c6, c7, c8 = st.columns(4)
    with c5: kpi_card("Req Avg/Claim", format_currency(req_avg_per_claim), "blue", subtitle=req_avg_delta, card_class="")
    with c6: kpi_card("Payment Avg/Claim", format_currency(pay_avg_per_claim), "green", subtitle=pay_avg_delta, card_class="green")
    with c7: kpi_card("Avg/Claim Gap", format_currency(avg_claim_gap), "red", subtitle=avg_claim_gap_delta, card_class="red")
    with c8: kpi_card("Avg/Claim Gap Percent", format_percentage(avg_claim_gap_percent), "orange", subtitle=avg_claim_gap_percent_delta, card_class="orange")
    
    st.markdown("### Performance & Insights")
    c9, c10 = st.columns(2)
    with c9: kpi_card("Revenue Gap Rate", format_percentage(revenue_gap_rate), "orange", subtitle=rev_gap_delta, card_class="orange")
    with c10: kpi_card("Top Provider (Denial)", top_provider, "orange", subtitle=top_provider_subtitle, card_class="orange")
    
    st.markdown("<hr>", unsafe_allow_html=True)
    
    # 2. OVERVIEW CHARTS
    st.header("Overview")
    
    # 3. DENIAL REASONS DEEP DIVE
    st.header("Denial Reasons Deep Dive")
    
    if "Denial Description" in denied_rows.columns:
        valid_denials = denied_rows[~denied_rows["Denial Description"].isin(["Unknown", ""])]
        measure_col = "Denied Amount"
        dr_data_dd = valid_denials.groupby("Denial Description")[measure_col].sum().nlargest(10).reset_index()
        dr_data_dd["Denial Description"] = dr_data_dd["Denial Description"].astype(str).apply(lambda x: "<br>".join(textwrap.wrap(x, width=60)))
        fig_dd = px.bar(dr_data_dd, x=measure_col, y="Denial Description", orientation='h', color_discrete_sequence=["#DC2626"], text_auto='.2s')
            
        fig_dd.update_layout(margin=dict(r=150), yaxis={'categoryorder':'total ascending'}, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='black', height=700, bargap=0.3)
        fig_dd.update_xaxes(tickfont=dict(size=16, color='black'), title_font=dict(size=18, color='black'))
        fig_dd.update_yaxes(tickfont=dict(size=16, color='black'), title_font=dict(size=18, color='black'), showline=True, linewidth=2, linecolor='black', showgrid=True, gridwidth=1, gridcolor='black', tickson='boundaries', ticks='outside', ticklen=10, tickwidth=2, tickcolor='black')
        fig_dd.update_traces(textfont_size=18, textfont_color='black', textangle=0, textposition="outside", cliponaxis=False)
        st.plotly_chart(fig_dd, use_container_width=True, key="fig_dd_3")
        


    st.markdown("<hr>", unsafe_allow_html=True)

    # 4. PROVIDERS ANALYSIS
    st.header("Providers Analysis")
    if "Provider Name" in denied_rows.columns:
        tp_data_prov = denied_rows.groupby("Provider Name")["Denied Amount"].sum().nlargest(15).reset_index()
        fig_prov = px.bar(tp_data_prov, x="Provider Name", y="Denied Amount", color_discrete_sequence=["#F97316"], text_auto='.2s')
        fig_prov.update_layout(margin=dict(r=150), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='black')
        fig_prov.update_xaxes(tickfont=dict(size=16, color='black'), title_font=dict(size=18, color='black'))
        fig_prov.update_yaxes(tickfont=dict(size=16, color='black'), title_font=dict(size=18, color='black'))
        fig_prov.update_traces(textfont_size=18, textfont_color='black', textangle=0, textposition="outside", cliponaxis=False)
        st.plotly_chart(fig_prov, use_container_width=True, key="fig_prov_4")
        


    st.markdown("<hr>", unsafe_allow_html=True)

    # 5. CLINICIANS ANALYSIS
    st.header("Clinicians Analysis")
    if "Clinician Name" in denied_rows.columns:
        clin_amt = denied_rows.groupby("Clinician Name")["Denied Amount"].sum().nlargest(10).reset_index()
        fig1_clin = px.bar(clin_amt, x="Clinician Name", y="Denied Amount", title="By Denied Amount", color_discrete_sequence=["#DC2626"], text_auto='.2s')
        fig1_clin.update_layout(margin=dict(t=80), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='black')
        fig1_clin.update_xaxes(tickfont=dict(size=16, color='black'), title_font=dict(size=18, color='black'))
        fig1_clin.update_yaxes(tickfont=dict(size=16, color='black'), title_font=dict(size=18, color='black'))
        fig1_clin.update_traces(textfont_size=18, textfont_color='black', textangle=0, textposition="outside", cliponaxis=False)
        st.plotly_chart(fig1_clin, use_container_width=True, key="fig1_clin_5")
        
        clin_cnt = denied_rows.groupby("Clinician Name").size().nlargest(10).reset_index(name='Count')
        fig2_clin = px.bar(clin_cnt, x="Clinician Name", y="Count", title="By Denial Count", color_discrete_sequence=["#F97316"], text_auto=True)
        fig2_clin.update_layout(margin=dict(t=80), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='black')
        fig2_clin.update_xaxes(tickfont=dict(size=16, color='black'), title_font=dict(size=18, color='black'))
        fig2_clin.update_yaxes(tickfont=dict(size=16, color='black'), title_font=dict(size=18, color='black'))
        fig2_clin.update_traces(textfont_size=18, textfont_color='black', textangle=0, textposition="outside", cliponaxis=False)
        st.plotly_chart(fig2_clin, use_container_width=True, key="fig2_clin_6")
            


    st.markdown("<hr>", unsafe_allow_html=True)

    # 6. SERVICES ANALYSIS
    st.header("Services Analysis")
    if "Service Type" in denied_rows.columns:
        st_data = denied_rows.groupby("Service Type")["Denied Amount"].sum().reset_index()
        fig_st = px.pie(st_data, values="Denied Amount", names="Service Type", hole=0.4, title="Denial by Service Type", color_discrete_sequence=px.colors.qualitative.Set2)
        fig_st.update_traces(textposition='outside', textinfo='percent+label', textfont_color='black', textfont_size=18)
        fig_st.update_layout(height=800, margin=dict(t=200, b=200, l=150, r=150), font_color='black', plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_st, use_container_width=True, key="fig_st_7")
        
    if "Benefit Description" in denied_rows.columns:
        bd_data = denied_rows.groupby("Benefit Description")["Denied Amount"].sum().nlargest(10).reset_index()
        fig_bd = px.bar(bd_data, x="Denied Amount", y="Benefit Description", orientation='h', title="Top Benefits by Denial", color_discrete_sequence=["#2563EB"], text_auto='.2s')
        fig_bd.update_layout(margin=dict(r=150), yaxis={'categoryorder':'total ascending'}, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='black')
        fig_bd.update_xaxes(tickfont=dict(size=16, color='black'), title_font=dict(size=18, color='black'))
        fig_bd.update_yaxes(tickfont=dict(size=16, color='black'), title_font=dict(size=18, color='black'))
        fig_bd.update_traces(textfont_size=18, textfont_color='black', textangle=0, textposition="outside", cliponaxis=False)
        st.plotly_chart(fig_bd, use_container_width=True, key="fig_bd_8")
        
    if "Service Type" in filtered_df.columns and "Requested AMT" in filtered_df.columns and "Payment AMT" in filtered_df.columns:
        claims_vs_col = filtered_df.groupby("Service Type")[["Requested AMT", "Payment AMT"]].sum().reset_index()
        claims_vs_col_melted = claims_vs_col.melt(id_vars="Service Type", value_vars=["Requested AMT", "Payment AMT"], var_name="Type", value_name="Amount")
        
        fig_cc = px.bar(claims_vs_col_melted, x="Amount", y="Service Type", color="Type", orientation='h', barmode='group', title="Requested AMT vs Payment AMT (By Service)", color_discrete_map={"Requested AMT": "#2563EB", "Payment AMT": "#047857"}, text_auto='.2s')
        fig_cc.update_layout(margin=dict(r=150), yaxis={'categoryorder':'total ascending'}, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='black')
        fig_cc.update_xaxes(tickfont=dict(size=16, color='black'), title_font=dict(size=18, color='black'))
        fig_cc.update_yaxes(tickfont=dict(size=16, color='black'), title_font=dict(size=18, color='black'))
        fig_cc.update_traces(textfont_size=18, textfont_color='black', textangle=0, textposition="outside", cliponaxis=False)
        st.plotly_chart(fig_cc, use_container_width=True, key="fig_cc_new")



    st.markdown("<hr>", unsafe_allow_html=True)

    # 7. SPECIALTIES ANALYSIS
    st.header("Specialties Analysis")
    if "Specialty Names" in denied_rows.columns:
        spec_data = denied_rows.groupby("Specialty Names")["Denied Amount"].sum().nlargest(15).reset_index()
        fig_spec = px.bar(spec_data, x="Denied Amount", y="Specialty Names", orientation='h', color_discrete_sequence=["#DC2626"], text_auto='.2s')
        fig_spec.update_layout(margin=dict(r=150), yaxis={'categoryorder':'total ascending'}, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='black')
        fig_spec.update_xaxes(tickfont=dict(size=16, color='black'), title_font=dict(size=18, color='black'))
        fig_spec.update_yaxes(tickfont=dict(size=16, color='black'), title_font=dict(size=18, color='black'))
        fig_spec.update_traces(textfont_size=18, textfont_color='black', textangle=0, textposition="outside", cliponaxis=False)
        st.plotly_chart(fig_spec, use_container_width=True, key="fig_spec_9")

    st.markdown("<hr>", unsafe_allow_html=True)

    # 8. ICD ANALYSIS
    st.header("ICD Codes Analysis")
    if "Principle ICD Code" in denied_rows.columns:
        icd_data = denied_rows.groupby("Principle ICD Code")["Denied Amount"].sum().nlargest(15).reset_index()
        fig_icd = px.bar(icd_data, x="Principle ICD Code", y="Denied Amount", color_discrete_sequence=["#DC2626"], text_auto='.2s')
        fig_icd.update_layout(margin=dict(t=80), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='black')
        fig_icd.update_xaxes(tickfont=dict(size=16, color='black'), title_font=dict(size=18, color='black'))
        fig_icd.update_yaxes(tickfont=dict(size=16, color='black'), title_font=dict(size=18, color='black'))
        fig_icd.update_traces(textfont_size=18, textfont_color='black', textangle=0, textposition="outside", cliponaxis=False)
        st.plotly_chart(fig_icd, use_container_width=True, key="fig_icd_10")
        


    st.markdown("<hr>", unsafe_allow_html=True)

    # 9. TRENDS
    st.header("Trend Analysis")
    if "Activity Service Date" in filtered_df.columns:
        trend_col = "Activity Service Date"
        if not filtered_prev_df.empty:
            trend_df = pd.concat([filtered_prev_df, filtered_df], ignore_index=True)
        else:
            trend_df = filtered_df.copy()
        
        if trend_df[trend_col].isna().all():
            st.warning("⚠️ عمود التاريخ المختار لا يحتوي على تواريخ صالحة في هذا الشيت لرسم المؤشر.")
        else:
            trend_df["Month"] = trend_df[trend_col].dt.to_period("M").dt.to_timestamp()
            
            agg_col = "Encounter ID" if "Encounter ID" in trend_df.columns else trend_df.columns[0]
            
            trend_agg_cols = {
                "Total_Claims": (agg_col, "count"),
                "Denied_Claims": ("Is Denied", "sum"),
                "Denied_Amount": ("Denied Amount", "sum")
            }
            if "Requested AMT" in trend_df.columns:
                trend_agg_cols["Requested_Amount"] = ("Requested AMT", "sum")
            if "Payment AMT" in trend_df.columns:
                trend_agg_cols["Payment_Amount"] = ("Payment AMT", "sum")
                
            trend_agg = trend_df.groupby("Month").agg(**trend_agg_cols).reset_index().dropna()
            
            if trend_agg.empty:
                st.warning("⚠️ لا توجد بيانات صحيحة كافية لرسم المؤشر الزمني.")
            else:
                if "Requested_Amount" in trend_agg.columns and "Payment_Amount" in trend_agg.columns:
                    trend_agg["Revenue Gap Rate %"] = ((trend_agg["Requested_Amount"] - trend_agg["Payment_Amount"]) / trend_agg["Requested_Amount"] * 100).fillna(0)
                else:
                    trend_agg["Revenue Gap Rate %"] = 0
                
                # Format month for better display
                trend_agg["Month_Name"] = trend_agg["Month"].dt.strftime('%B %Y')
                
                fig_t1 = px.bar(trend_agg, x="Month_Name", y="Denied_Amount", text="Denied_Amount", title="Denied Amount by Month", color_discrete_sequence=["#DC2626"])
                fig_t1.update_layout(margin=dict(t=80), font_color='black', plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                fig_t1.update_xaxes(tickfont=dict(size=16, color='black'), title_font=dict(size=18, color='black'))
                fig_t1.update_yaxes(tickfont=dict(size=16, color='black'), title_font=dict(size=18, color='black'))
                fig_t1.update_traces(textposition="outside", texttemplate='%{text:.2s}', textfont_color='black', textfont_size=18, cliponaxis=False)
                st.plotly_chart(fig_t1, use_container_width=True, key="fig_t1_11")
                
                fig_t2 = px.bar(trend_agg, x="Month_Name", y="Revenue Gap Rate %", text="Revenue Gap Rate %", title="Revenue Gap Rate % by Month", color_discrete_sequence=["#F97316"])
                fig_t2.update_layout(margin=dict(t=80), font_color='black', plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                fig_t2.update_xaxes(tickfont=dict(size=16, color='black'), title_font=dict(size=18, color='black'))
                fig_t2.update_yaxes(tickfont=dict(size=16, color='black'), title_font=dict(size=18, color='black'))
                fig_t2.update_traces(textposition="outside", texttemplate='%{text:.1f}%', textfont_color='black', textfont_size=18, cliponaxis=False)
                st.plotly_chart(fig_t2, use_container_width=True, key="fig_t2_12")

    st.markdown("<hr>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
