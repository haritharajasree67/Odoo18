from odoo import models


class ReportDioBankBook(models.AbstractModel):
    """
    QWeb report model for dio_bank_book.
    Odoo automatically calls _get_report_values() when rendering
    the template 'dio_bank_book.report_dio_bank_book'.
    The model name MUST be:  report.<report_name with dots replaced by dots>
    i.e. report.dio_bank_book.report_dio_bank_book
    """
    _name = 'report.dio_bank_book.report_dio_bank_book'
    _description = 'Bank Book Report Renderer'

    def _get_report_values(self, docids, data=None):
        """
        Called by Odoo's report engine before rendering the QWeb template.
        `data` contains everything passed from the controller, including
        data['accounts'] which we serialised in the controller.
        """
        accounts = []
        if data and isinstance(data, dict):
            accounts = data.get('accounts', [])

        return {
            'accounts': accounts,
            'data':     data or {},
        }