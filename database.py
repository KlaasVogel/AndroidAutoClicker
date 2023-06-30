from dotenv import load_dotenv
from os import environ
import mysql.connector

class MyDB():
    def __init__(self):
        load_dotenv()

        dbserver=environ.get('DBSERVER')
        dbuser=environ.get('DBUSER')
        dbpassword=environ.get('DBPW')
        db=environ.get('DATABASE')

        self.mydb=mysql.connector.connect(
            host=dbserver,
            user=dbuser,
            password=dbpassword,
            database=db
        )
        self.cursor=self.mydb.cursor()

    def getID(self, sql):
        result=self.query(sql)
        id=False
        for row in result:
            id=row["ID"]
        return id

    def query(self, sql):
        try:
            self.cursor.execute(sql)
            return self.cursor.fetchall()
        except Exception as e:
            print(e)
            return False

    def update(self, sql):
        try:
            self.cursor.execute(sql)
            self.mydb.commit()
            return True
        except Exception as e:
            print(e)
            return False

    def lastID(self):
        return self.cursor.lastrowid

    def close(self):
        self.cursor.close()
        self.mydb.close()
