# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools import float_is_zero


class TrialBalanceReport(models.TransientModel):
    _name = 'trial.balance.report'
    _description = 'Trial Balance Report'

    # Wizard fields (passed from wizard)
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')
    target_move = fields.Selection([
        ('posted', 'All Posted Entries'),
        ('all', 'All Entries'),
    ], string='Target Moves', default='posted')
    company_id = fields.Many2one('res.company', string='Company',
                                  default=lambda self: self.env.company)
    journal_ids = fields.Many2many('account.journal', string='Journals')
    account_ids = fields.Many2many('account.account', string='Accounts')

    def _get_domain(self, date_from=None, date_to=None):
        """Build domain for move lines"""
        domain = [('company_id', '=', self.company_id.id)]

        if self.target_move == 'posted':
            domain += [('move_id.state', '=', 'posted')]

        if self.journal_ids:
            domain += [('journal_id', 'in', self.journal_ids.ids)]

        if self.account_ids:
            domain += [('account_id', 'in', self.account_ids.ids)]

        if date_from:
            domain += [('date', '>=', date_from)]
        if date_to:
            domain += [('date', '<=', date_to)]

        return domain

    def _get_initial_balance(self):
        """Get balances BEFORE date_from (initial/opening balance)"""
        if not self.date_from:
            return {}

        domain = self._get_domain(date_to=fields.Date.from_string(self.date_from) if self.date_from else None)
        # Exclude entries from date_from onwards
        domain += [('date', '<', self.date_from)]

        lines = self.env['account.move.line'].read_group(
            domain,
            ['account_id', 'debit', 'credit'],
            ['account_id']
        )
        result = {}
        for line in lines:
            account_id = line['account_id'][0]
            result[account_id] = {
                'debit': line['debit'],
                'credit': line['credit'],
            }
        return result

    def _get_period_balance(self):
        """Get balances for the selected period (This Financial Year)"""
        domain = self._get_domain()
        if self.date_from:
            domain += [('date', '>=', self.date_from)]
        if self.date_to:
            domain += [('date', '<=', self.date_to)]

        lines = self.env['account.move.line'].read_group(
            domain,
            ['account_id', 'debit', 'credit'],
            ['account_id']
        )
        result = {}
        for line in lines:
            account_id = line['account_id'][0]
            result[account_id] = {
                'debit': line['debit'],
                'credit': line['credit'],
            }
        return result

    def get_report_data(self):
        """
        Main method to compute and return structured report data.
        Returns a list of account groups, each with their accounts.
        """
        initial_balances = self._get_initial_balance()
        period_balances = self._get_period_balance()

        # Get all relevant accounts
        all_account_ids = set(list(initial_balances.keys()) + list(period_balances.keys()))

        if not all_account_ids:
            # If no filter, get all accounts
            accounts = self.env['account.account'].search([
                ('company_ids', 'in', self.company_id.id)
            ])
            all_account_ids = set(accounts.ids)

        accounts = self.env['account.account'].browse(list(all_account_ids)).sorted(
            lambda a: (a.group_id.complete_name or 'zzz', a.code)
        )

        # Group accounts by account group
        groups = {}
        ungrouped_accounts = []

        for account in accounts:
            group = account.group_id
            init_bal = initial_balances.get(account.id, {'debit': 0.0, 'credit': 0.0})
            period_bal = period_balances.get(account.id, {'debit': 0.0, 'credit': 0.0})

            # Ending balance = initial + period
            ending_debit = init_bal['debit'] + period_bal['debit']
            ending_credit = init_bal['credit'] + period_bal['credit']

            account_data = {
                'id': account.id,
                'code': account.code,
                'name': account.name,
                'display_name': account.display_name,
                'initial_debit': init_bal['debit'],
                'initial_credit': init_bal['credit'],
                'period_debit': period_bal['debit'],
                'period_credit': period_bal['credit'],
                'ending_debit': ending_debit,
                'ending_credit': ending_credit,
            }

            if group:
                group_id = group.id
                if group_id not in groups:
                    groups[group_id] = {
                        'id': group_id,
                        'name': group.complete_name,
                        'code_prefix_start': group.code_prefix_start or '',
                        'code_prefix_end': group.code_prefix_end or '',
                        'accounts': [],
                        'initial_debit': 0.0,
                        'initial_credit': 0.0,
                        'period_debit': 0.0,
                        'period_credit': 0.0,
                        'ending_debit': 0.0,
                        'ending_credit': 0.0,
                    }
                groups[group_id]['accounts'].append(account_data)
                groups[group_id]['initial_debit'] += init_bal['debit']
                groups[group_id]['initial_credit'] += init_bal['credit']
                groups[group_id]['period_debit'] += period_bal['debit']
                groups[group_id]['period_credit'] += period_bal['credit']
                groups[group_id]['ending_debit'] += ending_debit
                groups[group_id]['ending_credit'] += ending_credit
            else:
                ungrouped_accounts.append(account_data)

        # Sort groups by name
        sorted_groups = sorted(groups.values(), key=lambda g: g['name'])

        # Handle ungrouped accounts
        if ungrouped_accounts:
            ungrouped = {
                'id': 0,
                'name': 'Ungrouped Accounts',
                'code_prefix_start': '',
                'code_prefix_end': '',
                'accounts': ungrouped_accounts,
                'initial_debit': sum(a['initial_debit'] for a in ungrouped_accounts),
                'initial_credit': sum(a['initial_credit'] for a in ungrouped_accounts),
                'period_debit': sum(a['period_debit'] for a in ungrouped_accounts),
                'period_credit': sum(a['period_credit'] for a in ungrouped_accounts),
                'ending_debit': sum(a['ending_debit'] for a in ungrouped_accounts),
                'ending_credit': sum(a['ending_credit'] for a in ungrouped_accounts),
            }
            sorted_groups.append(ungrouped)

        # Compute grand totals
        totals = {
            'initial_debit': sum(g['initial_debit'] for g in sorted_groups),
            'initial_credit': sum(g['initial_credit'] for g in sorted_groups),
            'period_debit': sum(g['period_debit'] for g in sorted_groups),
            'period_credit': sum(g['period_credit'] for g in sorted_groups),
            'ending_debit': sum(g['ending_debit'] for g in sorted_groups),
            'ending_credit': sum(g['ending_credit'] for g in sorted_groups),
        }

        return {
            'groups': sorted_groups,
            'totals': totals,
            'company': self.company_id.name,
            'date_from': str(self.date_from) if self.date_from else '',
            'date_to': str(self.date_to) if self.date_to else '',
            'currency_symbol': self.company_id.currency_id.symbol or 'BD',
        }
