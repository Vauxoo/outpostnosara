from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    set_folio_subscription(cr)


def set_folio_subscription(cr):
    env = api.Environment(cr, SUPERUSER_ID, {})
    cr.execute("select id, folio_id from sale_subscription where folio_id is not null")
    subs = cr.dictfetchall()
    for sub in subs:
        folio_id = env['pms.folio'].browse(sub['folio_id'])
        folio_id.subscription_id = sub['id']
