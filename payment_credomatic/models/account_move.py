# Copyright 2020 Vauxoo (https://www.vauxoo.com) <info@vauxoo.com>
# License OPL-1 (https://www.odoo.com/documentation/user/13.0/legal/licenses/licenses.html).

import uuid
from odoo import models, fields


class AccountMove(models.Model):

    _inherit = 'account.move'

    fac_order_id = fields.Char(help='External reference for FAC Order Id.')

    def get_credomatic_uuid(self):
        self.ensure_one()
        # it is always regenerated so that for each payment the reference is unique
        self.fac_order_id = 'INV_%i_%s' % (self.id, uuid.uuid4().hex)
        return self.fac_order_id
