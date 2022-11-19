"""
Pull starlink satellite data from NORAD
"""
from airflow import DAG
from airflow.decorators import task
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import BranchPythonOperator, PythonOperator

from database import SessionLocal

from models import Satellite, Process

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

    ''' Task Definitions '''
    def check_if_updated(ti):
        """Placeholder - Check if NORAD Satellite data has been updated"""

        # API call to pull data from NORAD Starlonk dataset
        satellites = {}

        # Placeholder
        if False:
            return ['done']

        # Else
        return ['started_event_task']

    check_if_updated_task = BranchPythonOperator(
    task_id='check_if_updated_task',
    python_callable=check_if_updated
    )

    def process_event(ti, **context):
        """Upsert Process - modify status portion later"""
        db = SessionLocal()

        pid = context['dag_run'].run_id

        print("pushing process to db")
        process_data = {
            "id" : pid
        }
        logging.info(f'pid: {pid}')
        # Query processes on pid
        exists = db.query(Process).filter(Process.id == pid)

        # Update value if exists, else create
        if exists.first():
            process_obj = exists.one()
            process_obj.status = 'completed'
            db.commit()
        else:
            process = Process(**process_data)
            process.status = 'started'
            db.add(process)
        
        db.commit()
        logging.info("pushed process to db")

        db.close()

    started_event_task = PythonOperator(
        task_id='started_event_task',
        python_callable=process_event
    )

    completed_event_task = PythonOperator(
        task_id='completed_event_task',
        python_callable=process_event
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

        return ['format_satellite_data']


    pull_satellite_data_task = PythonOperator(
        task_id='pull_satellite_data_task',
        python_callable=pull_satellite_data
    )


    def format_satellite_data(ti):
        satellites = []

        satellite_list = ti.xcom_pull(task_ids=['pull_satellite_data_task'], key='raw_satellite_data')[0]
        logging.info(satellite_list)

        # Change satellite keys to a more readable format
        for raw_satellite in satellite_list:

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


    def push_to_postgres(ti):
        """ Push Satellite Data to Postgres """
        db = SessionLocal()

        satellite_data = ti.xcom_pull(task_ids=['format_satellite_data_task'], key='satellites')[0]

        satellites_to_add = []
        updated_satellites = []

        for satellite_json in satellite_data:

            updated = False
            satellite_query = db.query(Satellite).filter(Satellite.satellite_id == satellite_json['satellite_id'])
            updated = satellite_query.update(satellite_json)
            db.commit()

            if not updated:
                satellite = Satellite(**satellite_json)
                satellites_to_add.append(satellite)

            ''' Push updated satellites for logging if exists '''
            sat_obj_exists = satellite_query.first()
            if sat_obj_exists:
                sat_dict = sat_obj_exists.to_dict()
                updated_satellites.append(sat_dict)

        # Log added/updated satellites
        added_satellites_json = [sat.to_dict() for sat in satellites_to_add]
        logging.info(f'added: {added_satellites_json}')
        logging.info(f'updated: {updated_satellites}')

        db.add_all(satellites_to_add)
        db.commit()
        db.close()


    push_to_postgres_task = PythonOperator(
        task_id='push_to_postgres_task',
        python_callable=push_to_postgres
    )
    
    done = EmptyOperator(
        task_id= 'done',
    )


    (check_if_updated_task >> started_event_task >> pull_satellite_data_task >> format_satellite_data_task >> push_to_postgres_task >> completed_event_task >> done)
    check_if_updated_task >> done