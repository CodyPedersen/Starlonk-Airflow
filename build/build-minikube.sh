#!/bin/bash

## Run from root airflow directory ##

minikube start --memory='6g' --cpus='4'
#minikube mount /Users/enso/.mnt/airflow-worker-vol:/mnt/pv/airflow-worker-vol &

# Apply requisite secrets
kubectl apply -f ./deployment/secrets/gitsync.yml
kubectl apply -f ./deployment/secrets/postgres-creds.yml

# Deploy airflow
kubectl apply -f ./deployment/airflow_deploy.yml

# Post-build instructions
    # run `minikube service airflow-webserver`