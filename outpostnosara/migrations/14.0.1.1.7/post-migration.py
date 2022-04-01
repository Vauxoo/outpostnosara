from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    if not version:
        return

    env = api.Environment(cr, SUPERUSER_ID, {})
    update_logo_url(env)
    update_menus(env)


def update_logo_url(env):
    website = env.ref('website.default_website', False)
    if website:
        website.write({'logo_url': "https://outpostnosara.com"})


def update_menus(env):
    website = env.ref('website.default_website', False)
    group_user = env.ref('base.group_user', False)
    group_portal = env.ref('base.group_portal', False)
    if website and group_user and group_portal:
        main_menu = website.menu_id
        groups = group_user | group_portal
        user_menu = main_menu.child_id.filtered(lambda m: m.url != '/contactus')
        user_menu.group_ids = [(6, 0, groups.ids)]
