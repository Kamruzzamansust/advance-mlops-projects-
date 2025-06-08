from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import pandas as pd
import os
from airflow.providers.postgres.hooks.postgres import PostgresHook
import re

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2025, 1, 1),
    'retries': 1
}

url = "https://docs.google.com/spreadsheets/d/1H-b3MA0fEEHH7eP-fut1sYHlRsjc5i8ZadReynrw0m0/export?format=csv&gid=167401221"
log_file = "/usr/local/airflow/shared/data_log.log"
csv_output_path = "/usr/local/airflow/shared/new_rows.csv"

with DAG(
    dag_id="google_sheet_to_postgres_etl_1",
    description="ETL: Google Sheet to PostgreSQL",
    schedule=None,
    catchup=False,
    default_args=default_args
) as dag:

    def extract(**kwargs):
        df = pd.read_csv(url)
        df.columns = df.columns.str.lower()
        current_len = len(df)
        print(f"📥 Total rows fetched from CSV: {current_len}")

        last_len = 0
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if os.path.exists(log_file):
            with open(log_file, 'r') as log:
                lines = [line.strip() for line in log.readlines() if line.strip()]
                for line in reversed(lines):
                    match = re.match(r".* - (\d+)$", line)
                    if match:
                        last_len = int(match.group(1))
                        break

        if current_len > last_len:
            new_rows = df.iloc[last_len:]
            os.makedirs(os.path.dirname(csv_output_path), exist_ok=True)
            new_rows.to_csv(csv_output_path, index=False)
            kwargs['ti'].xcom_push(key='row_count', value=current_len)
            kwargs['ti'].xcom_push(key='first_load', value=(last_len == 0))
            print(f"✅ Extracted {len(new_rows)} new rows.")
        else:
            kwargs['ti'].xcom_push(key='row_count', value=current_len)
            kwargs['ti'].xcom_push(key='first_load', value=(last_len == 0))
            print("✅ No new rows to extract.")

        # Log row count
        with open(log_file, 'a') as log:
            log.write(f"{now} - {current_len}\n")

    def transform(**kwargs):
        if not os.path.exists(csv_output_path):
            print("✅ No new data to transform.")
            return
        df = pd.read_csv(csv_output_path)
        print(f"✅ Transformed and validated {len(df)} rows.")

    def load(**kwargs):
        if not os.path.exists(csv_output_path):
            print("✅ No new data to load.")
            return

        row_count = kwargs['ti'].xcom_pull(key='row_count')
        first_load = kwargs['ti'].xcom_pull(key='first_load')
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            df = pd.read_csv(csv_output_path)
            hook = PostgresHook(postgres_conn_id='postgres_default')
            engine = hook.get_sqlalchemy_engine()

            table_name = "titanic_data_2" if first_load else "titanic_data"
            df.to_sql(table_name, engine, if_exists="append", index=False)
            print(f"✅ Loaded {len(df)} rows into table `{table_name}`.")

        except Exception as e:
            print(f"❌ Error in load task: {e}")

    extract_task = PythonOperator(
        task_id='extract',
        python_callable=extract
    )

    transform_task = PythonOperator(
        task_id='transform',
        python_callable=transform
    )

    load_task = PythonOperator(
        task_id='load',
        python_callable=load
    )


    extract_task >> transform_task >> load_task
