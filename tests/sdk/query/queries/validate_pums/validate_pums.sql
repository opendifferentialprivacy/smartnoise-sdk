SELECT SUM(age) FROM PUMS.PUMS;
SELECT COUNT(*), VAR(age) AS var_age FROM PUMS.PUMS;
SELECT married, educ, income, AVG(age) FROM PUMS.PUMS GROUP BY married, educ, income;
SELECT p.married, AVG(age) AS aa FROM PUMS.PUMS AS p GROUP BY married;
SELECT TOP 5 educ, AVG(income) FROM PUMS.PUMS GROUP BY educ;
SELECT COUNT(married), AVG(age) FROM PUMS.PUMS;
SELECT 3 AS three, p.married, educ, AVG(income) FROM PUMS.PUMS AS p GROUP BY educ, married;
SELECT educ FROM PUMS.PUMS GROUP BY educ;
SELECT SUM(age) AS age FROM PUMS.PUMS;
SELECT (SUM(age)) AS age FROM PUMS.PUMS;
SELECT SUM(age) * 1 AS age FROM PUMS.PUMS;
SELECT SUM(age), COUNT(*) FROM PUMS.PUMS;
SELECT PI(), RAND(), POWER(AVG(age), 2) FROM PUMS.PUMS;