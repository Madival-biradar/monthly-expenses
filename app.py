from flask import Flask, request,render_template, jsonify, current_app, redirect, url_for
import jwt
from functools import wraps
from dotenv import load_dotenv
from db_connection import PostgreSQLConnectionPool
import os
from datetime import datetime
import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key' 

db_host = os.environ.get('POSTGRES_HOST')
db_port = os.environ.get('POSTGRES_PORT', 5432)
db_name = os.environ.get('POSTGRES_DATABASE')
db_user = os.environ.get('POSTGRES_USER')
db_password = os.environ.get('POSTGRES_PASSWORD')
pool_size_config = int(os.environ.get('max_pool_connection'))
pool_conn_timeout_config = int(os.environ.get('pool_connection_timeout'))
connection_pool = PostgreSQLConnectionPool(db_host, db_port, db_name, db_user, db_password)
USERS_TABLE = os.environ.get('UsersTable')
EXPENSE_TABLE = os.environ.get('ExpenseTable')
TEAM_TABLE = os.environ.get('TeamTable')
TEAM_MEMBERS_TABLE = os.environ.get('TeamMembersTable')


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print(request)
        token = request.headers.get('Authorization')
        print('111111111',token)
        if not token:
            return jsonify({'message': 'Missing token'}), 401

        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = data['username']
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401

        return f(current_user, *args, **kwargs)

    return decorated_function


#FUNCTION FOR GETTING THE USER FROM db
def user_fetch(username, password=None):
    print('^^^^^^',username,password)
    sql_params = []
    where_cond = ''' WHERE username=%s '''
    sql_params.append(username)
    if password is not None:
        where_cond = ''' WHERE username=%s AND userpassword=%s'''
        sql_params.append(password)
    connection = connection_pool.get_connection()
    fetch_query = f''' SELECT * from {USERS_TABLE} {where_cond}'''
    print(fetch_query)
    try:
        # with connection.cursor() as cursor:
        with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(fetch_query, tuple(sql_params))  # Pass as a single tuple
            row = cursor.fetchone()
            print('*************')
            print(row)
        print('data fetched  successfully')
    except Exception as e:
        print(e)
    finally:
        connection_pool.put_connection(connection)
    if row:
        return row
    else:
        return False


# method to fetch all expenses based on his team--id
def fetch_expenses_by_team(team_id,is_approved=None):
    sql_query = f''' SELECT * FROM {EXPENSE_TABLE} WHERE team_id=%s '''
    print(sql_query)
    if is_approved==False :
        print('eeeeeeeeeeeeeeeee')
        print(is_approved)
        sql_query = f''' SELECT * FROM {EXPENSE_TABLE} WHERE is_approved=False and team_id=%s '''
        print(sql_query)
    connection = connection_pool.get_connection()
    try:
        with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(sql_query, (team_id,))  # Pass as a single tuple
            row = cursor.fetchall()
        print('data fetched  successfully')
    except Exception as e:
        print(e)
    finally:
        connection_pool.put_connection(connection)
    if row:
        return row
    else:
        return False


#to check team exists or not in team table
def team_id_check(team_id):
    sql_query = f''' SELECT * FROM {TEAM_TABLE} where team_id=%s ;

                '''
    connection = connection_pool.get_connection()
    try:
        with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(sql_query,(team_id,))
            rows = cursor.fetchall()
    except Exception as e:
        print(e)

    finally:
       connection_pool.put_connection(connection)
    if rows:
        return rows
    else:
        return False


#fetch user by mobilenumber
def user_fetch_by_pnoneno(phone_no):
    print('^^^^^^',phone_no)
    sql_params = []
    where_cond = ''' WHERE phone_no=%s '''
    sql_params.append(phone_no)
    connection = connection_pool.get_connection()
    fetch_query = f''' SELECT * from {USERS_TABLE} {where_cond}'''
    print(fetch_query)
    try:
        # with connection.cursor() as cursor:
        with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(fetch_query, tuple(sql_params))  # Pass as a single tuple
            row = cursor.fetchone()
            print('*************')
            print(row)
        print('data fetched  successfully')
    except Exception as e:
        print(e)
    finally:
        connection_pool.put_connection(connection)
    if row:
        return row
    else:
        return False


@app.route('/',methods=['GET','POST'])
def home_page():
    return render_template('landing_page.html')

#1. api for registration
#needs to check if mobilenumber already in db or not if ---> there we just ask them for password
@app.route('/registration', methods=['GET','POST'])
def registration():
    if request.method == 'GET':
        return render_template('register.html')
    
    else:

        user_name = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        phone_no = request.form.get('phone_number')
        user_mobile_exist = user_fetch_by_pnoneno(phone_no)
        user_id = user_mobile_exist.get('userid')
        if user_mobile_exist:
            connection = connection_pool.get_connection()
            try:
                with connection.cursor() as cursor:
                    cursor.execute(f'''
                        UPDATE {USERS_TABLE}
                        SET username=%s, userpassword=%s, email=%s
                        WHERE userid = %s;''', (user_name,password,email, user_id))
                connection.commit()
            except Exception as e:
                print(e)
            finally:
                connection_pool.put_connection(connection)
            print('data update to users table successfully')
            return jsonify(
                {'msg':" U are already refered by ur friend and ur account created please login with new updated password!! "})
        connection = connection_pool.get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(f'''
                            INSERT INTO {USERS_TABLE} (username, userpassword, email, phone_no,
                            team_id, createdby, createdon, updatedby,updatedon,is_admin)
                            VALUES (%s, %s, %s, %s,NULL, 'self', CURRENT_TIMESTAMP, NULL,NULL,NULL)
                            ''', (user_name, password,email,phone_no))
            connection.commit()
            print('data added successfully')
        except Exception as e:
            print(e)
        finally:
            connection_pool.put_connection(connection)

    return jsonify({"msg":"Account Created Successfully"})




# @app.route('/registration', methods=['GET','POST'])
# def registration():
    # if request.method == 'GET':
    #     return render_template('register.html')
    
    # else:

    #     user_name = request.form.get('username')
    #     password = request.form.get('password')
    #     email = request.form.get('email')
    #     phone_no = request.form.get('phone_number')
    #     connection = connection_pool.get_connection()
    #     try:
    #         with connection.cursor() as cursor:
    #             cursor.execute(f'''
    #                         INSERT INTO {USERS_TABLE} (username, userpassword, email, phone_no,
    #                         team_id, createdby, createdon, updatedby,updatedon,is_admin)
    #                         VALUES (%s, %s, %s, %s,NULL, 'self', CURRENT_TIMESTAMP, NULL,NULL,NULL)
    #                         ''', (user_name, password,email,phone_no))
    #         connection.commit()
    #         print('data added successfully')
    #     except Exception as e:
    #         print(e)
    #     finally:
    #         connection_pool.put_connection(connection)

    # return jsonify({"msg":"Account Created Successfully"})


#to join group just needs to give existing team_id
@app.route('/joinGroup',methods=['POST',])
@login_required
def join_group(current_user):
    user_data = user_fetch(username=current_user,password=None)
    user_id = user_data.get('userid')
    user_team_id = user_data.get('team_id')
    print('*******************')
    print(user_id, user_team_id)
    exist_team_id = request.form.get('team_id')
    teamdetails = team_id_check(team_id=exist_team_id)
    print('11111111111111111')
    print(teamdetails)
    if not teamdetails:
        return jsonify({"error":"Entred Team id not exists"})
    
    # if team_id exists--->needs to add his user_id to team_members and update in users table team_id
    connection = connection_pool.get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(f'''
                UPDATE {USERS_TABLE}
                SET team_id=%s
                WHERE userid = %s;''', (exist_team_id, user_id))
        connection.commit()
        print('data update to users table successfully')

        # after successfully added the users to users table---> adding in team_membesr
        with connection.cursor() as cursor:
            cursor.execute(f'''
                        INSERT INTO {TEAM_MEMBERS_TABLE} (userid, team_id,joinedon)
                        VALUES (%s, %s, CURRENT_TIMESTAMP)
                        ''', (user_id, exist_team_id))
        connection.commit()
        print('data isnerted first time into teammebers table successfully')
    except Exception as e:
        print(e)
    finally:
        connection_pool.put_connection(connection) 
    
    return jsonify({'msg':"Ur successfully joined","team_id":exist_team_id})



#to create a group ---> he is admin
@app.route('/CreateGroup',methods=['POST',])
@login_required
def create_group(current_user):
    user_data = user_fetch(username=current_user, password=None)
    user_id = user_data.get('userid')

    team_name = request.form.get('team_name')
    team_size = request.form.get('team_size')
    team_description = request.form.get('team_description')

    #needs to insert--->team table with--->adminuserid--->
    connection = connection_pool.get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(f'''
                        INSERT INTO {TEAM_TABLE} (team_name, team_size, team_description,
                        team_admin, team_created_on)
                        VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                        ''', (team_name, team_size, team_description, user_id))
        connection.commit()
        print('data added successfully')
    except Exception as e:
        print(e)
    finally:
        connection_pool.put_connection(connection)
    return jsonify({"msg":"ur team created successfully"})


#2. api for login ---> getting username, password----> generate token----> sent to private page
# -----> using validation of username, password
@app.route('/login', methods=['GET','POST',])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        username = request.form.get('username')
        password = request.form.get('password')
        print(username,password)

        user_data = user_fetch(username=username,password=password)
        if not user_data:
            return jsonify({'error':'User Not Found'},404)
        
        if user_data:
            try:
                token = jwt.encode({'username': username,'password':password, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)},
                                app.config['SECRET_KEY'], algorithm='HS256')
                return jsonify({'access_token': token})
                # localStorage.setItem('token', 'your_jwt_token_here');
                # return redirect(url_for('view_all_options', token=token))
            except Exception as e:
                print(e)
        else:
            return jsonify({'message': 'Invalid credentials'}), 401
    
    return jsonify({'error':"error during the JWT token"})



@app.route('/ViewOptions', methods=['GET','POST',])
@login_required
def view_all_options(current_user):
    print('!!!!!!!!!!!!!!!!')
    print(current_user)
    print('verified')
    return render_template('viewall.html')

#api for adding the all expenses:
#if get---> needs to give all expenses based on his team
@app.route('/AddExpense', methods=['GET','POST'])
@login_required
def add_expenses(current_user):

    user_data = user_fetch(username=current_user, password=None)
    user_id = user_data.get('userid')
    phone_no  = user_data.get('phone_no')
    team_id = user_data.get('team_id')
    if request.method == 'GET':
        print('inside GET method')
        all_expenses = fetch_expenses_by_team(team_id,is_approved=None)
        if not all_expenses:
            return jsonify({"error":"Ur Team dont have any expenses YET!!, Be First to add!!"})
        df = pd.DataFrame(all_expenses)
        resp = df.to_dict(orient='records')
        return jsonify({
                    "error":None,
                    "data":resp
                })
    else:
        expense_type = request.form.get('expense_type')
        amount = request.form.get('amount_paid')
        description = request.form.get('description')
        connection = connection_pool.get_connection()
        try:
            with connection.cursor() as cursor:
                # transaction_id	transaction_name	transaction_description	user_id	amount	createdon	
                # is_approved	approved_on	team_id
                cursor.execute(f'''
                            INSERT INTO {EXPENSE_TABLE} (transaction_name, transaction_description, user_id,
                            amount, team_id, createdon, is_approved, approved_on)
                            VALUES (%s, %s, %s, %s,%s,CURRENT_TIMESTAMP, NULL, NULL)
                            ''', (expense_type, description,user_id, amount,team_id))
            connection.commit()
            print('expense_tranctiontable inserted firsttime---> successfully')
        except Exception as e:
            print(e)
        finally:
            connection_pool.put_connection(connection)
    return jsonify({'msg':"Expense added successfully"})



#api for approving the expenses:
# needs to see all the expenses if not approved we needs to approve
@app.route('/ApproveTheExpense',methods=['GET','POST'])
@login_required
def approve_expenses(current_user):
    user_data = user_fetch(username=current_user, password=None)
    if not user_data.get('is_admin'):
        return jsonify({"error":"U dont have access to do it"})
    if request.method == 'GET':
        print('inside GET method')
        all_expenses = fetch_expenses_by_team(team_id=user_data.get('team_id'),is_approved=None)
        if not all_expenses:
            return jsonify({"error":"Ur Team dont have any expenses YET!!, Be First to add!!"})
        df = pd.DataFrame(all_expenses)
        resp = df.to_dict(orient='records')
        return jsonify({
                    "error":None,
                    "data":resp
                })
    else:
        is_approved = False
        transaction_id = request.form.get('transaction_id')
        all_expenses = fetch_expenses_by_team(team_id=user_data.get('team_id'),is_approved=False)
        print('all_expenses',all_expenses)
        connection = connection_pool.get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(f'''
                    UPDATE {EXPENSE_TABLE}
                    SET is_approved=True, approved_on=CURRENT_TIMESTAMP
                    WHERE transaction_id = %s;''', (transaction_id, ))
            connection.commit()
            print('data update to users table successfully')

        except Exception as e:
            print(e)
        finally:
            connection_pool.put_connection(connection) 

        return jsonify({"msg":"approved successfully"})




#api-for admin can add any members with their phone_numbers that too store inside the 
#transction_table

@app.route('/AddMember',methods=['GET','POST'])
@login_required
def add_members(current_user):
    user_data = user_fetch(username=current_user, password=None)
    userid = user_data.get('userid')
    if not user_data.get('is_admin'):
        return jsonify({"error":"U dont have access to do it"})

    user_name = request.form.get('username')
    phone_no = request.form.get('phone_number')
    password,email = None,None
    connection = connection_pool.get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(f'''
                        INSERT INTO {USERS_TABLE} (username, phone_no,
                            createdby, createdon, updatedby,userpassword, email,updatedon,is_admin)
                        VALUES (%s, %s, %s, CURRENT_TIMESTAMP, NULL,NULL,NULL,NULL, NULL)
                        ''', (user_name,phone_no, userid))
        connection.commit()

        # after successfully added the users to users table---> adding in team_membesr
        # user_data = user_fetch(username=user_name,password=password)
        # user_id = user_data.get('userid')
        # team_id = user_data.get('team_id')
        # with connection.cursor() as cursor:
        #     cursor.execute(f'''
        #                 INSERT INTO {TEAM_MEMBERS_TABLE} (user_id, team_id,joinedon)
        #                 VALUES (%s, %s, CURRENT_TIMESTAMP)
        #                 ''', (user_id, team_id))
        # connection.commit()
        # print('data added successfully')


        print('data added successfully')
    except Exception as e:
        print(e)
    finally:
        connection_pool.put_connection(connection)       

    return jsonify({"msg":"Member addedd successfully!!"}) 






@app.route('/CalculateExpenses',methods=['GET','POST'])
@login_required
def calculate_expenses(current_user):
        



#3. api for forgot password


#4.after successfull login ----> he needs to add expenses with discription
# he can see----> all his addings or expenses what he added
# and he can see all other expenses also without updatings

#5.admin ----> needs to approval for each expenses added by users
#he can see all others expenses----> he can edit
#he can sum all amount
# he can divides amount for each one with appopriate reports
#monthly reports can generate


#db:
# 1. users table
# ---> username, userpassword,team_name, is_admin,


# 2.expense type
#---> type_of_expensive, username, amount_added

# 3.team table
#---> team_name(primarykey),team_members


#users_team:
#userid, team_id



if __name__ == '__main__':
    app.run(debug=True)