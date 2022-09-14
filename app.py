import io

import pandas
from flask import Flask, request, jsonify
from psycopg2 import errors
import psycopg2
import exceptions
from flask_cors import CORS

ALLOWED_EXTENSIONS = set(['csv'])

app = Flask(__name__)
CORS(app)

conn = psycopg2.connect(database="postgres",
                        host="localhost",
                        user="postgres",
                        password="password123",
                        port="5432")
cursor = conn.cursor()
is_upload_allowed = True


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def process_csv_df(df):
    # Returns a list of employees to be added if everything is valid
    # Returns an empty list if a row is invalid
    results = []
    for row in df.itertuples():
        if row.id[0] == "#":
            # Row is a comment
            continue
        try:
            # Test converting type
            id = str(row.id)
            login = str(row.login)
            name = str(row.name)
            salary = float(row.salary)
            if id == '' or login == '' or name == '' or salary < 0:
                raise exceptions.InvalidParameterException
            results.append((id, login, name, salary))
        except exceptions.InvalidParameterException as e:
            return []
    return results


def insert_employee_list_sql(employee_list):
    insert_commands = []
    delete_commands = []
    for employee in employee_list:
        insert_commands.append(f"INSERT INTO Employee VALUES "
                               f"('{employee[0]}', '{employee[1]}', '{employee[2]}', {employee[3]})")
        delete_commands.append(f"DELETE FROM Employee WHERE id = '{employee[0]}'")

    # Attempt insertion
    for i in range(len(insert_commands)):
        try:
            cursor.execute(insert_commands[i])
            conn.commit()
        except (psycopg2.errors.UniqueViolation, psycopg2.errors.InFailedSqlTransaction) as e:
            # Rollback all commits by deleting
            conn.rollback()
            for n in range(i):
                cursor.execute(delete_commands[n])
                conn.commit()
            raise psycopg2.errors.UniqueViolation


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/users/upload', methods=['POST'])
def upload_csv():
    global is_upload_allowed
    if is_upload_allowed:
        is_upload_allowed = False
        file = request.files['file']
        if file.filename != '' and allowed_file(file.filename):
            # noinspection PyTypeChecker
            df = pandas.read_csv(io.StringIO(file.read().decode("utf-8")))
            employee_list = process_csv_df(df)
            if not employee_list:
                # Invalid employee list, return 400
                return jsonify({"success": False, "error": "Invalid rows provided"}), 400
            # Employee list is valid
            try:
                insert_employee_list_sql(employee_list)
                return jsonify({"success": True}), 200
            except psycopg2.errors.UniqueViolation as e:
                return jsonify({"success": False, "error": "Invalid rows provided"}), 400
            finally:
                is_upload_allowed = True
        else:
            is_upload_allowed = True
            return jsonify({"success": False, "error": "Invalid file format"}), 400
    else:
        return jsonify({"success": False, "error": "Parallel upload not allowed, please try again later!"}), 400


@app.route('/users', methods=['GET', 'POST'])
def users():
    try:
        if request.method == 'GET':
            min_salary = request.args.get('minSalary')
            max_salary = request.args.get('maxSalary')
            offset = request.args.get('offset')
            limit = request.args.get('limit')
            sort = request.args.get('sort')

            if min_salary is None or max_salary is None or offset is None or limit is None or sort is None:
                raise exceptions.MissingParameterException
            if len(min_salary) == 0 or len(max_salary) == 0 or len(offset) == 0 or len(sort) == 0:
                raise exceptions.EmptyParameterArgumentException
            min_salary = int(min_salary)
            max_salary = int(max_salary)
            offset = int(offset)
            limit = int(limit)

            if sort[0] == '+':
                sort_type = "ASC"
            elif sort[0] == '-':
                sort_type = "DESC"
            else:
                raise exceptions.InvalidParameterException

            sort_by = sort[1:]
            print(min_salary, max_salary, sort_by, sort_type, limit, offset)
            cursor.execute(f"SELECT * FROM Employee "
                           f"WHERE salary > {min_salary} AND salary < {max_salary} "
                           f"ORDER BY {sort_by} {sort_type} "
                           f"LIMIT {limit} OFFSET {offset}")
            results = cursor.fetchmany(limit)
            print("hmm")

            response = []
            print(results)
            for result in results:
                response.append({'id': result[0], 'login': result[1], 'name': result[2], 'salary': result[3]})

            return jsonify({"results": response}), 200
        elif request.method == 'POST':
            id = request.args.get('id')
            login = request.args.get('login')
            name = request.args.get('name')
            salary = request.args.get('salary')

            if id is None or login is None or name is None or salary is None:
                raise exceptions.MissingParameterException
            if len(id) == 0 or len(login) == 0 or len(name) == 0 or len(salary) == 0:
                raise exceptions.EmptyParameterArgumentException
            id = str(id)
            login = str(login)
            name = str(name)
            salary = float(salary)

            cursor.execute(f"INSERT INTO Employee VALUES ('{id}', '{login}', '{name}', {salary})")
            conn.commit()

            return jsonify({"success": True}), 200
    except exceptions.MissingParameterException as e:
        conn.rollback()
        return jsonify({"success": False, "error": "Missing parameter"}), 400
    except (exceptions.InvalidParameterException, psycopg2.errors.InFailedSqlTransaction,
            psycopg2.errors.UndefinedColumn) as e:
        conn.rollback()
        return jsonify({"success": False, "error": "Invalid parameter"}), 400
    except psycopg2.errors.UniqueViolation as e:
        conn.rollback()
        return jsonify({"success": False, "error": "User already exists"}), 400


@app.route('/users/<id>', methods=['GET', 'PUT', 'DELETE'])
def user(id):
    try:
        if request.method == 'GET':
            cursor.execute(f"SELECT * FROM Employee "
                           f"WHERE id = '{id}'")
            results = cursor.fetchone()
            response = {'id': results[0], 'login': results[1], 'name': results[2], 'salary': results[3]}

            return jsonify({"success": True, "results": response}), 200
        elif request.method == 'DELETE':
            cursor.execute(f"DELETE FROM Employee WHERE id = '{id}'")
            conn.commit()

            return jsonify({"success": True}), 200
        elif request.method == 'PUT':
            login = request.args.get('login')
            name = request.args.get('name')
            salary = request.args.get('salary')

            if login is None and name is None and salary is None:
                raise exceptions.MissingParameterException

            is_first_parameter = True
            update_command = ""
            if login is not None and len(login) > 0:
                if is_first_parameter:
                    update_command += f"login = '{login}'"
                    is_first_parameter = False
                else:
                    update_command += f", login = '{login}'"
            if name is not None and len(name) > 0:
                if is_first_parameter:
                    update_command += f"name = '{name}'"
                    is_first_parameter = False
                else:
                    update_command += f", name = '{name}'"
            if salary is not None and len(salary) > 0:
                if is_first_parameter:
                    update_command += f"salary = '{salary}'"
                    is_first_parameter = False
                else:
                    update_command += f", salary = '{salary}'"

            if is_first_parameter:
                raise exceptions.EmptyParameterArgumentException
            else:
                cursor.execute(f"UPDATE Employee "
                               f"SET {update_command} "
                               f"WHERE id = '{id}'")
                conn.commit()

                return jsonify({"success": True}), 200
    except (exceptions.InvalidParameterException, psycopg2.errors.InFailedSqlTransaction,
            psycopg2.errors.UndefinedColumn) as e:
        conn.rollback()
        return jsonify({"success": False, "error": "Invalid parameter"}), 400


if __name__ == '__main__':
    app.run()
