#!/bin/bash

kubectl delete statefulset airflow-postgresql
kubectl delete statefulset airflow-redis
kubectl delete statefulset airflow-worker

kubectl delete deploy airflow-scheduler
kubectl delete deploy airflow-statsd
kubectl delete deploy airflow-triggerer
kubectl delete deploy airflow-webserver

kubectl delete pvc data-airflow-postgresql-0
kubectl delete pvc logs-airflow-worker-0
kubectl delete pvc redis-db-airflow-redis-0

kubectl delete pv airflow-pg-vol
kubectl delete pv airflow-worker-vol
kubectl delete pv redis-vol

kubectl delete job airflow-create-user
kubectl delete job airflow-run-airflow-migrations

kubectl delete -f ~/Desktop/airflow_kube.yml

