{
    'name': 'Outstanding Statement',
    'summary': 'Customer & Supplier outstanding statement',
    'version': '18.0.0.1',
    'category': 'Account',
    'description': """ This module allows to find the outstanding amount.""",
    'depends': ['account',],
    'data': [
        'report/report_template.xml',
        'report/supplier_template.xml',
        'views/menu.xml',
    ],

    "assets": {
            "web.assets_backend": [
                'outstanding_statement/static/src/js/customer_invoice.js',
                'outstanding_statement/static/src/js/supplier.js',
                'outstanding_statement/static/src/xml/customer_invoice.xml',
                'outstanding_statement/static/src/xml/supplier.xml',
            ],
        },



    'images': ['static/description/banner.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'AGPL-3',
    
}