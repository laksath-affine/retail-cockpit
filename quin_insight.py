# from insight_df_summary import insight_df_summary
# from insight import insight
# import streamlit as st
import os
import pyodbc as odbc
import pyodbc
import pandas as pd
import openai
from dotenv import load_dotenv
load_dotenv()
from openai import AzureOpenAI
import ast 



connection_string = "Driver={ODBC Driver 18 for SQL Server};Server=tcp:quickazuredemo.database.windows.net,1433;Database=quickinsight;Uid=bhaskar;Pwd=Affine@123;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
conn = odbc.connect(connection_string)
cursor = conn.cursor()


client = AzureOpenAI(
    azure_endpoint="https://aipractices.openai.azure.com/",
    api_version="2024-02-01",
    api_key="e5990e77abe04e74b6de34cdb4d1cce4")


model_name = 'gpt-4o-05-13'
# print(client)

def insight(pre_prompt_gpt):
    """
    This function is called from main function to get the sql query.
    Generates the sql query to get releveant data with respect to question.

    Args:
        pre_prompt_gpt (string): prompt for GPT model.

    Returns:
        dict: The dictionary containing title of insight as key and sql query as values
    """
    # add instruction in the prompt
    prompt = pre_prompt_gpt
        
    # Generate sql query using the OpenAI GPT-4 model.

    completion = client.chat.completions.create(
            model=model_name,
            temperature=0.1,
            messages=[{'role': 'system', 'content': 'You are a business analytics insight generater'},
                    {"role": "user", "content": prompt}])

    output = completion.choices[0].message.content

    if output.find('{') != -1:
        output_dict_str = output[output.find('{'):output.rfind('}')+1]
        output_dic = ast.literal_eval(output_dict_str)
        return output_dic
    else:
        return {}



def insight_df_summary(insight_title, df_insight, question_prompt ):
    """
    Gives natural language insight and python code for better visualization of this insight.

    Args:
        insight_title (str): title of the insight.
        df_insight (dataframe): relevant filterd out database with respect to question.
        show_code (bool): Boolean value to see the python code.
        explain_code (bool): Boolean value to get the explanation of the code.
        question_prompt (str): question asked by user.

    Returns:
         1.The natural language insights with your opinion
         2.Python code for plot

    """
    # define prompt to get the required output in expected format.
    prompt = f"""
    From following dataframe create textual summary and insights based in the user question.
    
    User question: {question_prompt}
    Dataframe:  {df_insight}

    Answer in the below format:

    Insights:  '(Insights)'
    """
    # Generate insights and python code using the OpenAI GPT-4 model.

    completion = client.chat.completions.create(
            model=model_name,
            temperature=0.1,
            messages=[{'role': 'system', 'content': 'You are a text summarizer'},
                    {"role": "user", "content": prompt+df_insight.to_csv(index=False)}])

    output = completion.choices[0].message.content


    output_summary = output[:output.find('{')]
    return output_summary



def quin_description(user_query):
    pre_prompt = ''
    try:
        selected_tables = ['[dbo].[AnomalyDetectionBase]', '[dbo].[DATA-NEW-BM]', '[dbo].[AnomalyDetectionBase]']
        for table_idx, table in enumerate(selected_tables):
            table_query = f'SELECT column_name AS "column_name", data_type FROM INFORMATION_SCHEMA.COLUMNS WHERE LOWER(table_name) = LOWER(\'{table}\')'
            column_df = pd.read_sql(table_query, conn)
            five_rows_query = f'select top 3 * from {table}'
            dataframe_five_rows = pd.read_sql(five_rows_query, conn)
            each_table = f"""

            Table: {str(table_idx)}
                Table name : {table}

                Table properties: 
                {column_df.to_csv(index=False)}

                Sample records:
                {dataframe_five_rows.to_csv(index=False)}
                
            -------------------
            """

            pre_prompt = pre_prompt + each_table
        question_prompt = user_query
        sample_res = {'insight_name': '''sql query'''}
        pre_prompt_gpt = f"""You are an expert in SQL query generation.

        You are given with a Schema which contains tables, their properties and sample data

        From the given Schema generate insight and SQL query based on the {question_prompt}.
        If the question is not relevant to the Schema provided give output as "Irrelevant question"
        Give output in the form of dictionary where key will be the name of the insight and value will be the SQL query to fetch data from the Azure SQL database.
        Insight is a one liner on what that SQL query data would represent
        Use MSSQL - Azure SQL dialect when framing SQL query
        Use TOP instead of LIMIT
        Give proper name to the column in the SQL query. Give the query in triple quotes. Do NOT give google bigquery.
        There has to be only one sql query.

        Schema:

        {pre_prompt}


        Answer in the form of a dictionary key is insight and value is SQL query.

        Sample response:

        {str(sample_res)}


        """
        output_dic = insight(pre_prompt_gpt)
        if output_dic and isinstance(output_dic, dict):
            generated_sql_query = ''
            for k, v in output_dic.items():
                v = v.replace('quickinsight.', '')
                v = str(v).strip().lstrip("```sql").rstrip("```").strip()
                generated_sql_query = v
                query_job = cursor.execute(v)

                insight_fetch = query_job.fetchall()
                insight_fetch = [
                    tuple(i) for i in insight_fetch]

                insight_df = pd.DataFrame(insight_fetch)

                insight_df.columns = [x[0] for x in query_job.description]

                if not insight_df.empty:
                    try:
                        textual_insights = insight_df_summary(k, insight_df, question_prompt)
                        return generated_sql_query, textual_insights, insight_df
                    except openai.error.InvalidRequestError as r:
                        print('Relevant data exceeded token limit')
                    except Exception as e:
                        print('Something went wrong')
    except Exception as e:
        print(e)

    return None, None, None



# user_query = "What is the value of the highest sale on 2024-02-05?"
# generated_sql_query, textual_insights, insight_df = quin_description(user_query=user_query)
# print("generated_sql_query:  ", generated_sql_query)
# print("textual_insights:  ", textual_insights)
# print("insight_df:  ", insight_df.head())
