"""
Ames
Handles the connection of DB
"""

import mysql.connector
from mysql.connector import errorcode

def connect_db(flags, db, mode=1):
    func = 'connect_db: '
    
    if mode:
        print(func+'connecting to database...')
        try:
            flags['cb_db'] = mysql.connector.connect(
                user =      db['db_name'],
                password =  db['db_pw'],
                host =      db['db_host'],
                database =  db['db_dbname'])
            
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print(func,'connection failed - access denied')
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print(func,'connection failed - database does not exist')
            else:
                print(func,err)
            return flags
            
        else:
            print(func+'connected')
            flags['db_isconnected'] = True
            return flags
        
    else:
        print('disconnecting from database...')
        try:
            flags['cb_db'].close()
            
        except mysql.connector.Error as err:
            print(func,err)
            return flags
        
        else:
            print(func+'disconnected')
            flags['db_isconnected'] = False
            return flags
