import psycopg2
from config import config

sql_add_client = """INSERT INTO CLIENT(username,email,password) VALUES(%s,%s,%s) RETURNING id;"""
sql_add_log="""INSERT INTO LOG(username,action,details) VALUES(%s,%s,%s) RETURNING id;"""

#check connection between flask and db
def connect():
    """ Connect to the PostgreSQL database server """
    conn = None
    try:
        # read connection parameters
        params = config()

        # connect to the PostgreSQL server
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(**params)
		
        # create a cursor
        cur = conn.cursor()
        
	# execute a statement
        print('PostgreSQL database version:')
        cur.execute('SELECT version()')

        # display the PostgreSQL database server version
        db_version = cur.fetchone()
        print(db_version)
       
	# close the communication with the PostgreSQL
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            print('Database connection closed.')

#connection with db
def get_db_connection():
    conn = psycopg2.connect(
        host="postgres",
        database="postgres",
        user="postgres",
        password="1234")
    return conn

#########TABLE LOG########
#get all logs
def get_all_logs():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM LOG ORDER BY date_created DESC;')
    logs = cur.fetchall()
    cur.close()
    conn.close()
    return logs

#add log
def add_log(username,action,details):
    conn = get_db_connection()
    cur = conn.cursor()
    id = cur.execute(sql_add_log,(username,action,details))
    conn.commit()
    cur.close()
    conn.close()
    return id

#########TABLE CLIENT#############
#get all clients
def get_all_clients():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM CLIENT;')
    clients = cur.fetchall()
    cur.close()
    conn.close()
    return clients

#get client info from id
def search_by_id(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM CLIENT WHERE id=%s;',[id])
    client = cur.fetchall()
    cur.close()
    conn.close()
    return client[0]

#get client info from access
def search_by_access(access):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM CLIENT WHERE access=%s;',[access])
    clients = cur.fetchall()
    cur.close()
    conn.close()
    return clients

#delete client
def delete_client(client_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM CLIENT WHERE id = %s;',[client_id])
    conn.commit()
    cur.close()
    conn.close()
    return

#add client
def add_client(username,email,password):
    conn = get_db_connection()
    cur = conn.cursor()
    id = cur.execute(sql_add_client,(username,email,password))
    conn.commit()
    cur.close()
    conn.close()
    return id

#updates client
def update_client(id,username,access,date_created,email,password):
    print(id,username,access,date_created,email,password)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('UPDATE CLIENT SET username = %s,access=%s,date_created=%s,\
        email=%s,password=%s WHERE id = %s;',[username,access,date_created,email,password,id])
    conn.commit()
    cur.close()
    conn.close()
    return

#main
if __name__ == '__main__':
    connect()