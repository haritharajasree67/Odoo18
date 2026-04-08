{
    'name': 'POS Discount Price',
    'summary': 'POS Discount in Price',
    'version': '18.0.1.0.0',
    'category': 'Point of Sale',
    'description': """ This module allows to add discount in amount.""",
    'depends': ['point_of_sale',],
    'data': [
        'views/pos_form.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_discount_price/static/src/app/discount_button.xml',
            'pos_discount_price/static/src/app/discount_button.js',
        ],
    },
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'AGPL-3',

}