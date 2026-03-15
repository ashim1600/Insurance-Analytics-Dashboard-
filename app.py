import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Set page config for wider layout and better title
st.set_page_config(
    page_title="Insurance Analytics Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for premium look
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background-color: #0E1117;
    }
    
    /* Global Font */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* KPI Cards Container */
    .metric-container {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        background-color: #262730;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        margin-bottom: 20px;
        border: 1px solid #3A3B45;
        transition: transform 0.2s, border-color 0.2s;
    }
    
    .metric-container:hover {
        transform: translateY(-5px);
        border-color: #4B8BFF;
    }
    
    .metric-title {
        color: #A3A8B8;
        font-size: 14px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 5px;
    }
    
    .metric-value {
        color: #FFFFFF;
        font-size: 28px;
        font-weight: 700;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #FFFFFF !important;
    }
    
    /* Divider */
    hr {
        border-color: #3A3B45;
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        color: #4B8BFF !important;
        border-bottom: 2px solid #4B8BFF !important;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    """Loads and preprocesses the insurance datasets."""
    # Base directory
    base_dir = "."
    
    try:
        # Load tables, skipping the metadata headers
        # Based on data exploration, we skip ~7 rows for most files
        # Let's inspect them carefully and drop unnamed headers
        
        # 1. Fact Table
        fact_df = pd.read_csv(os.path.join(base_dir, "FCT.Insurance_Policy_Table.csv"), skiprows=4)
        fact_df = fact_df.loc[:, ~fact_df.columns.str.contains('^Unnamed')]
        
        # 2. Customers
        cust_df = pd.read_csv(os.path.join(base_dir, "DM.Customer_Detail_Table 1.csv"), skiprows=6)
        cust_df = cust_df.loc[:, ~cust_df.columns.str.contains('^Unnamed')]
        
        # 3. Agents
        agent_df = pd.read_csv(os.path.join(base_dir, "DM.Insurance_Agent_Table.csv"), skiprows=4)
        agent_df = agent_df.loc[:, ~agent_df.columns.str.contains('^Unnamed')]
        
        # 4. Policy Protection Plan
        plan_df = pd.read_csv(os.path.join(base_dir, "DM.Policy_Protection_Plan.csv"), skiprows=6)
        plan_df = plan_df.loc[:, ~plan_df.columns.str.contains('^Unnamed')]
        
        # 5. Policy Type
        type_df = pd.read_csv(os.path.join(base_dir, "DM.Policy_Type.csv"), skiprows=6)
        type_df = type_df.loc[:, ~type_df.columns.str.contains('^Unnamed')]
        
        # Convert Dates in Fact Table
        if 'Start Date' in fact_df.columns:
            fact_df['Start Date'] = pd.to_datetime(fact_df['Start Date'], errors='coerce')
        if 'Date of Purchase' in fact_df.columns:
            fact_df['Date of Purchase'] = pd.to_datetime(fact_df['Date of Purchase'], errors='coerce')
        
        # Merge datasets using pandas merge
        # Join Customers
        if 'Customer ID' in fact_df.columns and 'Customer ID' in cust_df.columns:
            merged_df = pd.merge(fact_df, cust_df, on="Customer ID", how="left", suffixes=("", "_cust"))
        else:
            merged_df = fact_df.copy()
            
        # Join Agents
        if 'Sales Agent Code' in merged_df.columns and 'Agent Code' in agent_df.columns:
            merged_df = pd.merge(merged_df, agent_df, left_on="Sales Agent Code", right_on="Agent Code", how="left")
            
        # Join Policy Type
        if 'Policy Type Code' in merged_df.columns and 'Policy Type Code' in type_df.columns:
            merged_df = pd.merge(merged_df, type_df, on="Policy Type Code", how="left", suffixes=("", "_type"))
            
        # Join Policy Protection Plan
        if 'Policy Code' in merged_df.columns and 'Policy Code' in plan_df.columns:
            merged_df = pd.merge(merged_df, plan_df, on="Policy Code", how="left", suffixes=("", "_plan"))
            
        return merged_df
        
    except Exception as e:
        st.error(f"Error loading data: {e}")
        # Return empty dataframe schema as fallback
        return pd.DataFrame()


@st.cache_data
def convert_df_to_csv(df):
    """Caches the conversion of a dataframe to CSV to optimize performance."""
    return df.to_csv(index=False).encode('utf-8')


def main():
    st.title("🛡️ Insurance Analytics Dashboard")
    st.markdown("Interactive overview of policy sales, demographics, and agent performance.")
    st.divider()

    with st.spinner("Loading and processing dataset..."):
        df = load_data()
        
    if df.empty:
        st.warning("No data found or failed to load. Please ensure the CSV files are in the directory.")
        return

    # --- SIDEBAR FILTERS ---
    st.sidebar.header("Global Filters")
    st.sidebar.write("Filters apply dynamically across all tabs.")
    
    # Year Filter
    if 'Purchase Year' in df.columns:
        years = ["All"] + sorted(df['Purchase Year'].dropna().unique().tolist())
        selected_year = st.sidebar.selectbox("Purchase Year", years)
        if selected_year != "All":
            df = df[df['Purchase Year'] == selected_year]
            
    # State Filter
    state_col = 'State_cust' if 'State_cust' in df.columns else 'State'
    if state_col in df.columns:
        states = ["All"] + sorted(df[state_col].dropna().unique().tolist())
        selected_state = st.sidebar.selectbox("Customer State", states)
        if selected_state != "All":
            df = df[df[state_col] == selected_state]

    # Status Filter
    if 'Policy Status' in df.columns:
        statuses = ["All"] + sorted(df['Policy Status'].dropna().unique().tolist())
        selected_status = st.sidebar.selectbox("Policy Status", statuses)
        if selected_status != "All":
            df = df[df['Policy Status'] == selected_status]

    # Shared Plotly configuration mapping
    corporate_colors = px.colors.sequential.Tealgrn

    # --- NAVIGATION TABS ---
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Executive Summary", 
        "🌎 Geography & Demographics", 
        "🛡️ Compliance & Risk", 
        "📋 Policy Data & Insights",
        "📈 Agent Performance", 
        "📥 Reports & Download"
    ])
    
    # === TAB 1: EXECUTIVE SUMMARY ===
    with tab1:
        st.subheader("High-Level KPIs")
        col1, col2, col3, col4 = st.columns(4)
        
        # Calculations
        total_policies = len(df)
        
        total_premium = 0
        if 'Premium Amount' in df.columns:
            total_premium = df['Premium Amount'].sum()
            
        total_sum_assured = 0
        if 'Sum Assured INR/Coverage Amount' in df.columns:
            total_sum_assured = df['Sum Assured INR/Coverage Amount'].sum()
            
        avg_loan = 0
        if 'Loan Amount Allowed' in df.columns:
            avg_loan = df['Loan Amount Allowed'].mean()

        # Formatted KPI HTML
        def kpi_html(title, value):
            return f"""
            <div class="metric-container">
                <div class="metric-title">{title}</div>
                <div class="metric-value">{value}</div>
            </div>
            """

        col1.markdown(kpi_html("Total Policies Sold", f"{total_policies:,}"), unsafe_allow_html=True)
        col2.markdown(kpi_html("Total Premium (INR)", f"₹ {total_premium:,.2f}"), unsafe_allow_html=True)
        col3.markdown(kpi_html("Total Sum Assured", f"₹ {total_sum_assured:,.2f}"), unsafe_allow_html=True)
        col4.markdown(kpi_html("Avg Loan Allowed", f"₹ {avg_loan:,.2f}"), unsafe_allow_html=True)

        st.divider()

        st.subheader("Revenue (Premium) Over Time")
        if 'Date of Purchase' in df.columns and 'Premium Amount' in df.columns:
            time_df = df.copy()
            time_df = time_df.dropna(subset=['Date of Purchase'])
            if not time_df.empty:
                time_df['Month_Year'] = time_df['Date of Purchase'].dt.to_period('M').astype(str)
                trend = time_df.groupby('Month_Year')['Premium Amount'].sum().reset_index()
                trend = trend.sort_values('Month_Year')
                
                fig_trend = px.area(
                    trend, x='Month_Year', y='Premium Amount',
                    color_discrete_sequence=['#4B8BFF'],
                    template="plotly_dark"
                )
                fig_trend.update_layout(
                    margin=dict(l=0, r=0, t=30, b=0),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    xaxis_title="Timeline",
                    yaxis_title="Premium Collected (₹)",
                    yaxis_tickformat=",.0f"
                )
                st.plotly_chart(fig_trend, use_container_width=True)
            else:
                st.info("Insufficient timeline data available.")
        else:
            st.info("Required columns for Time Series are missing.")


    # === TAB 2: GEOGRAPHY & DEMOGRAPHICS ===
    with tab2:
        st.subheader("Customer Insights")
        kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
        
        # Calculations
        smoker_pct = 0
        if 'Smoker Status' in df.columns:
            smoker_counts = df['Smoker Status'].value_counts(normalize=True)
            smoker_pct = smoker_counts.get('Yes', 0) * 100
            
        avg_age = 0
        if 'Current Age' in df.columns:
            avg_age = df['Current Age'].mean()
            if pd.isna(avg_age):
                avg_age = 0
                
        med_exam_pct = 0
        if 'Medical Exam Required' in df.columns:
            med_counts = df['Medical Exam Required'].value_counts(normalize=True)
            med_exam_pct = med_counts.get('Yes', 0) * 100

        kpi_col1.markdown(kpi_html("Smoker Percentage", f"{smoker_pct:.1f}%"), unsafe_allow_html=True)
        kpi_col2.markdown(kpi_html("Average Age", f"{avg_age:.1f} yrs"), unsafe_allow_html=True)
        kpi_col3.markdown(kpi_html("Medical Exam Required", f"{med_exam_pct:.1f}%"), unsafe_allow_html=True)
        
        st.divider()

        r1c1, r1c2 = st.columns(2)
        
        # Geography Chart
        with r1c1:
            st.subheader("Geographical Distribution")
            if state_col in df.columns:
                state_counts = df[state_col].value_counts().reset_index()
                state_counts.columns = ['State', 'Total Count']
                fig_state = px.bar(
                    state_counts.head(10), x='Total Count', y='State', orientation='h',
                    color='Total Count', color_continuous_scale="Blues",
                    template="plotly_dark"
                )
                fig_state.update_layout(
                    margin=dict(l=0, r=0, t=30, b=0),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    yaxis={'categoryorder': 'total ascending'},
                    xaxis_title="Number of Policies"
                )
                st.plotly_chart(fig_state, use_container_width=True)
            else:
                st.info("State data not available.")

        # Demographics Chart (Gender)
        with r1c2:
            st.subheader("Customer Demographics (Gender)")
            if 'Gender' in df.columns:
                gender_cnt = df['Gender'].value_counts().reset_index()
                gender_cnt.columns = ['Gender', 'Count']
                fig_gender = px.pie(
                    gender_cnt, names='Gender', values='Count', hole=0.7,
                    color_discrete_sequence=['#4B8BFF', '#2BCBBA', '#FF6B6B'],
                    template="plotly_dark"
                )
                fig_gender.update_layout(
                    margin=dict(l=0, r=0, t=30, b=0),
                    paper_bgcolor="rgba(0,0,0,0)"
                )
                fig_gender.update_traces(textposition='inside', textinfo='percent+label', marker=dict(line=dict(color='#0E1117', width=2)))
                st.plotly_chart(fig_gender, use_container_width=True)
            else:
                st.info("Gender data not available.")
                
        st.divider()
        r2c1, r2c2 = st.columns(2)
        # Occupation distribution
        with r2c1:
            st.subheader("Top Occupations")
            if 'Occupation' in df.columns:
                occ_cnt = df['Occupation'].value_counts().reset_index().head(5)
                occ_cnt.columns = ['Occupation', 'Count']
                fig_occ = px.bar(
                    occ_cnt, x='Occupation', y='Count',
                    color_discrete_sequence=['#2BCBBA'],
                    template="plotly_dark"
                )
                fig_occ.update_layout(
                    margin=dict(l=0, r=0, t=30, b=0),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    xaxis_title=""
                )
                st.plotly_chart(fig_occ, use_container_width=True)
            else:
                st.info("Occupation data not available.")

        # Product Mix
        with r2c2:
            st.subheader("Product Mix (By Policy Code)")
            if 'Policy Code' in df.columns:
                type_cnt = df['Policy Code'].value_counts().reset_index()
                type_cnt.columns = ['Policy Code', 'Count']
                fig_type = px.treemap(
                    type_cnt, path=[px.Constant("All Policies"), 'Policy Code'], values='Count',
                    color='Count', color_continuous_scale='Blues',
                    template="plotly_dark"
                )
                fig_type.update_layout(
                    margin=dict(l=0, r=0, t=30, b=0),
                    paper_bgcolor="rgba(0,0,0,0)"
                )
                st.plotly_chart(fig_type, use_container_width=True)
            else:
                st.info("Policy Code data not available.")


    # === TAB 3: COMPLIANCE & RISK ===
    with tab3:
        st.subheader("Risk & Underwriting Compliance metrics")
        risk_col1, risk_col2, risk_col3 = st.columns(3)
        
        # Calculations: High-Risk Customer %
        hr_pct = 0
        if 'Smoker Status' in df.columns and 'Current Age' in df.columns:
            # Over 50 and Smoker
            high_risk_mask = (df['Smoker Status'] == 'Yes') & (df['Current Age'] > 50)
            hr_pct = (high_risk_mask.sum() / len(df)) * 100 if len(df) > 0 else 0
            
        # Calculations: Age Compliance Exception %
        exception_pct = 0
        if 'Medical Exam Required' in df.columns and 'Current Age' in df.columns:
            # Over 50 but Medical Exam is 'No'
            exception_mask = (df['Current Age'] > 50) & (df['Medical Exam Required'] == 'No')
            exception_pct = (exception_mask.sum() / len(df)) * 100 if len(df) > 0 else 0
            
        # Calculations: Average Coverage Leverage
        leverage = 0
        if 'Sum Assured INR/Coverage Amount' in df.columns and 'Premium Amount' in df.columns:
            # (Sum Assured / Premium Amount). Handles zero division internally.
            valid_prem = df[df['Premium Amount'] > 0]
            leverage = (valid_prem['Sum Assured INR/Coverage Amount'] / valid_prem['Premium Amount']).mean()
            if pd.isna(leverage):
                leverage = 0
                
        risk_col1.markdown(kpi_html("High-Risk Exposure", f"{hr_pct:.2f}%"), unsafe_allow_html=True)
        risk_col2.markdown(kpi_html("Age Underwriting Exceptions", f"{exception_pct:.2f}%"), unsafe_allow_html=True)
        risk_col3.markdown(kpi_html("Avg Coverage Leverage Ratio", f"{leverage:.1f}x"), unsafe_allow_html=True)
        
        st.divider()
        st.info("💡 **Age Underwriting Exceptions** flags policies issued to individuals over 50 years of age without requiring a medical exam. High-Risk Exposure represents individuals over 50 who are smokers.")


    # === TAB 4: POLICY INSIGHTS ===
    with tab4:
        r2c1, r2c2 = st.columns(2)
        
        with r2c1:
            st.subheader("Policy Plan Popularity")
            if 'Policy Name' in df.columns:
                plan_cnt = df['Policy Name'].value_counts().reset_index()
                plan_cnt.columns = ['Policy Name', 'Sales Count']
                fig_plan = px.pie(
                    plan_cnt, names='Policy Name', values='Sales Count',
                    color_discrete_sequence=corporate_colors,
                    hole=0.4,
                    template="plotly_dark"
                )
                fig_plan.update_traces(textposition='inside', textinfo='percent+label', marker=dict(line=dict(color='#0E1117', width=2)))
                fig_plan.update_layout(
                    margin=dict(l=0, r=0, t=30, b=0),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    showlegend=False
                )
                st.plotly_chart(fig_plan, use_container_width=True)
            else:
                st.info("Policy Plan Name data not available. (Check data join logic)")
                
        with r2c2:
            st.subheader("Payment Frequency Breakdown")
            if 'Payment Frequency' in df.columns:
                freq_cnt = df['Payment Frequency'].value_counts().reset_index()
                freq_cnt.columns = ['Payment Frequency', 'Count']
                fig_freq = px.bar(
                    freq_cnt, x='Payment Frequency', y='Count',
                    color='Payment Frequency',
                    color_discrete_sequence=px.colors.qualitative.Prism,
                    template="plotly_dark",
                    text_auto='.2s'
                )
                fig_freq.update_layout(
                    margin=dict(l=0, r=0, t=30, b=0),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    xaxis_title="Frequency",
                    yaxis_title="Policy Volume",
                    showlegend=False
                )
                st.plotly_chart(fig_freq, use_container_width=True)
            else:
                st.info("Payment Frequency Data missing.")


    # === TAB 5: AGENT PERFORMANCE ===
    with tab5:
        st.subheader("Top Performing Agents (Premium Collected)")
        if 'Sales Agent' in df.columns and 'Premium Amount' in df.columns:
            agent_sales = df.groupby('Sales Agent')['Premium Amount'].sum().reset_index()
            agent_sales = agent_sales.sort_values(by='Premium Amount', ascending=False).head(15)
            
            fig_agent = px.bar(
                agent_sales, x='Sales Agent', y='Premium Amount',
                color='Premium Amount', color_continuous_scale="Blues",
                template="plotly_dark"
            )
            fig_agent.update_layout(
                margin=dict(l=0, r=0, t=30, b=0),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                xaxis_tickangle=-45,
                xaxis_title="Agent Name",
                yaxis_title="Premium Collected (₹)",
                yaxis_tickformat=",.0f"
            )
            st.plotly_chart(fig_agent, use_container_width=True)
        else:
            st.info("Agent Performance data not available.")


    # === TAB 6: REPORTS & DOWNLOAD ===
    with tab6:
        st.subheader("Filtered Corporate Data Table")
        st.write("Review the currently filtered dataset representing the precise metrics observed in the dashboard above.")
        
        # Display data with commas for currency inside the Streamlit dataframe viewer
        display_df = df.copy()
        
        # Drop columns created by merge suffixes that are redundant
        cols_to_drop = [col for col in display_df.columns if col.endswith('_cust') or col.endswith('_type')]
        display_df = display_df.drop(columns=cols_to_drop, errors='ignore')
        
        st.dataframe(display_df, use_container_width=True, height=400)
        
        st.divider()
        st.markdown("### Export Dataset")
        st.info("Download the exact view shown above as an Excel-compatible CSV file for offline stakeholder distribution.")
        
        if not display_df.empty:
            csv_data = convert_df_to_csv(display_df)
            st.download_button(
                label="⬇️ Download Filtered Report as CSV",
                data=csv_data,
                file_name="insurance_analytics_export.csv",
                mime="text/csv",
                type="primary"
            )
        else:
            st.warning("No data available to download based on the current filters.")

if __name__ == "__main__":
    main()
