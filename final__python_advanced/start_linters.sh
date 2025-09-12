#!/bin/bash

# Определяем что обработать
if [ -z "$1" ]; then
    param="*.py"
else
    param="$1"
fi

# Проверить форматирование кода
echo "black tool start..."
black --check --diff --line-length 79 $param
result=$?
if [ $result -eq 0 ]; then
  echo "black tool done successfully."
else
  echo "black tool fail."
  read -p "Let's run the \"black\" utility (y[es] or other for no) " answer
  if [[ "$answer" == "y" || "$answer" == "Y" ]]; then
    black --line-length 79 $param
    result=$?
    echo "black tool done with result $result."
    exit $result
  fi
  exit 1
fi

# Проверить сортировку импорта
echo "isort tool start..."
isort --check-only --diff --profile black $param
result=$?
if [ $result -eq 0 ]; then
  echo "isort tool done successfully."
else
  echo "isort tool fail."
  read -p "Let's run the \"isort\" utility (y[es] or other for no) " answer
  if [[ "$answer" == "y" || "$answer" == "Y" ]]; then
    isort --profile black $param
    result=$?
    echo "isort tool done with result $result."
    exit $result
  fi
  exit 1
fi

# Проверить форматирование кода
echo "flake8 tool start..."
flake8 $param
result=$?
if [ $result -eq 0 ]; then
  echo "flake8 tool done successfully."
else
  echo "flake8 tool fail."
  exit 1
fi

# Проверить форматирование кода
echo "mypy tool start..."
mypy $param
result=$?
if [ $result -eq 0 ]; then
  echo "mypy tool done successfully."
else
  echo "mypy tool fail."
  exit 1
fi

echo "All linter checks have been completed"
exit 0
