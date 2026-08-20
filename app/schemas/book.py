from marshmallow import Schema, fields, validate


class BookSchema(Schema):
    id = fields.Integer(dump_only=True)
    title = fields.String(required=True, validate=validate.Length(min=1, max=200))
    isbn = fields.String(required=True, validate=validate.Length(min=10, max=20))
    year = fields.Integer(allow_none=True)
    genre = fields.String(allow_none=True)
    available = fields.Boolean(dump_only=True)
    author_id = fields.Integer(required=True)
