from datetime import datetime
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase
from odoo.tests.common import Form


class TestPmsReservation(TransactionCase):

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

    def _create_reservation(self):
        today = datetime.today().date()
        reservation = self.env['pms.reservation'].create({
            'room_type_id': self.room_type.id,
            'partner_id': self.partner.id,
            'pms_property_id': self.property.id,
            'checkin': today,
            'checkout': today,
            "reservation_line_ids": [
                (0, False, {"date": today}),
            ],
        })
        return reservation

    def test_001_pms_reservation(self):
        msg = "Room line Exact Check In Datetime Should be less than the Exact Check Out Datetime!"
        reservation = self._create_reservation()
        with self.assertRaisesRegex(UserError, msg):
            with Form(reservation) as reserv:
                reserv.arrival_hour = '14:00'
            reservation.check_in_out_dates()
        reservation = self._create_reservation()
        self.assertRecordValues(reservation, [{
            'arrival_hour': '12:00',
            'departure_hour': '14:00',
        }])
