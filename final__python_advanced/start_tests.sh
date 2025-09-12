#!/bin/bash

# Остановить другие контейнеры во избежание конфликта
echo "Stopping containers..."
docker stop server_nginx
docker stop server_app
docker stop postgres

# Запустить контейнер postgres для тестов
echo "Docker up!"
docker-compose -f ./docker-test.yml up --remove-orphans -d

# Готовимся к запуску тестов
echo "Running tests..."
source ~/.virtualenvs/python_advanced_diploma/bin/activate

export PYTHONPATH=$PWD:$PWD/server_app:$PWD/tests

# Чтение данных из файла .env_test и экспорт переменных
while IFS='=' read -r key value
do
  echo "Set $key=some value"
  export $key=$value
done < .env_test

if [ ! -d $APP_IMAGE_PATH ]; then
  echo "Add dir $APP_IMAGE_PATH"
  mkdir $APP_IMAGE_PATH
#  chown -R app_usr:app_grp /tmp/images
#  chmod -R ug+w /tmp/images
fi

# Запуск тестов
input="Y"
while true; do
  if [ "$input" = "Y" ] || [ "$input" = "y" ]; then
    pytest ./ --cov=server_app/
    # -m api   -m utils  -m db_utils
    echo "Код возврата $?"
  fi

  read -p "Повторить тесты (y/n)? " input

  if [ "$input" = "Y" ] || [ "$input" = "y" ]; then
    clear
    continue
  elif [ "$input" = "N" ] || [ "$input" = "n" ]; then
    break
  else
    echo "Некорректный ввод, пожалуйста, введите y или n."
  fi
done

# Удаление переменных
while IFS='=' read -r key _
do
  unset "$key"
done < .env_test

deactivate

# Убрать тестовый контейнер postgres
echo "Docker down!"
docker-compose -f ./docker-test.yml down --volumes

echo "All done!"
