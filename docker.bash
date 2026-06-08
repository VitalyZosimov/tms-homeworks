# Сборка образа
docker build -t etl-pipeline .

# Запуск контейнера
docker run -d --name etl-scheduler \
  --network host \
  -e PG_HOST=host.docker.internal \
  -e CH_HOST=host.docker.internal \
  etl-pipeline

# Просмотр логов
docker logs -f etl-scheduler

# Ручной запуск внутри контейнера
docker exec -it etl-scheduler /app/manual_run.sh