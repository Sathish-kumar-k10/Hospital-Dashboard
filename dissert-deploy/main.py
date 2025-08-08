# -*- coding: utf-8 -*-
"""
NHS Hospital Dashboard — unified hover + clean tooltips across all tabs
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import base64

# ---------------------- Config ----------------------
st.set_page_config(page_title="NHS Hospital Patient Dashboard", layout="wide")
INPUT_CSV = "https://www.dropbox.com/scl/fi/6t39mmgx6uha3l7jv1sxb/final_patient_data_with_medication_8.csv?rlkey=ta0o4m5x56inor33t15kq1r7c&st=hk5buwpr&raw=1"
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
    .kpi-card { border: 2px solid #005EB8; border-radius: 8px; padding: 15px; background-color: #005EB8;
                text-align: center; margin-bottom: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); color: white; }
    .kpi-card h3 { font-size: 1rem; margin-bottom: 8px; font-weight: 600; color: white !important; }
    .kpi-card h2 { font-size: 1.8rem; margin-top: 0; font-weight: 700; color: white !important; }
    .kpi-fixed { min-height: 120px; display:flex; flex-direction:column; justify-content:center; }
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
    return df

@st.cache_data
def load_monitoring_data(path: str):
    df = pd.read_csv(path)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], dayfirst=True, errors='coerce')
    return df

patient_data = load_patient_data(INPUT_CSV)
monitoring_data = load_monitoring_data(MONITORING_CSV)

# ---------------------- Plot helpers (unified hover + no 'undefined') ----------------------
def style_fig(fig):
    fig.update_layout(
        title_text="", title=None,
        hovermode="x unified",  # unified hover everywhere
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

# ---------------------- Sidebar Filters ----------------------
valid_dates = patient_data['Admission_DateTime'].dropna()
if valid_dates.empty:
    st.error("No valid Admission_DateTime values in the dataset.")
    st.stop()

min_date = valid_dates.dt.date.min()
max_date = valid_dates.dt.date.max()

with st.sidebar:
    st.title("📅 Global Filter Options")
    from_date = st.date_input("From Date", min_date, min_value=min_date, max_value=max_date)
    to_date = st.date_input("To Date", max_date, min_value=min_date, max_value=max_date)
    if from_date > to_date:
        st.error("Error: From Date must be before To Date.")

    condition_options = sorted(patient_data['Condition'].dropna().unique())
    condition_filter = st.multiselect("Filter by Condition", options=condition_options)

filtered_patients = patient_data[
    (patient_data['Admission_DateTime'].dt.date >= from_date) &
    (patient_data['Admission_DateTime'].dt.date <= to_date)
]
if condition_filter:
    filtered_patients = filtered_patients[filtered_patients['Condition'].isin(condition_filter)]

# ---------------------- Tabs ----------------------
tab_pressures, tab1, tab2, tab3 = st.tabs(
    ["⚠️ System Pressures", "🏥 Revenue & KPIs", "👨‍⚕️ Doctor Overview", "📊 Live Monitoring"]
)

# =================================================================
# TAB 1: SYSTEM PRESSURES
# =================================================================
with tab_pressures:
    st.header("System Pressures: Budget, Staffing, Waiting, Demand, Aging")
    dfp = filtered_patients.copy()

    # Ensure columns exist
    for c in [
        "Total_Cost_Spent","Proposed_Budget","Funding_Gap_Percent",
        "Staff_Shortage_Index","Demand_Index","Waiting_List_Days",
        "Aging_Population_Share","Year","Month","Condition"
    ]:
        if c not in dfp.columns:
            dfp[c] = pd.NA

    years_available = sorted(dfp["Year"].dropna().unique())
    if len(years_available) == 0:
        st.info("No valid years in current filter.")
        st.stop()
    sel_year = st.selectbox("Select Year for KPIs & charts", years_available, index=len(years_available)-1)

    # Deduplicate to one row per (Condition, Year), then aggregate by year
    cy_unique = (
        dfp.dropna(subset=["Condition","Year"])
           .drop_duplicates(subset=["Condition","Year"])
           [["Condition","Year","Total_Cost_Spent","Proposed_Budget","Aging_Population_Share"]]
           .copy()
    )
    by_year = (
        cy_unique.groupby("Year", dropna=False)
                 .agg(
                     Total_Cost_Spent=("Total_Cost_Spent","sum"),
                     Proposed_Budget=("Proposed_Budget","sum"),
                     Aging_Population_Share=("Aging_Population_Share","mean"),
                 )
                 .reset_index()
                 .sort_values("Year")
    )

    # KPIs based on selected year
    this_year = by_year[by_year["Year"] == sel_year]
    if this_year.empty:
        total_cost_sel = budget_sel = avg_age_share = 0.0
        funding_gap_sel = 0.0
    else:
        total_cost_sel = float(this_year["Total_Cost_Spent"].iloc[0] or 0)
        budget_sel      = float(this_year["Proposed_Budget"].iloc[0] or 0)
        avg_age_share   = float(this_year["Aging_Population_Share"].iloc[0] or 0)
        denom = budget_sel if budget_sel != 0 else None
        funding_gap_sel = float(((budget_sel - total_cost_sel)/denom*100) if denom else 0)

    # Staffing & Waiting summaries (selected year)
    dfp_year = dfp[dfp["Year"] == sel_year].copy()
    dfp_year["Month"] = dfp_year["Admission_DateTime"].dt.to_period("M").astype(str)

    staff_idx_avg = float(dfp_year["Staff_Shortage_Index"].dropna().mean() or 0)
    waiting_med   = dfp_year["Waiting_List_Days"].dropna().median()
    waiting_med   = int(waiting_med) if pd.notna(waiting_med) else 0

    # KPI cards
    a1, a2, a3 = st.columns(3)
    b1, b2, b3 = st.columns(3)
    a1.markdown(f'<div class="kpi-card kpi-fixed"><h3>Total Cost (Year {sel_year})</h3><h2>£{total_cost_sel:,.0f}</h2></div>', unsafe_allow_html=True)
    a2.markdown(f'<div class="kpi-card kpi-fixed"><h3>Budget (Year {sel_year})</h3><h2>£{budget_sel:,.0f}</h2></div>', unsafe_allow_html=True)
    a3.markdown(f'<div class="kpi-card kpi-fixed"><h3>Funding Gap (Year {sel_year})</h3><h2>{funding_gap_sel:.1f}%</h2></div>', unsafe_allow_html=True)
    b1.markdown(f'<div class="kpi-card kpi-fixed"><h3>Staff Shortage Index</h3><h2>{staff_idx_avg:.1f}</h2></div>', unsafe_allow_html=True)
    b2.markdown(f'<div class="kpi-card kpi-fixed"><h3>Median Waiting (days)</h3><h2>{waiting_med}</h2></div>', unsafe_allow_html=True)
    b3.markdown(f'<div class="kpi-card kpi-fixed"><h3>Aging Pop. Share</h3><h2>{avg_age_share:.1f}%</h2></div>', unsafe_allow_html=True)

    st.markdown("---")

    # Budget vs Spend (all years)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Budget vs Spend (by Year)")
        if not by_year.empty:
            df_bar = by_year.melt(id_vars="Year",
                                  value_vars=["Total_Cost_Spent","Proposed_Budget"],
                                  var_name="Type", value_name="Amount")
            fig = px.bar(
                df_bar, x="Year", y="Amount", color="Type",
                title="", labels={"Year":"Year", "Amount":"Amount (£)", "Type":"Type"}
            )
            fig.update_traces(
                hovertemplate="<b>%{fullData.name}</b><br>Year: %{x}<br>Amount: £%{y:,.0f}<extra></extra>"
            )
            fig.update_yaxes(title_text="Amount (£)", tickprefix="£")
            st.plotly_chart(tidy(fig), use_container_width=True)
        else:
            st.info("No budget/spend data available for the selection.")

    # Funding Gap trend
    with c2:
        st.subheader("Funding Gap % Trend (by Year)")
        if not by_year.empty:
            denom = by_year["Proposed_Budget"].replace({0: pd.NA})
            by_year_plot = by_year.assign(Funding_Gap_Percent=((by_year["Proposed_Budget"] - by_year["Total_Cost_Spent"]) / denom * 100))
            fig = px.line(
                by_year_plot, x="Year", y="Funding_Gap_Percent", markers=True,
                title="", labels={"Year":"Year","Funding_Gap_Percent":"Funding Gap (%)"}
            )
            fig.update_traces(
                hovertemplate="Year: %{x}<br>Funding Gap: %{y:.1f}%<extra></extra>"
            )
            fig.update_yaxes(title_text="Funding Gap (%)")
            st.plotly_chart(tidy(fig), use_container_width=True)
        else:
            st.info("No funding gap data available for the selection.")

    st.markdown("---")

    # Staff Shortage rolling + Waiting rolling
    d1, d2 = st.columns(2)

    def month_to_ts(df, col="Month"):
        out = df.copy()
        out["MonthTS"] = pd.PeriodIndex(out[col], freq="M").to_timestamp()
        return out.sort_values("MonthTS")

    with d1:
        st.subheader("Staff Shortage Index (12-month Rolling Avg)")
        s_month = dfp.groupby("Month", dropna=False)["Staff_Shortage_Index"].mean().reset_index()
        s_month = month_to_ts(s_month)
        if not s_month.empty:
            s_month["Rolling_12m"] = s_month["Staff_Shortage_Index"].rolling(12, min_periods=3).mean()
            fig = px.line(
                s_month, x="MonthTS", y="Rolling_12m", title="",
                labels={"MonthTS":"Month","Rolling_12m":"Staff Shortage (12m avg)"}
            )
            fig.update_traces(
                hovertemplate="Month: %{x|%Y-%m}<br>Index: %{y:.1f}<extra></extra>"
            )
            fig.update_xaxes(dtick="M3", tickformat="%Y-%m")
            fig.update_yaxes(title_text="Index (0–100)")
            st.plotly_chart(tidy(fig), use_container_width=True)
        else:
            st.info("No staffing data available for the selection.")

    with d2:
        st.subheader("Waiting List (12-month Rolling Median Days)")
        w_month = dfp.groupby("Month", dropna=False)["Waiting_List_Days"].median().reset_index()
        w_month = month_to_ts(w_month)
        if not w_month.empty:
            w_month["Rolling_12m"] = w_month["Waiting_List_Days"].rolling(12, min_periods=3).median()
            fig = px.line(
                w_month, x="MonthTS", y="Rolling_12m", title="",
                labels={"MonthTS":"Month","Rolling_12m":"Waiting Days (12m median)"}
            )
            fig.update_traces(
                hovertemplate="Month: %{x|%Y-%m}<br>Days: %{y:.0f}<extra></extra>"
            )
            fig.update_xaxes(dtick="M3", tickformat="%Y-%m")
            fig.update_yaxes(title_text="Days")
            st.plotly_chart(tidy(fig), use_container_width=True)
        else:
            st.info("No waiting list data available for the selection.")

# =================================================================
# TAB 2: Hospital Revenue & KPI Overview
# =================================================================
with tab1:
    st.header("Hospital Revenue & KPI Overview")

    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        cost_from = st.date_input("Cost Trend From", min_date, min_value=min_date, max_value=max_date)
    with col_filter2:
        cost_to = st.date_input("Cost Trend To", max_date, min_value=min_date, max_value=max_date)

    if cost_from > cost_to:
        st.error("Error: Cost Trend From date must be before To date.")
    else:
        filtered_cost_df = filtered_patients[
            (filtered_patients['Admission_DateTime'].dt.date >= cost_from) &
            (filtered_patients['Admission_DateTime'].dt.date <= cost_to)
        ]

        total_patients = filtered_cost_df['Patient_ID'].nunique()
        total_cost = filtered_cost_df['Cost'].sum()
        avg_cost = filtered_cost_df.groupby('Patient_ID')['Cost'].sum().mean()
        deaths = filtered_cost_df[filtered_cost_df['Survive'] == 0].shape[0]
        recovered = filtered_cost_df[filtered_cost_df['Survive'] == 1].shape[0]
        readmissions = filtered_cost_df[filtered_cost_df['Readmission'] == 'Yes'].shape[0]

        col1, col2, col3 = st.columns(3)
        col4, col5, col6 = st.columns(3)
        col1.markdown(f'<div class="kpi-card"><h3>Total Patients Admitted</h3><h2>{total_patients}</h2></div>', unsafe_allow_html=True)
        col2.markdown(f'<div class="kpi-card"><h3>Total Cost (£)</h3><h2>£{total_cost:,.0f}</h2></div>', unsafe_allow_html=True)
        col3.markdown(f'<div class="kpi-card"><h3>Avg Cost per Patient (£)</h3><h2>£{avg_cost:,.2f}</h2></div>', unsafe_allow_html=True)
        col4.markdown(f'<div class="kpi-card"><h3>Recovered Count</h3><h2>{recovered}</h2></div>', unsafe_allow_html=True)
        col5.markdown(f'<div class="kpi-card"><h3>Deaths Count</h3><h2>{deaths}</h2></div>', unsafe_allow_html=True)
        col6.markdown(f'<div class="kpi-card"><h3>Readmissions</h3><h2>{readmissions}</h2></div>', unsafe_allow_html=True)

        st.markdown("---")

        cost_trend = filtered_cost_df.copy()
        cost_trend['Month'] = cost_trend['Admission_DateTime'].dt.to_period('M').astype(str)
        cost_by_month = cost_trend.groupby('Month')['Cost'].sum().reset_index()
        top_procedures = (
            filtered_cost_df.groupby('Procedure')['Cost']
            .sum().sort_values(ascending=False).head(7).reset_index()
        )

        col_chart1, col_chart2 = st.columns(2)
        with col_chart1:
            fig_cost_trend = px.line(
                cost_by_month, x='Month', y='Cost', markers=True, title="",
                labels={"Month":"Month","Cost":"Amount (£)"}
            )
            fig_cost_trend.update_traces(
                hovertemplate="Month: %{x}<br>Amount: £%{y:,.0f}<extra></extra>"
            )
            fig_cost_trend.update_yaxes(title_text="Amount (£)", tickprefix="£")
            st.plotly_chart(tidy(fig_cost_trend, height=400), use_container_width=True)
        with col_chart2:
            fig_procedures = px.bar(
                top_procedures, x='Procedure', y='Cost', text='Cost', title="",
                labels={"Procedure":"Procedure","Cost":"Amount (£)"}
            )
            fig_procedures.update_traces(
                texttemplate='£%{text:,.0f}', textposition='outside',
                hovertemplate="Procedure: %{x}<br>Amount: £%{y:,.0f}<extra></extra>"
            )
            fig_procedures.update_yaxes(title_text="Amount (£)", tickprefix="£")
            st.plotly_chart(tidy(fig_procedures, height=400), use_container_width=True)

# =================================================================
# TAB 3: Doctor Performance & Patient Overview
# =================================================================
with tab2:
    st.header("Doctor Performance & Patient Overview")

    df_doctors = filtered_patients.copy()
    visits_per_month = df_doctors.groupby(df_doctors['Admission_DateTime'].dt.to_period('M')).size()
    avg_patient_visits_per_month = visits_per_month.mean() if not visits_per_month.empty else 0
    patients_per_doctor = df_doctors.groupby('Doctor_ID')['Patient_ID'].nunique()
    avg_patients_per_doctor = patients_per_doctor.mean() if not patients_per_doctor.empty else 0
    deaths_df = df_doctors[df_doctors['Outcome'] == 'Death']
    deaths_per_month = deaths_df.groupby(deaths_df['Admission_DateTime'].dt.to_period('M')).size()
    total_deaths = deaths_per_month.sum() if not deaths_per_month.empty else 0
    avg_satisfaction_score = df_doctors['Customer_Satisfaction_Score'].mean() if 'Customer_Satisfaction_Score' in df_doctors.columns else 0
    satisfaction_1_5 = (avg_satisfaction_score / 100) * 5

    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.markdown(f'<div class="kpi-card"><h3>Avg Patient Visits / Month</h3><h2>{avg_patient_visits_per_month:.1f}</h2></div>', unsafe_allow_html=True)
    kpi2.markdown(f'<div class="kpi-card"><h3>Avg Patients per Doctor</h3><h2>{avg_patients_per_doctor:.1f}</h2></div>', unsafe_allow_html=True)
    kpi3.markdown(f'<div class="kpi-card"><h3>Patient Satisfaction Score</h3><h2>{satisfaction_1_5:.1f} / 5</h2></div>', unsafe_allow_html=True)

    st.markdown("---")

    col1, col2 = st.columns([1, 1.2])
    with col1:
        st.markdown('<div class="visual-container">', unsafe_allow_html=True)
        df_doctors = df_doctors.copy()
        df_doctors['Length_of_Stay'] = (df_doctors['Discharge_DateTime'] - df_doctors['Admission_DateTime']).dt.days
        avg_stay_by_med = df_doctors.groupby('Medication_Name')['Length_of_Stay'].mean().reset_index()
        st.subheader("Average Patient Stay (Days) by Medication")
        fig_pie = px.pie(avg_stay_by_med, names='Medication_Name', values='Length_of_Stay', title=None, height=350)
        # Pie charts don't use unified hover; we keep default hover here
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(showlegend=False, margin=dict(t=0, b=0))
        st.plotly_chart(style_fig(fig_pie), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="visual-container">', unsafe_allow_html=True)
        top_doctors = df_doctors.groupby('Doctor_ID')['Patient_ID'].nunique().sort_values(ascending=False).head(5).reset_index()
        top_doctors.columns = ['Doctor_ID', 'Patients_Treated']
        st.subheader("Top 5 Doctors by Patients Treated")
        fig_top_doctors = px.bar(
            top_doctors, x='Doctor_ID', y='Patients_Treated', text='Patients_Treated',
            labels={'Patients_Treated':'Patients Treated', 'Doctor_ID':'Doctor ID'},
            title="", height=350
        )
        fig_top_doctors.update_traces(
            textposition='outside',
            hovertemplate="Doctor: %{x}<br>Patients Treated: %{y}<extra></extra>"
        )
        fig_top_doctors.update_yaxes(title_text="Patients Treated")
        fig_top_doctors.update_layout(margin=dict(t=0, b=0))
        st.plotly_chart(style_fig(fig_top_doctors), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    st.markdown('<div class="center-container"><div class="center-content">', unsafe_allow_html=True)
    st.subheader("Patient - Doctor - Procedure Details")
    details_cols = ['Patient_ID', 'Doctor_ID', 'Procedure', 'Admission_DateTime',
                    'Discharge_DateTime', 'Condition', 'Outcome', 'Cost', 'Readmission']
    st.dataframe(df_doctors[details_cols].sort_values(by='Admission_DateTime', ascending=False),
                 height=350, use_container_width=True)
    st.markdown('</div></div>', unsafe_allow_html=True)

# =================================================================
# TAB 4: 24-Hour Patient Live Monitoring
# =================================================================
with tab3:
    st.header("24-Hour Patient Live Monitoring")

    patient_ids = monitoring_data['Patient_ID'].unique()
    selected_patient = st.selectbox("Select Patient ID", options=patient_ids)

    patient_monitoring = monitoring_data[monitoring_data['Patient_ID'] == selected_patient].copy()
    patient_monitoring = patient_monitoring.sort_values('Timestamp')

    latest_condition = patient_data[patient_data['Patient_ID'] == selected_patient] \
        .sort_values('Admission_DateTime', ascending=False).iloc[0]['Condition']

    st.markdown(f'<div class="kpi-card"><h3>Current Condition Status</h3><h2>{latest_condition}</h2></div>',
                unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1.3, 1.3, 1])

    with col1:
        st.subheader("Heart Rate")
        fig_hr = px.line(patient_monitoring, x='Timestamp', y='Heart Rate', markers=True, title="",
                         labels={"Timestamp":"Time","Heart Rate":"Heart Rate"})
        fig_hr.update_traces(hovertemplate="Time: %{x}<br>Heart Rate: %{y}<extra></extra>")
        st.plotly_chart(tidy(fig_hr, height=230), use_container_width=True)

        st.subheader("Body Temperature")
        fig_temp = px.line(patient_monitoring, x='Timestamp', y='Body Temperature', markers=True, title="",
                           labels={"Timestamp":"Time","Body Temperature":"Body Temp"})
        fig_temp.update_traces(hovertemplate="Time: %{x}<br>Body Temp: %{y}°C<extra></extra>")
        st.plotly_chart(tidy(fig_temp, height=230), use_container_width=True)

    with col2:
        st.subheader("Oxygen Saturation")
        fig_o2 = px.line(patient_monitoring, x='Timestamp', y='Oxygen Saturation', markers=True, title="",
                         labels={"Timestamp":"Time","Oxygen Saturation":"SpO₂"})
        fig_o2.update_traces(hovertemplate="Time: %{x}<br>SpO₂: %{y}%<extra></extra>")
        st.plotly_chart(tidy(fig_o2, height=230), use_container_width=True)

        st.subheader("Blood Pressure")
        bp_long = patient_monitoring.melt(
            id_vars=['Timestamp'],
            value_vars=['Systolic Blood Pressure', 'Diastolic Blood Pressure'],
            var_name='Type', value_name='BP'
        )
        fig_bp = px.line(
            bp_long, x='Timestamp', y='BP', color='Type', title="",
            labels={'Timestamp':'Time','BP':'Blood Pressure (mmHg)','Type':'Type'}
        )
        fig_bp.update_traces(hovertemplate="Time: %{x}<br>%{fullData.name}: %{y} mmHg<extra></extra>")
        st.plotly_chart(tidy(fig_bp, height=230), use_container_width=True)

    with col3:
        st.subheader("Medication History")
        meds = patient_data[patient_data['Patient_ID'] == selected_patient][
            ['Admission_DateTime', 'Medication_Name']].dropna().sort_values('Admission_DateTime')
        if not meds.empty:
            st.dataframe(meds, height=480)
        else:
            st.write("No medication history available.")
