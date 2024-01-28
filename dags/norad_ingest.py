# pylint: disable=pointless-statement, pointless-string-statement
"""
Pull starlink satellite data from NORAD
"""
import os
import logging

import pendulum
import requests
from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import BranchPythonOperator, PythonOperator

from utils.database import SessionLocal
from utils.models import Satellite, Process

log = logging.getLogger(__name__)


with DAG(
    dag_id='norad_ingest',
    schedule='*/20 * * * *',
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False
) as dag:

    os.environ["no_proxy"]="*" # Dumb workaround to avoid mac sigsegv

    def check_if_updated(ti):
        """Placeholder - Check if NORAD Satellite data has been updated"""
        # if False:
        #     return ['done']
        return ['started_event_task', 'pull_satellite_data_task']

    check_if_updated_task = BranchPythonOperator(
        task_id='check_if_updated_task',
        python_callable=check_if_updated
    )

    def process_event(ti, **context):
        """Upsert Process - modify status portion later"""
        with SessionLocal() as db:

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
            satellite_response = requests.get(url=starlink, timeout=None)

            if satellite_response.status_code != 200:
                raise Exception("NORAD status code was not 200")

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
        """Reformat satellite data fields w/ friendlier keys"""
        satellites = []

        satellite_list = ti.xcom_pull(task_ids='pull_satellite_data_task', key='raw_satellite_data')
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
        with SessionLocal() as db:

            satellite_data = ti.xcom_pull(task_ids='format_satellite_data_task', key='satellites')

            # Delete to avoid time cost
            db.query(Satellite).delete()

            satellite_merge_list = [
                Satellite(**satellite_json)
                for satellite_json in satellite_data
            ]
            db.add_all(satellite_merge_list)

            # Log added/updated satellites
            logging.info(f'Upsert of {satellite_data}')
            db.commit()

        return ['completed_event_task', 'done']

    push_to_postgres_task = PythonOperator(
        task_id='push_to_postgres_task',
        python_callable=push_to_postgres
    )
    
    done = EmptyOperator(
        task_id= 'done',
    )

    ''' Full NORAD ingest execution path '''
    (
        check_if_updated_task >>
        pull_satellite_data_task >>
        format_satellite_data_task >>
        push_to_postgres_task >>
        done
    )

    ''' Short-circuit execution path '''
    check_if_updated_task >> done

    ''' Generate start event tasks '''
    check_if_updated_task >> started_event_task
    push_to_postgres_task >> completed_event_task
