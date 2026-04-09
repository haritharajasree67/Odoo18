# -*- coding: utf-8 -*-
from odoo import models, fields, api
import json


class TrialBalanceWizard(models.TransientModel):
    _name = 'trial.balance.wizard'
    _description = 'Trial Balance Report Wizard'

    date_from = fields.Date(
        string='Start Date',
        default=lambda self: fields.Date.today().replace(month=1, day=1)
    )
    date_to = fields.Date(
        string='End Date',
        default=fields.Date.today
    )
    target_move = fields.Selection([
        ('posted', 'All Posted Entries'),
        ('all', 'All Entries'),
    ], string='Target Moves', required=True, default='posted')
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )
    journal_ids = fields.Many2many(
        'account.journal',
        string='Journals'
    )
    account_ids = fields.Many2many(
        'account.account',
        string='Accounts'
    )

    def action_view_report(self):
        """Open the dynamic trial balance report view"""
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'trial_balance_report.action_trial_balance_report'
        )
        action['context'] = {
            'wizard_id': self.id,
            'date_from': str(self.date_from) if self.date_from else '',
            'date_to': str(self.date_to) if self.date_to else '',
            'target_move': self.target_move,
            'company_id': self.company_id.id,
            'journal_ids': self.journal_ids.ids,
            'account_ids': self.account_ids.ids,
        }
        return action

    def _create_report_record(self):
        """Create a trial.balance.report transient record and return it"""
        self.ensure_one()
        report = self.env['trial.balance.report'].create({
            'date_from': self.date_from,
            'date_to': self.date_to,
            'target_move': self.target_move,
            'company_id': self.company_id.id,
        })
        if self.journal_ids:
            report.journal_ids = self.journal_ids
        if self.account_ids:
            report.account_ids = self.account_ids
        return report

    def get_report_data_json(self):
        """Return report data as JSON for the JS client"""
        report = self._create_report_record()
        data = report.get_report_data()
        return data
