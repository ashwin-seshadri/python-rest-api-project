import os
import redis
import secrets
from flask import Flask, jsonify
from flask_smorest import Api
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from dotenv import load_dotenv
from rq import Queue

from db import db
from blocklist import BLOCKLIST
import models # This is the advantage of having __init__.py in the models folder as import models == import models.__init__.py

from resources.store import blp as StoreBlueprint
from resources.item import blp as ItemBlueprint
from resources.tag import blp as TagBlueprint
from resources.user import blp as UserBlueprint

def create_app(db_url=None):
    app = Flask(__name__)
    load_dotenv()

    connection = redis.from_url(
        os.getenv("REDIS_URL")
    )

    app.queue = Queue("emails", connection=connection)

    app.config["PROPAGATE_EXCEPTIONS"] = True
    app.config["API_TITLE"] = "Stores REST API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.1.1"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url or os.getenv("DATABASE_URL", "sqlite:///data.db")
    app.config["SQLALCHEMY_TRACK_MIDIFICATIONS"] = False
    db.init_app(app)
    migrate = Migrate(app, db)

    api = Api(app)

    app.config["JWT_SECRET_KEY"] = "313673859152140546809216563287355563644"
    # got by running python cmd line, import secrets followed by secrets.SystemRandom().getrandbits(128)
    # this is to avoid generating new secret everytime the app is restarted

    jwt = JWTManager(app)

    @jwt.token_in_blocklist_loader
    def check_if_token_in_blocklist(jwt_header, jwt_payload):
        return jwt_payload["jti"] in BLOCKLIST
    
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return (
            jsonify(
                {
                    "description": "The token has been revoked.",
                    "error": "token_revoked"
                }
            ),
            401
        )
    @jwt.needs_fresh_token_loader
    def token_not_fresh_callback(jwr_header, jwt_payload):
        return (
            jsonify(
                {
                    "description": "Token is not fresh",
                    "error": "fresh_token_required"
                }
            ) ,
            401
        )

    @jwt.additional_claims_loader
    def add_claims_to_jwt(identity):
        # This is just to illustrate the point. Should look for other criteria in db
        if identity == "1":
            return {"is_admin" : True}
        return {"is_admin" : False}


    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return (
            jsonify({"message": "The token has expired.", "error":"token_expired"}),
            401
        )
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return (
            jsonify({"message": "Signature verification failed.", "error":"invalid_token"}),
            401
        )
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return (
            jsonify(
                {
                    "description": "Request does not contain an access token.",
                    "error": "authorization_required"
                }
            ), 
            401
        )

    # with app.app_context(): # since we are using Flask-Migrate to create our db tables, we dont need SqlAlchemy to do it.
    #     db.create_all()

    api.register_blueprint(ItemBlueprint)
    api.register_blueprint(StoreBlueprint)
    api.register_blueprint(TagBlueprint)
    api.register_blueprint(UserBlueprint)

    return app