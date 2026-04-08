{
    'name': 'Global Discount in Invoice',
    'version': '18.0.1.0.0',
    'summary': 'Global Discount in Invoice',
    'category': 'Account',
    'depends': ['account'],
    'data': [

        'security/ir.model.access.csv',
        'views/account.xml',
        'wizard/account_move_discount_view.xml',



    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'AGPL-3',
}