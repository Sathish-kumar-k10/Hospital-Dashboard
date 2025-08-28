# -*- coding: utf-8 -*-
"""
NHS Hospital Dashboard — unified hover + clean tooltips across all tabs
(With new visuals: Tab1 Waterfall, Tab2 Funnel, Tab3 Bubble scatter)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import base64

# ---------------------- Config ----------------------
# ---------------------- Config ----------------------
st.set_page_config(page_title="NHS Hospital Patient Dashboard", layout="wide")
INPUT_CSV = "https://www.dropbox.com/scl/fi/1tb4zi3hufk11njxew6h7/final_patient_data_with_medication_92.csv?rlkey=smc1ax6sllot8zsvwqmfcxxwz&st=26mqb8sg&dl=0"
MONITORING_CSV = "https://www.dropbox.com/scl/fi/ed61m8ykbbg1bux5bsfjc/patient_24hr_monitoring_data_30min.csv?rlkey=x597uj3bln0tljh4heme9r6h8&st=xc6iwljr&raw=1"

LOGO_PATH = "dissert-deploy/assets/background-1.png"

# ---------------------- CSS ----------------------
st.markdown("""
<style>
    .main-content { background-color: rgba(255,255,255,0.2); padding: 20px; border-radius: 10px; }
    [data-testid="stSidebar"] { background-color: #005EB8 !important; }
    .st-b7, .st-c0, .stDateInput label, .stMultiSelect label { color: black !important; }
    .stDateInput, .stMultiSelect { background-color: white; border-radius: 4px; padding: 8px; }
    .stTabs [data-baseweb="tab-list"] { display: flex; justify-content: space-between; width: auto; }
    .stTabs [data-baseweb="tab"] {
        flex: 1 1 auto; text-align: center; height: 50px; padding: 0; background-color: #f0f2f6;
        border: none; font-weight: 600; color: #333; transition: all 0.3s ease;
    }
    .stTabs [data-baseweb="tab"]:hover { background-color: #e0e5ec; }
    .stTabs [aria-selected="true"] { background-color: #005EB8; color: white !important; border-bottom: 3px solid white; }

    .kpi-card {
        border: 2px solid #005EB8;
        border-radius: 8px;
        padding: 15px;
        background-color: #005EB8;
        text-align: center;
        margin-bottom: 15px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        color: white;

        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;

        height: 140px;
        overflow: hidden;
    }

    .kpi-card h3 { font-size: 1rem; margin: 0 0 6px 0; font-weight: 600; color: white !important; }
    .kpi-card h2 { font-size: 1.8rem; margin: 0; font-weight: 700; color: white !important; }
    .kpi-card small { font-size: 0.8rem; margin-top: 6px; line-height: 1.1; color: white; }

    .kpi-fixed { flex: 1; }
    .visual-container { border: 1px solid #e0e0e0; border-radius: 8px; padding: 15px; background-color: rgba(255,255,255,0.95); margin-bottom: 20px; }
    .center-container { display: flex; justify-content: center; width: 100%; }
    .center-content { width: 90%; max-width: 1200px; }
    .logo-container { position: absolute; top: 10px; right: 20px; }
    .logo-container img { height: 40px; }
</style>
""", unsafe_allow_html=True)

# ---------------------- Logo ----------------------
logo_base64 = base64.b64encode(open(LOGO_PATH, "rb").read()).decode()
st.markdown(f"""<div class="logo-container"><img src="data:image/png;base64,{logo_base64}"></div>""", unsafe_allow_html=True)
st.markdown('<div class="main-content">', unsafe_allow_html=True)

# ---------------------- Data ----------------------
@st.cache_data
def load_patient_data(path: str):
    df = pd.read_csv(path)
    df['Admission_DateTime'] = pd.to_datetime(df['Admission_DateTime'], dayfirst=True, errors='coerce')
    df['Discharge_DateTime'] = pd.to_datetime(df['Discharge_DateTime'], dayfirst=True, errors='coerce')
    df['Year'] = df['Admission_DateTime'].dt.year
    df['Month'] = df['Admission_DateTime'].dt.to_period('M').astype(str)
    # safety: numeric cost
    if 'Cost' in df.columns:
        df['Cost'] = pd.to_numeric(df['Cost'], errors='coerce').fillna(0.0)
    return df

@st.cache_data
def load_monitoring_data(path: str):
    df = pd.read_csv(path)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], dayfirst=True, errors='coerce')
    return df

patient_data = load_patient_data(INPUT_CSV)
monitoring_data = load_monitoring_data(MONITORING_CSV)

# ---------------------- Plot helpers ----------------------
def style_fig(fig):
    fig.update_layout(
        title_text="", title=None,
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#005EB8", font_color="white", font_size=12),
        xaxis=dict(showspikes=True, spikemode="across", spikesnap="cursor", spikedash="solid"),
        yaxis=dict(showspikes=True, spikemode="across", spikesnap="cursor", spikedash="solid"),
        plot_bgcolor='rgba(255,255,255,0.85)', paper_bgcolor='rgba(255,255,255,0.85)',
        font=dict(color='black'),
        legend=dict(title_text="", font=dict(color='black'))
    )
    fig.update_traces(hoverlabel=dict(bgcolor="#005EB8", font_color="white", font_size=12))
    if hasattr(fig, "layout") and getattr(fig.layout, "annotations", None):
        fig.layout.annotations = [a for a in fig.layout.annotations if (getattr(a, "text", "") or "") != "undefined"]
    return fig

def tidy(fig, height=380):
    fig.update_layout(height=height, margin=dict(l=20, r=20, t=30, b=20))
    return style_fig(fig)

def kpi_card(title, value, status="ok", message=""):
    color = {
        "ok": "#005EB8", "success": "#2E8B57", "warning": "#e6b800", "danger": "#d90429"
    }.get(status, "#005EB8")
    return f'''
    <div class="kpi-card kpi-fixed" style="background-color:{color};">
        <h3>{title}</h3>
        <h2>{value}</h2>
        {f'<small>{message}</small>' if message else ''}
    </div>
    '''

# ---------------------- Sidebar Filters ----------------------
valid_dates = patient_data['Admission_DateTime'].dropna()
if valid_dates.empty:
    st.error("No valid Admission_DateTime values in the dataset.")
    st.stop()

min_date = valid_dates.dt.date.min()
max_date = valid_dates.dt.date.max()

with st.sidebar:
    st.title("Report filters")
    from_date = st.date_input("From Date", min_date, min_value=min_date, max_value=max_date)
    to_date = st.date_input("To Date", max_date, min_value=min_date, max_value=max_date)
    if from_date > to_date:
        st.error("Error: From Date must be before To Date.")

    condition_options = sorted(patient_data['Condition'].dropna().unique()) if 'Condition' in patient_data.columns else []
    procedure_options = sorted(patient_data['Procedure'].dropna().unique()) if 'Procedure' in patient_data.columns else []

    condition_filter = st.multiselect("Filter by Condition", options=condition_options)
    procedure_filter = st.multiselect("Filter by Procedure", options=procedure_options)

filtered_patients = patient_data[
    (patient_data['Admission_DateTime'].dt.date >= from_date) &
    (patient_data['Admission_DateTime'].dt.date <= to_date)
]
if condition_filter:
    filtered_patients = filtered_patients[filtered_patients['Condition'].isin(condition_filter)]
if procedure_filter:
    filtered_patients = filtered_patients[filtered_patients['Procedure'].isin(procedure_filter)]

# ---------------------- Tabs ----------------------
tab1, tab2, tab3 = st.tabs(
    ["**Budget & System Pressures**", "**Patient Outcomes & KPIs**", "**Staff & Resource Management**"]
)


# =================================================================
# TAB 1: SYSTEM PRESSURES — real budgets; robust year total logic + WATERFALL
# =================================================================
with tab1:
    #st.header("System Pressures: Budget, Staffing, Waiting, Demand, Aging")
    dfp = filtered_patients.copy()

    years_available = sorted(dfp["Year"].dropna().unique())
    if not years_available:
        st.info("No valid years in current filter.")
        st.stop()

    sel_year = st.selectbox("Select Year for KPIs & charts", years_available, index=len(years_available) - 1)

    dfp_year = dfp[dfp["Year"] == sel_year].copy()
    if "Admission_DateTime" in dfp_year:
        dfp_year["Month"] = dfp_year["Admission_DateTime"].dt.to_period("M").astype(str)
    dfp_year["Cost"] = pd.to_numeric(dfp_year.get("Cost", 0), errors="coerce").fillna(0.0)

    # ---- budget helpers (no row-sum inflation) ----
    def sum_unique_per_condition_budget(dfy):
        if "Condition" not in dfy.columns or "Proposed_Budget_Condition" not in dfy.columns:
            return 0.0
        b = (dfy.dropna(subset=["Condition"])
                .sort_values(["Condition"])
                .drop_duplicates(subset=["Condition"])[["Condition", "Proposed_Budget_Condition"]])
        return float(pd.to_numeric(b["Proposed_Budget_Condition"], errors="coerce").fillna(0.0).sum())

    def sum_unique_per_procedure_budget(dfy):
        col = "Proposed_Budget_Procedure" if "Proposed_Budget_Procedure" in dfy.columns else ("Proposed_Budget" if "Proposed_Budget" in dfy.columns else None)
        if col is None or "Procedure" not in dfy.columns:
            return 0.0
        b = (dfy.dropna(subset=["Procedure"])
                .sort_values(["Procedure"])
                .drop_duplicates(subset=["Procedure"])[["Procedure", col]])
        return float(pd.to_numeric(b[col], errors="coerce").fillna(0.0).sum())

    def get_budget_year_total(dfy):
        s1 = sum_unique_per_condition_budget(dfy)
        if s1 > 0: return s1
        s2 = sum_unique_per_procedure_budget(dfy)
        if s2 > 0: return s2
        for col in ["Proposed_Budget_Year", "Proposed_Budget"]:
            if col in dfy.columns:
                vals = pd.to_numeric(dfy[col], errors="coerce").dropna().unique()
                if len(vals) > 0: return float(vals[0])
        return 0.0

    def get_budget_for_selected_procs(dfy_selected):
        return sum_unique_per_procedure_budget(dfy_selected)

    # ---- selection ----
    if procedure_filter:
        df_sel = dfp_year[dfp_year["Procedure"].isin(procedure_filter)].copy()
        st.info(f"Filtered by procedure(s): {', '.join(procedure_filter)}")
    else:
        df_sel = dfp_year.copy()

    # ---- KPIs ----
    total_cost_sel = float(df_sel["Cost"].sum())
    patients_sel = int(df_sel.shape[0])
    avg_cost_per_patient = (total_cost_sel / patients_sel) if patients_sel else 0.0

    if procedure_filter:
        budget_sel = get_budget_for_selected_procs(df_sel)
    else:
        budget_sel = get_budget_year_total(dfp_year)

    funding_gap_sel = ((budget_sel - total_cost_sel) / budget_sel * 100) if budget_sel else 0.0
a
    # Context
    staff_idx_avg = float(dfp_year["Staff_Shortage_Index"].dropna().mean() or 0)
    waiting_med_val = dfp_year["Waiting_List_Days"].dropna().median()
    waiting_med = int(waiting_med_val) if pd.notna(waiting_med_val) else 0
    avg_age_share = float(dfp_year["Aging_Population_Share"].dropna().mean() or 0)

    # KPI cards
    a1, a2 = st.columns(2)
    a1.markdown(kpi_card(f"Total Cost (Year {sel_year})", f"£{total_cost_sel:,.0f}"), unsafe_allow_html=True)
    # Funding Gap logic
    if funding_gap_sel < (-10):
        fg_status, fg_msg = "danger", "🔺 Funding gap too high. Increase budget or reduce costs."
    elif funding_gap_sel < (-5):
        fg_status, fg_msg = "warning", "⚠️ Funding gap above 5%. Monitor closely."
    else:
        fg_status, fg_msg = "ok", ""

    # Budget should follow funding gap status
    a2.markdown(
        kpi_card(f"Budget (Year {sel_year})", f"£{budget_sel:,.0f}", fg_status),
        unsafe_allow_html=True
    )


    # ---- Funding Gap KPI ----
    b1, b2 = st.columns(2)

    if funding_gap_sel < (-10):
        fg_status, fg_msg = "danger", "🔺 Funding gap too high. Increase budget or reduce costs."
    elif funding_gap_sel < (-5):
        fg_status, fg_msg = "warning", "⚠️ Funding gap above 5%. Monitor closely."
    else:
        fg_status, fg_msg = "ok", ""

    b1.markdown(
        kpi_card("Funding Gap (%)", f"{funding_gap_sel:.1f}%", fg_status, fg_msg),
        unsafe_allow_html=True
    )

    b2.markdown(
        kpi_card("Avg Cost per Patient", f"£{avg_cost_per_patient:,.2f}"),
        unsafe_allow_html=True
    )

    #b2.markdown(kpi_card("Avg Cost per Patient", f"£{avg_cost_per_patient:,.2f}"), unsafe_allow_html=True)

    # ---- NEW: Waterfall explaining the gap ----
    st.subheader("Budget vs Actual")
    if budget_sel > 0:
        gap = total_cost_sel - budget_sel  # positive = overspend
        measures = ["absolute", "relative", "total"]
        x = ["Budget", "Gap", "Actual Spend"]
        y = [budget_sel, gap, total_cost_sel]

        fig_wf = go.Figure(go.Waterfall(
            name="Budget Waterfall",
            orientation="v",
            measure=measures,
            x=x,
            y=y,
            text=[f"£{budget_sel:,.0f}", f"{'+' if gap>=0 else ''}£{gap:,.0f}", f"£{total_cost_sel:,.0f}"],
            textposition="outside",
            connector={"line": {"width": 1}}
        ))
        fig_wf.update_yaxes(title_text="Amount (£)", tickprefix="£")
        st.plotly_chart(tidy(fig_wf, height=360), use_container_width=True)
    else:
        st.info("No budget available to build the waterfall.")

    # ---- Create two columns for the last two visuals ----
    col1, col2 = st.columns(2)
    
    # ---- Amount Spent on Procedures (current year) ----
    with col1:
        st.subheader("Amount Spent on Procedures")
        _df_for_proc = dfp_year.copy()
        if procedure_filter:
            _df_for_proc = _df_for_proc[_df_for_proc["Procedure"].isin(procedure_filter)]

        proc_costs = (_df_for_proc.groupby("Procedure", as_index=False)["Cost"]
                      .sum().sort_values("Cost", ascending=False))
        if not proc_costs.empty and float(proc_costs["Cost"].sum()) > 0:
            fig_proc = px.bar(proc_costs.head(7), x="Procedure", y="Cost", text="Cost",
                              labels={"Procedure": "Procedure", "Cost": "Amount (£)"})
            fig_proc.update_traces(texttemplate='£%{text:,.0f}', textposition='outside',
                                   hovertemplate="Procedure: %{x}<br>Amount: £%{y:,.0f}<extra></extra>")
            fig_proc.update_yaxes(title_text="Amount (£)", tickprefix="£")
            st.plotly_chart(tidy(fig_proc, height=360), use_container_width=True)
        else:
            st.info("No procedure cost data available for the selection.")

    # ---- Monthly Spend Trend ----
    with col2:
        st.subheader("Amount Spent Over Months")
        _df_for_month = dfp_year.copy()
        if procedure_filter:
            _df_for_month = _df_for_month[_df_for_month["Procedure"].isin(procedure_filter)]

        monthly = (_df_for_month
                   .assign(Month=lambda d: d["Admission_DateTime"].dt.to_period("M").astype(str))
                   .groupby("Month", as_index=False)["Cost"].sum()
                   .sort_values("Month"))
        if not monthly.empty and float(monthly["Cost"].sum()) > 0:
            fig_cost_trend = px.line(monthly, x="Month", y="Cost", markers=True,
                                     labels={"Month": "Month", "Cost": "Amount (£)"})
            fig_cost_trend.update_traces(hovertemplate="Month: %{x}<br>Amount: £%{y:,.0f}<extra></extra>")
            fig_cost_trend.update_yaxes(title_text="Amount (£)", tickprefix="£")
            st.plotly_chart(tidy(fig_cost_trend, height=360), use_container_width=True)
        else:
            st.info("No cost data available for the selected filters.")

# =================================================================
# TAB 2: Hospital Revenue & KPI Overview — with extra bubble visual
# =================================================================
with tab2:
    #st.header("Hospital Revenue & KPI Overview")

    # ROW 1: Filters
    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        cost_from = st.date_input("Cost Trend From", min_date, min_value=min_date, max_value=max_date)
    with col_filter2:
        cost_to = st.date_input("Cost Trend To", max_date, min_value=min_date, max_value=max_date)

    if cost_from > cost_to:
        st.error("Error: Cost Trend From date must be before To date.")
        st.stop()

    filtered_cost_df = filtered_patients[
        (filtered_patients['Admission_DateTime'].dt.date >= cost_from) &
        (filtered_patients['Admission_DateTime'].dt.date <= cost_to)
    ].copy()

    # Make sure key columns are typed safely
    if 'Cost' in filtered_cost_df:
        filtered_cost_df['Cost'] = pd.to_numeric(filtered_cost_df['Cost'], errors='coerce').fillna(0.0)

    # KPI Calculations
    total_patients = filtered_cost_df['Patient_ID'].nunique() if 'Patient_ID' in filtered_cost_df else 0
    total_cost = filtered_cost_df['Cost'].sum() if 'Cost' in filtered_cost_df else 0.0

    deaths = (
        filtered_cost_df[filtered_cost_df['Survive'] == 0].shape[0]
        if 'Survive' in filtered_cost_df.columns else 0
    )
    recovered = (
        filtered_cost_df[filtered_cost_df['Survive'] == 1].shape[0]
        if 'Survive' in filtered_cost_df.columns else 0
    )

    if 'Readmission' in filtered_cost_df.columns:
        readmissions = (filtered_cost_df['Readmission']
                        .astype(str).str.strip().str.lower().eq('yes')).sum()
    else:
        readmissions = 0
    
    aging_share = (
        float(filtered_cost_df['Aging_Population_Share'].mean())
        if 'Aging_Population_Share' in filtered_cost_df.columns else 0.0
    )
    waiting_med = (
        float(filtered_cost_df['Waiting_List_Days'].median())
        if 'Waiting_List_Days' in filtered_cost_df.columns else 0.0
    )

    # ROW 2: KPIs
    col1, col2, col3 = st.columns(3)
    col1.markdown(kpi_card("Total Patients Admitted", f"{total_patients}"), unsafe_allow_html=True)
    # ✅ Recovered Count (green if ≥90% of patients)
    if total_patients > 0 and (recovered / total_patients) >= 0.9:
        rec_status, rec_msg = "success", "✅ Excellent recovery rate!"
    else:
        rec_status, rec_msg = "ok", ""
    col2.markdown(kpi_card("Recovered Count", f"{recovered}", rec_status, rec_msg), unsafe_allow_html=True)
    col3.markdown(kpi_card("Deaths Count", f"{deaths}"), unsafe_allow_html=True)

    col4, col5, col6 = st.columns(3)
    # ✅ Readmissions (RED if >25% of total patients)
    if total_patients > 0 and (readmissions / total_patients) > 0.25:
        readmit_status, readmit_msg = "danger", f"🚨 High readmission rate ({(readmissions/total_patients)*100:.1f}%)"
    else:
        readmit_status, readmit_msg = "ok", ""
    col4.markdown(kpi_card("Readmissions", f"{readmissions}", readmit_status, readmit_msg), unsafe_allow_html=True)

    age_status = "warning" if (aging_share or 0) > 25 else "ok"
    age_msg = "👴 High aging population." if age_status == "warning" else ""
    col5.markdown(kpi_card("Aging Pop. Share", f"{(aging_share or 0):.1f}%", age_status, age_msg), unsafe_allow_html=True)

    wait_status = "danger" if (waiting_med or 0) > 30 else "ok"
    wait_msg = "⏳ Long waiting time." if wait_status == "danger" else ""
    col6.markdown(kpi_card("Median Waiting (days)", f"{int(waiting_med or 0)}", wait_status, wait_msg), unsafe_allow_html=True)

    # ROW 3: Visuals — Patients & Deaths | Care Path Funnel
    d1, d2 = st.columns(2)
    with d1:
        st.subheader("Patients Admitted and Deaths by Condition")
        if 'Condition' in filtered_cost_df.columns:
            condition_stats = filtered_cost_df.groupby('Condition').agg(
                Patients=('Patient_ID', 'count'),
                Deaths=('Survive', lambda x: (x == 0).sum() if x.notna().any() else 0)
            ).reset_index()

            if not condition_stats.empty:
                fig = px.bar(condition_stats, x='Condition', y=['Patients', 'Deaths'], barmode='group', title="")
                fig.update_layout(yaxis_title="Count", xaxis_title="Condition")
                st.plotly_chart(tidy(fig, height=400), use_container_width=True)
            else:
                st.info("No condition data available for the selection.")
        else:
            st.info("No 'Condition' column in data.")

    with d2:
        st.subheader("Care Path Funnel")
        admitted = int(total_patients)
        treated = int(filtered_cost_df[filtered_cost_df['Procedure'].notna()].shape[0]) if 'Procedure' in filtered_cost_df.columns else admitted
        recovered_cnt = int(recovered)
        readmit_cnt = int(readmissions)

        funnel_df = pd.DataFrame({
            "stage": ["Admitted", "Treated", "Recovered", "Readmitted"],
            "count": [admitted, treated, recovered_cnt, readmit_cnt]
        })
        fig_funnel = px.funnel(funnel_df, x="count", y="stage")
        fig_funnel.update_layout(xaxis_title="Patients", yaxis_title="")
        st.plotly_chart(tidy(fig_funnel, height=380), use_container_width=True)

    # ROW 4: NEW Visual — Readmission Rate by Condition (Bubble scatter)
    st.markdown("---")
    st.subheader("Readmission Risk by Condition — Bubble")

    if 'Condition' in filtered_cost_df.columns and 'Patient_ID' in filtered_cost_df.columns and 'Readmission' in filtered_cost_df.columns:
        # Normalize readmission values
        readmit_series = filtered_cost_df['Readmission'].astype(str).str.strip().str.lower()
        tmp = filtered_cost_df.assign(ReadmitBin=readmit_series.eq('yes'))

        cond_stats = (
            tmp.groupby('Condition')
               .agg(
                    Patients=('Patient_ID', 'nunique'),
                    Readmissions=('ReadmitBin', 'sum')
               )
               .reset_index()
        )

        # Avoid division by zero
        cond_stats['ReadmissionRate'] = cond_stats.apply(
            lambda r: (r['Readmissions'] / r['Patients'] * 100) if r['Patients'] else 0.0, axis=1
        )

        # Optional: remove ultra-low-volume noise (toggle/comment if not needed)
        # cond_stats = cond_stats[cond_stats['Patients'] >= 3]

        if not cond_stats.empty:
            fig_readmit = px.scatter(
                cond_stats,
                x="Patients",
                y="ReadmissionRate",
                size="Readmissions",
                color="Condition",
                hover_name="Condition",
                size_max=40,
                labels={
                    "Patients": "Total Patients",
                    "ReadmissionRate": "Readmission Rate (%)",
                    "Readmissions": "Readmissions"
                },
                title=""
            )
            fig_readmit.update_traces(
                hovertemplate=(
                    "Condition: %{hovertext}<br>"
                    "Patients: %{x}<br>"
                    "Readmissions: %{marker.size}<br>"
                    "Rate: %{y:.1f}%<extra></extra>"
                )
            )
            fig_readmit.update_yaxes(title_text="Readmission Rate (%)")
            fig_readmit.update_xaxes(title_text="Total Patients")
            st.plotly_chart(tidy(fig_readmit, height=450), use_container_width=True)
        else:
            st.info("No readmission data available for the current selection.")
    else:
        st.info("Readmission/Condition columns not available to build this chart.")


# =================================================================
# TAB 3: Staff and Doctor Resource Overview — BUBBLE scatter
# =================================================================
with tab3:
    #st.header("🧑‍⚕️ Staff & Resource Overview")

    df_staff = filtered_patients.copy()

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        year_options = sorted(df_staff['Year'].dropna().unique())
        selected_year = st.selectbox("Select Year", options=year_options, index=len(year_options)-1)
    with col_f2:
        month_options = sorted(df_staff[df_staff['Year'] == selected_year]['Month'].dropna().unique())
        selected_month = st.selectbox("Select Month", options=month_options)

    df_filtered = df_staff[(df_staff['Year'] == selected_year) & (df_staff['Month'] == selected_month)].copy()
    df_filtered["Cost"] = pd.to_numeric(df_filtered.get("Cost", 0), errors="coerce").fillna(0.0)

    # KPI CARDS — Total Staff & Avg Patients per Staff
    col1, col2 = st.columns(2)
    doctor_ids = df_filtered['Doctor_ID'].dropna().unique() if 'Doctor_ID' in df_filtered else []
    nurse_ids = df_filtered['Nurse_ID'].dropna().unique() if 'Nurse_ID' in df_filtered else []
    total_staff = len(set(doctor_ids).union(set(nurse_ids)))
    total_patients = df_filtered['Patient_ID'].nunique() if 'Patient_ID' in df_filtered else 0
    avg_patients_per_staff = round(total_patients / total_staff, 1) if total_staff else 0

    col1.markdown(kpi_card("Total Staff Count", f"{total_staff}"), unsafe_allow_html=True)
    col2.markdown(kpi_card("Avg Patients per Staff", f"{avg_patients_per_staff}"), unsafe_allow_html=True)

    # Understaffed Departments & Efficiency (same)
    col3, col4 = st.columns(2)
    if 'Condition' in df_filtered:
        condition_group = df_filtered.groupby('Condition').agg(
            Patients=('Patient_ID', 'count'),
            Avg_Shortage_Index=('Staff_Shortage_Index', 'mean')
        ).reset_index()
        staff_per_condition = df_filtered.groupby('Condition').agg(
            Doctors=('Doctor_ID', lambda x: x.nunique()),
            Nurses=('Nurse_ID', lambda x: x.nunique())
        ).reset_index()
        condition_group = condition_group.merge(staff_per_condition, on='Condition', how='left')
        condition_group["Current_Staff"] = condition_group["Doctors"].fillna(0) + condition_group["Nurses"].fillna(0)

        base_staff_ratio = 5
        condition_group["Base_Required_Staff"] = condition_group["Patients"] / base_staff_ratio
        condition_group["Required_Staff"] = condition_group["Base_Required_Staff"] / (1 - (condition_group["Avg_Shortage_Index"].fillna(0) / 100))
        condition_group["Staff_Needed"] = (condition_group["Required_Staff"] - condition_group["Current_Staff"]).apply(lambda x: max(0, round(x)))
        condition_group["Understaffed"] = condition_group["Staff_Needed"] > 0

        under_depts = int(condition_group["Understaffed"].sum())
        total_current_staff = float(condition_group["Current_Staff"].sum())
        total_required_staff = float(condition_group["Required_Staff"].sum())
        efficiency = (total_current_staff / total_required_staff * 100) if total_required_staff > 0 else 100
    else:
        under_depts = 0
        efficiency = 100

    efficiency_status = "success" if efficiency >= 90 else ("ok" if efficiency >= 70 else ("warning" if efficiency >= 50 else "danger"))
    col3.markdown(kpi_card("Understaffed Departments", f"{under_depts}"), unsafe_allow_html=True)
    col4.markdown(kpi_card("Staffing Efficiency (%)", f"{efficiency:.1f}%", efficiency_status), unsafe_allow_html=True)

    # VISUALS
    ch1, ch2 = st.columns(2)

    with ch1:
        st.subheader("📊 Staffing Requirement vs Availability")
        if 'Condition' in df_filtered:
            df_melt = condition_group.melt(
                id_vars=["Condition"],
                value_vars=["Current_Staff", "Required_Staff"],
                var_name="Staff_Type",
                value_name="Count"
            )
            fig1 = px.bar(df_melt, x="Condition", y="Count", color="Staff_Type", barmode="group")
            fig1.update_layout(legend_title_text="", height=350, yaxis_title="Number of Staff", xaxis_title="Medical Condition")
            st.plotly_chart(style_fig(fig1), use_container_width=True)
        else:
            st.info("No 'Condition' column for staffing chart.")

    # NEW: Bubble scatter — Doctor performance
    with ch2:
        st.subheader("🫧 Doctor Performance — Throughput vs Cost (size = Readmit%)")
        if 'Doctor_ID' in df_filtered and 'Patient_ID' in df_filtered:
            # per-doctor aggregates
            grp = df_filtered.groupby('Doctor_ID').agg(
                Patients_Treated=('Patient_ID', 'nunique'),
                Total_Cost=('Cost', 'sum'),
                Readmit_Count=('Readmission', lambda s: (s.astype(str).str.lower().str.strip() == 'yes').sum() if s is not None else 0)
            ).reset_index()
            grp['Avg_Cost_Per_Patient'] = grp['Total_Cost'] / grp['Patients_Treated'].replace(0, pd.NA)
            grp['Readmit_Rate'] = grp.apply(lambda r: (r['Readmit_Count'] / r['Patients_Treated']) if r['Patients_Treated'] else 0, axis=1)

            # optional color by Department if exists
            if 'Department' in df_filtered.columns:
                dept_map = df_filtered.groupby('Doctor_ID')['Department'].agg(lambda s: s.dropna().iloc[0] if not s.dropna().empty else 'NA')
                grp = grp.merge(dept_map, on='Doctor_ID', how='left')
                color_arg = 'Department'
            else:
                color_arg = None

            fig_bubble = px.scatter(
                grp,
                x='Patients_Treated',
                y='Avg_Cost_Per_Patient',
                size='Readmit_Rate',
                color=color_arg,
                hover_data=['Doctor_ID', 'Total_Cost', 'Readmit_Count', 'Readmit_Rate'],
                labels={
                    'Patients_Treated': 'Patients Treated',
                    'Avg_Cost_Per_Patient': 'Avg Cost per Patient (£)'
                }
            )
            fig_bubble.update_yaxes(title_text="Avg Cost per Patient (£)", tickprefix="£")
            fig_bubble.update_layout(height=350)
            st.plotly_chart(style_fig(fig_bubble), use_container_width=True)
        else:
            st.info("Doctor data not available for bubble chart.")

    # PATIENT–DOCTOR–PROCEDURE TABLE
    st.markdown("---")
    st.subheader("📋 Patient–Doctor–Procedure Details")
    details_cols = [c for c in ['Patient_ID', 'Doctor_ID', 'Procedure', 'Admission_DateTime',
                                'Discharge_DateTime', 'Condition', 'Outcome', 'Cost', 'Readmission'] if c in df_filtered.columns]
    st.dataframe(df_filtered[details_cols].sort_values(by='Admission_DateTime', ascending=False),
                 use_container_width=True, height=350)
