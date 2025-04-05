from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required, get_jwt
from sqlalchemy.exc import SQLAlchemyError

from db import db
from schemas import ItemSchema, ItemUpdateSchema
from models import ItemModel

blp = Blueprint("items", __name__, description="Operations on items")

@blp.route("/item")
class ItemList(MethodView):

    @blp.response(200, ItemSchema(many=True))
    def get(self):
        return ItemModel.query.all() # returning a list instead of dictionary previously
    
    @jwt_required(fresh=True)
    @blp.arguments(ItemSchema)
    @blp.response(201, ItemSchema)
    def post(self, item_data): # item_data is passed in by marshmallow after validation
        item = ItemModel(**item_data)

        try:
            db.session.add(item)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="An error occurred while inserting the item")
        return item, 201
    
@blp.route("/item/<string:item_id>")
class Item(MethodView):

    @blp.response(200, ItemSchema)
    def get(self,item_id):
        item = ItemModel.query.get_or_404(item_id)
        return item
    
    @jwt_required(fresh=True)
    @blp.arguments(ItemUpdateSchema)
    @blp.response(200, ItemSchema)
    def put(self, item_data, item_id): # first parameter will always be the one passed in by marshmallow
        item = ItemModel.query.get(item_id)
        if item:
            item.price = item_data["price"]
            item.name = item_data["name"]
        else:
            item = ItemModel(id=item_id, **item_data) # Need to make sure you create an item with same id as that is passed in

        db.session.add(item)
        db.session.commit()

        return item

    @jwt_required()
    def delete(self, item_id):
        jwt = get_jwt()
        if not jwt.get("is_admin"):
            abort(401, message="Admin privilege required.")

        item = ItemModel.query.get_or_404(item_id)
        db.session.delete(item)
        db.session.commit()
        return {"message": "Item deleted"}