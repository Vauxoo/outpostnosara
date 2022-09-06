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
    'version': '14.0.1.1.11',
    'depends': [
        'l10n_cr',
        'l10n_cr_edi',
        'account_accountant',
        'helpdesk',
        'hr_holidays',
        'hr_attendance',
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
        'theme_nosara',
        'payment_credomatic',
        'website_helpdesk',
        'website_point_of_sale',
        'payment_immediate_credit',
    ],
    'test': [
    ],
    'data': [
        # Data
        'data/res_company_data.xml',
        'data/res_users_data.xml',
        'data/reservation_type.xml',
        'data/website_data.xml',
        'data/crm_tags.xml',
        'data/website_crm.xml',
        'data/ir_config_parameter.xml',
        'data/email_templates.xml',

        # Views
        'views/hr_employee_views.xml',
        'views/sale_subscription_views.xml',
        'views/sale_views.xml',
        'views/pms_room_type_views.xml',
        'views/pms_reservation_views.xml',
        'views/pms_lock_views.xml',
        'views/pms_folio_views.xml',
        'views/product_views.xml',
        'views/res_partner.xml',
        'views/pms_property_views.xml',
        'views/website_views.xml',

        # Website
        'views/assets.xml',
        'views/images_library.xml',
        'views/templates/portal_templates.xml',
        'views/templates/layout_templates.xml',
        'views/templates/website_sale_templates.xml',
        'views/templates/website_application_templates.xml',
        'views/templates/contact_page.xml',

        # Security
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
