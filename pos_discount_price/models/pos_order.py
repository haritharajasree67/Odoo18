from odoo import models


class PosOrder(models.Model):
    _inherit = 'pos.order'

    def action_reset_to_draft(self):
        for order in self:
            if order.state not in ('draft', 'cancel'):  # only allow reset if already confirmed
                order.write({'state': 'draft'})
                # Remove posted moves/invoices if needed
                if order.account_move:
                    order.account_move.button_draft()  # optional, reset related journal entry
        return True