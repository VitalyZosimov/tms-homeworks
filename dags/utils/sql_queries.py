#SQL запросы для ETL пайплайна

# DDL для создания DDS таблиц
DDS_CREATE_TABLES = """
CREATE SCHEMA IF NOT EXISTS dds;

CREATE TABLE IF NOT EXISTS dds.dim_countries (
		country_code VARCHAR(2) PRIMARY KEY,
		country_name TEXT NOT NULL,
		loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dds.dim_users (
		user_id SERIAL PRIMARY KEY,
		user_email TEXT UNIQUE NOT NULL,
		user_name TEXT,
		user_country_code VARCHAR(2) REFERENCES dds.dim_countries(country_code),
		loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dds.dim_products (
		product_id SERIAL PRIMARY KEY,
		product_name TEXT UNIQUE NOT NULL,
		loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dds.fact_transactions (
		fact_id SERIAL PRIMARY KEY,
		user_id INTEGER NOT NULL REFERENCES dds.dim_users(user_id),
		product_id INTEGER NOT NULL REFERENCES dds.dim_products(product_id),
		quantity INTEGER NOT NULL CHECK (quantity > 0),
		price DECIMAL(10,2) NOT NULL CHECK (price >= 0),
		total_amount DECIMAL(10,2) NOT NULL CHECK (total_amount >= 0),
		transaction_date TIMESTAMP NOT NULL,
		ip_address TEXT,
		source_system TEXT DEFAULT 'postgres',
		loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# UPSERT для стран
UPSERT_COUNTRIES = """
INSERT INTO dds.dim_countries (country_code, country_name)
SELECT country_code, country_name FROM public.countries
ON CONFLICT (country_code) 
DO UPDATE SET country_name = EXCLUDED.country_name,
							loaded_at = CURRENT_TIMESTAMP;
"""

# UPSERT для пользователей
UPSERT_USERS = """
INSERT INTO dds.dim_users (user_email, user_name, user_country_code)
SELECT DISTINCT user_email, user_name, user_country_code
FROM public.raw_transactions
WHERE user_email IS NOT NULL
ON CONFLICT (user_email) 
DO UPDATE SET user_name = EXCLUDED.user_name,
							user_country_code = EXCLUDED.user_country_code,
							loaded_at = CURRENT_TIMESTAMP;
"""

# UPSERT для товаров
UPSERT_PRODUCTS = """
INSERT INTO dds.dim_products (product_name)
SELECT DISTINCT product_name
FROM public.raw_transactions
WHERE product_name IS NOT NULL
ON CONFLICT (product_name) 
DO UPDATE SET loaded_at = CURRENT_TIMESTAMP;
"""

# Загрузка фактов
LOAD_FACTS = """
INSERT INTO dds.fact_transactions 
		(user_id, product_id, quantity, price, total_amount, 
		 transaction_date, ip_address, source_system)
SELECT 
		du.user_id,
		dp.product_id,
		rt.quantity,
		rt.price,
		rt.total_amount,
		rt.transaction_date,
		rt.ip_address,
		rt.source_system
FROM public.raw_transactions rt
JOIN dds.dim_users du ON du.user_email = rt.user_email
JOIN dds.dim_products dp ON dp.product_name = rt.product_name
ON CONFLICT (fact_id) DO NOTHING;
"""

# Индексы
DDS_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_fact_user_id ON dds.fact_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_fact_product_id ON dds.fact_transactions(product_id);
CREATE INDEX IF NOT EXISTS idx_fact_date ON dds.fact_transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_users_email ON dds.dim_users(user_email);
CREATE INDEX IF NOT EXISTS idx_users_country ON dds.dim_users(user_country_code);
CREATE INDEX IF NOT EXISTS idx_products_name ON dds.dim_products(product_name);
"""

# Статистика для ClickHouse
CLICKHOUSE_STATS_QUERY = """
SELECT 
		c.country_code,
		c.country_name,
		COALESCE(SUM(ft.total_amount), 0) AS total_sales,
		COALESCE(AVG(ft.total_amount), 0) AS avg_transaction_value,
		COUNT(ft.fact_id) AS transaction_count
FROM dds.dim_countries c
LEFT JOIN dds.dim_users du ON c.country_code = du.user_country_code
LEFT JOIN dds.fact_transactions ft ON du.user_id = ft.user_id
GROUP BY c.country_code, c.country_name
ORDER BY total_sales DESC
"""