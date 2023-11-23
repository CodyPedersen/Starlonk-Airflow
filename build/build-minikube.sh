#!/bin/bash

## Run from root airflow directory ##


# mount string for docker driver (M1)
# Must chmod the bitnami directory sudo chown -R 1001:1001 /<mount folder>
minikube start --mount-string='/Users/enso/.bitnami/postgresql/data:/bitnami/postgresql/data' --memory='6g' --cpus='4'
kubectl apply -f ./deployment/secrets/gitsync.yml
kubectl apply -f ./deployment/secrets/postgres-creds.yml
kubectl apply -f ./deployment/airflow_deploy.yml