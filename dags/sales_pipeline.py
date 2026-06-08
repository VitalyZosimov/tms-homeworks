import logging
from datetime import datetime
from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.operators.python import PythonOperator
from airflow.operators.email import EmailOperator
from airflow.models import Variable
from airflow.exceptions import AirflowFailException

# Получаем run_id
RUN_ID = "{{ ds_nodash }}"

# Аргументы по умолчанию
default_args = {
		'owner': 'data_engineer',
		'depends_on_past': False,
		'start_date': datetime(2024, 1, 1),
		'email_on_failure': False,
		'email_on_retry': False,
		'retries': 1,
}

# Определение DAG
with DAG(
		dag_id='sales_pipeline',
		default_args=default_args,
		description='Генерация данных, расчет статистики и отправка email',
		schedule_interval='@daily',
		catchup=False,
		tags=['sales', 'stats'],
) as dag:

		create_source_table = PostgresOperator(
				task_id='create_source_table',
				postgres_conn_id='postgres_default',
				sql="""
				CREATE SCHEMA IF NOT EXISTS raw;
				CREATE TABLE IF NOT EXISTS raw.lesson37_source_sales (
						run_id TEXT NOT NULL,
						order_id TEXT NOT NULL,
						amount NUMERIC(10,2) NOT NULL,
						created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
						PRIMARY KEY (run_id, order_id)
				);
				"""
		)

		generate_data = PostgresOperator(
				task_id='generate_data',
				postgres_conn_id='postgres_default',
				sql="""
				INSERT INTO raw.lesson37_source_sales (run_id, order_id, amount)
				SELECT
						%(run_id)s,
						'ord_' || gs::text,
						round((random() * 90 + 10)::numeric, 2)
				FROM generate_series(1, 20) gs
				ON CONFLICT (run_id, order_id) DO NOTHING;
				""",
				parameters={"run_id": RUN_ID},
		)

		def calculate_statistics(**context):
				run_id = context['params']['run_id']
				
				hook = PostgresHook(postgres_conn_id='postgres_default')
				sql = """
				SELECT 
						COUNT(*) as rows_count,
						SUM(amount) as total_amount,
						MIN(amount) as min_amount,
						MAX(amount) as max_amount,
						AVG(amount) as avg_amount
				FROM raw.lesson37_source_sales
				WHERE run_id = %s
				"""
				
				result = hook.get_first(sql, parameters=[run_id])
				
				if not result:
						raise AirflowFailException(f"Нет данных для run_id = {run_id}")
						
				rows_count, total_amount, min_amount, max_amount, avg_amount = result
				
				stats = {
						'run_id': run_id,
						'rows_count': rows_count,
						'total_amount': float(total_amount),
						'min_amount': float(min_amount),
						'max_amount': float(max_amount),
						'avg_amount': round(float(avg_amount), 2),
				}
				
				logging.info("=" * 60)
				logging.info(f"Статистика для run)id: {run_id}")
				logging.info(f"   • Количество строк: {stats['rows_count']}")
				logging.info(f"   • Общая сумма: {stats['total_amount']}")
				logging.info(f"   • Минимальная сумма: {stats['min_amount']}")
				logging.info(f"   • Максимальная сумма: {stats['max_amount']}")
				logging.info(f"   • Средняя сумма: {stats['avg_amount']}")
				logging.info("=" * 60)
				
				context['ti'].xcom_push(key='sales_stats', value=stats)
				
				return stats

		calculate_stats = PythonOperator(
				task_id='calculate_statistics',
				python_callable=calculate_statistics,
				params={"run_id": RUN_ID},
		)

		create_stats_table = PostgresOperator(
				task_id='create_stats_table',
				postgres_conn_id='postgres_default',
				sql="""
				CREATE SCHEMA IF NOT EXISTS mart;
				CREATE TABLE IF NOT EXISTS mart.lesson37_sales_stats (
						run_id TEXT PRIMARY KEY,
						rows_count INTEGER NOT NULL,
						total_amount NUMERIC(12,2) NOT NULL,
						min_amount NUMERIC(10,2) NOT NULL,
						max_amount NUMERIC(10,2) NOT NULL,
						avg_amount NUMERIC(10,2) NOT NULL,
						created_at TIMESTAMPTZ NOT NULL DEFAULT now()
				);
				"""
		)

		insert_stats = PostgresOperator(
				task_id='insert_stats',
				postgres_conn_id='postgres_default',
				sql="""
				INSERT INTO mart.lesson37_sales_stats 
						(run_id, rows_count, total_amount, min_amount, max_amount, avg_amount)
				VALUES (
						%(run_id)s,
						%(rows_count)s,
						%(total_amount)s,
						%(min_amount)s,
						%(max_amount)s,
						%(avg_amount)s
				)
				ON CONFLICT (run_id) DO UPDATE SET
						rows_count = EXCLUDED.rows_count,
						total_amount = EXCLUDED.total_amount,
						min_amount = EXCLUDED.min_amount,
						max_amount = EXCLUDED.max_amount,
						avg_amount = EXCLUDED.avg_amount,
						created_at = now();
				""",
				parameters={
						"run_id": RUN_ID,
						"rows_count": "{{ ti.xcom_pull(task_ids='calculate_statistics', key='sales_stats')['rows_count'] }}",
						"total_amount": "{{ ti.xcom_pull(task_ids='calculate_statistics', key='sales_stats')['total_amount'] }}",
						"min_amount": "{{ ti.xcom_pull(task_ids='calculate_statistics', key='sales_stats')['min_amount'] }}",
						"max_amount": "{{ ti.xcom_pull(task_ids='calculate_statistics', key='sales_stats')['max_amount'] }}",
						"avg_amount": "{{ ti.xcom_pull(task_ids='calculate_statistics', key='sales_stats')['avg_amount'] }}",
				}
		)

		# Получаем email из переменной Airflow (можно менять в UI)
		EMAIL_RECIPIENT = Variable.get("EMAIL_RECIPIENT", default_var="admin@example.com")
		
		send_email = EmailOperator(
				task_id='send_email',
				to=EMAIL_RECIPIENT,
				subject="Airflow ETL: статистика продаж",
				html_content="""
				<h2>Отчет о выполнении ETL пайплайна</h2>
				<p><strong>Run ID:</strong> {{ ti.xcom_pull(task_ids='calculate_statistics', key='sales_stats')['run_id'] }}</p>
				
				<h3>Статистика по продажам:</h3>
				<ul>
						<li><strong>Количество строк:</strong> {{ ti.xcom_pull(task_ids='calculate_statistics', key='sales_stats')['rows_count'] }}</li>
						<li><strong>Общая сумма:</strong> {{ ti.xcom_pull(task_ids='calculate_statistics', key='sales_stats')['total_amount'] }}</li>
						<li><strong>Минимальная сумма:</strong> {{ ti.xcom_pull(task_ids='calculate_statistics', key='sales_stats')['min_amount'] }}</li>
						<li><strong>Максимальная сумма:</strong> {{ ti.xcom_pull(task_ids='calculate_statistics', key='sales_stats')['max_amount'] }}</li>
						<li><strong>Средняя сумма:</strong> {{ ti.xcom_pull(task_ids='calculate_statistics', key='sales_stats')['avg_amount'] }}</li>
				</ul>
				
				<p><em>Время завершения: {{ ds }}</em></p>
				<hr>
				<p style="color: gray; font-size: 12px;">Это письмо сгенерировано автоматически Airflow DAG 'sales_pipeline'</p>
				""",
		)

		create_source_table >> generate_data >> calculate_stats >> create_stats_table >> insert_stats >> send_email