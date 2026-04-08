{
    'name': "Account Reconcile",
    'version': '18.0.1.0.0',
    'author': "",
    'website': '',
    'category': 'Accounts',
    'description': """ Make account reconciliation in Odoo Community faster and more reliable,
    ensuring your invoices and payments are properly matched with minimal effort.""",
    'depends': [ 'account'],
    'data': [

        'security/ir.model.access.csv',
        'views/account_move_line.xml',
        'wizard/account_reconcile_wizard.xml',
        'views/menu.xml',




    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
 
}