"""
Pull starlink satellite data from NORAD
"""
from airflow import DAG
from airflow.decorators import task
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import BranchPythonOperator, PythonOperator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import logging
import requests
import pendulum
import json
import os

log = logging.getLogger(__name__)

with DAG(
    dag_id='norad_ingest',
    schedule='*/5 * * * *',
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False
) as dag:

    os.environ["no_proxy"]="*" # Dumb workaround to avoid mac sigsegv

    ''' Database Setup'''
    load_dotenv()
    host = os.getenv('DB_HOST')
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    port = os.getenv('DB_PORT')
    database = os.getenv('DB_NAME')

    logging.info(f'postgresql://{user}:{password}@{host}:{port}/{database}')
    DATABASE_CONNECTION_URI = f'postgresql://{user}:{password}@{host}:{port}/{database}'
    
    # SQL Alchemy
    engine = create_engine(DATABASE_CONNECTION_URI)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


    ''' Task Definitions '''
    def check_if_updated(ti):
        """Placeholder - Check if NORAD Satellite data has been updated"""

        # API call to pull data from NORAD Starlonk dataset
        satellites = {}

        if False:
            return ['done']

        # Else
        return ['pull_satellite_data_task']

    check_if_updated_task = BranchPythonOperator(
    task_id='check_if_updated_task',
    python_callable=check_if_updated
    )


    def pull_satellite_data(ti):
        """Pull Starlink satellite data raw from NORAD"""

        # Pull STARLINK satellites
        starlink = 'https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=json-pretty'
        
        try:
            logging.info("Pulling data from NORAD")
            satellite_response = requests.get(url=starlink)
            logging.info(f"satellite_response: {satellite_response}")
        except Exception as e:
            logging.error(f"Unable to complete request: {repr(e)}")

        try:
            logging.info("Parsing data from NORAD")
            raw_data = satellite_response.json()
        except Exception as e:
            logging.error(f"Unable to parse data: {repr(e)}")

        ti.xcom_push(key='raw_satellite_data', value=raw_data)

        return ['push_to_postgres_task']


    pull_satellite_data_task = PythonOperator(
        task_id='pull_satellite_data_task',
        python_callable=pull_satellite_data
    )


    def format_satellite_data(ti):
        satellites = []

        satellite_json = ti.xcom_pull(task_ids=['pull_satellite_data'], key='raw_satellite_data')

        # Change satellite keys to a more readable format
        for raw_satellite in satellite_json:

            # Modify keys to Satellite model standards
            satellite = {
                key.replace('OBJECT', 'satellite').lower():value for (key,value) in raw_satellite.items()
            }
            del satellite['mean_motion_ddot']
            satellite['source'] = 'STARLINK'

            # Push `clean` satellite to `cleaned_data`
            satellites.append(satellite)

        ti.xcom_push(key='satellites', value=satellites)

    
    format_satellite_data_task = PythonOperator(
        task_id='format_satellite_data_task',
        python_callable=format_satellite_data
    )

    def push_to_postgres():
        logging.info('pushing to pg')


    push_to_postgres_task = PythonOperator(
        task_id='push_to_postgres_task',
        python_callable=push_to_postgres
    )
    
    done = EmptyOperator(
        task_id= 'done',
    )


    (check_if_updated_task >> pull_satellite_data_task >> format_satellite_data_task >> push_to_postgres_task >> done)
    check_if_updated_task >> done