{
    'name': 'Bank Book',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Reporting',
    'summary': 'Bank Book Report — interactive OWL view with PDF & XLSX export',
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
    'depends': ['account'],
    'data': [
        'report/paperformat.xml',
        'report/bankbook_tmpl.xml',
        'report/bankbook_action.xml',
        'views/menu.xml',

    ],

    "assets": {
        "web.assets_backend": [
            "dio_bank_book/static/src/css/bank_book.css",
            "dio_bank_book/static/src/js/bank_book.js",
            "dio_bank_book/static/src/xml/bank_book.xml",

        ],
    },
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'AGPL-3',
    
}

