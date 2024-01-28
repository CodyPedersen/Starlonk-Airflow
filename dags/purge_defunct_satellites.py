# pylint: disable=pointless-statement, pointless-string-statement
"""
Purge all Satellites with epoch < some value
"""
import logging
import datetime

import pendulum
from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator

from utils.database import SessionLocal
from utils.models import Satellite

log = logging.getLogger(__name__)

# Globals
DELETE_DELTA_D = 7

with DAG(
    dag_id='purge_defunct_satellites',
    schedule='@daily',
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False
) as dag:

    def purge_satellites(ti):
        """Purge all satellites from prior to cutoff"""
        with SessionLocal() as db:
            utc_cutoff = (
                datetime.datetime.utcnow() - datetime.timedelta(days=DELETE_DELTA_D)
            ).isoformat()
            logging.info(f"deleting all satellites with epoch < {utc_cutoff}")

            # Find satellites
            satellites = db.query(Satellite).filter(Satellite.epoch < utc_cutoff).all()
            deletes = [satellite.to_dict()["satellite_name"] for satellite in satellites]
            logging.info(f"Satellites to be deleted: {deletes}")

            # Delete satellites
            num_deleted = db.query(Satellite).filter(Satellite.epoch < utc_cutoff).delete()
            logging.info(f'deleted_objects: {num_deleted}')

            db.commit()

    purge_satellites_task = PythonOperator(
        task_id='purge_satellites_task',
        python_callable=purge_satellites
    )

    done = EmptyOperator(
        task_id= 'done',
    )

    purge_satellites_task >> done # Delete execution path
