# Copyright 2021 Vauxoo
# License LGPL-3 or later (http://www.gnu.org/licenses/lgpl).
{
    'name': 'Instance Creator',
    'summary': '''
    Instance creator for outpostnosara. This is the app.
    ''',
    'author': 'Vauxoo',
    'website': 'https://www.vauxoo.com',
    'license': 'LGPL-3',
    'category': 'Installer',
    'version': '14.0.1.0.3',
    'depends': [
        'l10n_cr',
        'l10n_cr_edi',
        'account_accountant',
        'helpdesk',
        'hr_holidays',
        'iot',
        'mass_mailing',
        'point_of_sale',
        'purchase',
        'sale_management',
        'sale_subscription',
        'stock',
        'timesheet_grid',
        'website_sale',
        'website_calendar',
        'report_xlsx_helper',
        'pms_housekeeping',
        'pms_rooming_xls',
        'maintenance',
        'crm',
    ],
    'test': [
    ],
    'data': [
        # Data
        'data/res_company_data.xml',
        'data/reservation_type.xml',
        # Views
        'views/hr_employee_views.xml',
        'views/sale_subscription_views.xml',
        'views/pms_room_type_views.xml',
        # Website
        'views/assets.xml',
        'views/templates/portal_templates.xml',
        'views/templates/website_sale_templates.xml',
        # Security
        'security/ir.model.access.csv',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
