from flask import Flask, jsonify, request
from flask_paginate import Pagination
from flask_mysqldb import MySQL

app = Flask(__name__)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '5283'
app.config['MYSQL_DB'] = 'sakila'
mysql = MySQL(app)
   
@app.route('/')
def home():
    return "Sakila Flask API is running! Go to /allfilms to see films."
 
@app.route('/films')
def films():
    cursor = mysql.connection.cursor()
    query = """select film_id, title from film limit 10"""
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True)