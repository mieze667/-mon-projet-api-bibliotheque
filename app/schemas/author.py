from marshmallow import Schema, fields, validate


class AuthorSchema(Schema):
    id = fields.Integer(dump_only=True)
    name = fields.String(required=True, validate=validate.Length(min=1, max=150))
    nationality = fields.String(allow_none=True)
    bio = fields.String(allow_none=True)
