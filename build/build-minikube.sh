#!/bin/bash

######################
### Prerequisites ####
######################

# 1. Deploy postgres db to kube (starlonk api)
# 2. Ensure connection details are correct per secrets below
# 3. minikube mount host:dest for persistent data

######################
### K8s Initialize ###
######################

# Run from root airflow directory
minikube start --memory='6g' --cpus='4'

# Apply requisite secrets
kubectl apply -f ./deployment/secrets/gitsync.yml
kubectl apply -f ./deployment/secrets/postgres-creds.yml

# Deploy airflow monolith file
kubectl apply -f ./deployment/airflow_deploy.yml

# Deploy supplementary resources
kubectl apply -f ./deployment/db/postgres_db.yml

######################
### Post-Build In. ###
######################

 # run `minikube service airflow-webserver`