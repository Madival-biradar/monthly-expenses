from flask import Blueprint, request, jsonify
import jwt
from datetime import datetime
import datetime
import pandas as pd
import numpy as np
from db_connection import PostgreSQLConnectionPool
from utils import login_required, user_fetch, fetch_expenses_by_team,\
                    team_id_check,user_fetch_by_pnoneno, team_details_fetch_for_user, \
                    team_member_details_fetch_for_user


from constants import db_host, db_port, db_name, db_user, db_password, pool_size_config,\
                        pool_conn_timeout_config, USERS_TABLE, EXPENSE_TABLE,\
                        TEAM_TABLE, TEAM_MEMBERS_TABLE 
connection_pool = PostgreSQLConnectionPool(db_host, db_port, db_name, db_user, db_password)

admin = Blueprint('admin', __name__, url_prefix='/')

#to create a group ---> he is admin
@admin.route('/CreateGroup',methods=['POST',])
@login_required
def create_group(current_user):
    # user_data = user_fetch(username=current_user, password=None)
    user_data = user_fetch_by_pnoneno(phone_no=current_user,password=None)
    user_id = user_data.get('userid')

    team_name = request.form.get('team_name')
    team_size = request.form.get('team_size')
    team_description = request.form.get('team_description')

    #if team name dupliacted based on user
    team_name_details = team_details_fetch_for_user(team_admin=user_id) 
    if  team_name_details:
        for i in team_name_details:  
            if team_name == i.get('team_name'):
                return jsonify({'msg':"team name already exists!!",'status_code':400})

    #needs to insert--->team table with--->adminuserid--->
    # if group created we needs to make him admin
    # we needs to make transction
    users_table_admin_update_where_cond = f''' WHERE userid=%s '''
    users_table_admin_update_query = f''' UPDATE {USERS_TABLE} SET is_admin=TRUE 
                                            {users_table_admin_update_where_cond} '''

    team_insert_query = f''' INSERT INTO {TEAM_TABLE} (team_name, team_size, 
                                    team_description,team_admin, team_created_on)
                                    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP) ''' 
    team_sql_param = [team_name, team_size, team_description, user_id] 


    team_members_insert_query =  f''' INSERT INTO {TEAM_MEMBERS_TABLE} 
                                        (userid, team_id,joinedon)
                                        VALUES (%s, %s, CURRENT_TIMESTAMP) '''                                                               
    connection = connection_pool.get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(users_table_admin_update_query, (user_id,))

            cursor.execute(team_insert_query, team_sql_param)
        connection.commit()
        print('data added successfully')

        team_id_fetch = team_details_fetch_for_user(team_admin=user_id,data=True)
        team_id_data = []
        for i in team_id_fetch:   
            team_id_data.append(i.get('team_id'))

        with connection.cursor() as cursor:
            cursor.execute(team_members_insert_query,(user_id, team_id_data[0]))
        connection.commit()
        print('data added successfully')

    except Exception as e:
        print(e)
    finally:
        connection_pool.put_connection(connection)
    return jsonify({"msg":"ur team created successfully"})



#api for approving the expenses:
# needs to see all the expenses if not approved we needs to approve
@admin.route('/ApproveTheExpense',methods=['GET','POST'])
@login_required
def approve_expenses(current_user):
    # user_data = user_fetch(username=current_user, password=None)
    user_data = user_fetch_by_pnoneno(phone_no=current_user,password=None)
    if not user_data.get('is_admin'):
        return jsonify({"error":"U dont have access to do it"})
    if request.method == 'GET':
        print('inside GET method')
        all_expenses = fetch_expenses_by_team(team_id=user_data.get('team_id'),is_approved=False)
        if not all_expenses:
            return jsonify({"error":"Ur Team dont have any expenses YET!!, Be First to add!!"})
        df = pd.DataFrame(all_expenses)

        df['createdon'] = df['createdon'].replace({pd.NaT: None})
        df['approved_on'] = df['approved_on'].replace({pd.NaT: None})

        print(df)
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

@admin.route('/AddMember',methods=['GET','POST'])
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




#1.Calculate total_sum of transctions all
#2.average = total_sum//size
#individual_contribution = theypaid-average
#if plus they needs to owes and - means they needs to borrows

@admin.route('/CalculateExpenses',methods=['GET','POST'])
@login_required
def calculate_expenses(current_user):
    user_data = user_fetch(username=current_user, password=None)
    user_id = user_data.get('userid')

    team_id_data = team_member_details_fetch_for_user(user_id)
    for team_info in team_id_data:
        print('777777777777777777')
        print(team_info)
        team_id = team_info.get('team_id') 
    print(team_id)
    
    expense_transdata = fetch_expenses_by_team(team_id,is_approved=True)
    print(expense_transdata)
    team_data = team_id_check(team_id)

    team_size = team_data[0].get('team_size')
    df = pd.DataFrame(expense_transdata)
    total_sum = df['amount'].sum()

    # Group the DataFrame by 'user_id' and calculate total sum and user's contribution
    grouped = df.groupby('user_id').agg(total_sum_user=('amount', 'sum')).reset_index()
    grouped['average'] = total_sum//team_size  # Set the average as the total sum of all amounts
    grouped['contribution'] = grouped['total_sum_user'] - grouped['average']
    resp = grouped.to_dict(orient='records')
    return jsonify({'msg':resp})
    




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
