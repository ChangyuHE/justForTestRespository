#!/bin/bash

echo "recreating DB"
sudo -u postgres psql -f ./recreate_dbs.sql

echo "copying backup to home directory"
cp /mnt/nncv05a-cifs/msdk_ext4/backups/db/latest/reporting_db.sql.gz ~/
if [ $? -ne 0 ]; then
    rm ~/reporting_db.sql.gz
    exit $?
fi

echo "restoring db"
gzip -d ~/reporting_db.sql.gz
psql --dbname=postgresql://psql_user:password@127.0.0.1:5432/reporting_db < ~/reporting_db.sql

rm ~/reporting_db.sql
echo "done"

