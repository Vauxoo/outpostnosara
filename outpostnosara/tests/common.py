from odoo.tests.common import TransactionCase


class PmsTransactionCase(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env.ref('base.res_partner_address_15')
        self.property = self.env['pms.property'].create({
            'name': 'Property Test',
            'company_id': self.env.company.id,
        })
        self.room_type_class = self.env['pms.room.type.class'].create({
            'name': "Room Type Test",
            'default_code': 'RTT01',
        })
        self.room_type = self.env['pms.room.type'].create({
            'name': 'Single Room Test',
            'pms_property_ids': [self.property.id],
            'default_code': 'STT01',
            'class_id': self.room_type_class.id,
        })
        self.room = self.env['pms.room'].create({
            'name': 'Single Room Test',
            'pms_property_id': self.property.id,
            'room_type_id': self.room_type.id,
            'capacity': 1,
        })
