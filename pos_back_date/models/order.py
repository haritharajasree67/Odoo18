from odoo import models, api,fields




class PosConfig(models.Model):
    _inherit = 'pos.config'

    allow_backdate = fields.Boolean(
        string="Allow Backdate",
        help="If enabled, POS orders and sessions will use the session start date as their order date and closing date."
    )


class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.model
    def create(self, vals):
        if vals.get('session_id'):
            session = self.env['pos.session'].browse(vals['session_id'])
            if session and session.config_id.allow_backdate:  # ✅ only apply if config allows
                if session.start_at:
                    vals['date_order'] = session.start_at
                elif session.create_date:
                    vals['date_order'] = session.create_date
        return super(PosOrder, self).create(vals)


class PosSession(models.Model):
    _inherit = 'pos.session'

    def action_pos_session_close(self, balancing_account=False, amount_to_balance=0, bank_payment_method_diffs=None):
        res = super(PosSession, self).action_pos_session_close(
            balancing_account, amount_to_balance, bank_payment_method_diffs
        )
        for session in self:
            if session.config_id.allow_backdate:
                if session.start_at:
                    session.write({'stop_at': session.start_at})
                elif session.create_date:
                    session.write({'stop_at': session.create_date})

            if session.config_id.allow_backdate:
                backdate = session.start_at or session.create_date

                if backdate:
                    session.write({'stop_at': backdate})
                    if session.move_id:
                        move = session.move_id.sudo()
                        if move.state == "posted":
                            move.button_draft()  # unpost
                            move.write({"date": backdate.date()})
                            move._post()  # repost
                        else:
                            move.write({"date": backdate.date()})
        return res