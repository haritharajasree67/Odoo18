from odoo import models,fields,_
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'


    global_discount = fields.Float(string="Global Discount")


    def action_open_discount_wizard(self):
        self.ensure_one()
        return {
            'name': _("Global Discount"),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move.discount',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_id': self.id,
                'active_model': 'account.move',
            }
        }



    def _apply_global_discount(self, discount_type, value):

        # 🔥 ALWAYS reload invoice from DB
        invoice = self.env['account.move'].browse(
            self.env.context.get('active_id')
        )
        invoice.ensure_one()

        # 1️⃣ Fetch Discount Product
        discount_product = invoice._get_discount_product()

        # 2️⃣ Remove existing discount lines
        discount_lines = invoice.line_ids.filtered(
            lambda l: l.product_id == discount_product
        )

        discount_lines.unlink()

        inv = self.invoice_line_ids

        # 3️⃣ Fetch real invoice lines
        invoice_lines = self.invoice_line_ids


        total_amount = sum(
            line.quantity * line.price_unit for line in invoice_lines
        )


        if total_amount <= 0:
            return

        # 4️⃣ Calculate discount
        if discount_type == 'percent':
            discount_amount = total_amount * (value / 100)
        else:
            discount_amount = value

        if discount_amount <= 0:
            return

        # 5️⃣ Resolve income account
        account = (
                discount_product.property_account_income_id
                or discount_product.categ_id.property_account_income_categ_id
        )

        if not account:
            raise UserError(_("Income account not set on Discount product."))

        # 6️⃣ Create discount line
        self.env['account.move.line'].with_context(
            check_move_validity=False
        ).create({
            'move_id': invoice.id,
            'product_id': discount_product.id,
            'name': discount_product.display_name,
            'quantity': 1,
            'price_unit': -discount_amount,
            'account_id': account.id,
        })

        invoice.global_discount = discount_amount

    def _get_discount_product(self):
        product = self.env['product.product'].search(
                [('name', '=', 'Discount')], limit=1
            )
        if not product:
                raise UserError(_("Discount product not found."))
        return product