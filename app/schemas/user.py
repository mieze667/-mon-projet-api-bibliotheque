from marshmallow import Schema, fields, validate


class UserRegisterSchema(Schema):
    email = fields.Email(required=True)
    username = fields.String(required=True, validate=validate.Length(min=3, max=80))
    password = fields.String(required=True, load_only=True, validate=validate.Length(min=6))
    role = fields.String(validate=validate.OneOf(["member", "staff"]), load_default="member")


class UserLoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True, load_only=True)


class UserPublicSchema(Schema):
    id = fields.Integer(dump_only=True)
    email = fields.Email(dump_only=True)
    username = fields.String(dump_only=True)
    role = fields.String(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
