import json
import sys
import os
import csv
import psycopg2 as psy
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import subprocess


#Read file with loads instead of load in order to check if key exists
def read_file(file_to_open):
    input_from_file = {}
    file = open(file_to_open, 'r')
    input_from_file = json.loads(file.read())
    file.close()
    return input_from_file


def connect(host, database, user, password, port):
    """ Connect to the PostgreSQL database server """
    conn = None
    try:
        # read connection parameters
        params = dict()
        params['host'] = host
        params['database'] = database
        params['user'] = user
        params['password'] = password
        params['port'] = port

        # connect to the PostgreSQL server
        print('Connecting to the PostgreSQL database...')
        conn = psy.connect(**params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)


    except (Exception, psy.DatabaseError) as error:
        print(error)
        print("Erreur")
        sys.exit()

    return conn

def create_database(conn, dbname):
    cur = conn.cursor()
    cur.execute('CREATE DATABASE ' + dbname)
    cur.close()

def create_tables(conn, dbname, tables):
    print("Create tables")
    cur = conn.cursor()
    sql_file = open(tables,'r')
    cur.execute(sql_file.read())
    cur.close()

def populate_tables(conn, dbname, csv_file, headers):
    cur = conn.cursor()
    for table, file in csv_file.items():
        #print(table, ' : ', file)

        with open(file, 'r') as f:
            if(table in headers and headers[table]):
                reader = csv.reader(f)
                selected_col = tuple(next(reader))
                cur.copy_from(f, table, sep=',', columns=selected_col)
            else:
                cur.copy_from(f, table, sep=',')
    conn.commit()
    cur.close()

def drop_database(conn, dbname):
    cur = conn.cursor()
    cur.execute(f"DROP DATABASE {dbname} WITH (FORCE)")
    cur.close()

def drop_tables(conn, dbname, tables):
    cur = conn.cursor()
    for table in tables:
        cur.execute(f"DROP TABLE {table}" )
    cur.close()



if __name__ == '__main__':
    done = set()
    db_exist = True
    if len(sys.argv) >= 3:
        connection = sys.argv[1]
        gestion = sys.argv[2]
        # print(connection)
        # print(gestion)
    else:
        print("Usage : file1 (containing database connection), file 2 (containg explainations on what to do")
        sys.exit()

    bdd = read_file(connection)
    handler = read_file(gestion)
    #print("BDD : ", bdd)

    db_name_connect = handler['db_name']
    if handler['action'] == 'create_db':
        db_name_connect = 'postgres'
        db_exist = False
    
    connection = connect(bdd['host'], db_name_connect, bdd['username'], bdd['password'], bdd['server_port'])
    #print(connection)

    #Create db
    if handler['action'] == 'create_db' and not db_exist:
        #print("Create db")
        create_database(connection, handler['db_name'])
        done.add(f"{handler['db_name']} has been created")

    #Create tables
    if handler['action'] == 'create' and "tables_to_create" in handler:
        create_tables(connection, handler['db_name'], handler['tables_to_create'])
        done.add("Many tables have been created")

    #Populate tables
    if handler['action'] == 'populate' and "data_to_import" in handler:
        #print("Populate some tables")
        headers = False
        if "headers_in_csv" in handler:
            headers = handler['headers_in_csv']
            populate_tables(connection, handler['db_name'], handler['data_to_import'], headers)
        done.add("Some data have been stored in several tables")

    #Drop db
    if handler['action'] == 'delete_db' and db_exist:
        #print("Delete a db")
        drop_database(connection, handler['db_name'])
        done.add(f"{handler['db_name']} has been deleted")

    #Drop tables
    if handler['action'] == 'delete' and "tables" in handler:
        #print("Delete tables")
        drop_tables(connection, handler['db_name'], handler['tables'])
        done.add("Some tables have been deleted")


    if(len(done) >= 1):
        print("Let's sum up what has been done : ")
        for action in done:
            print(action)
    else:
        print("Nothing has been done. That's maybe due to an error in "+gestion)

    print("Everything should be ok !")
