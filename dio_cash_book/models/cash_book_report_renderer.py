# -*- coding: utf-8 -*-
from odoo import models


class ReportDioCashBook(models.AbstractModel):
    """
    QWeb report model for dio_cash_book.
    Odoo automatically calls _get_report_values() when rendering
    the template 'dio_cash_book.report_dio_cash_book'.
    The model name MUST match: report.<module>.<report_name>
    """
    _name = 'report.dio_cash_book.report_dio_cash_book'
    _description = 'Cash Book Report Renderer'

    def _get_report_values(self, docids, data=None):
        """
        Called by Odoo's report engine before rendering the QWeb template.
        `data` contains everything passed from the controller, including
        data['accounts'] which is serialised in the controller.
        """
        accounts = []
        if data and isinstance(data, dict):
            accounts = data.get('accounts', [])

        return {
            'accounts': accounts,
            'data':     data or {},
        }
