from datetime import datetime, timedelta, time
from odoo.exceptions import UserError
from odoo.tests.common import Form
from odoo import fields

from . import common


class TestPmsReservation(common.PmsTransactionCase):

    def setUp(self):
        super().setUp()
        self.room_type_availability = self.env["pms.availability.plan"].create({
            "name": "Availability plan for TEST",
        })

    def _create_reservation(self, checkin=None, checkout=None, arrival_hour=None, departure_hour=None):
        today = fields.date.today()
        reservation = self.env['pms.reservation'].create({
            'room_type_id': self.room_type.id,
            'partner_id': self.partner.id,
            'pms_property_id': self.property.id,
            'checkin': checkin or today,
            'checkout': checkout or today,
            'arrival_hour': arrival_hour or self.property.default_arrival_hour,
            'departure_hour': departure_hour or self.property.default_departure_hour,
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

    def test_002_reserve_datetime(self):
        self.property.write({
            'default_arrival_hour': '06:00',
            'default_departure_hour': '18:00',
        })
        reservation = self._create_reservation(arrival_hour='06:00', departure_hour='12:00')
        self.assertEqual(reservation.preferred_room_id, self.room, 'The reservation room should be auto assigned')

        second_reservation = self._create_reservation(arrival_hour='13:00', departure_hour='18:00')
        self.assertEqual(second_reservation.preferred_room_id, self.room,
                         'The reservation room should be auto assigned and should be the same room.'
                         'The hours are not collapsed')

    def test_003_reservation_dates_compute_checkin_out(self):
        """Check the reservation creation with specific reservation lines
        and compute checkin checkout
        ----------------
        Create reservation with correct reservation lines and check
        the checkin and checkout fields. Take into account that the
        checkout of the reservation must be the last day captured
        """
        today = fields.date.today()
        tomorrow = fields.date.today() + timedelta(days=1)
        two_days_later = fields.date.today() + timedelta(days=2)
        reservation = self.env["pms.reservation"].create({
            "room_type_id": self.room_type.id,
            "partner_id": self.partner.id,
            "pms_property_id": self.property.id,
            "reservation_line_ids": [
                (0, False, {"date": today}),
                (0, False, {"date": tomorrow}),
                (0, False, {"date": two_days_later}),
            ],
        })
        self.assertEqual(reservation.checkin, today, "The calculated checkin of the reservation does not correspond "
                                                     "to the first day indicated in the dates")
        self.assertEqual(reservation.checkout, two_days_later,
                         "The calculated checkout of the reservation does not correspond to the last day "
                         "indicated in the dates")

    def test_004_create_reservation_lines_dates(self):
        """Check that the reservation lines are created with the expected date and datetimes
        and if the hours arrival_hour and departure_hour are changed, the datetimes in the lines too.
        """
        def check_line_datetimes(line, arrival_hour=None, departure_hour=None):
            arrival_hour = arrival_hour or 6
            departure_hour = departure_hour or 18
            expected_checkin_datetime = datetime.combine(line.date, time(hour=arrival_hour))
            self.assertEqual(line.checkin_datetime, expected_checkin_datetime)
            expected_checkout_datetime = datetime.combine(line.date, time(hour=departure_hour))
            self.assertEqual(line.checkout_datetime, expected_checkout_datetime)

        self.env.user.tz = 'UTC'
        self.property.write({
            'default_arrival_hour': '06:00',
            'default_departure_hour': '18:00',
        })
        checkin = fields.date.today() + timedelta(days=8)
        checkout = checkin + timedelta(days=11)
        reservation = self._create_reservation(checkin, checkout)
        total_days = (checkout - checkin).days + 1
        self.assertEqual(len(reservation.reservation_line_ids), total_days,
                         "There should be a resevation line per day")
        # Check if the first reservation line date are the same date that the checkin date.
        line = reservation.reservation_line_ids[0]
        self.assertEqual(line.date, checkin, "Reservation lines don't start in the correct date")
        check_line_datetimes(line)
        # Now check the datetimes with the second line
        check_line_datetimes(reservation.reservation_line_ids[1])
        # Now check that the datetimes are updated if arrival_hour and departure_hour are changed
        reservation.write({
            'arrival_hour': '10:00',
            'departure_hour': '16:00',
        })
        check_line_datetimes(line, 10, 16)
        check_line_datetimes(reservation.reservation_line_ids[1], 10, 16)

    def test_005_reservation_action_assign(self):
        """Checks the correct operation of the assign method
        Create a new reservation with only room_type(autoassign -> to_assign = True),
        and the we call to action_assign method to confirm the assignation
        """
        reservation = self._create_reservation(checkout=fields.date.today()+timedelta(days=1))
        reservation.action_assign()
        self.assertFalse(reservation.to_assign, "The reservation should be marked as assigned")

    def test_006_reservation_auto_assign_on_create(self):
        """When creating a reservation with a specific room,
        it is not necessary to mark it as to be assigned
        ---------------
        Create a new reservation with specific preferred_room_id,
        "to_assign" should be set to false automatically
        """
        reservation = self.env["pms.reservation"].create({
            "checkin": fields.date.today(),
            "checkout": fields.date.today() + timedelta(days=1),
            "preferred_room_id":  self.room.id,
            "partner_id": self.partner.id,
            "pms_property_id": self.property.id,
        })
        self.assertFalse(reservation.to_assign, "Reservation with preferred_room_id set to to_assign = True")

    def test_007_reservation_to_assign_on_create(self):
        """Check the reservation action assign.
        -------------
        Create a reservation and change the reservation to 'to_assign' = False
        through action_assign() method
        """
        reservation = self._create_reservation(checkout=fields.date.today()+timedelta(days=1))
        reservation.action_assign()
        self.assertFalse(reservation.to_assign, "The reservation should be marked as assigned")

    def test_008_reservation_action_cancel(self):
        """Check if the reservation has been cancelled correctly.
        -------------
        Create a reservation and change his state to cancelled
        through the action_cancel() method.
        """
        reservation = self._create_reservation(checkout=fields.date.today()+timedelta(days=1))
        reservation.action_cancel()
        self.assertEqual(reservation.state, "cancel", "The reservation should be cancelled")

    def test_009_reservation_auto_assign_after_create(self):
        """When assigning a room manually to a reservation marked "to be assigned",
        this field should be automatically unchecked
        ---------------
        Create a new reservation without preferred_room_id (only room_type),
        "to_assign" is True, then set preferred_room_id and "to_assign" should
        be set to false automatically
        """
        self.room2 = self.env['pms.room'].create({
            'name': 'Single Room 2 Test',
            'pms_property_id': self.property.id,
            'room_type_id': self.room_type.id,
            'capacity': 1,
        })
        # set the priority of the rooms to control the room chosen by auto assign
        self.room.sequence = 1
        self.room2.sequence = 2
        reservation = self._create_reservation(checkout=fields.date.today() + timedelta(days=1))
        # res should be room1 in preferred_room_id (minor sequence)
        self.assertEqual(reservation.preferred_room_id, self.room)
        reservation.preferred_room_id = self.room2.id
        self.assertFalse(reservation.to_assign, "The reservation should be marked as assigned automatically when "
                                                "assigning the specific room")

    def test_010_check_checkin_datetime(self):
        """Check that the checkin datetime of a reservation is correct."""
        self.env.user.tz = "America/Mexico_City"
        reservation = self._create_reservation(checkout=fields.date.today() + timedelta(days=5))
        checkin = reservation.checkin
        # twelve because the property.default_arrival_hour is 12:00
        checkin_expected = datetime(checkin.year, checkin.month, checkin.day, 12, 00)
        checkin_expected = self.property.date_property_timezone(checkin_expected)
        self.assertEqual(str(reservation.checkin_datetime), str(checkin_expected), "Date Order isn't correct")

    def test_011_check_allowed_room_ids(self):
        """Check available rooms after creating a reservation.
        -----------
        Create an availability rule, create a reservation,
        and then check that the allopwed_room_ids field of the
        reservation and the room_type_id.room_ids field of the
        availability rule match.
        """
        availability_rule = self.env["pms.availability.plan.rule"].create({
            "pms_property_id": self.property.id,
            "room_type_id": self.room_type.id,
            "availability_plan_id": self.room_type_availability.id,
            "date": fields.date.today() + timedelta(days=153),
        })
        room_type = self.env['pms.room.type'].create({
            'name': 'Single Room Test',
            'pms_property_ids': [self.property.id],
            'default_code': 'STT02',
            'class_id': self.room_type_class.id,
        })
        self.room2 = self.env['pms.room'].create({
            'name': 'Single Room 2 Test',
            'pms_property_id': self.property.id,
            'room_type_id': room_type.id,
            'capacity': 1,
        })
        checkin = fields.date.today() + timedelta(days=150)
        checkout = fields.date.today() + timedelta(days=152)
        reservation = self._create_reservation(checkin=checkin, checkout=checkout)
        # The second room should not appear
        self.assertEqual(reservation.allowed_room_ids, availability_rule.room_type_id.room_ids,
                         "Rooms allowed don't match")

    def test_012_is_not_modified_reservation(self):
        """Checked that the is_modified_reservation field is correctly set
        to False when the reservation is modified but not the checkin
        or checkout fields.
        ----------------------
        A reservation is created. The adults, arrival_hour and departure_hours
        fields of the reservation are modified.The it is verified that the state
        of this field is False.
        """
        checkin = fields.date.today()
        checkout = fields.date.today() + timedelta(days=2)
        reservation = self._create_reservation(checkin=checkin, checkout=checkout)
        reservation.write({"adults": 1, "arrival_hour": "18:00", "departure_hour": "08:00"})
        self.assertFalse(reservation.is_modified_reservation, "is_modified_reservation field should be False ")
