from dotenv import load_dotenv
import os

load_dotenv()

db_host = os.environ.get('POSTGRES_HOST')
db_port = os.environ.get('POSTGRES_PORT', 5432)
db_name = os.environ.get('POSTGRES_DATABASE')
db_user = os.environ.get('POSTGRES_USER')
db_password = os.environ.get('POSTGRES_PASSWORD')
pool_size_config = int(os.environ.get('max_pool_connection'))
pool_conn_timeout_config = int(os.environ.get('pool_connection_timeout'))
USERS_TABLE = os.environ.get('UsersTable')
EXPENSE_TABLE = os.environ.get('ExpenseTable')
TEAM_TABLE = os.environ.get('TeamTable')
TEAM_MEMBERS_TABLE = os.environ.get('TeamMembersTable')