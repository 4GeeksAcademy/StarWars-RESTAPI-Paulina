"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Character, Planet, Favourite
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)
# ------------------------------------------------------------------
@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    users_serialized = list(map(lambda item: item.serialized(), users))
    response_body = {
        "msg": "Users",
        "result": users_serialized
    }
    return jsonify(response_body), 200
# ------------------------------------------------------------------
@app.route('/user/<int:id>', methods=['GET'])
# OBTENER UN SOLO USUARIO
def get_user(id):
    user = User.query.filter_by(id=id).first() #Consulta la base de datos para encontrar un usuario que coincida el id con el valor proporcionado.
    if user is None:
        return jsonify({"msg": "User not found"}), 404
    user_serialized = user.serialize() #convierte el objeto en un formato serializable (diccionario).
    response_body = {
        "msg": "Hello, this is your GET /user/id response ",
        "result": user_serialized
    }
    return jsonify(response_body), 200 #Devuelve el primer resultado encontrado, si no se encuentra ningún usuario, devuelve None.
# ------------------------------------------------------------------
# OBTENER TODOS LOS PERSONAJES
@app.route('/character', methods=['GET'])
def get_characters():
    characters = Character.query.all() #Consulta la base de datos para obtener todos los registros de la tabla 'Character'
    characters_serialized = list(map(lambda item: item.serialize(), characters)) #Usa 'map' para aplicar la función serialize a cada elemento en la lista 'characters' y convierte el resultado en una lista.
    response_body = { #Crea un diccionario response_body que contiene un mensaje y los resultados serializados de los personajes
        "msg": "Hello, this is your GET /characters response ",
        "results": characters_serialized
    }
    return jsonify(response_body), 200 #Devuelve una respuesta JSON y un código de estado 200 (OK).

# OBTENER UN PERSONAJE
@app.route('/character/<int:character_id>', methods=['GET'])
def get_character_id(character_id):

    character = Character.query.filter_by(id=character_id).first()
    if character is None:
        return jsonify({"msg": "Not found"}), 404
    character_serialized = character.serialize()
    response_body = {
        "msg": "Hello, this is your GET /character/id response ",
        "result": character_serialized
    }

    return jsonify(response_body), 200
# ------------------------------------------------------------------
# OBTENER TODOS LOS PLANETAS
@app.route('/planets', methods=['GET'])
def get_planets():
    planets = Planet.query.all()
    planets_serialized = list(map(lambda item: item.serialize(), planets))
    response_body = {
        "msg": "Hello, this is your GET /planets response ",
        "results": planets_serialized
    }
    return jsonify(response_body), 200

#OBTENER UN PLANETA 
@app.route('/planet/<int:planet_id>', methods=['GET'])
def get_planet_id(planet_id):
    planet = Planet.query.filter_by(id=planet_id).first()
    if planet is None:
        return jsonify({"msg": "Not found"}), 404
    planet_serialized = planet.serialize()
    response_body = {
        "msg": "Hello, this is your GET /planet/id response ",
        "result": planet_serialized
    }

    return jsonify(response_body), 200
# ------------------------------------------------------------------
# GET DE FAVORITOS   
@app.route('/user/<int:user_id>/favourites', methods=['GET'])
def get_user_favourites(user_id):
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return jsonify({"msg": "Not found"}), 404

    favorites = Favourite.query.filter_by(user_id = user_id).all()
    fav_serialize = list(map(lambda item: item.serialize(), favorites))
    response_body = {
        "msg": "Your favorites",
        "result": fav_serialize
    }

    return jsonify(response_body), 200
# ------------------------------------------------------------------
#MÉTODO POST DE USER
@app.route("/user", methods=["POST"])
def create_user():
    #traer datos de la solicitud
    data = request.json
    email = data.get("email")
    password = data.get("password")
    username = data.get("username")

    if None in [email, password, username]:
        return jsonify({
            "message": "Username, Email and Password are Required"
        }), 400
    
    #Creamos un nuevo usuario
    new_user = User(email=email, password=password, username=username, is_active=True)
    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"msg": "Usuario creado"}), 201
    except Exception as error:
        print(error)
        db.session.rollback()
        return jsonify({"message":"Error in server"}), 500
# -----------------------------------------------------------------
# POST DE PLANETAS
@app.route("/favorites/planet/<int:planet_id>", methods=["POST"])
def add_favourite_planet(planet_id):
    #Extraemos la info 
    user_id= request.json.get("user_id")
    #Verificamos 
    if not user_id:
        return jsonify({"message": "User ID is required"}), 400
    
    #VERIFICAMOS SI EXISTE EL USUARIO EN LA BASE DE DATOS
    exist_user = User.query.filter_by(id=user_id).first()
    if exist_user is None:
        return jsonify({"msg": "User not found"}), 404
    
    #VERIFICAMOS SI EXISTE EL PLANETA EN LA BASE DE DATOS
    exist_planet = Planet.query.filter_by(id=planet_id).first()
    if exist_planet is None:
        return jsonify({"msg": "Planet not found"}), 404
    
    #Verificamos si el planeta ya está en favoritos 
    existing_favourite = Favourite.query.filter_by(user_id=user_id, planet_id=planet_id).first()
    if existing_favourite:
        return jsonify({"message": "Planet ya es un favorito"}), 400 
    
    #Agregamos un nuevo favorito
    new_favourite = Favourite(user_id=user_id, planet_id=planet_id)
    try:
        db.session.add(new_favourite)
        db.session.commit()
        return jsonify({"message": "se agregó el planeta a favorito"}), 201
    except Exception as error:
        print(error)
        db.session.rollback()
        return jsonify({"message": "Error in server"}), 500
# ------------------------------------------------------------------
@app.route("/favorites/character/<int:character_id>", methods=["POST"])
def add_favourite_character(character_id):
    #Extraemos la info 
    user_id= request.json.get("user_id")
    #Verificamos 
    if not user_id:
        return jsonify({"message": "User ID is required"}), 400
    
    #VERIFICAMOS SI EXISTE EL USUARIO EN LA BASE DE DATOS
    exist_user = User.query.filter_by(id=user_id).first()
    if exist_user is None:
        return jsonify({"msg": "User not found"}), 404
    
    #VERIFICAMOS SI EXISTE EL PLANETA EN LA BASE DE DATOS 
    exist_character = Planet.query.filter_by(id=character_id).first()
    if exist_character is None:
        return jsonify({"msg": "Character not found"}), 404
    
    #Verificamos si el personaje ya está en favoritos
    existing_favourite = Favourite.query.filter_by(user_id=user_id, character_id=character_id).first()
    if existing_favourite:
        return jsonify({"message": "El personaje ya existe en favoritos"}), 400 
    
    #Agregamos un nuevo favorito
    new_favourite = Favourite(user_id=user_id, character_id=character_id)
    try:
        db.session.add(new_favourite)
        db.session.commit()
        return jsonify({"message": "Personaje añadido a favoritos"}), 201

    except Exception as error:
        print(error)
        db.session.rollback()
        return jsonify({"message": "Error in server"}), 500

# ------------------------------------------------------------------
#DELETE FAVORITO
@app.route("/favorites/<int:character_id>", methods=["DELETE"])
def delete_favourite(id):
    #BUSCAR EL FAVORITO
    favourite = Favourite.query.filter_by(id=id).first()

    if favourite is None:
        return jsonify({"message": "Favorito no encontrado"}), 404
   
    # Eliminar el favorito
    try:
        db.session.delete(favourite)
        db.session.commit()
        return jsonify({"message": "Favorito eliminado correctamente"}), 200

    except Exception as error:
        print(error)
        db.session.rollback()
        return jsonify({"message": "Error in server"}), 500
# ------------------------------------------------------------------

# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
