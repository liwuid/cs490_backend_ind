from flask import Flask, jsonify, request
from flask_paginate import Pagination
from flask_mysqldb import MySQL

app = Flask(__name__)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '5283'
app.config['MYSQL_DB'] = 'sakila'
mysql = MySQL(app)

#-------------------------landing page---------------------------#
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

@app.route('/film/<film_id>')
def filmdetails(film_id):
    cursor = mysql.connection.cursor()
    query = """
        select film.film_id, film.title, film.description, film.release_year, category.name as category, language.name as language
        from film
        join film_category on film.film_id = film_category.film_id
        join category on category.category_id = film_category.category_id
        join language on language.language_id = film.language_id
        where film.film_id = %s;
    """
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    return jsonify(result)

@app.route('/topfiveactors')
def topfiveactors():
    cursor = mysql.connection.cursor()
    query = """
        select actor.actor_id, actor.first_name, actor.last_name, count(film.film_id) as movies
        from film_actor
        join actor on actor.actor_id = film_actor.actor_id
        join film on film.film_id = film_actor.film_id
        group by actor.actor_id
        order by movies desc
        limit 5;
    """
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    return jsonify(result)

@app.route('/actor/<actor_id>')
def actordetails(actor_id):
    cursor = mysql.connection.cursor()
    query = """
        select actor.actor_id, actor.first_name, actor.last_name, count(film.film_id) as movies
        from film_actor
        join actor on actor.actor_id = film_actor.actor_id
        join film on film.film_id = film_actor.film_id
        where actor.actor_id = %s
        group by actor.actor_id;
    """
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    return jsonify(result)

@app.route('/topfive/actor/<actor_id>')
def topfiveactorfilms(actor_id):
    cursor = mysql.connection.cursor()
    query = """
        select film.film_id, film.title, count(rental_id) as rental_count
        from rental
        join inventory on inventory.inventory_id = rental.inventory_id
        join film on film.film_id = inventory.film_id
        join film_actor on film_actor.film_id = film.film_id
        where film_actor.actor_id = %s
        group by film.film_id, film.title
        order by rental_count desc
        limit 5;
    """
    cursor.execute(query, (actor_id,))
    result = cursor.fetchall()
    cursor.close()
    return jsonify(result)

#-------------------------films page---------------------------#

@app.route('/films/search')
def searchfilms():
    search = request.args.get('search', '')
    cursor = mysql.connection.cursor()
    query = """
        select film.film_id, film.title, category.name as category
        from film
        join film_category on film_category.film_id = film.film_id
        join category on category.category_id = film_category.category_id
        join film_actor on film_actor.film_id = film.film_id
        join actor on actor.actor_id = film_actor.actor_id
        where film.title like %s or category.name like %s or actor.first_name like %s or actor.last_name like %s
    """
    like = f"%{search}%"
    cursor.execute(query, (like, like, like, like))
    result = cursor.fetchall()
    cursor.close()
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True)