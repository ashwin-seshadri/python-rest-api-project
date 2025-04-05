from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import SQLAlchemyError

from db import db
from schemas import TagSchema, TagAndItemSchema
from models import TagModel, StoreModel, ItemModel

blp = Blueprint("tags", __name__, description="Operations on tags")

@blp.route("/store/<int:store_id>/tag")
class TagsInStore(MethodView):
    @blp.response(200, TagSchema(many=True))
    def get(self, store_id):
        store = StoreModel.query.get_or_404(store_id)

        return store.tags.all()

    @blp.arguments(TagSchema)
    @blp.response(201, TagSchema)
    def post(self, tag_data, store_id):
        
        # In case the tag name was just unique within the store, then we need to set unique = false in schema and add a check like below.
        #if TagModel.query.filter(TagModel.store_id == store_id, TagModel.name == tag_data["name"]).first():
        #    abort(400, message="A tag with that name already exists in that store.")

        tag = TagModel(**tag_data, store_id=store_id)

        try:
            db.session.add(tag)
            db.session.commit()
        except SQLAlchemyError as e:
            abort(500, message=str(e))
        return tag
    
@blp.route("/item/<int:item_id>/tag/<int:tag_id>")
class LinkItemToTag(MethodView):
    @blp.response(201, TagSchema)
    def post(self, item_id, tag_id):
        item = ItemModel.query.get_or_404(item_id)
        tag = TagModel.query.get_or_404(tag_id)

        try:
            item.tags.append(tag)

            db.session.add(item)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="An error occurred while inserting tag")

        return tag
    
    @blp.response(201, TagAndItemSchema)
    def delete(self, item_id, tag_id):
        item = ItemModel.query.get_or_404(item_id)
        tag = TagModel.query.get_or_404(tag_id)

        try:
            item.tags.remove(tag)

            db.session.add(item)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="An error occurred while deleting tag")
            
        return {"message": "Tag removed from item", "item": item, "tag": tag}

@blp.route("/tag/<string:tag_id>")
class Tag(MethodView):
    @blp.response(200, TagSchema)
    def get(self, tag_id):
        tag = TagModel.query.get_or_404(tag_id)
        return tag
    
    @blp.response(
            202, 
            description="Deletes a tag if no item is tagged with it.",
            example={"message": "Tag deleted."}
            )
    @blp.alt_response(404, description="Tag not found.")
    @blp.alt_response(400, description="Returned if the tag is assigned to one or more items, In this case, tag will not be deleted.")
    def delete(self, tag_id):
        tag = TagModel.query.get_or_404(tag_id)

        if not tag.items:
            db.session.delete(tag)
            db.session.commit()
            return {"message": "Tag deleted"}
        abort(
            400,
            message="Could not delete tag. Make sure tag is not associated with any items, then try again."
        )