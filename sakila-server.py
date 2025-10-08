from flask import Flask, jsonify, request
from flask_mysqldb import MySQL
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '5283'
app.config['MYSQL_DB'] = 'sakila'
mysql = MySQL(app)

#-------------------------landing page---------------------------#
@app.route('/')
def home():
    return jsonify({
        "message": "Sakila Database",
        "endpoints": [
            "/topfivefilms",
            "/films/search?search=...",
            "/film/<film_id>",
            "/topfiveactors",
            "/actor/<actor_id>",
            "/topfive/actor/<actor_id>",
            "/customers?page=1"
        ]
    })

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
        select film.film_id, film.title, film.description, film.rating, film.release_year, category.name as category, language.name as language 
        from film
        join film_category on film.film_id = film_category.film_id
        join category on category.category_id = film_category.category_id
        join language on language.language_id = film.language_id
        where film.film_id = %s;
    """
    cursor.execute(query, (film_id,))
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
    cursor.execute(query, (actor_id,))
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
        select distinct film.film_id, film.title, category.name as category, film.rating, film.release_year
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

    if not result:
        return jsonify({"message": "No results"})
    return jsonify(result)

@app.route('/films/inventory/<film_id>')
def film_inventory(film_id):
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT COUNT(inventory.inventory_id)
        FROM inventory
        WHERE inventory.film_id = %s
        AND inventory.inventory_id NOT IN (
            SELECT inventory_id 
            FROM rental 
            WHERE return_date IS NULL
        );
    """, (film_id,))
    inventory = cursor.fetchone()[0]
    cursor.close()
    return jsonify({"film_copies": inventory})

@app.route('/rent', methods=['POST'])
def rent_film():
    data = request.get_json()
    film_id = data.get("film_id")
    customer_id = data.get("customer_id")

    if not customer_id or not film_id:
        return jsonify({"message": "No id provided"})
    
    cursor = mysql.connection.cursor()

    cursor.execute("""
        select inventory_id
        from inventory
        where film_id = %s
        and inventory_id not in (
            select inventory_id
            from rental
            where return_date is NULL
        )
        limit 1;
    """, (film_id,))
    inventory = cursor.fetchone()

    if not inventory:
        cursor.close()
        return jsonify({"message": "There are no available copies for this film"})
    
    inventory_id = inventory[0]

    cursor.execute("""
        insert into rental (rental_date, inventory_id, customer_id, staff_id)
        values (NOW(), %s, %s, 1);
    """, (inventory_id, customer_id))

    mysql.connection.commit()
    cursor.close()

    return jsonify({"message": "Film rented successfully!"})

@app.route('/return', methods=['POST'])
def return_film():
    data = request.get_json()
    rental_id = data.get("rental_id")

    if not rental_id:
        return jsonify({"message": "No rental id provided"})
    
    cursor = mysql.connection.cursor()
    cursor.execute("""
        update rental
        set return_date = NOW()
        where rental_id = %s and return_date is null;
    """, (rental_id,))

    if cursor.rowcount == 0:
        cursor.close()
        return jsonify({"message": "Rental not found"})
    
    mysql.connection.commit()
    cursor.close()

    return jsonify({"message": "Film returned successfully!"})

#-------------------------customer page---------------------------#
@app.route('/customers')
def customers():
    cursor = mysql.connection.cursor()

    page = request.args.get("page", type=int, default=1)
    per_page = 10
    offset = (page - 1) * per_page

    search = request.args.get("search", "").strip()
    sort_by = request.args.get("sort_by", "last_name")
    sort_order = request.args.get("sort_order", "asc").lower()
    columns = {"customer_id", "first_name", "last_name", "email"}
    
    if sort_by not in columns:
        sort_by = "last_name"
    if sort_order not in {"asc", "desc"}:
        sort_order = "asc"

    query = """
        select count(*)
        from customer
        where (%s = '' 
            or customer_id = %s 
            or first_name like %s 
            or last_name like %s)
    """
    like = f"%{search}%"
    cursor.execute(query, (search, search, like, like))
    total = cursor.fetchone()[0]
    pages = (total + per_page - 1) // per_page
    
    query = f"""
        select customer_id, first_name, last_name, email
        from customer
        where (%s = ''
            or customer_id = %s
            or first_name like %s
            or last_name like %s)
        order by {sort_by} {sort_order}
        limit %s offset %s;
    """
    cursor.execute(query, (search, search, like, like, per_page, offset))
    customers = cursor.fetchall()
    cursor.close()

    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'pages': pages
    }

    return jsonify({'customers': customers, 'pagination': pagination})

if __name__ == '__main__':
    app.run(debug=True)