# -*- coding: utf-8 -*-
{
    'name': 'DIO Cash Book',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Reporting',
    'summary': 'Cash Book Report — interactive OWL view with PDF & XLSX export',
    'description': """
        A dedicated Cash Book report module that mirrors the Bank Book module.
        Filters data to cash-type journals only.
        Features:
          - Interactive OWL-based view with live filtering
          - Filter by date range, journals, accounts, target moves, sort order
          - Initial balances toggle
          - PDF export via QWeb
          - XLSX export via xlsxwriter
    """,
    'author': "",
    'website': '',
    'depends': ['account', 'om_account_daily_reports'],
    'data': [
        'security/ir.model.access.csv',
        'reports/cash_book_report_template.xml',
        'reports/cash_book_report_action.xml',
        'reports/paperformat.xml',
        'views/cash_book_menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'dio_cash_book/static/src/css/cash_book.css',
            'dio_cash_book/static/src/js/cash_book.js',
            'dio_cash_book/static/src/xml/cash_book.xml',
        ],
    },
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'AGPL-3',
    
}
