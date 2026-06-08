#!/bin/bash
# healthcheck.sh - проверка доступности сервисов

# Проверка PostgreSQL
if pg_isready -h ${PG_HOST:-localhost} -p ${PG_PORT:-5432} -U ${PG_USER:-etl_user}; then
		echo "PostgreSQL доступен"
else
		echo "PostgreSQL недоступен"
		exit 1
fi

# Проверка ClickHouse
if curl -s "http://${CH_HOST:-localhost}:${CH_PORT:-8123}/ping" | grep -q "Ok"; then
		echo "ClickHouse доступен"
else
		echo "ClickHouse недоступен"
		exit 1
fi

exit 0