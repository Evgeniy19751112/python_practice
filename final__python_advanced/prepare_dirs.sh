#!/bin/bash

if [ ! -d logs ]; then
  mkdir logs
fi
cd logs

if [ ! -d app ]; then
  mkdir app
fi
sudo chown :999 app && sudo chmod -R 666 app && sudo chmod 2777 app

if [ ! -d nginx ]; then
  mkdir nginx
fi
sudo chown :999 nginx && sudo chmod -R 666 nginx && sudo chmod 2777 nginx

if [ ! -d postgresql ]; then
  mkdir postgresql
fi
sudo chown :999 postgresql && sudo chmod -R 666 postgresql && sudo chmod 2777 postgresql

if [ ! -d postgres_test ]; then
  mkdir postgres_test
fi
sudo chown :999 postgres_test && sudo chmod -R 666 postgres_test && sudo chmod 2777 postgres_test
cd ..

if [ ! -d db ]; then
  mkdir db
  sudo chown :999 db && sudo chmod -R 666 db && sudo chmod 2777 db
fi

if [ ! -d db_test ]; then
  mkdir db_test
  sudo chown :999 db_test && sudo chmod -R 666 db_test && sudo chmod 2777 db_test
fi

sudo chown :999 server_nginx/static/images && sudo chmod 2775 server_nginx/static/images
