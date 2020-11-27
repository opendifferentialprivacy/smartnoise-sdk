SELECT 'CREATE DATABASE pums' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'pums')\gexec
GRANT ALL PRIVILEGES ON DATABASE "pums" TO postgres;
\c pums
DROP SCHEMA IF EXISTS PUMS CASCADE;
CREATE SCHEMA PUMS
	CREATE TABLE PUMS (age int, sex char(2), educ int, race char(2), income float, married boolean )
	CREATE TABLE PUMS_large (PersonID bigint, state int, puma bigint, sex int, age int, educ int, income float, latino boolean, black boolean, asian boolean, married boolean);

\copy PUMS.PUMS FROM 'PUMS.csv' CSV;
\copy PUMS.PUMS_large FROM 'PUMS_large.csv' CSV;
