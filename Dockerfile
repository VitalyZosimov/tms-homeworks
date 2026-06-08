FROM apache/airflow:2.10.5-python3.11

USER root
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
USER airflow

COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

COPY ./dags /opt/airflow/dags

ENV AIRFLOW__CORE__LOAD_EXAMPLES=False