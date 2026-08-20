from marshmallow import Schema, fields


class LoanCreateSchema(Schema):
    book_id = fields.Integer(required=True)


class LoanSchema(Schema):
    id = fields.Integer(dump_only=True)
    book_id = fields.Integer(dump_only=True)
    user_id = fields.Integer(dump_only=True)
    borrowed_at = fields.DateTime(dump_only=True)
    due_date = fields.DateTime(dump_only=True)
    returned_at = fields.DateTime(dump_only=True, allow_none=True)
    overdue = fields.Boolean(dump_only=True)
