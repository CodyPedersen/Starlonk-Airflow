FROM apache/airflow:2.5.1
COPY ./requirements.txt /
WORKDIR /
RUN pip install -r requirements.txt