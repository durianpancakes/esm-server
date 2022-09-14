DROP TABLE Employee;

CREATE TABLE Employee (
  id VARCHAR(30) PRIMARY KEY,
  login VARCHAR(30) NOT NULL,
  name VARCHAR(100) NOT NULL,
  salary FLOAT(2) NOT NULL,
  CONSTRAINT employee_unique UNIQUE(login),
  CHECK (salary >= 0.00)
);