# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def get_customer_statement(self, partner_id, date_from, date_to):
        """
        Get customer statement showing outstanding invoices and payments within a date range
        """
        if not partner_id:
            return {
                'lines': [],
                'total_invoice': '0.000',
                'total_received': '0.000',
                'total_balance': '0.000',
            }

        # Convert date strings to date objects
        date_from_obj = fields.Date.from_string(date_from)
        date_to_obj = fields.Date.from_string(date_to)

        # Validate dates
        if date_from_obj > date_to_obj:
            raise UserError("From Date cannot be after To Date")

        # Get all customer invoices within the date range
        invoices = self.env['account.move'].search([
            ('partner_id', '=', partner_id),
            ('move_type', '=', 'out_invoice'),  # Changed: only out_invoice, excluded out_refund
            ('state', '=', 'posted'),
            ('invoice_date', '>=', date_from_obj),
            ('invoice_date', '<=', date_to_obj),
        ], order='invoice_date asc, name asc')

        lines = []
        total_invoice = 0.0
        total_received = 0.0
        total_balance = 0.0

        for invoice in invoices:
            # Calculate invoice amount (no need to check move_type anymore)
            invoice_amount = invoice.amount_total

            # Calculate received amount considering only payments up to date_to
            received_amount_upto_date = 0.0

            # Get the receivable line from the invoice
            receivable_line = invoice.line_ids.filtered(
                lambda l: l.account_id.account_type == 'asset_receivable'
            )

            if receivable_line:
                # Get all partial reconciliations
                for partial in receivable_line.matched_debit_ids | receivable_line.matched_credit_ids:
                    # Determine which line is the payment line
                    if partial.debit_move_id.id == receivable_line.id:
                        payment_line = partial.credit_move_id
                        reconcile_amount = partial.amount
                    else:
                        payment_line = partial.debit_move_id
                        reconcile_amount = partial.amount

                    # Check if payment was made before or on date_to
                    if payment_line.date <= date_to_obj:
                        received_amount_upto_date += reconcile_amount

            # Calculate balance (outstanding amount as of the specified date)
            balance = invoice_amount - received_amount_upto_date

            # Include all invoices in the date range, even if fully paid
            # If you want only outstanding invoices, uncomment the condition below:
            # if abs(balance) > 0.01:

            lines.append({
                'id': invoice.id,
                'date': invoice.invoice_date.strftime('%d/%m/%Y') if invoice.invoice_date else '',
                'invoice_no': invoice.name or '',
                'invoice_amount': '{:.3f}'.format(abs(invoice_amount)),
                'received_amount': '{:.3f}'.format(received_amount_upto_date),
                'balance': '{:.3f}'.format(abs(balance)),
            })

            total_invoice += abs(invoice_amount)
            total_received += received_amount_upto_date
            total_balance += abs(balance)

        return {
            'lines': lines,
            'total_invoice': '{:.3f}'.format(total_invoice),
            'total_received': '{:.3f}'.format(total_received),
            'total_balance': '{:.3f}'.format(total_balance),
        }

    @api.model
    def get_supplier_statement(self, partner_id, date_from, date_to):
        """
        Get supplier statement for vendor bills
        Returns outstanding bills and payment information
        """
        if not partner_id:
            return {
                'lines': [],
                'total_invoice': '0.000',
                'total_paid': '0.000',
                'total_balance': '0.000'
            }

        # Search for vendor bills in the date range
        domain = [
            ('partner_id', '=', partner_id),
            ('move_type', '=', 'in_invoice'),  # Vendor bills
            ('state', '=', 'posted'),
            ('invoice_date', '>=', date_from),
            ('invoice_date', '<=', date_to),
        ]

        bills = self.search(domain, order='invoice_date asc, name asc')

        lines = []
        total_invoice = 0.0
        total_paid = 0.0
        total_balance = 0.0

        for bill in bills:
            # Get bill amount (should be positive for vendor bills)
            bill_amount = abs(bill.amount_total)

            # Get paid amount
            paid_amount = abs(bill.amount_total - bill.amount_residual)

            # Get balance (remaining to pay)
            balance = abs(bill.amount_residual)

            lines.append({
                'id': bill.id,
                'date': bill.invoice_date.strftime('%Y-%m-%d') if bill.invoice_date else '',
                'bill_no': bill.name or '',
                'bill_amount': '{:,.3f}'.format(bill_amount),
                'paid_amount': '{:,.3f}'.format(paid_amount),
                'balance': '{:,.3f}'.format(balance),
            })

            total_invoice += bill_amount
            total_paid += paid_amount
            total_balance += balance

        return {
            'lines': lines,
            'total_invoice': '{:,.3f}'.format(total_invoice),
            'total_paid': '{:,.3f}'.format(total_paid),
            'total_balance': '{:,.3f}'.format(total_balance),
        }


class CustomerStatementReport(models.AbstractModel):
    _name = 'report.outstanding_statement.customer_statement_report'
    _description = 'Customer Statement Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        Generate the report values for the customer statement PDF
        """
        if not data:
            data = {}

        partner_id = data.get('partner_id')
        date_from = data.get('date_from')
        date_to = data.get('date_to')

        # Get the statement data using the existing method
        account_move = self.env['account.move']
        statement_data = account_move.get_customer_statement(
            partner_id=partner_id,
            date_from=date_from,
            date_to=date_to
        )

        # Get partner name
        partner = self.env['res.partner'].browse(partner_id)

        # Format dates for display
        date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
        date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')

        # date_from_formatted = date_from_obj.strftime('%B %d, %Y')
        # date_to_formatted = date_to_obj.strftime('%B %d, %Y')

        # Prepare the document data
        docs = {
            'partner_name': partner.name,
            'date_from': date_from,
            'date_to': date_to,
            # 'date_from_formatted': date_from_formatted,
            # 'date_to_formatted': date_to_formatted,
            'lines': statement_data.get('lines', []),
            'total_invoice': statement_data.get('total_invoice', '0.000'),
            'total_received': statement_data.get('total_received', '0.000'),
            'total_balance': statement_data.get('total_balance', '0.000'),
        }

        return {
            'doc_ids': docids,
            'doc_model': 'account.move',
            'docs': docs,
            'data': data,
        }


class SupplierStatementReport(models.AbstractModel):
    _name = 'report.outstanding_statement.supplier_statement_report_template'
    _description = 'Supplier Statement Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        Get report values for supplier statement
        """
        # Get parameters from context
        date_from = self.env.context.get('date_from')
        date_to = self.env.context.get('date_to')
        partner_id = self.env.context.get('active_id')

        # If partner_id not in context, try to get from docids
        if not partner_id and docids:
            partner_id = docids[0] if isinstance(docids, list) else docids

        # Get partner record
        partner = self.env['res.partner'].browse(partner_id)

        # Get statement data using the same method as the web interface
        statement_data = self.env['account.move'].get_supplier_statement(
            partner_id=partner_id,
            date_from=date_from,
            date_to=date_to
        )

        # Format dates for display
        from datetime import datetime
        formatted_date_from = ''
        formatted_date_to = ''

        if date_from:
            date_obj = datetime.strptime(date_from, '%Y-%m-%d')
            formatted_date_from = date_obj.strftime('%B %d, %Y')

        if date_to:
            date_obj = datetime.strptime(date_to, '%Y-%m-%d')
            formatted_date_to = date_obj.strftime('%B %d, %Y')

        return {
            'doc_ids': [partner_id],
            'doc_model': 'res.partner',
            'docs': partner,
            'partner': partner,
            'date_from': date_from,
            'date_to': date_to,
            'formatted_date_from': formatted_date_from,
            'formatted_date_to': formatted_date_to,
            'statement_lines': statement_data.get('lines', []),
            'total_invoice': statement_data.get('total_invoice', '0.000'),
            'total_paid': statement_data.get('total_paid', '0.000'),
            'total_balance': statement_data.get('total_balance', '0.000'),
            'company': self.env.company,
        }
