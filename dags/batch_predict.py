# pylint: disable=pointless-statement, pointless-string-statement
"""
Bulk prediction of Starlink satellite locations from t=(now + n, now + 2n) by interval
    - To do:
        - Pre-generate time series and check if data has been calculated for that time series. If so, 'done'
"""
import datetime
import logging

import pendulum
from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
from skyfield.api import load, EarthSatellite

from utils.prediction import convert_to_tle, round_time, deNaN
from utils.models import Satellite, Prediction
from utils.database import SessionLocal

log = logging.getLogger(__name__)

# Batch Predict Globals
TIME_INTERVAL_S = 60
TOTAL_TIME_DELTA_M = 10

with DAG(
    dag_id='batch_predict',
    schedule='*/10 * * * *',
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False
) as dag:

    # Task definitions
    def pull_satellites(ti):
        """Grab satellites from the DB"""
        with SessionLocal() as db:

            # Pull satellites
            satellites = db.query(Satellite).all()
            satellite_dicts = [sat.to_dict() for sat in satellites]

            ti.xcom_push(key='satellites', value=satellite_dicts)

    pull_satellites_task = PythonOperator(
        task_id='pull_satellites_task',
        python_callable=pull_satellites
    )


    def generate_tles(ti):
        """Generate TLE from satellite data"""
        satellites = ti.xcom_pull(task_ids='pull_satellites_task', key='satellites')
        satellite_tles = []

        logging.info("Generating TLEs")
        for satellite in satellites:
            s, t = convert_to_tle(**satellite)
            satellite_tles.append((satellite['satellite_name'], satellite['satellite_id'], s, t))

        ti.xcom_push(key='satellite_tles', value=satellite_tles)

    generate_tles_task = PythonOperator(
        task_id='generate_tles_task',
        python_callable=generate_tles
    )


    def generate_predictions_push(ti):
        """Calculate/push satellite predictions for ("now" + n + 1, now + 2n), interval=60s"""
        with SessionLocal() as db:

            tle_list = ti.xcom_pull(task_ids='generate_tles_task', key='satellite_tles')
            logging.info(tle_list)

            # Initialize time-series data
            now = round_time(None, 600) # Round to most recent 10 minute mark
            start_time = prediction_epoch = now + datetime.timedelta(minutes=TOTAL_TIME_DELTA_M)
            end_time = start_time + datetime.timedelta(minutes=TOTAL_TIME_DELTA_M - 1)
            interval = datetime.timedelta(seconds=TIME_INTERVAL_S)

            while prediction_epoch <= end_time:
                logging.info(f'Calculating prediction epoch {prediction_epoch}')

                # Iterate over all satellites for prediction epoch
                satellite_epoch = []
                for tle in tle_list:
                    name, sat_id, s,t = tle

                    ts = load.timescale()
                    sky_sat =  EarthSatellite(s, t, name, ts)

                    t = ts.utc(
                        int(prediction_epoch.year),
                        int(prediction_epoch.month), 
                        int(prediction_epoch.day),
                        int(prediction_epoch.hour),
                        int(prediction_epoch.minute),
                        int(prediction_epoch.second)
                    )

                    # Calculate coords & data points
                    geocentric_coords = sky_sat.at(t)
                    lat = geocentric_coords.subpoint().latitude
                    lon = geocentric_coords.subpoint().longitude
                    elevation_km = geocentric_coords.subpoint().elevation.km
                    geo_pos_km = geocentric_coords.position.km.tolist()
                    velocity_m_per_s = geocentric_coords.velocity.m_per_s

                    prediction = {
                        "satellite_name" : name,
                        "satellite_id" : sat_id,
                        "epoch" : prediction_epoch,
                        "elevation" : deNaN(elevation_km),
                        "geocentric_coords" : [deNaN(coord) for coord in geo_pos_km],
                        "geo_velocity_m_per_s": [
                            deNaN(component) 
                            for component in velocity_m_per_s
                        ],
                        "latitude" : deNaN(lat.degrees),
                        "longitude": deNaN(lon.degrees) 
                    }

                    satellite_epoch.append(Prediction(**prediction))

                # Bulk push all satellites for this epoch
                try:
                    db.bulk_save_objects(satellite_epoch)
                    db.commit()
                except Exception as e:
                    logging.info(f"Failed to satellites for {prediction_epoch} prediction epoch - {repr(e)}")

                prediction_epoch = prediction_epoch + interval

    generate_predictions_task = PythonOperator(
        task_id='generate_predictions_task',
        python_callable=generate_predictions_push
    )

    def delete_old_predictions(ti):
        """Delete all satellites earlier than prediction era"""

        with SessionLocal() as db:
            f_now = datetime.datetime.utcnow()
            now = datetime.datetime(f_now.year, f_now.month, f_now.day, f_now.hour, f_now.minute, f_now.second)

            logging.info(f"DELETE FROM prediction WHERE epoch < '{now}'")

            deletes = db.query(Prediction).filter(Prediction.epoch < now).delete()

            logging.info(f"Deleted {deletes} records")
            db.commit()

    delete_old_predictions_task = PythonOperator(
        task_id='delete_old_predictions_task',
        python_callable=delete_old_predictions
    )

    done = EmptyOperator(
        task_id= 'done',
    )

    (
        pull_satellites_task >>
        generate_tles_task >>
        generate_predictions_task >>
        delete_old_predictions_task >>
        done
    )
