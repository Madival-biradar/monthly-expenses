from flask import Blueprint, request, jsonify, current_app, render_template
import jwt
from datetime import datetime
import datetime
import pandas as pd
from db_connection import PostgreSQLConnectionPool
from utils import login_required, user_fetch, fetch_expenses_by_team,\
                    team_id_check,user_fetch_by_pnoneno


from constants import db_host, db_port, db_name, db_user, db_password, pool_size_config,\
                        pool_conn_timeout_config, USERS_TABLE, EXPENSE_TABLE,\
                        TEAM_TABLE, TEAM_MEMBERS_TABLE 
connection_pool = PostgreSQLConnectionPool(db_host, db_port, db_name, db_user, db_password)


user = Blueprint('user', __name__, url_prefix='/')

@user.route('/',methods=['GET','POST'])
def home_page():
    return render_template('landing_page.html')

#1. api for registration
#needs to check if mobilenumber already in db or not if ---> there we just ask them for password
@user.route('/registration', methods=['GET','POST'])
def registration():
    if request.method == 'GET':
        return render_template('register.html')
    
    else:

        user_name = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        phone_no = request.form.get('phone_number')
        user_mobile_exist = user_fetch_by_pnoneno(phone_no)
        if user_mobile_exist:
            user_id = user_mobile_exist.get('userid')
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





#to join group just needs to give existing team_id
@user.route('/joinGroup',methods=['POST',])
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





#2. api for login ---> getting username, password----> generate token----> sent to private page
# -----> using validation of username, password
@user.route('/login', methods=['GET','POST',])
def login():
    print('came here inside')
    if request.method == 'GET':
        return render_template('login.html')
    else:
        username = request.form.get('username')
        password = request.form.get('password')
        print(username,password)

        user_data = user_fetch(username=username,password=password)
        print('*************',user_data)
        if not user_data:
            return jsonify({'error':'User Not Found'},404)
        
        if user_data:
            try:
                token = jwt.encode({'username': username,'password':password, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)},
                                current_app.config['SECRET_KEY'], algorithm='HS256')
                return jsonify({'access_token': token})
                # localStorage.setItem('token', 'your_jwt_token_here');
                # return redirect(url_for('view_all_options', token=token))
            except Exception as e:
                print(e)
        else:
            return jsonify({'message': 'Invalid credentials'}), 401
    
    return jsonify({'error':"error during the JWT token"})



@user.route('/ViewOptions', methods=['GET','POST',])
@login_required
def view_all_options(current_user):
    print('!!!!!!!!!!!!!!!!')
    print(current_user)
    print('verified')
    return render_template('viewall.html')

#api for adding the all expenses:
#if get---> needs to give all expenses based on his team
@user.route('/AddExpense', methods=['GET','POST'])
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







#1.Calculate total_sum of transctions all
#2.average = total_sum//size
#individual_contribution = theypaid-average
#if plus they needs to owes and - means they needs to borrows




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


