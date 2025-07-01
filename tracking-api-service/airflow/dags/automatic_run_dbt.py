from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'hosi04',
    'retry_delay': timedelta(minutes=5),
    'retries': 2
}

with DAG(
    dag_id='dbt_run_checkout_pipeline',
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval='*/15 * * * *',  # mỗi 15 phút
    catchup=False
) as dag:

    dbt_run = BashOperator(
        task_id='auto_run_dbt',
        bash_command='cd /opt/airflow/dbt && dbt run --profiles-dir /opt/airflow/.dbt/',
    )

dbt_run
