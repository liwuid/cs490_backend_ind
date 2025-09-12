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

@app.route('/topfivefilms')
def topfivefilms():
    cursor = mysql.connection.cursor()
    query = """
        select film.film_id, film.title, category.name, count(rental_id) as rented
        from rental 
        join inventory on inventory.inventory_id = rental.inventory_id
        join film on film.film_id = inventory.film_id
        join film_category on film_category.film_id = film.film_id
        join category on category.category_id = film_category.category_id
        group by film.film_id, film.title, category.name
        order by rented desc, film.title asc
        limit 5;
    """
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    return jsonify(result)

@app.route('/filmdetails/<film_id>')
def filmdetails(film_id):
    cursor = mysql.connection.cursor()
    query = """ select * from film where film_id = %s; """
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)