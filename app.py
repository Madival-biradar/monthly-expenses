from flask import Flask, request,render_template, jsonify, current_app, redirect, url_for
import jwt
from functools import wraps
from dotenv import load_dotenv
from db_connection import PostgreSQLConnectionPool
import os
from datetime import datetime
import datetime

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
def user_fetch(username, password):
    where_cond = ''' WHERE username=%s AND userpassword=%s'''
    connection = connection_pool.get_connection()
    fetch_query = f''' SELECT username, userpassword from {USERS_TABLE} {where_cond}'''
    print(fetch_query)
    try:
        with connection.cursor() as cursor:
            cursor.execute(fetch_query, (username, password))  # Pass as a single tuple
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
@app.route('/registration', methods=['GET','POST'])
def registration():
    if request.method == 'GET':
        return render_template('register.html')
    
    else:

        user_name = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        phone_no = request.form.get('phone_number')
        team_name = request.form.get('team_name')
        connection = connection_pool.get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(f'''
                            INSERT INTO {USERS_TABLE} (username, userpassword, email, phone_no,
                            team_name, createdby, createdon, updatedby,updatedon,is_admin)
                            VALUES (%s, %s, %s, %s, %s, 'self', CURRENT_TIMESTAMP, NULL,NULL,NULL)
                            ''', (user_name, password,email,phone_no,team_name))
            connection.commit()
            print('data added successfully')
        except Exception as e:
            print(e)
        finally:
            connection_pool.put_connection(connection)

    return jsonify({"msg":"Account Created Successfully"})

        
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

        user_data = user_fetch(username,password)
        if not user_data:
            return jsonify({'error':'User Not Found'},404)
        
        if user_data:
            try:
                token = jwt.encode({'username': username,'password':password, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)},
                                app.config['SECRET_KEY'], algorithm='HS256')
                return jsonify({'access_token': token})
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


@app.route('/GetExpTypes',methods=['GET','POST'])
@login_required
def get_exp_add_exp():
    pass



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




if __name__ == '__main__':
    app.run(debug=True)