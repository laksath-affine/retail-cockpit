import pandas as pd
from sqlalchemy import create_engine, text
import urllib
from data_dict import data_dict
import random
from datetime import datetime, timedelta
import streamlit as st

server = st.secrets["database"]["server"]
database = st.secrets["database"]["database"]
username = st.secrets["database"]["username"]
password = st.secrets["database"]["password"]


params = urllib.parse.quote_plus(
    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
    f"SERVER=tcp:{server},1433;"
    f"DATABASE={database};"
    f"UID={username};"
    f"PWD={password};"
    "Encrypt=yes;"
    "TrustServerCertificate=no;"
    "Connection Timeout=30;"
)
connection_engine_string = f"mssql+pyodbc:///?odbc_connect={params}"
engine = create_engine(connection_engine_string)

def create_masters_data(date, status = 'A'):
    df = pd.DataFrame({'Date': [date], 'Status': [status]})
    try:
        table_name = 'AnomalyDetectionBase'
        with engine.connect() as connection:
            df.to_sql(table_name, con=engine, if_exists='append', index=False)
        print(f"Data successfully exported to table '{table_name}' in SQL database.")
    except Exception as e:
        print(f"Error exporting data: {e}")

def create_anomaly_data(master_id, df):
    try:
        table_name = 'DATA-NEW-BM'

        df['MasterId'] = [master_id]* len(df)
        
        with engine.connect() as connection:
            df.to_sql(table_name, con=engine, if_exists='append', index=False)
        print(f"Data successfully exported to table '{table_name}' in SQL database.")
    except Exception as e:
        print(f"Error exporting data: {e}")

def create_agg_data(df):
    try:
        table_name = 'AGGREGATIONS-MAIN'
        with engine.connect() as connection:
            df.to_sql(table_name, con=engine, if_exists='append', index=False)
        print(f"Data successfully exported to table '{table_name}' in SQL database.")
    except Exception as e:
        print(f"Error exporting data: {e}")

def update_status(master_id, status='N'):
    query = text(f"""
        UPDATE AnomalyDetectionBase
        SET Status = '{status}'
        WHERE Id = {master_id}
    """)
    
    # Execute the query with parameters
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            # Execute the query
            connection.execute(query)
            # Commit the transaction
            transaction.commit()
            print("Update successful.")
        except Exception as e:
            # Rollback in case of error
            transaction.rollback()
            print(f"Error during update: {e}")


def add_sales_data(date, file_path, sheet_name):
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    df = df[df['Date'] == date]
    
    query = f"SELECT * FROM AnomalyDetectionBase WHERE Date='{date}';"
    with engine.connect() as connection:
        df_temp = pd.read_sql(query, connection)
    
    if len(df_temp) == 0:
        create_masters_data(date)
        
        with engine.connect() as connection:
            master_df = pd.read_sql("SELECT TOP 1 * FROM AnomalyDetectionBase WHERE Status='A';", connection)
        master_id = master_df.Id[0]
    
        create_anomaly_data(master_id, df)
    
        update_status(master_id)
    else:
        print('Date Already Exists for this entry for this date')
        

def fetch_latest_date():
    query = 'SELECT TOP 1 Date FROM AnomalyDetectionBase ORDER BY id DESC;'
    with engine.connect() as connection:
        df = pd.read_sql(query, connection)

    if len(df) == 0:
        print('No entries made')        
        return datetime.strptime('2024-01-01', "%Y-%m-%d").date()
    else:
        return df['Date'][0] + timedelta(weeks=1)

def slice_sales_data(df, time_range, store_code, current_week):
    """
    Filters the sales data based on dynamic time range and store code, calculates metrics, and returns results in a dictionary.

    Parameters:
        df (DataFrame): Input sales data DataFrame.
        time_range (str): Time range key, e.g., 'last_week', 'last_month'.
        store_code (int): Store code to filter data for.
        current_week (int): The current week number to dynamically calculate time ranges.

    Returns:
        dict: Aggregated metrics for the specified time range and store code.
    """
    # Define dynamic week ranges based on current_week
    time_ranges = {
        "last_week": (current_week, current_week),
        "last_month": (current_week, max(current_week - 3, 1)),  # Last 4 weeks
        "last_quarter": (current_week, max(current_week - 11, 1)),  # Last 12 weeks
        "last_year": (current_week, max(current_week - 51, 1)),  # Last 52 weeks
        "last_to_last_week": (max(current_week - 1, 1), max(current_week - 1, 1)),
        "last_to_last_month": (max(current_week - 4, 1), max(current_week - 7, 1)),  # 4 weeks before last month
        "last_to_last_quarter": (max(current_week - 12, 1), max(current_week - 23, 1)),  # 12 weeks before last quarter
        "last_to_last_year": (max(current_week - 52, 1), max(current_week - 103, 1))  # 52 weeks before last year
    }

    # Validate time_range input
    if time_range not in time_ranges:
        raise ValueError("Invalid time range specified.")

    # Extract week range for the specified time_range
    week_start, week_end = time_ranges[time_range]

    # Filter for the specified store_code and week range
    sliced_df = df[(df['STORECODE'] == store_code) & 
                   (df['WEEK_NUMBER'] <= week_start) & 
                   (df['WEEK_NUMBER'] >= week_end)]

    # Perform calculations on filtered data
    current_value = sliced_df['VALUE'].sum()
    average_bucket_size = sliced_df['PRICE'].mean()
    discounted_sales_value = sliced_df[sliced_df['DISCOUNT'] != 0]['VALUE'].sum()
    discount_proportion = discounted_sales_value / current_value if current_value != 0 else 0

    # Random number addition for inventory and footfall
    ran_no = random.choice([3, 4, 5, 6, 7, 8])
    total_inventory = max(sliced_df['INVENTORY'].fillna(0).to_list(), default=0) + ran_no
    footfall_sum = max(sliced_df['FOOTFALL'].fillna(0).to_list(), default=0) + ran_no
    gross_margin_mean = sliced_df['GROSSMARGIN'].mean()

    # Prepare output dictionary
    output_dict = {
        "current_value": current_value,
        "discount_proportion": round(discount_proportion, 2),
        "total_inventory": total_inventory,
        "average_bucket_size": round(average_bucket_size) if not pd.isna(average_bucket_size) else 0,
        "footfall_sum": footfall_sum,
        "gross_margin_mean": round(gross_margin_mean, 2) if not pd.isna(gross_margin_mean) else 0,
        "time_range": time_range,
        "store_code": store_code,
        "current_week":current_week
    }

    return output_dict

# Example input parameters
time_ranges_ = ['last_week', 'last_month', 'last_quarter', 'last_year', 
                'last_to_last_week', 'last_to_last_month', 'last_to_last_quarter', 'last_to_last_year']
storecodes_lst = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
current_week = 93  # Example current week number

# Generate final list of results


def first_level_agg(df, current_week):
    final_lst = []
    for tr in time_ranges_:
        for storecode in storecodes_lst:
            try:
                output_dict = slice_sales_data(df, tr, storecode, current_week)
                final_lst.append(output_dict)
            except Exception as e:
                print(f"Error processing {tr} for store code {storecode}: {e}")

    # Convert results to DataFrame and save as CSV
    df_new = pd.DataFrame(final_lst)
    return df_new


target_values_with_time_range = {
  "last_week": {
    "current_value_target": 8500,
    "total_inventory_target": 450,
    "footfall_sum_target": 1000,
    "gross_margin_mean_target": 33
  },
  "last_month": {
    "current_value_target": 48000,
    "total_inventory_target": 800,
    "footfall_sum_target": 1600,
    "gross_margin_mean_target": 33
  },
  "last_quarter": {
    "current_value_target": 340000,
    "total_inventory_target": 7000,
    "footfall_sum_target": 11500,
    "gross_margin_mean_target": 33
  },
  "last_year": {
    "current_value_target": 2500000,
    "total_inventory_target": 10000,
    "footfall_sum_target": 12500,
    "gross_margin_mean_target": 33
  }
}

def process_and_generate(df):
    # Read the input CSV file
    # df = pd.read_csv(input_csv)

    # Define time ranges
    time_ranges_ = ['last_week', 'last_month', 'last_quarter', 'last_year']
    df_new = pd.DataFrame()

    # Loop over time ranges and modify column names with appropriate suffixes
    for tr in time_ranges_:
        df_ = df[df['time_range'] == tr]
        df_ = df_[[
            "current_value_wow",
            "discount_proportion_wow",
            "ecom_fulfilment_wow",
            "average_bucket_size_wow"
        ]]

        # Create a mapping of suffixes based on time_range
        suffix_mapping = {
            'last_week': 'wow',
            'last_month': 'mom',
            'last_quarter': 'qoq',
            'last_year': 'yoy'
        }

        # Add the appropriate suffix based on the time_range
        df_.columns = [col.replace('wow', suffix_mapping[tr]) for col in df_.columns]
        
        # Exclude the 'last_quarter' time range from concatenation
        if tr != 'last_quarter':
            df_new = pd.concat([df_new, df_.reset_index()], axis=1)

    # Remove the 'index' column after concatenation
    df_new = df_new.drop(columns=['index'], errors='ignore')

    # Replicate the DataFrame 4 times
    df_replicated = pd.concat([df_new] * 4, ignore_index=True)

    # Remove the specified columns from the original input CSV
    columns_to_remove = [
        "current_value_wow",
        "discount_proportion_wow",
        "ecom_fulfilment_wow",
        "average_bucket_size_wow"
    ]
    df = df.drop(columns=columns_to_remove, errors='ignore')

    # Concatenate the modified original data and replicated transformed data along axis=1
    df_combined = pd.concat([df, df_replicated], axis=1)

    # Save the result to the output CSV file
    return df_combined
    
def generate_aggregations(df, current_week):
    """
    Perform second-level aggregation based on benchmark store and time ranges.

    Args:
        df (pd.DataFrame): DataFrame from the first-level aggregation.

    Returns:
        pd.DataFrame: Second-level aggregated results.
    """

    def round_off(val):
        try:
            return round(val)
        except:
            return None

    time_ranges_ = ['last_week', 'last_month', 'last_quarter', 'last_year']
    final = []

    for tr in time_ranges_:
        df_bm = df[(df['time_range'] == tr) & (df['store_code'] == 11)]
        if df_bm.empty:
            continue

        current_value_bm = df_bm['current_value'].iloc[0]
        total_inventory_bm = df_bm['total_inventory'].iloc[0]
        gross_margin_mean_bm = df_bm['gross_margin_mean'].iloc[0]
        footfall_sum_bm = df_bm['footfall_sum'].iloc[0]
        discount_proportion_bm = df_bm['discount_proportion'].iloc[0]
        average_bucket_size_bm = df_bm['average_bucket_size'].iloc[0]

        if tr == 'last_week':
            df_last_ = df[df['time_range'] == 'last_to_last_week']
        elif tr == 'last_month':
            df_last_ = df[df['time_range'] == 'last_to_last_month']
        elif tr == 'last_quarter':
            df_last_ = df[df['time_range'] == 'last_to_last_quarter']
        elif tr == 'last_year':
            df_last_ = df[df['time_range'] == 'last_to_last_year']

        for sc in range(1, 11):
            dt = {}
            dt['store_code'] = sc
            dt['time_range'] = tr

            df_last = df_last_[df_last_['store_code'] == sc]
            dr_row = df[(df['time_range'] == tr) & (df['store_code'] == sc)]

            if dr_row.empty or df_last.empty:
                continue

            # Retrieve current values
            current_value = dr_row['current_value'].iloc[0]
            discount_proportion = dr_row['discount_proportion'].iloc[0]
            total_inventory = dr_row['total_inventory'].iloc[0]
            average_bucket_size = dr_row['average_bucket_size'].iloc[0]
            footfall_sum = dr_row['footfall_sum'].iloc[0]
            gross_margin_mean = dr_row['gross_margin_mean'].iloc[0]

            # Target values
            current_value_bm_target = target_values_with_time_range[tr]['current_value_target']
            total_inventory_bm_target = target_values_with_time_range[tr]['total_inventory_target']
            footfall_sum_bm_target = target_values_with_time_range[tr]['footfall_sum_target']
            gross_margin_mean_bm_target = target_values_with_time_range[tr]['gross_margin_mean_target']

            # Aggregations
            dt['current_value'] = current_value
            dt['coupon_driven_sales'] = discount_proportion * 100
            dt['average_bucket_size'] = average_bucket_size
            dt['sales_per'] = round(current_value)
            dt['footfall_per'] = round(footfall_sum)
            dt['inventory_per'] = round(total_inventory)
            dt['gross_margin_per'] = round(gross_margin_mean)
            dt['current_value_bm_target'] = current_value_bm_target
            dt['total_inventory_bm_target'] = total_inventory_bm_target
            dt['footfall_sum_bm_target'] = footfall_sum_bm_target
            dt['gross_margin_mean_bm_target'] = gross_margin_mean_bm_target

            # Ecommerce fulfilment
            inventory_per = round(total_inventory * 100 / total_inventory_bm_target)
            ecommerce_fulfilment = (
                inventory_per + random.choice([-3, -2, -1, 1, 2, 3])
                if 4 <= inventory_per <= 96
                else inventory_per
            )
            dt['ecommerce_fulfilment'] = round(ecommerce_fulfilment)

            # Store score
            store_score = (dt['sales_per'] + dt['inventory_per'] + dt['footfall_per'] + dt['gross_margin_per']) / 4
            dt['store_score'] = round(store_score)

            # Gap vs. forecast
            gap_forecast_sales = current_value - current_value_bm_target
            gap_forecast_discount_proportion = (
                (discount_proportion - discount_proportion_bm) * 100 / discount_proportion_bm
            )
            gap_forecast_ecom_fulfilment = (
                (total_inventory - total_inventory_bm) * 100 / total_inventory_bm
            )
            gap_forecase_average_bucket_size = average_bucket_size - average_bucket_size_bm

            dt['gap_forecast_sales'] = round_off(gap_forecast_sales)
            dt['gap_forecast_discount_proportion'] = round_off(gap_forecast_discount_proportion)
            dt['gap_forecast_ecom_fulfilment'] = round_off(gap_forecast_ecom_fulfilment)
            dt['gap_forecase_average_bucket_size'] = round_off(gap_forecase_average_bucket_size)

            # Week-over-week metrics
            current_value_last = df_last['current_value'].iloc[0]
            discount_proportion_last = df_last['discount_proportion'].iloc[0]
            total_inventory_last = df_last['total_inventory'].iloc[0]
            average_bucket_size_last = df_last['average_bucket_size'].iloc[0]

            current_value_wow = (current_value - current_value_last) * 100 / max(current_value, current_value_last)
            discount_proportion_wow = (
                (discount_proportion - discount_proportion_last)
                * 100
                / max(discount_proportion, discount_proportion_last)
            )
            ecom_fulfilment_wow = (
                (total_inventory - total_inventory_last)
                * 100
                / max(total_inventory, total_inventory_last)
            )
            average_bucket_size_wow = (
                (average_bucket_size - average_bucket_size_last)
                * 100
                / max(average_bucket_size, average_bucket_size_last)
            )

            dt['current_value_wow'] = round_off(current_value_wow)
            dt['discount_proportion_wow'] = round_off(discount_proportion_wow)
            dt['ecom_fulfilment_wow'] = round_off(ecom_fulfilment_wow)
            dt['average_bucket_size_wow'] = round_off(average_bucket_size_wow)

            dt['current_week'] = current_week

            # Calculate the average of the four columns to get store_score
            dt['store_score'] = round((
                dt['sales_per']*100/current_value_bm_target + 
                dt['footfall_per']*100/footfall_sum_bm_target + 
                dt['inventory_per']*100/total_inventory_bm_target + 
                dt['gross_margin_per']*100/gross_margin_mean_bm_target
                ) / 4)

            # Calculate store_score_target as 100 minus the store_score
            dt['store_score_target'] = 100 - dt['store_score']

            final.append(dt)
        
    return process_and_generate(pd.DataFrame(final))


def fetch_master_id_date():
    query = "SELECT TOP 1 * FROM AnomalyDetectionBase WHERE Status='N';"
    with engine.connect() as connection:
        master_df = pd.read_sql(query, connection)
    try:
        master_id, date = master_df.Id[0], master_df.Date[0]
    except:
        return [None, None, None, None]
    
    query = f"SELECT TOP 1 * FROM [DATA-NEW-BM] WHERE MasterId={master_id};"
    with engine.connect() as connection:
        master_df = pd.read_sql(query, connection)
    week_number = master_df.WEEK_NUMBER[0]
    
    with engine.connect() as connection:
        query = f"SELECT * FROM [DATA-NEW-BM] WHERE [Date] <= '{date}';"
        filtered_df = pd.read_sql(query, connection)
    
    return [master_id, date, week_number, filtered_df]

def match_col_names(df_second_agg):
    values = [
        'store_code', 'time_range', 'Store score (Main KPIs)', 'Sales (Main KPIs)', 'Footfall (Main KPIs)', 'Utilization (Main KPIs)', 'Gross Margin (Main KPIs)', 'Daily Sales (Current value)', 'Coupon Driven Sales (%) (Current value)', 'Average Basket Size (ABS) (Current value)', 'Ecommerce fulfilment (%) (Current value)', 'Daily Sales (Gap. vs forecast)', 'Coupon Driven Sales (%) (Gap. vs forecast)', 'Ecommerce fulfilment (%) (Gap. vs forecast)', 'Average Basket Size (ABS) (Gap. vs forecast)', 'Daily Sales (WoW (%))', 'Coupon Driven Sales (%) (WoW (%))', 'Ecommerce fulfilment (%) (WoW (%))', 'Average Basket Size (ABS) (WoW (%))', 'Daily Sales (MoM (%))', 'Coupon Driven Sales (%) (MoM (%))', 'Ecommerce fulfilment (%) (MoM (%))', 'Average Basket Size (ABS) (MoM (%))', 'Daily Sales (YoY (%))', 'Coupon Driven Sales (%) (YoY (%))', 'Ecommerce fulfilment (%) (YoY (%))', 'Average Basket Size (ABS) (YoY (%))', 'current_value_bm_target', 'total_inventory_bm_target', 'footfall_sum_bm_target', 'gross_margin_mean_bm_target', 'store_score_target', 'WEEK_NUMBER'
    ]
    keys = [
        'store_code', 'time_range', 'store_score', 'sales_per', 'footfall_per', 'inventory_per', 'gross_margin_per', 'current_value', 'coupon_driven_sales', 'average_bucket_size', 'ecommerce_fulfilment', 'gap_forecast_sales', 'gap_forecast_discount_proportion', 'gap_forecast_ecom_fulfilment', 'gap_forecase_average_bucket_size', 'current_value_wow', 'discount_proportion_wow', 'ecom_fulfilment_wow', 'average_bucket_size_wow', 'current_value_mom', 'discount_proportion_mom', 'ecom_fulfilment_mom', 'average_bucket_size_mom', 'current_value_yoy', 'discount_proportion_yoy', 'ecom_fulfilment_yoy', 'average_bucket_size_yoy', 'current_value_bm_target', 'total_inventory_bm_target', 'footfall_sum_bm_target', 'gross_margin_mean_bm_target', 'store_score_target', 'current_week'
    ]

    d = {}
    for k, v in zip(keys, values):
        d[k] = v

    final_col = []
    for k in df_second_agg.columns:
        final_col.append(d[k])

    df_second_agg.columns = final_col
    
    return df_second_agg


def final_data(df_second_agg, week_number, date):
    temp_data = {}
    final_col = list(df_second_agg.columns)
    for col in final_col:
        if col != 'WEEK_NUMBER':
            temp_data[col] = data_dict[col]
    final_df = pd.concat([df_second_agg, pd.DataFrame(temp_data)], ignore_index=True)
    final_df['Date'] = [date]*len(final_df)
    final_df['WEEK_NUMBER'] = [week_number]*len(final_df)
    
    return final_df

def generate_insights_main():
    master_id, date, week_number, filtered_df = fetch_master_id_date()
    if master_id:
        df_first_agg = first_level_agg(filtered_df, week_number)
        df_second_agg = generate_aggregations(df_first_agg, week_number)
        df_second_agg = match_col_names(df_second_agg)
        final_df = final_data(df_second_agg, week_number, date)
        create_agg_data(final_df)
        update_status(master_id, 'Y')
        print(' updations completed successfully')

        return final_df
    else:
        print('No updations made')
        
    return None


