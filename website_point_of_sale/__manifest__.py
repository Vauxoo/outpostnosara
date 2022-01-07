# Copyright 2022 Vauxoo (https://www.vauxoo.com) <info@vauxoo.com>
# License OPL-1 (https://www.odoo.com/documentation/user/13.0/legal/licenses/licenses.html).
{
    'name': 'Website POS Information',
    'summary': '''
    Users with portal accounts can see their Pos Orders on My Account page
    ''',
    'author': 'Vauxoo',
    'website': 'http://www.vauxoo.com',
    'license': 'OPL-1',
    'category': 'Website/Website',
    'version': '14.0.0.0.0',
    'price': 50,
    'currency': 'USD',
    'depends': [
        'point_of_sale',
        'portal',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/templates.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
