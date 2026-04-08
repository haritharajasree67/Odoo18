from odoo import models, fields
from odoo.exceptions import UserError


class AccountMoveDiscount(models.TransientModel):
    _name = 'account.move.discount'
    _description = 'Invoice Global Discount'

    discount_type = fields.Selection(
        [('percent', 'Percentage'), ('amount', 'Fixed Amount')],
        default='percent',
        required=True
    )
    discount_value = fields.Float(string="Discount")

    def action_apply_discount(self):
        invoice = self.env['account.move'].browse(self.env.context.get('active_id'))

        if not invoice or invoice.state != 'draft':
            raise UserError("Discount can only be applied on draft invoice.")

        if self.discount_value <= 0:
            raise UserError("Discount must be greater than zero.")

        invoice._apply_global_discount(
            self.discount_type, self.discount_value
        )
