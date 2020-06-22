#!/bin/bash

BACKUP_USER=root
BACKUP_DIR=/mnt/nncv05a-cifs/msdk_ext4/backups/db/
DATABASE="reporting_db"
DATABASE_ADDR="postgresql://psql_user:password@127.0.0.1:5432/reporting_db"
DAYS_OLDER_THAN=7


# Make sure we're running as the required backup user
if [ "$BACKUP_USER" != "" -a "$(id -un)" != "$BACKUP_USER" ]; then
    echo "This script must be run as '$BACKUP_USER', you are '$(whoami)'. Exiting." 1>&2
    exit 1;
fi;

# remove old backups on server
find $BACKUP_DIR*-*-* -type d -ctime +$DAYS_OLDER_THAN -exec rm -rf {} \;


# create dir to backup to
FINAL_BACKUP_DIR=$BACKUP_DIR"`date +\%Y-\%m-\%d`/"
echo "Making backup directory in $FINAL_BACKUP_DIR"

if ! mkdir -p $FINAL_BACKUP_DIR; then
    echo "Cannot create backup directory in $FINAL_BACKUP_DIR :(" 1>&2
    exit 1;
fi;

# do backup
echo "Backup database '$DATABASE'"

if ! pg_dump -Fp --dbname="$DATABASE_ADDR" | gzip > $FINAL_BACKUP_DIR"$DATABASE".sql.gz.in_progress; then
    echo "FAILED: Can't produce backup database $DATABASE" 1>&2
else
    mv $FINAL_BACKUP_DIR"$DATABASE".sql.gz.in_progress $FINAL_BACKUP_DIR"$DATABASE".sql.gz
    cp $FINAL_BACKUP_DIR"$DATABASE".sql.gz $BACKUP_DIR"latest/"$DATABASE".sql.gz"
fi

echo -e "done"
