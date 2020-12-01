-- Delete 'Agnostic' Os branches
BEGIN;
DELETE FROM api_result r
    USING api_validation v, api_os os, api_os grp
    WHERE r.validation_id = v.id
        AND v.os_id = os.id
        AND os.group_id = grp.id
        AND grp.name = 'Agnostic';

DELETE FROM api_validation v
    USING api_os os, api_os grp
    WHERE v.os_id = os.id
        AND os.group_id = grp.id
        AND grp.name = 'Agnostic';
COMMIT;


-- Delete outdated validations created by 'admin' except of some cases for structure demo purposes
BEGIN;
DELETE FROM api_result r
    USING api_validation v, auth_user u
    WHERE r.validation_id = v.id
        AND v.owner_id = u.id
        AND u.username = 'admin'
        AND v.id NOT IN (8, 9, 49, 55, 56, 58, 59, 62, 74, 75, 76, 84, 93, 99, 118, 128, 129, 133, 137, 141, 146, 147, 148, 167, 168, 183, 185, 187, 190, 194, 202, 213, 225, 251, 263, 264);

DELETE FROM api_validation v
    USING auth_user u
    WHERE v.owner_id = u.id
        AND u.username = 'admin'
        AND v.id NOT IN (8, 9, 49, 55, 56, 58, 59, 62, 74, 75, 76, 84, 93, 99, 118, 128, 129, 133, 137, 141, 146, 147, 148, 167, 168, 183, 185, 187, 190, 194, 202, 213, 225, 251, 263, 264);
COMMIT;


-- Perform database housekeeping
REINDEX DATABASE reporting_db;
VACUUM FULL;
VACUUM ANALYZE;
