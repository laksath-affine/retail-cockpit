import streamlit as st
from streamlit_toggle import st_toggle_switch
from scheduler import start_scheduler, stop_scheduler
from automation_aggregation import add_sales_data, fetch_latest_date
import pandas as pd

def initialize_session_state():
    """Initialize the session state variables."""
    if "toggle_status" not in st.session_state:
        st.session_state["toggle_status"] = False
    if "latest_date" not in st.session_state:
        st.session_state["latest_date"] = fetch_latest_date()

def create_toggle_switch():
    """Render the toggle switch for starting/stopping the scheduler."""
    col1, _, _ = st.columns([2, 3, 3])  # Adjust column ratios as needed
    with col1:
        return st_toggle_switch(
            label="Run Scheduler",
            key="toggle_status",
            default_value=st.session_state["toggle_status"],
            label_after=False,
            inactive_color="#B0BEC5",
            active_color="#00C853",
            track_color="#B0BEC5",
        )


def manage_scheduler():
    """Start or stop the scheduler based on the toggle state."""
    if st.session_state["toggle_status"]:
        start_scheduler()
        preview_dataframe(st.session_state['scheduler_output_df'], None)
    else:
        stop_scheduler()
        

def show_scheduler_status():
    """Display the current status of the scheduler."""
    if st.session_state["toggle_status"]:
        st.success("Scheduler is currently running.")
        show_spinner()
    else:
        st.info("Scheduler is not running.")


def show_spinner():
    """Display a spinner animation to indicate the scheduler is active."""
    with st.spinner("Scheduler is running..."):
        st.markdown(
            """
            <style>
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            .spinner {
                border: 4px solid #f3f3f3;
                border-top: 4px solid #00C853;
                border-radius: 50%;
                width: 24px;
                height: 24px;
                animation: spin 1s linear infinite;
                margin: 10px auto;
            }
            </style>
            <div class="spinner"></div>
            """,
            unsafe_allow_html=True,
        )


def show_latest_date():
    """Display the upcoming date entry in a styled format."""
    st.markdown(
        f"""
        <p style="font-size: 20px; font-weight: bold; color: #333;">
            📅 Upcoming Date Entry: <span style="color: #4CAF50;">{st.session_state['latest_date'].strftime("%B %d, %Y")}</span>
        </p>
        """,
        unsafe_allow_html=True,
    )


def preview_dataframe(df, date=None):
    """Display a preview of the DataFrame."""
    st.markdown(
        """
        <p style="font-size: 20px; font-weight: bold; color: #333;">
            📊 Data Preview <span style="color: #4CAF50;">(First 5 Rows)</span>
        </p>
        """,
        unsafe_allow_html=True,
    )
    if date:
        filtered_df = df[df['Date'] == str(date)]
    else:
        filtered_df = df

    filtered_columns = [col for col in filtered_df.columns if col != "Date"]
    st.dataframe(filtered_df[filtered_columns].head(5))
    

def add_sales_data_to_db(file_name, sheet_name, date):
    """Add sales data to the database."""
    with st.spinner("Adding sales data to the database..."):
        add_sales_data(str(date), file_name, sheet_name)
    st.success("Sales data has been successfully added to the database!")
    

def display_dashboard_link():
    """Render a button linking to the Power BI dashboard."""
    dashboard_url = (
        "https://app.powerbi.com/groups/31cd4505-c275-4536-b6de-e265490aeec6/"
        "reports/509c243d-0d5a-47fd-a546-4f75254b49d2/2c2ce9210e2887691a0d?"
        "ctid=9be81a95-7870-42f4-bb8d-a44ada88130a&experience=power-bi"
    )
    st.markdown(
        f"""
        <style>
        .custom-link {{
            display: inline-block;
            font-size: 20px;
            font-weight: 600;
            color: white !important;
            background-color: #007BFF !important;
            padding: 10px 20px;
            border-radius: 6px;
            text-decoration: none !important;
            text-align: center;
            transition: background-color 0.3s ease, transform 0.2s ease;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        .custom-link:visited {{
            color: white !important;
        }}
        .custom-link:hover {{
            background-color: #0056b3 !important;
            transform: scale(1.05);
        }}
        </style>
        <a class="custom-link" href="{dashboard_url}" target="_blank">Go To Dashboard</a>
        """,
        unsafe_allow_html=True,
    )


def main():
    """Main function to control the Streamlit app."""
    st.title("Sales Automation Dashboard")

    # Display dashboard link
    display_dashboard_link()

    # Display the latest date
    show_latest_date()

    # Load data and display a preview
    file_name = "AnomalyDetection -Automation.xlsx"
    sheet_name = "DATA-NEW-BM"
    df = pd.read_excel(file_name, sheet_name=sheet_name)
    preview_dataframe(df, st.session_state['latest_date'])

    # Button to add sales data
    if st.button("Add Sales Data"):
        add_sales_data_to_db(file_name, sheet_name, st.session_state["latest_date"])

    # Toggle switch for the scheduler
    create_toggle_switch()

    # Manage scheduler state
    manage_scheduler()

    # Show the scheduler's status
    show_scheduler_status()


if __name__ == "__main__":
    initialize_session_state()
    main()
