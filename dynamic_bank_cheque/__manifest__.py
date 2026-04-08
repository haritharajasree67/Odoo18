{
    'name': 'Dynamic Bank Cheque Management',
    'version': '18.0.5.0.0',
    'summary': 'Bank Cheque Print',
    'author': '',
    'license': 'LGPL-3',
    'depends': ['base', 'account_payment', 'website', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/cheque_print.xml',
        'wizard/cheque_report.xml',
        'wizard/cheque_print_preview_report.xml',
        'wizard/cheque_attribute_wizard.xml',
        'views/bank_cheque.xml',
        'views/bank_cheque_leaf.xml',
        'views/chequebook.xml',
        'views/cheque_attribute.xml',
        "views/account_payment.xml",
        "views/cheque_configure_template.xml",
        "views/cheque_attribute_template.xml",
        "reports/bank_cheque_report.xml",
        "reports/cheque_report_template.xml",
        "reports/cheque_format_templates.xml",
        "reports/bank_cheque_preview.xml",
    ],

    'assets': {
        'web.assets_backend': [
            'dynamic_bank_cheque/static/src/js/cheque_configure.js',
            'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css',
            'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js',
        ]
    },
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': False,
    'auto_install': False,'license': 'AGPL-3',
   
}


