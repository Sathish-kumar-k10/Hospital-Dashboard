#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NHS Hospital Dashboard with Consistent Blue Styling
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import base64

# --- Page Config ---
st.set_page_config(page_title="NHS Hospital Patient Dashboard", layout="wide")

# --- Custom CSS ---
st.markdown("""
<style>
    .main-content {
        background-color: rgba(255,255,255,0.2);
        padding: 20px;
        border-radius: 10px;
    }
    [data-testid="stSidebar"] {
        background-color: #005EB8 !important;
    }
    .st-b7, .st-c0, .stDateInput label, .stMultiSelect label {
        color: black !important;
    }
    .stDateInput, .stMultiSelect {
        background-color: white;
        border-radius: 4px;
        padding: 8px;
    }
    /* Full-width tabs */
    .stTabs [data-baseweb="tab-list"] {
        display: flex;
        justify-content: space-between;
        width: auto;
    }
    .stTabs [data-baseweb="tab"] {
        flex: 1 1 auto;
        text-align: center;
        height: 50px;
        padding: 0;
        background-color: #f0f2f6;
        border: none;
        font-weight: 600;
        color: #333;
        transition: all 0.3s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #e0e5ec;
    }
    .stTabs [aria-selected="true"] {
        background-color: #005EB8;
        color: white !important;
        border-bottom: 3px solid white;
    }
    .kpi-card {
        border: 2px solid #005EB8;
        border-radius: 8px;
        padding: 15px;
        background-color: #005EB8;
        text-align: center;
        margin-bottom: 15px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        color: white;
    }
    .kpi-card h3 {
        font-size: 1rem;
        margin-bottom: 8px;
        font-weight: 600;
        color: white !important;
    }
    .kpi-card h2 {
        font-size: 1.8rem;
        margin-top: 0;
        font-weight: 700;
        color: white !important;
    }
    .visual-container {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        background-color: rgba(255,255,255,0.95);
        margin-bottom: 20px;
    }
    .center-container {
        display: flex;
        justify-content: center;
        width: 100%;
    }
    .center-content {
        width: 90%;
        max-width: 1200px;
    }
    .logo-container {
        position: absolute;
        top: 10px;
        right: 20px;
    }
    .logo-container img {
        height: 40px; /* 4x bigger logo */
    }
</style>
""", unsafe_allow_html=True)

# --- Logo in top right corner ---
logo_path = "dissert-deploy/assets/background-1.png"
logo_base64 = base64.b64encode(open(logo_path, "rb").read()).decode()
st.markdown(
    f"""
    <div class="logo-container">
        <img src="data:image/png;base64,{logo_base64}">
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="main-content">', unsafe_allow_html=True)

# --- Data Loading ---
@st.cache_data
def load_patient_data():
    df = pd.read_csv('final_patient_data_with_medication_8.csv')
    df['Admission_DateTime'] = pd.to_datetime(df['Admission_DateTime'], dayfirst=True, errors='coerce')
    df['Discharge_DateTime'] = pd.to_datetime(df['Discharge_DateTime'], dayfirst=True, errors='coerce')
    return df

@st.cache_data
def load_monitoring_data():
    df = pd.read_csv('patient_24hr_monitoring_data_30min.csv')
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], dayfirst=True, errors='coerce')
    return df

patient_data = load_patient_data()
monitoring_data = load_monitoring_data()

def style_fig(fig):
    fig.update_layout(
        hoverlabel=dict(
            bgcolor="#005EB8",
            font_color="white",
            font_size=12
        ),
        plot_bgcolor='rgba(255,255,255,0.85)',
        paper_bgcolor='rgba(255,255,255,0.85)',
        font=dict(color='black'),
        title_font=dict(color='black'),
        legend=dict(font=dict(color='black'))
    )
    fig.update_traces(
        hoverlabel=dict(
            bgcolor="#005EB8",
            font_color="white",
            font_size=12
        )
    )
    return fig



# --- Sidebar Filters ---
with st.sidebar:
    st.title("📅 Global Filter Options")
    min_date = patient_data['Admission_DateTime'].dt.date.min()
    max_date = patient_data['Admission_DateTime'].dt.date.max()
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


# --- Tabs ---
tab1, tab2, tab3 = st.tabs(["🏥 Revenue & KPIs", "👨‍⚕️ Doctor Overview", "📊 Live Monitoring"])

# -------- Tab 1: Hospital Revenue & KPI Overview --------
with tab1:
    st.header("Hospital Revenue & KPI Overview")

    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        cost_from = st.date_input("Cost Trend From", from_date, min_value=min_date, max_value=max_date)
    with col_filter2:
        cost_to = st.date_input("Cost Trend To", to_date, min_value=min_date, max_value=max_date)

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
        recovered = filtered_cost_df[filtered_cost_df['Outcome'] == 'Recovered'].shape[0]
        readmissions = filtered_cost_df[filtered_cost_df['Readmission'] == 'Yes'].shape[0]

        col1, col2, col3 = st.columns(3)
        col4, col5, col6 = st.columns(3)
        
        # KPI cards with black borders
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
        top_procedures = filtered_cost_df.groupby('Procedure')['Cost'].sum().sort_values(ascending=False).head(7).reset_index()

        col_chart1, col_chart2 = st.columns(2)
        with col_chart1:
            fig_cost_trend = px.line(cost_by_month, x='Month', y='Cost', markers=True, title="Cost Trends (Monthly)")
            fig_cost_trend.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=400)
            st.plotly_chart(fig_cost_trend, use_container_width=True)
        with col_chart2:
            fig_procedures = px.bar(top_procedures, x='Procedure', y='Cost', text='Cost', title="Top Procedures by Revenue")
            fig_procedures.update_traces(texttemplate='£%{text:,.0f}', textposition='outside')
            fig_procedures.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=400)
            st.plotly_chart(fig_procedures, use_container_width=True)

# -------- Tab 2: Doctor Performance & Patient Overview (Refined) --------
with tab2:
    st.header("Doctor Performance & Patient Overview")
    
    # Use the same filtered data as other tabs
    df_doctors = filtered_patients.copy()
    
    # Calculate KPIs
    visits_per_month = df_doctors.groupby(df_doctors['Admission_DateTime'].dt.to_period('M')).size()
    avg_patient_visits_per_month = visits_per_month.mean() if not visits_per_month.empty else 0
    patients_per_doctor = df_doctors.groupby('Doctor_ID')['Patient_ID'].nunique()
    avg_patients_per_doctor = patients_per_doctor.mean() if not patients_per_doctor.empty else 0
    deaths_df = df_doctors[df_doctors['Outcome'] == 'Death']
    deaths_per_month = deaths_df.groupby(deaths_df['Admission_DateTime'].dt.to_period('M')).size()
    total_deaths = deaths_per_month.sum() if not deaths_per_month.empty else 0
    avg_satisfaction_score = df_doctors['Customer_Satisfaction_Score'].mean() if 'Customer_Satisfaction_Score' in df_doctors.columns else 0
    # KPI cards with black borders
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.markdown(f'<div class="kpi-card"><h3>Avg Patient Visits / Month</h3><h2>{avg_patient_visits_per_month:.1f}</h2></div>', unsafe_allow_html=True)
    kpi2.markdown(f'<div class="kpi-card"><h3>Avg Patients per Doctor</h3><h2>{avg_patients_per_doctor:.1f}</h2></div>', unsafe_allow_html=True)
    satisfaction_1_5 = (avg_satisfaction_score / 100) * 5
    kpi3.markdown(f'<div class="kpi-card"><h3>Patient Satisfaction Score</h3><h2>{satisfaction_1_5:.1f} / 5</h2></div>', unsafe_allow_html=True)

    st.markdown("---")
    
    # First row of visuals - properly sized and aligned
    col1, col2 = st.columns([1, 1.2])  # Adjusted column ratios for better alignment
    
    with col1:
        st.markdown('<div class="visual-container">', unsafe_allow_html=True)
        # Average patient stay by medication as pie chart
        df_doctors = df_doctors.copy()
        df_doctors['Length_of_Stay'] = (df_doctors['Discharge_DateTime'] - df_doctors['Admission_DateTime']).dt.days
        avg_stay_by_med = df_doctors.groupby('Medication_Name')['Length_of_Stay'].mean().reset_index()
        
        st.subheader("Average Patient Stay (Days) by Medication")
        fig_pie = px.pie(avg_stay_by_med, names='Medication_Name', values='Length_of_Stay', 
                         title="", height=350)  # Removed title to reduce clutter
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(showlegend=False, margin=dict(t=0, b=0))
        st.plotly_chart(fig_pie, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="visual-container">', unsafe_allow_html=True)
        # Top 5 doctors by patients treated
        top_doctors = df_doctors.groupby('Doctor_ID')['Patient_ID'].nunique().sort_values(ascending=False).head(5).reset_index()
        top_doctors.columns = ['Doctor_ID', 'Patients_Treated']
        
        st.subheader("Top 5 Doctors by Patients Treated")
        fig_top_doctors = px.bar(top_doctors, x='Doctor_ID', y='Patients_Treated', text='Patients_Treated',
                                 labels={'Patients_Treated': 'Patients Treated', 'Doctor_ID': 'Doctor ID'},
                                 height=350)
        fig_top_doctors.update_traces(marker_color='#1f77b4', textposition='outside')
        fig_top_doctors.update_layout(xaxis_title="Doctor ID", yaxis_title="Patients Treated",
                                    margin=dict(t=0, b=0))
        st.plotly_chart(fig_top_doctors, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Second row - Perfectly centered Patient-Doctor-Procedure details
    st.markdown('<div class="center-container"><div class="center-content">', unsafe_allow_html=True)
    
    st.subheader("Patient - Doctor - Procedure Details")
    details_cols = ['Patient_ID', 'Doctor_ID', 'Procedure', 'Admission_DateTime', 
                    'Discharge_DateTime', 'Condition', 'Outcome', 'Cost', 'Readmission']
    st.dataframe(df_doctors[details_cols].sort_values(by='Admission_DateTime', ascending=False), 
                 height=350, use_container_width=True)
    
    st.markdown('</div></div>', unsafe_allow_html=True)

# -------- Tab 3: 24-Hour Patient Live Monitoring --------
with tab3:
    st.header("24-Hour Patient Live Monitoring")

    patient_ids = monitoring_data['Patient_ID'].unique()
    selected_patient = st.selectbox("Select Patient ID", options=patient_ids)

    patient_monitoring = monitoring_data[monitoring_data['Patient_ID'] == selected_patient].copy()
    patient_monitoring = patient_monitoring.sort_values('Timestamp')

    # Latest condition from patient_data
    latest_condition = patient_data[patient_data['Patient_ID'] == selected_patient].sort_values(
        'Admission_DateTime', ascending=False).iloc[0]['Condition']

    # KPI card for condition status with black border
    st.markdown(f'<div class="kpi-card"><h3>Current Condition Status</h3><h2>{latest_condition}</h2></div>', 
                unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1.3, 1.3, 1])

    # Left column: Heart Rate + Body Temp
    with col1:
        st.subheader("Heart Rate")
        fig_hr = px.line(patient_monitoring, x='Timestamp', y='Heart Rate', markers=True)
        fig_hr.update_layout(height=230, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_hr, use_container_width=True)

        st.subheader("Body Temperature")
        fig_temp = px.line(patient_monitoring, x='Timestamp', y='Body Temperature', markers=True)
        fig_temp.update_layout(height=230, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_temp, use_container_width=True)

    # Middle column: Oxygen Saturation + Blood Pressure
    with col2:
        st.subheader("Oxygen Saturation")
        fig_o2 = px.line(patient_monitoring, x='Timestamp', y='Oxygen Saturation', markers=True)
        fig_o2.update_layout(height=230, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_o2, use_container_width=True)

        st.subheader("Blood Pressure")
        fig_bp = px.line(
            patient_monitoring.melt(
                id_vars=['Timestamp'],
                value_vars=['Systolic Blood Pressure', 'Diastolic Blood Pressure']
            ),
            x='Timestamp', y='value', color='variable',
            labels={'value': 'Blood Pressure (mmHg)', 'variable': 'Type'}
        )
        fig_bp.update_layout(height=230, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_bp, use_container_width=True)

    # Right column: Medication History
    with col3:
        st.subheader("Medication History")
        meds = patient_data[patient_data['Patient_ID'] == selected_patient][
            ['Admission_DateTime', 'Medication_Name']].dropna().sort_values('Admission_DateTime')
        if not meds.empty:
            st.dataframe(meds, height=480)
        else:
            st.write("No medication history available.")
