# Copyright 2020 Vauxoo (https://www.vauxoo.com) <info@vauxoo.com>
# License OPL-1 (https://www.odoo.com/documentation/user/13.0/legal/licenses/licenses.html).
{
    'name': 'Payment credomatic',
    'summary': '''
    Payment Acquirer for credomatic
    ''',
    'author': 'Vauxoo',
    'website': 'http://www.vauxoo.com',
    'license': 'OPL-1',
    'category': 'Installer',
    'version': '14.0.0.0.0',
    'price': 570,
    'currency': 'USD',
    'depends': [
        'payment',
        'sale',
        'sale_management',
        'website_sale'
    ],
    'data': [
        'views/assets.xml',
        'views/card_form_template.xml',
        'views/website_sale.xml',
        'views/payment_views.xml',
        'data/payment_acquirer_data.xml',
    ],
    "demo": [
        "demo/res_user_demo.xml",
        "demo/product_pricelist.xml",
    ],
    'qweb': [
        'static/src/xml/providers.xml',
    ],
    'images': [
        'static/description/main_screen.jpeg'
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'live_test_url': 'https://www.vauxoo.com/r/credomaticpay_130',
}
