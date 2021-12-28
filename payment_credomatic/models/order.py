# Copyright 2020 Vauxoo (https://www.vauxoo.com) <info@vauxoo.com>
# License OPL-1 (https://www.odoo.com/documentation/user/13.0/legal/licenses/licenses.html).

import uuid
from odoo import models, fields


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    fac_order_id = fields.Char(help='External reference for FAC Order Id.')

    def get_credomatic_uuid(self):
        self.ensure_one()
        # it is always regenerated so that for each payment the reference is unique
        self.fac_order_id = 'SO_%i_%s' % (self.id, uuid.uuid4().hex)
        return self.fac_order_id
