# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request, content_disposition
from io import BytesIO
import xlsxwriter


class CustomerStatementController(http.Controller):

    @http.route('/web/export/customer_statement_excel', type='http', auth='user')
    def export_customer_statement_excel(self, partner_id, date_from, date_to, **kwargs):
        """Export customer statement to Excel"""

        # Get the statement data
        partner_id = int(partner_id)
        AccountMove = request.env['account.move']

        result = AccountMove.get_customer_statement(
            partner_id=partner_id,
            date_from=date_from,
            date_to=date_to
        )

        # Get partner name
        partner = request.env['res.partner'].browse(partner_id)

        # Create Excel file
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Statement')

        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D3D3D3',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })

        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center'
        })

        date_format = workbook.add_format({
            'border': 1,
            'align': 'left'
        })

        number_format = workbook.add_format({
            'border': 1,
            'align': 'right',
            'num_format': '#,##0.000'
        })

        total_format = workbook.add_format({
            'bold': True,
            'bg_color': '#E8E8E8',
            'border': 1,
            'align': 'right',
            'num_format': '#,##0.000'
        })

        total_label_format = workbook.add_format({
            'bold': True,
            'bg_color': '#E8E8E8',
            'border': 1,
            'align': 'center'
        })

        # Set column widths
        worksheet.set_column('A:A', 15)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:D', 20)
        worksheet.set_column('E:E', 20)

        # Write title
        worksheet.merge_range('A1:E1', 'Outstanding Statement', title_format)
        worksheet.write('A2', f'Customer: {partner.name}')
        worksheet.write('A3', f'Period: {date_from} to {date_to}')

        # Write headers
        row = 4
        worksheet.write(row, 0, 'Date', header_format)
        worksheet.write(row, 1, 'Invoice No', header_format)
        worksheet.write(row, 2, 'Invoice Amount (BHD)', header_format)
        worksheet.write(row, 3, 'Received Amount (BHD)', header_format)
        worksheet.write(row, 4, 'Balance (BHD)', header_format)

        # Write data
        row = 5
        for line in result.get('lines', []):
            worksheet.write(row, 0, line.get('date', ''), date_format)
            worksheet.write(row, 1, line.get('invoice_no', ''), date_format)

            # Convert string amounts to floats
            try:
                invoice_amount = float(line.get('invoice_amount', '0').replace(',', ''))
            except:
                invoice_amount = 0.0

            try:
                received_amount = float(line.get('received_amount', '0').replace(',', ''))
            except:
                received_amount = 0.0

            try:
                balance = float(line.get('balance', '0').replace(',', ''))
            except:
                balance = 0.0

            worksheet.write_number(row, 2, invoice_amount, number_format)
            worksheet.write_number(row, 3, received_amount, number_format)
            worksheet.write_number(row, 4, balance, number_format)
            row += 1

        # Write totals
        try:
            total_invoice = float(result.get('total_invoice', '0').replace(',', ''))
        except:
            total_invoice = 0.0

        try:
            total_received = float(result.get('total_received', '0').replace(',', ''))
        except:
            total_received = 0.0

        try:
            total_balance = float(result.get('total_balance', '0').replace(',', ''))
        except:
            total_balance = 0.0

        worksheet.merge_range(row, 0, row, 1, 'Total', total_label_format)
        worksheet.write_number(row, 2, total_invoice, total_format)
        worksheet.write_number(row, 3, total_received, total_format)
        worksheet.write_number(row, 4, total_balance, total_format)

        workbook.close()
        output.seek(0)

        # Prepare filename
        filename = f'Customer_Statement_{partner.name}_{date_from}_to_{date_to}.xlsx'

        # Return the Excel file
        return request.make_response(
            output.read(),
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', content_disposition(filename))
            ]
        )


class SupplierStatementController(http.Controller):

    @http.route('/web/export/supplier_statement_excel', type='http', auth='user')
    def export_supplier_statement_excel(self, partner_id, date_from, date_to, **kwargs):
        """Export supplier statement to Excel"""

        # Get the statement data
        partner_id = int(partner_id)
        AccountMove = request.env['account.move']

        result = AccountMove.get_supplier_statement(
            partner_id=partner_id,
            date_from=date_from,
            date_to=date_to
        )

        # Get partner name
        partner = request.env['res.partner'].browse(partner_id)

        # Create Excel file
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Statement')

        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D3D3D3',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })

        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center'
        })

        date_format = workbook.add_format({
            'border': 1,
            'align': 'left'
        })

        number_format = workbook.add_format({
            'border': 1,
            'align': 'right',
            'num_format': '#,##0.000'
        })

        total_format = workbook.add_format({
            'bold': True,
            'bg_color': '#E8E8E8',
            'border': 1,
            'align': 'right',
            'num_format': '#,##0.000'
        })

        total_label_format = workbook.add_format({
            'bold': True,
            'bg_color': '#E8E8E8',
            'border': 1,
            'align': 'center'
        })

        # Set column widths
        worksheet.set_column('A:A', 15)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:D', 20)
        worksheet.set_column('E:E', 20)

        # Write title
        worksheet.merge_range('A1:E1', 'Supplier Outstanding Statement', title_format)
        worksheet.write('A2', f'Supplier: {partner.name}')
        worksheet.write('A3', f'Period: {date_from} to {date_to}')

        # Write headers
        row = 4
        worksheet.write(row, 0, 'Date', header_format)
        worksheet.write(row, 1, 'Bill No', header_format)
        worksheet.write(row, 2, 'Bill Amount (BHD)', header_format)
        worksheet.write(row, 3, 'Paid Amount (BHD)', header_format)
        worksheet.write(row, 4, 'Balance (BHD)', header_format)

        # Write data
        row = 5
        for line in result.get('lines', []):
            worksheet.write(row, 0, line.get('date', ''), date_format)
            worksheet.write(row, 1, line.get('bill_no', ''), date_format)

            # Convert string amounts to floats
            try:
                bill_amount = float(line.get('bill_amount', '0').replace(',', ''))
            except:
                bill_amount = 0.0

            try:
                paid_amount = float(line.get('paid_amount', '0').replace(',', ''))
            except:
                paid_amount = 0.0

            try:
                balance = float(line.get('balance', '0').replace(',', ''))
            except:
                balance = 0.0

            worksheet.write_number(row, 2, bill_amount, number_format)
            worksheet.write_number(row, 3, paid_amount, number_format)
            worksheet.write_number(row, 4, balance, number_format)
            row += 1

        # Write totals
        try:
            total_invoice = float(result.get('total_invoice', '0').replace(',', ''))
        except:
            total_invoice = 0.0

        try:
            total_paid = float(result.get('total_paid', '0').replace(',', ''))
        except:
            total_paid = 0.0

        try:
            total_balance = float(result.get('total_balance', '0').replace(',', ''))
        except:
            total_balance = 0.0

        worksheet.merge_range(row, 0, row, 1, 'Total', total_label_format)
        worksheet.write_number(row, 2, total_invoice, total_format)
        worksheet.write_number(row, 3, total_paid, total_format)
        worksheet.write_number(row, 4, total_balance, total_format)

        workbook.close()
        output.seek(0)

        # Prepare filename
        filename = f'Supplier_Statement_{partner.name}_{date_from}_to_{date_to}.xlsx'

        # Return the Excel file
        return request.make_response(
            output.read(),
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', content_disposition(filename))
            ]
        )