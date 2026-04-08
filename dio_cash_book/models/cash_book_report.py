# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from datetime import date
import logging

_logger = logging.getLogger(__name__)


class AccountCashBookReport(models.TransientModel):
    _name = "account.cashbook.report"
    _description = "Cash Book Report"

    def _get_default_account_ids(self):
        """Return default accounts from cash-type journals."""
        journals = self.env['account.journal'].search([('type', '=', 'cash')])
        accounts = self.env['account.account']
        for journal in journals:
            if journal.default_account_id:
                accounts += journal.default_account_id
            for acc_out in journal.outbound_payment_method_line_ids:
                if acc_out.payment_account_id:
                    accounts += acc_out.payment_account_id
            for acc_in in journal.inbound_payment_method_line_ids:
                if acc_in.payment_account_id:
                    accounts += acc_in.payment_account_id
        return accounts

    date_from = fields.Date(string='Start Date', default=date.today(), required=True)
    date_to = fields.Date(string='End Date', default=date.today(), required=True)
    target_move = fields.Selection(
        [('posted', 'Posted Entries'), ('all', 'All Entries')],
        string='Target Moves', required=True, default='posted'
    )
    journal_ids = fields.Many2many(
        'account.journal', string='Journals', required=True,
        default=lambda self: self.env['account.journal'].search([('type', '=', 'cash')])
    )
    account_ids = fields.Many2many(
        'account.account', 'account_account_cashbook_report',
        'report_line_id', 'account_id', 'Accounts',
        default=_get_default_account_ids
    )
    display_account = fields.Selection(
        [('all', 'All'), ('movement', 'With movements'),
         ('not_zero', 'With balance is not equal to 0')],
        string='Display Accounts', required=True, default='movement'
    )
    sortby = fields.Selection(
        [('sort_date', 'Date'), ('sort_journal_partner', 'Journal & Partner')],
        string='Sort by', required=True, default='sort_date'
    )
    initial_balance = fields.Boolean(string='Include Initial Balances')

    def _build_comparison_context(self, data):
        return {
            'journal_ids': data['form'].get('journal_ids') or False,
            'state': data['form'].get('target_move') or '',
            'date_from': data['form'].get('date_from') or False,
            'date_to': data['form'].get('date_to') or False,
            'strict_range': bool(data['form'].get('date_from')),
        }

    def check_report(self):
        data = {}
        data['form'] = self.read([
            'target_move', 'date_from', 'date_to', 'journal_ids',
            'account_ids', 'sortby', 'initial_balance', 'display_account'
        ])[0]
        data['form']['comparison_context'] = self._build_comparison_context(data)
        return self.env.ref(
            'om_account_daily_reports.action_report_cash_book'
        ).report_action(self, data=data)

    @api.model
    def get_cash_book_data(self, params):
        """
        Called via RPC from the OWL CashBook component.
        Accepts a single dict `params`.
        """
        try:
            date_from       = params.get('date_from') or False
            date_to         = params.get('date_to') or False
            target_move     = params.get('target_move', 'posted')
            sortby          = params.get('sortby', 'sort_date')
            display_account = params.get('display_account', 'movement')
            initial_balance = params.get('initial_balance', False)
            journal_ids     = params.get('journal_ids') or []
            account_ids     = params.get('account_ids') or []

            ctx = {
                'journal_ids':  journal_ids or False,
                'state':        target_move,
                'date_from':    date_from,
                'date_to':      date_to,
                'strict_range': bool(date_from),
            }

            accounts = self.env['account.account']
            if account_ids:
                accounts = self.env['account.account'].browse(account_ids).exists()

            if not accounts:
                journals = self.env['account.journal'].search([('type', '=', 'cash')])
                for journal in journals:
                    if journal.default_account_id:
                        accounts |= journal.default_account_id
                    for line in journal.outbound_payment_method_line_ids:
                        if line.payment_account_id:
                            accounts |= line.payment_account_id
                    for line in journal.inbound_payment_method_line_ids:
                        if line.payment_account_id:
                            accounts |= line.payment_account_id

            if not accounts:
                return []

            report = self.env['report.om_account_daily_reports.report_cashbook']
            records = report.with_context(**ctx)._get_account_move_entry(
                accounts, initial_balance, sortby, display_account
            )

            result = []
            for account in records:
                move_lines = []
                for line in account.get('move_lines', []):
                    ldate = line.get('ldate', '')
                    move_lines.append({
                        'lid':             line.get('lid') or 0,
                        'ldate':           str(ldate) if ldate else '',
                        'lcode':           line.get('lcode') or '',
                        'partner_name':    line.get('partner_name') or '',
                        'lref':            line.get('lref') or '',
                        'move_name':       line.get('move_name') or '',
                        'lname':           line.get('lname') or '',
                        'debit':           float(line.get('debit') or 0.0),
                        'credit':          float(line.get('credit') or 0.0),
                        'balance':         float(line.get('balance') or 0.0),
                        'amount_currency': float(line.get('amount_currency') or 0.0),
                        'currency_code':   line.get('currency_code') or '',
                    })
                result.append({
                    'code':       account.get('code', ''),
                    'name':       account.get('name', ''),
                    'debit':      float(account.get('debit') or 0.0),
                    'credit':     float(account.get('credit') or 0.0),
                    'balance':    float(account.get('balance') or 0.0),
                    'move_lines': move_lines,
                })
            return result

        except Exception:
            _logger.exception("get_cash_book_data failed — params: %s", params)
            raise
