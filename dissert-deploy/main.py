#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced NHS Hospital Dashboard with Chatbot
"""

# --- Streamlit Config ---
import streamlit as st
st.set_page_config(page_title="NHS Hospital Patient Dashboard-1", layout="wide")

# --- Imports ---
import pandas as pd
import plotly.express as px
import base64
from transformers import pipeline
from datetime import datetime, timedelta
import os

# --- Custom CSS ---
st.markdown("""
<style>
    /* Main dashboard styles */
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
        height: 40px;
    }
    
    /* Enhanced Chatbot styles */
    .user-message {
        background-color: #005EB8;
        color: white;
        padding: 10px 15px;
        border-radius: 18px 18px 0 18px;
        margin: 8px 0;
        max-width: 80%;
        align-self: flex-end;
        word-wrap: break-word;
    }
    .bot-message {
        background-color: #e9e9e9;
        color: black;
        padding: 10px 15px;
        border-radius: 18px 18px 18px 0;
        margin: 8px 0;
        max-width: 80%;
        align-self: flex-start;
        word-wrap: break-word;
    }
    .chat-container {
        max-height: 400px;
        overflow-y: auto;
        padding: 15px;
        background-color: #f8f9fa;
        border-radius: 10px;
        margin-bottom: 15px;
    }
    .chat-input-container {
        padding-top: 10px;
        border-top: 1px solid #eee;
    }
    .chat-form {
        display: flex;
        gap: 10px;
    }
    .chat-input {
        flex-grow: 1;
    }
    .chat-send-btn {
        background-color: #005EB8;
        color: white;
        border: none;
        border-radius: 20px;
        padding: 0 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- Data Loading with Error Handling ---
@st.cache_data
def load_patient_data():
    try:
        if os.path.exists('final_patient_data_with_medication_9.csv'):
            df = pd.read_csv('final_patient_data_with_medication_9.csv')
            # Ensure required columns exist
            required_cols = ['Patient_ID', 'Admission_DateTime', 'Condition', 'Cost', 'Outcome']
            if all(col in df.columns for col in required_cols):
                df['Admission_DateTime'] = pd.to_datetime(df['Admission_DateTime'], dayfirst=True, errors='coerce')
                if 'Discharge_DateTime' in df.columns:
                    df['Discharge_DateTime'] = pd.to_datetime(df['Discharge_DateTime'], dayfirst=True, errors='coerce')
                return df
            
        # Fallback to sample data if real data isn't available
        data = {
            'Patient_ID': [1, 2, 3, 4, 5],
            'Admission_DateTime': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05']),
            'Condition': ['Fever', 'Fracture', 'Diabetes', 'Hypertension', 'Fever'],
            'Cost': [1000, 2500, 800, 1200, 950],
            'Outcome': ['Recovered', 'Recovered', 'Ongoing', 'Recovered', 'Death'],
            'Procedure': ['Blood Test', 'X-Ray', 'Glucose Test', 'BP Check', 'Blood Test']
        }
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error loading patient data: {e}")
        return pd.DataFrame()

@st.cache_data
def load_monitoring_data():
    try:
        if os.path.exists('patient_24hr_monitoring_data_30min.csv'):
            df = pd.read_csv('patient_24hr_monitoring_data_30min.csv')
            if 'Timestamp' in df.columns:
                df['Timestamp'] = pd.to_datetime(df['Timestamp'], dayfirst=True, errors='coerce')
                return df
            
        # Fallback to sample monitoring data
        data = {
            'Patient_ID': [1, 1, 1, 2, 2],
            'Timestamp': pd.to_datetime(['2023-01-01 08:00', '2023-01-01 08:30', '2023-01-01 09:00', 
                                       '2023-01-02 10:00', '2023-01-02 10:30']),
            'Heart Rate': [72, 75, 80, 68, 70],
            'Body Temperature': [98.6, 98.7, 98.5, 98.4, 98.6],
            'Oxygen Saturation': [98, 97, 96, 99, 98],
            'Systolic Blood Pressure': [120, 118, 122, 115, 119],
            'Diastolic Blood Pressure': [80, 78, 82, 75, 79]
        }
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error loading monitoring data: {e}")
        return pd.DataFrame()

# Load data
patient_data = load_patient_data()
monitoring_data = load_monitoring_data()

# --- Chatbot Backend ---
@st.cache_resource
def load_classifier():
    try:
        return pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
    except Exception as e:
        st.error(f"Error loading chatbot model: {e}")
        return None

classifier = load_classifier()

def process_chatbot_query(user_question):
    try:
        if classifier is None:
            return "Chatbot is currently unavailable. Please try again later."
            
        candidate_labels = [
            "total_cost_last_2_months",
            "patient_count_last_2_weeks",
            "recovered_count_last_3_months",
            "appointment_scheduling",
            "hospital_services",
            "emergency_contact"
        ]
        
        prediction = classifier(user_question, candidate_labels)
        intent = prediction["labels"][0]
        now = datetime.now()

        if intent == "total_cost_last_2_months":
            two_months_ago = now - timedelta(days=60)
            total_cost = patient_data[patient_data['Admission_DateTime'] >= two_months_ago]['Cost'].sum()
            return f"Total cost in the last 2 months: £{total_cost:,.0f}"

        elif intent == "patient_count_last_2_weeks":
            two_weeks_ago = now - timedelta(days=14)
            count = patient_data[patient_data['Admission_DateTime'] >= two_weeks_ago].shape[0]
            return f"Patients admitted in last 2 weeks: {count}"

        elif intent == "recovered_count_last_3_months":
            three_months_ago = now - timedelta(days=90)
            count = patient_data[
                (patient_data['Admission_DateTime'] >= three_months_ago) &
                (patient_data['Outcome'] == 'Recovered')
            ].shape[0]
            return f"Recoveries in last 3 months: {count}"
        
        elif intent == "appointment_scheduling":
            return "To schedule an appointment, please call our booking line at 0300 123 6789 or visit our website."
        
        elif intent == "hospital_services":
            return "Our hospital offers: Emergency Care, Maternity Services, Surgical Procedures, and Outpatient Clinics."
        
        elif intent == "emergency_contact":
            return "For emergencies, please call 999 immediately or visit our A&E department."

        return "I'm sorry, I couldn't understand your question. Please try asking about hospital services, appointments, or patient statistics."
    except Exception as e:
        return f"Sorry, I encountered an error processing your request: {str(e)}"

# --- Logo ---
logo_path = "assets/background-1.png"
logo_base64 = base64.b64encode(open(logo_path, "rb").read()).decode() if os.path.exists(logo_path) else ""
if logo_base64:
    st.markdown(f"""
    <div class="logo-container">
        <img src="data:image/png;base64,{logo_base64}">
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-content">', unsafe_allow_html=True)

# --- Sidebar with Enhanced Chatbot ---
with st.sidebar:
    st.title("🗓 Global Filter Options")
    
    # Date filters with proper initialization
    if not patient_data.empty and 'Admission_DateTime' in patient_data.columns:
        min_date = patient_data['Admission_DateTime'].dropna().min().date()
        max_date = patient_data['Admission_DateTime'].dropna().max().date()
    else:
        min_date = datetime(2023,1,1).date()
        max_date = datetime(2023,1,31).date()
    
    from_date = st.date_input("From Date", min_date, min_value=min_date, max_value=max_date)
    to_date = st.date_input("To Date", max_date, min_value=min_date, max_value=max_date)
    
    if from_date > to_date:
        st.error("Error: From Date must be before To Date.")
    
    # Condition filter
    condition_options = patient_data['Condition'].dropna().unique() if not patient_data.empty and 'Condition' in patient_data.columns else []
    condition_filter = st.multiselect("Filter by Condition", options=condition_options)
    
    # --- Enhanced Chatbot Assistant ---
    st.markdown("---")
    st.header("💬 NHSBot Assistant")
    
    # Initialize chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Display chat messages in a scrollable container
    with st.container():
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        for sender, message in st.session_state.chat_history:
            if sender == "user":
                st.markdown(f'<div class="user-message">{message}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="bot-message">{message}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Chat input with form for better UX
    with st.form("chat_form", clear_on_submit=True):
        col1, col2 = st.columns([4, 1])
        with col1:
            user_input = st.text_input(
                "Type your question:", 
                key="chat_input",
                label_visibility="collapsed",
                placeholder="Ask about appointments, services, or patient data..."
            )
        with col2:
            submitted = st.form_submit_button("Send", use_container_width=True)
        
        if submitted and user_input.strip():
            # Add user message to chat history
            st.session_state.chat_history.append(("user", user_input))
            
            # Get bot response (show loading state)
            with st.spinner("Thinking..."):
                response = process_chatbot_query(user_input)
            
            # Add bot response to chat history
            st.session_state.chat_history.append(("bot", response))
            
            # Force a rerun of the app to update the display
            st.rerun()

# Filter patients based on sidebar selections
if not patient_data.empty and 'Admission_DateTime' in patient_data.columns:
    filtered_patients = patient_data[
        (patient_data['Admission_DateTime'].dt.date >= from_date) &
        (patient_data['Admission_DateTime'].dt.date <= to_date)
    ]
    if condition_filter:
        filtered_patients = filtered_patients[filtered_patients['Condition'].isin(condition_filter)]
else:
    filtered_patients = pd.DataFrame()

# --- Main Dashboard Tabs ---
tab1, tab2, tab3 = st.tabs(["🏥 Revenue & KPIs", "👨‍⚕️ Doctor Overview", "📊 Live Monitoring"])

# -------- Tab 1: Hospital Revenue & KPI Overview --------
with tab1:
    st.header("Hospital Revenue & KPI Overview")

    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        cost_from = st.date_input("Cost Trend From", from_date, min_value=min_date, max_value=max_date, key="cost_from")
    with col_filter2:
        cost_to = st.date_input("Cost Trend To", to_date, min_value=min_date, max_value=max_date, key="cost_to")

    if cost_from > cost_to:
        st.error("Error: Cost Trend From date must be before To date.")
    else:
        filtered_cost_df = filtered_patients[
            (filtered_patients['Admission_DateTime'].dt.date >= cost_from) &
            (filtered_patients['Admission_DateTime'].dt.date <= cost_to)
        ] if not filtered_patients.empty else pd.DataFrame()

        if not filtered_cost_df.empty:
            total_patients = filtered_cost_df['Patient_ID'].nunique()
            total_cost = filtered_cost_df['Cost'].sum()
            avg_cost = filtered_cost_df.groupby('Patient_ID')['Cost'].sum().mean()
            deaths = filtered_cost_df[filtered_cost_df['Survive'] == 0].shape[0] if 'Survive' in filtered_cost_df.columns else 0
            recovered = filtered_cost_df[filtered_cost_df['Outcome'] == 'Recovered'].shape[0] if 'Outcome' in filtered_cost_df.columns else 0
            readmissions = filtered_cost_df[filtered_cost_df['Readmission'] == 'Yes'].shape[0] if 'Readmission' in filtered_cost_df.columns else 0

            col1, col2, col3 = st.columns(3)
            col4, col5, col6 = st.columns(3)
            
            col1.markdown(f'<div class="kpi-card"><h3>Total Patients</h3><h2>{total_patients}</h2></div>', unsafe_allow_html=True)
            col2.markdown(f'<div class="kpi-card"><h3>Total Cost (£)</h3><h2>£{total_cost:,.0f}</h2></div>', unsafe_allow_html=True)
            col3.markdown(f'<div class="kpi-card"><h3>Avg Cost</h3><h2>£{avg_cost:,.2f}</h2></div>', unsafe_allow_html=True)
            col4.markdown(f'<div class="kpi-card"><h3>Recovered</h3><h2>{recovered}</h2></div>', unsafe_allow_html=True)
            col5.markdown(f'<div class="kpi-card"><h3>Deaths</h3><h2>{deaths}</h2></div>', unsafe_allow_html=True)
            col6.markdown(f'<div class="kpi-card"><h3>Readmissions</h3><h2>{readmissions}</h2></div>', unsafe_allow_html=True)

            st.markdown("---")

            cost_trend = filtered_cost_df.copy()
            cost_trend['Month'] = cost_trend['Admission_DateTime'].dt.to_period('M').astype(str)
            cost_by_month = cost_trend.groupby('Month')['Cost'].sum().reset_index()
            top_procedures = filtered_cost_df.groupby('Procedure')['Cost'].sum().sort_values(ascending=False).head(7).reset_index() if 'Procedure' in filtered_cost_df.columns else pd.DataFrame()

            col_chart1, col_chart2 = st.columns(2)
            with col_chart1:
                if not cost_by_month.empty:
                    fig_cost_trend = px.line(cost_by_month, x='Month', y='Cost', markers=True, title="Cost Trends (Monthly)")
                    fig_cost_trend.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=400)
                    st.plotly_chart(fig_cost_trend, use_container_width=True)
                else:
                    st.warning("No cost trend data available")
            with col_chart2:
                if not top_procedures.empty:
                    fig_procedures = px.bar(top_procedures, x='Procedure', y='Cost', text='Cost', title="Top Procedures by Revenue")
                    fig_procedures.update_traces(texttemplate='£%{text:,.0f}', textposition='outside')
                    fig_procedures.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=400)
                    st.plotly_chart(fig_procedures, use_container_width=True)
                else:
                    st.warning("No procedure data available")
        else:
            st.warning("No data available for the selected date range")

# -------- Tab 2: Doctor Performance & Patient Overview --------
with tab2:
    st.header("Doctor Performance & Patient Overview")
    
    if not filtered_patients.empty:
        df_doctors = filtered_patients.copy()
        
        visits_per_month = df_doctors.groupby(df_doctors['Admission_DateTime'].dt.to_period('M')).size()
        avg_patient_visits_per_month = visits_per_month.mean() if not visits_per_month.empty else 0
        patients_per_doctor = df_doctors.groupby('Doctor_ID')['Patient_ID'].nunique() if 'Doctor_ID' in df_doctors.columns else pd.Series()
        avg_patients_per_doctor = patients_per_doctor.mean() if not patients_per_doctor.empty else 0
        deaths_df = df_doctors[df_doctors['Outcome'] == 'Death'] if 'Outcome' in df_doctors.columns else pd.DataFrame()
        deaths_per_month = deaths_df.groupby(deaths_df['Admission_DateTime'].dt.to_period('M')).size() if not deaths_df.empty else pd.Series()
        total_deaths = deaths_per_month.sum() if not deaths_per_month.empty else 0
        avg_satisfaction_score = df_doctors['Customer_Satisfaction_Score'].mean() if 'Customer_Satisfaction_Score' in df_doctors.columns else 0

        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.markdown(f'<div class="kpi-card"><h3>Avg Visits/Month</h3><h2>{avg_patient_visits_per_month:.1f}</h2></div>', unsafe_allow_html=True)
        kpi2.markdown(f'<div class="kpi-card"><h3>Avg Patients/Doctor</h3><h2>{avg_patients_per_doctor:.1f}</h2></div>', unsafe_allow_html=True)
        satisfaction_1_5 = (avg_satisfaction_score / 100) * 5
        kpi3.markdown(f'<div class="kpi-card"><h3>Satisfaction</h3><h2>{satisfaction_1_5:.1f}/5</h2></div>', unsafe_allow_html=True)

        st.markdown("---")
        
        col1, col2 = st.columns([1, 1.2])
        
        with col1:
            st.markdown('<div class="visual-container">', unsafe_allow_html=True)
            if 'Discharge_DateTime' in df_doctors.columns:
                df_doctors['Length_of_Stay'] = (df_doctors['Discharge_DateTime'] - df_doctors['Admission_DateTime']).dt.days
                if 'Medication_Name' in df_doctors.columns:
                    avg_stay_by_med = df_doctors.groupby('Medication_Name')['Length_of_Stay'].mean().reset_index()
                    st.subheader("Avg Stay by Medication")
                    if not avg_stay_by_med.empty:
                        fig_pie = px.pie(avg_stay_by_med, names='Medication_Name', values='Length_of_Stay', height=350)
                        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                        fig_pie.update_layout(showlegend=False, margin=dict(t=0, b=0))
                        st.plotly_chart(fig_pie, use_container_width=True)
                    else:
                        st.warning("No medication data available")
                else:
                    st.warning("Medication data not available")
            else:
                st.warning("Discharge data not available")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="visual-container">', unsafe_allow_html=True)
            if 'Doctor_ID' in df_doctors.columns:
                top_doctors = df_doctors.groupby('Doctor_ID')['Patient_ID'].nunique().sort_values(ascending=False).head(5).reset_index()
                top_doctors.columns = ['Doctor_ID', 'Patients_Treated']
                st.subheader("Top 5 Doctors")
                if not top_doctors.empty:
                    fig_top_doctors = px.bar(top_doctors, x='Doctor_ID', y='Patients_Treated', 
                                           text='Patients_Treated', height=350)
                    fig_top_doctors.update_traces(marker_color='#1f77b4', textposition='outside')
                    fig_top_doctors.update_layout(margin=dict(t=0, b=0))
                    st.plotly_chart(fig_top_doctors, use_container_width=True)
                else:
                    st.warning("No doctor data available")
            else:
                st.warning("Doctor data not available")
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        st.markdown('<div class="center-container"><div class="center-content">', unsafe_allow_html=True)
        st.subheader("Patient Details")
        details_cols = ['Patient_ID', 'Doctor_ID', 'Procedure', 'Admission_DateTime', 
                       'Discharge_DateTime', 'Condition', 'Outcome', 'Cost', 'Readmission']
        available_cols = [col for col in details_cols if col in df_doctors.columns]
        if available_cols:
            st.dataframe(df_doctors[available_cols].sort_values(by='Admission_DateTime', ascending=False), 
                        height=350, use_container_width=True)
        else:
            st.warning("No patient details available")
        st.markdown('</div></div>', unsafe_allow_html=True)
    else:
        st.warning("No patient data available for the selected filters")

# -------- Tab 3: 24-Hour Patient Live Monitoring --------
with tab3:
    st.header("24-Hour Patient Live Monitoring")

    if not monitoring_data.empty:
        patient_ids = monitoring_data['Patient_ID'].unique()
        selected_patient = st.selectbox("Select Patient ID", options=patient_ids)

        patient_monitoring = monitoring_data[monitoring_data['Patient_ID'] == selected_patient].copy()
        patient_monitoring = patient_monitoring.sort_values('Timestamp')

        latest_condition = ""
        if not patient_data.empty and 'Patient_ID' in patient_data.columns:
            patient_records = patient_data[patient_data['Patient_ID'] == selected_patient]
            if not patient_records.empty:
                latest_condition = patient_records.sort_values('Admission_DateTime', ascending=False).iloc[0]['Condition'] if 'Condition' in patient_records.columns else "Unknown"

        st.markdown(f'<div class="kpi-card"><h3>Current Condition</h3><h2>{latest_condition or "Unknown"}</h2></div>', 
                    unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1.3, 1.3, 1])

        with col1:
            st.subheader("Heart Rate")
            if 'Heart Rate' in patient_monitoring.columns:
                fig_hr = px.line(patient_monitoring, x='Timestamp', y='Heart Rate', markers=True)
                fig_hr.update_layout(height=230, margin=dict(l=20, r=20, t=30, b=20))
                st.plotly_chart(fig_hr, use_container_width=True)
            else:
                st.warning("Heart rate data not available")

            st.subheader("Body Temperature")
            if 'Body Temperature' in patient_monitoring.columns:
                fig_temp = px.line(patient_monitoring, x='Timestamp', y='Body Temperature', markers=True)
                fig_temp.update_layout(height=230, margin=dict(l=20, r=20, t=30, b=20))
                st.plotly_chart(fig_temp, use_container_width=True)
            else:
                st.warning("Temperature data not available")

        with col2:
            st.subheader("Oxygen Saturation")
            if 'Oxygen Saturation' in patient_monitoring.columns:
                fig_o2 = px.line(patient_monitoring, x='Timestamp', y='Oxygen Saturation', markers=True)
                fig_o2.update_layout(height=230, margin=dict(l=20, r=20, t=30, b=20))
                st.plotly_chart(fig_o2, use_container_width=True)
            else:
                st.warning("Oxygen data not available")

            st.subheader("Blood Pressure")
            if all(col in patient_monitoring.columns for col in ['Systolic Blood Pressure', 'Diastolic Blood Pressure']):
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
            else:
                st.warning("Blood pressure data not available")

        with col3:
            st.subheader("Medication History")
            if not patient_data.empty and 'Patient_ID' in patient_data.columns:
                meds = patient_data[patient_data['Patient_ID'] == selected_patient]
                if 'Admission_DateTime' in meds.columns and 'Medication_Name' in meds.columns:
                    meds = meds[['Admission_DateTime', 'Medication_Name']].dropna().sort_values('Admission_DateTime')
                    if not meds.empty:
                        st.dataframe(meds, height=480)
                    else:
                        st.write("No medication history available")
                else:
                    st.warning("Medication data not available")
            else:
                st.warning("Patient data not available")
    else:
        st.warning("No monitoring data available")

st.markdown('</div>', unsafe_allow_html=True)
