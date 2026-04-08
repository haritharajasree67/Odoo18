from odoo import models, fields, api

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    qty_available = fields.Float(string="Quantity On Hand", compute="_compute_qty_available")

    @api.depends('product_id')
    def _compute_qty_available(self):
        for line in self:
            if line.product_id:
                line.qty_available = line.product_id.qty_available
            else:
                line.qty_available = 0.0
