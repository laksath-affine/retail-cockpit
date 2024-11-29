import schedule
import time
from automation_aggregation import generate_insights_main
import threading
import streamlit as st

def start_scheduler():
    def run_scheduler():
        while st.session_state.get('toggle_status', False):
            schedule.run_pending()
            time.sleep(1)

    st.session_state['scheduler_output_df'] = generate_insights_main()
    schedule.every(15).seconds.do(generate_insights_main)
    
    # Run the scheduler in a separate thread
    threading.Thread(target=run_scheduler, daemon=True).start()

def stop_scheduler():
    schedule.clear()
