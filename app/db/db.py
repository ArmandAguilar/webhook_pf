import os
import pymysql

    
class dbMysql:
    
    def conMysql():
        client = pymysql.connect(host=os.environ.get('_HOST_MySQL_'),
                    user=os.environ.get('_USER_MySQL_'),
                    password=os.environ.get('_PASS_MySQL_'),
                    db=os.environ.get('_DB_MySQL_'),
                    local_infile=True,
                    connect_timeout=30,  # 30 seconds connection timeout
                    read_timeout=30,     # 30 seconds read timeout
                    write_timeout=30     # 30 seconds write timeout
                    )
        return client