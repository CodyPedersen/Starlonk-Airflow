FROM apache/airflow:2.5.1
COPY requirements.txt /
RUN pip install --no-cache-dir -r /requirements.txt

# Utilizes gitsync, so there's no need to bundle dags with the image