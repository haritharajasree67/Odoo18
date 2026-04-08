# -*- coding: utf-8 -*-
import io
import base64
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class CashBookController(http.Controller):

    def _resolve_params(self, kwargs):
        return {
            'date_from':       kwargs.get('date_from') or False,
            'date_to':         kwargs.get('date_to') or False,
            'target_move':     kwargs.get('target_move', 'posted'),
            'sortby':          kwargs.get('sortby', 'sort_date'),
            'display_account': kwargs.get('display_account', 'movement'),
            'initial_balance': bool(kwargs.get('initial_balance', False)),
            'journal_ids':     kwargs.get('journal_ids') or [],
            'account_ids':     kwargs.get('account_ids') or [],
        }

    def _get_accounts(self, env, account_ids):
        """Resolve accounts — defaults to cash-type journal accounts."""
        accounts = env['account.account']
        if account_ids:
            accounts = env['account.account'].browse(account_ids).exists()
        if not accounts:
            journals = env['account.journal'].search([('type', '=', 'cash')])
            for journal in journals:
                if journal.default_account_id:
                    accounts |= journal.default_account_id
                for line in journal.outbound_payment_method_line_ids:
                    if line.payment_account_id:
                        accounts |= line.payment_account_id
                for line in journal.inbound_payment_method_line_ids:
                    if line.payment_account_id:
                        accounts |= line.payment_account_id
        return accounts

    def _get_records(self, env, params):
        ctx = {
            'journal_ids':  params['journal_ids'] or False,
            'state':        params['target_move'],
            'strict_range': bool(params['date_from']),
        }
        if params['date_from']:
            ctx['date_from'] = params['date_from']
        if params['date_to']:
            ctx['date_to'] = params['date_to']

        accounts = self._get_accounts(env, params['account_ids'])
        if not accounts:
            return []
        # Reuse the existing om_account_daily_reports cashbook report engine
        report = env['report.om_account_daily_reports.report_cashbook']
        return report.with_context(**ctx)._get_account_move_entry(
            accounts,
            params['initial_balance'],
            params['sortby'],
            params['display_account'],
        )

    def _serialize(self, records):
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

    # ── JSON preview ──────────────────────────────────────────────────────────
    @http.route('/cash_book/get_data', type='json', auth='user', methods=['POST'])
    def get_cash_book_data(self, **kwargs):
        try:
            params  = self._resolve_params(kwargs)
            records = self._get_records(request.env, params)
            return {'status': 'ok', 'data': self._serialize(records)}
        except Exception:
            _logger.exception("CashBookController.get_cash_book_data failed")
            return {'status': 'error', 'data': [], 'message': 'Server error — check Odoo logs'}

    # ── PDF download ──────────────────────────────────────────────────────────
    @http.route('/cash_book/get_pdf', type='json', auth='user', methods=['POST'])
    def get_cash_book_pdf(self, **kwargs):
        try:
            params  = self._resolve_params(kwargs)
            env     = request.env

            records  = self._get_records(env, params)
            accounts = self._serialize(records)

            if not accounts:
                return {'status': 'error', 'message': 'No data found for the selected filters.'}

            report_data = {
                'accounts':    accounts,
                'date_from':   params['date_from'] or '',
                'date_to':     params['date_to']   or '',
                'target_move': params['target_move'],
                'form': {
                    'date_from':   params['date_from'] or '',
                    'date_to':     params['date_to']   or '',
                    'target_move': params['target_move'],
                },
            }

            report_name = 'dio_cash_book.report_dio_cash_book'
            pdf_content, _ = env['ir.actions.report']._render_qweb_pdf(
                report_name, [], data=report_data
            )

            date_label = (params['date_from'] or 'all').replace('-', '')
            filename   = f"cash_book_{date_label}.pdf"
            attachment = env['ir.attachment'].sudo().create({
                'name':      filename,
                'type':      'binary',
                'datas':     base64.b64encode(pdf_content).decode(),
                'mimetype':  'application/pdf',
                'res_model': 'account.cashbook.report',
            })
            return {
                'status':   'ok',
                'url':      f'/web/content/{attachment.id}?download=true',
                'filename': filename,
            }

        except Exception:
            _logger.exception("CashBookController.get_cash_book_pdf failed")
            return {'status': 'error', 'message': 'PDF generation failed — check Odoo logs'}

    # ── XLSX export ───────────────────────────────────────────────────────────
    @http.route('/cash_book/get_xlsx', type='json', auth='user', methods=['POST'])
    def get_cash_book_xlsx(self, **kwargs):
        try:
            import xlsxwriter

            params  = self._resolve_params(kwargs)
            records = self._get_records(request.env, params)
            data    = self._serialize(records)

            output    = io.BytesIO()
            workbook  = xlsxwriter.Workbook(output, {'in_memory': True})
            worksheet = workbook.add_worksheet('Cash Book')

            # ── Formats ──────────────────────────────────────────────────────
            fmt_title    = workbook.add_format({'bold': True, 'font_size': 14, 'font_color': '#1b5e20'})
            fmt_header   = workbook.add_format({'bold': True, 'bg_color': '#1b5e20', 'font_color': '#ffffff',
                                                'border': 1, 'align': 'center', 'valign': 'vcenter'})
            fmt_account  = workbook.add_format({'bold': True, 'bg_color': '#e8f5e9', 'border': 1, 'font_size': 11})
            fmt_num_acc  = workbook.add_format({'bold': True, 'bg_color': '#e8f5e9', 'border': 1,
                                                'num_format': '#,##0.00', 'align': 'right'})
            fmt_line     = workbook.add_format({'border': 1, 'font_size': 10})
            fmt_num      = workbook.add_format({'border': 1, 'num_format': '#,##0.00', 'align': 'right', 'font_size': 10})
            fmt_num_pos  = workbook.add_format({'border': 1, 'num_format': '#,##0.00', 'align': 'right',
                                                'font_color': '#2e7d32', 'font_size': 10})
            fmt_num_neg  = workbook.add_format({'border': 1, 'num_format': '#,##0.00', 'align': 'right',
                                                'font_color': '#c62828', 'font_size': 10})
            fmt_init     = workbook.add_format({'italic': True, 'bg_color': '#fff9c4', 'border': 1, 'font_size': 10})
            fmt_init_num = workbook.add_format({'italic': True, 'bg_color': '#fff9c4', 'border': 1,
                                                'num_format': '#,##0.00', 'align': 'right', 'font_size': 10})

            # ── Column widths ─────────────────────────────────────────────────
            worksheet.set_column(0, 0, 14)   # Date
            worksheet.set_column(1, 1, 8)    # JRNL
            worksheet.set_column(2, 2, 22)   # Partner
            worksheet.set_column(3, 3, 18)   # Ref
            worksheet.set_column(4, 4, 18)   # Move
            worksheet.set_column(5, 5, 35)   # Label
            worksheet.set_column(6, 8, 16)   # Debit / Credit / Balance

            # ── Title row ─────────────────────────────────────────────────────
            date_from_label = params['date_from'] or 'All'
            date_to_label   = params['date_to']   or 'All'
            worksheet.merge_range(0, 0, 0, 8,
                f"Account Cash Book   {date_from_label} — {date_to_label}", fmt_title)
            worksheet.set_row(0, 22)

            # ── Header row ────────────────────────────────────────────────────
            for col, h in enumerate(['Date', 'JRNL', 'Partner', 'Ref', 'Move',
                                      'Entry Label', 'Debit', 'Credit', 'Balance']):
                worksheet.write(1, col, h, fmt_header)
            worksheet.set_row(1, 18)

            # ── Data rows ─────────────────────────────────────────────────────
            row = 2
            for account in data:
                worksheet.merge_range(row, 0, row, 5,
                    f"{account['code']} — {account['name']}", fmt_account)
                worksheet.write(row, 6, account['debit'],   fmt_num_acc)
                worksheet.write(row, 7, account['credit'],  fmt_num_acc)
                worksheet.write(row, 8, account['balance'], fmt_num_acc)
                row += 1
                for line in account['move_lines']:
                    is_init = line['lname'] == 'Initial Balance'
                    lf  = fmt_init     if is_init else fmt_line
                    nf  = fmt_init_num if is_init else fmt_num
                    pf  = fmt_init_num if is_init else fmt_num_pos
                    ngf = fmt_init_num if is_init else fmt_num_neg
                    worksheet.write(row, 0, line['ldate'],        lf)
                    worksheet.write(row, 1, line['lcode'],        lf)
                    worksheet.write(row, 2, line['partner_name'], lf)
                    worksheet.write(row, 3, line['lref'],         lf)
                    worksheet.write(row, 4, line['move_name'],    lf)
                    worksheet.write(row, 5, line['lname'],        lf)
                    worksheet.write(row, 6, line['debit'],        nf)
                    worksheet.write(row, 7, line['credit'],       nf)
                    worksheet.write(row, 8, line['balance'],
                                    pf if line['balance'] >= 0 else ngf)
                    row += 1

            workbook.close()

            filename   = f"cash_book_{(params['date_from'] or 'all').replace('-', '')}.xlsx"
            attachment = request.env['ir.attachment'].sudo().create({
                'name':      filename,
                'type':      'binary',
                'datas':     base64.b64encode(output.getvalue()).decode(),
                'mimetype':  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'res_model': 'account.cashbook.report',
            })
            return {
                'status':   'ok',
                'url':      f'/web/content/{attachment.id}?download=true',
                'filename': filename,
            }

        except Exception:
            _logger.exception("CashBookController.get_cash_book_xlsx failed")
            return {'status': 'error', 'message': 'XLSX generation failed — check Odoo logs'}
