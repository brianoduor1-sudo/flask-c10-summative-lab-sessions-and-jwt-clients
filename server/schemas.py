from marshmallow import Schema, fields

class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    username = fields.Str(required=True)

class NoteSchema(Schema):
    id = fields.Int(dump_only=True)
    title = fields.Str(required=True)
    content = fields.Str(required=True)
    category = fields.Str()
    created_at = fields.DateTime(dump_only=True)
    user_id = fields.Int(dump_only=True)

user_schema = UserSchema()
note_schema = NoteSchema()
notes_schema = NoteSchema(many=True)