import mysql.connector

def get_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Absolutemysql#1",
        database="secure_app"
    )
    return conn