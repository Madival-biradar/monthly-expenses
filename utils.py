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
from constants import db_host, db_port, db_name, db_user, db_password, pool_size_config,\
                        pool_conn_timeout_config, USERS_TABLE, EXPENSE_TABLE,\
                        TEAM_TABLE, TEAM_MEMBERS_TABLE 
connection_pool = PostgreSQLConnectionPool(db_host, db_port, db_name, db_user, db_password)


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
    if is_approved == False :
        print('is_approved', is_approved)
        sql_query = f''' SELECT * FROM {EXPENSE_TABLE} WHERE is_approved=False and team_id=%s '''
        print(sql_query)
    elif is_approved == True :
        print('is_approved', is_approved)
        sql_query = f''' SELECT * FROM {EXPENSE_TABLE} WHERE is_approved=True and team_id=%s '''
        print(sql_query)
    else:
        print(is_approved, 'enter else')
        sql_query = f''' SELECT * FROM {EXPENSE_TABLE} WHERE team_id=%s '''
        print(sql_query)
    connection = connection_pool.get_connection()
    try:
        with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(sql_query, (team_id,))  # Pass as a single tuple
            row = cursor.fetchall()
            # print(row)
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

