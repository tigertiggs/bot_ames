import os, sys
import ast
import mysql.connector
from mysql.connector import pooling
from mysql.connector import errorcode
dir = os.path.dirname(__file__)

class logger:
    def __init__(self, client):
        self.logc = None
        self.client = client
    
    async def send(self, *msg):
        if self.logc == None:
            with open('commands/_pass/log') as logf:
                guild =     int(logf.readline().strip())
                channel =   int(logf.readline().strip())
                self.logc = self.client.get_guild(guild).get_channel(channel)
        try:
            await self.logc.send(" ".join([str(w) for w in msg]))
        except:
            pass

class database:
    def __init__(self, logger, size=10):
        self.name =         '[database]: '
        self.db_pointer =   None
        self.response =     None
        self.pool =         None
        self.pool_size =    size
        self.reset_conn =   True
        self.logger =       logger
    
    async def connect(self):
        if self.db_pointer != None:
            await self.logger.send(self.name,'database is connected - forcing reconnect')
            #self.disconnect()
        try:
            with open(os.path.join(dir,'commands/_pass/db')) as df:
                db = dict()
                db['name'] =    df.readline().strip()
                db['pw'] =      df.readline().strip()
                db['host'] =    df.readline().strip()
                db['dbname'] =  df.readline().strip()
            self.db_pointer = mysql.connector.pooling.MySQLConnectionPool(
                pool_name =             'hatsune_pool',
                pool_size =             self.pool_size,
                pool_reset_session =    self.reset_conn,
                user =                  db['name'],
                password =              db['pw'],
                host =                  db['host'],
                database =              db['dbname']
            )
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                await self.logger.send(self.name,'connection failed - access denied')
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                await self.logger.send(self.name,'connection failed - database does not exist')
            else:
                await self.logger.send(self.name,'connection failed - ',err)
            self.db_pointer = None
            return False
        else:
            await self.logger.send(self.name,'connection successful')
            return True
    
    def release(self, conn):
        #mysql.connector.pooling.PooledMySQLConnection(self.db_pointer, conn).close()
        conn.close()
    
    """
    def disconnect(self):
        if self.db_pointer == None:
            self.logger.send(self.name,'database already disconnected')
        else:
            try:
                self.db_pointer.close()
            except mysql.connector.Error as err:
                self.logger.send(self.name,'disconnection failed - ', err)
            else:
                self.logger.send(self.name,'disconnection successful')
    """

    async def execute(self, statement):
        conn = self.db_pointer.get_connection()
        if conn.is_connected(): 
            self.response = conn.cursor(buffered=True).execute(statement)
            return self.response
        else:
            await self.logger.send(self.name,'execution failed - could not connect')
    
    async def status(self):
        conn = self.db_pointer.get_connection()
        if conn.is_connected():
            info = conn.get_server_info()
            await self.logger.send(self.name,info)
        else:
            await self.logger.send(self.name,'server disconnected')