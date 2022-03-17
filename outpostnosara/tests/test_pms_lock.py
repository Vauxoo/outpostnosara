from odoo.tools.misc import mute_logger
from odoo.exceptions import UserError
from psycopg2 import IntegrityError

from . import common


class TestPmsLock(common.PmsTransactionCase):

    def setUp(self):
        super().setUp()
        self.pms_lock_slot = self.env['pms.lock.slot']
        self.lock = self.env['pms.lock'].create({
            'name': 'Test Lock',
            'room_id': self.room.id,
        })

    def create_lock(self, name, room=None, slot_list=False):
        room = room or self.room
        return self.env['pms.lock'].create({
            'name': name,
            'room_id': room.id,
            'slot_ids': slot_list,
        })

    def test_001_pms_lock_slot(self):
        msg = "Please set the key pms.locks_hostname in the configuration parameters."
        with self.assertRaisesRegex(UserError, msg):
            self.pms_lock_slot._get_connection_parameters()
        self.env['ir.config_parameter'].set_param('pms.locks_hostname', 'hostname_test')
        msg = "Please set the key pms.locks_auth_token in the configuration parameters."
        with self.assertRaisesRegex(UserError, msg):
            self.pms_lock_slot._get_connection_parameters()
        self.env['ir.config_parameter'].set_param('pms.locks_auth_token', '1234567890')
        connection = self.pms_lock_slot._get_connection_parameters()
        self.assertEqual(connection, {'hostname': 'hostname_test', 'auth_token': '1234567890'})

    def test_002_pms_lock(self):
        lock_slot = self.pms_lock_slot.search([('lock_id', '=', self.lock.id)])
        self.assertFalse(lock_slot)
        self.lock.action_set_user_code(123, '00000001')
        lock_slot = self.pms_lock_slot.search([('lock_id', '=', self.lock.id)])
        self.assertTrue(lock_slot)
        lock_slot.usercode = '00000001'
        msg = 'duplicate key value violates unique constraint "pms_lock_slot_lock_code_uniq"'
        with mute_logger("odoo.sql_db"):
            with self.assertRaisesRegex(IntegrityError, msg):
                self.pms_lock_slot.create({
                    'lock_id': self.lock.id,
                    'name': 123,
                    'usercode': '00000001',
                })

    def test_003_pms_room_set_clear_slot(self):
        usercode = '01234567'
        lock_2 = self.create_lock(
            name='Test Lock 2',
            slot_list=[
                [0, 0, {'name': 1, 'usercode': '20000001'}],
                [0, 0, {'name': 2}],
            ]
        )
        lock_3 = self.create_lock(
            name='Test Lock 3',
            slot_list=[
                [0, 0, {'name': 1, 'usercode': '30000001'}],
                [0, 0, {'name': 2, 'usercode': '30000002'}],
            ]
        )
        lock_4 = self.create_lock(
            name='Test Lock 4',
            slot_list=[
                [0, 0, {'name': count, 'usercode': '400000%s' % count}] for count in range(1, 31)
            ]
        )
        lock_5 = self.create_lock(
            name='Test Lock 5',
            slot_list=[
                [0, 0, {'name': 1}],
                [0, 0, {'name': 2, 'usercode': usercode}],
            ]
        )
        self.assertEqual(len(self.room.lock_ids), 5)
        self.room._set_lock(usercode)
        # Check case 1: No slots exists on lock, so create first slot and set code
        self.assertEqual(len(self.lock.slot_ids), 1)
        self.assertRecordValues(self.lock.slot_ids, [{'name': 1, 'usercode': usercode}])
        # Check case 2: There is a slot available, so set code in that slot
        self.assertEqual(len(lock_2.slot_ids), 2)
        self.assertRecordValues(lock_2.slot_ids[-1], [{'name': 2, 'usercode': usercode}])
        # Check case 3: There are not slots available, but there is space for more slots, so create a new slot and set
        self.assertEqual(len(lock_3.slot_ids), 3)
        self.assertRecordValues(lock_3.slot_ids[-1], [{'name': 3, 'usercode': usercode}])
        # Check case 4: There are not slots available and there is no space for more slots, so we don't set code
        self.assertEqual(len(lock_4.slot_ids), 30)
        self.assertRecordValues(lock_4.slot_ids[-1], [{'name': 30, 'usercode': '40000030'}])
        # Check case 5: The code is already set on a slot
        self.assertEqual(len(lock_5.slot_ids), 2)
        self.assertRecordValues(lock_5.slot_ids, [
            {'name': 1, 'usercode': False},
            {'name': 2, 'usercode': usercode},
        ])

        # Verify that the code is cleared from all locks where was set in any of their slots
        self.room._clear_lock(usercode)
        self.assertEqual(len(self.lock.slot_ids), 1)
        self.assertFalse(self.lock.slot_ids[-1].usercode)
        self.assertEqual(len(lock_2.slot_ids), 2)
        self.assertFalse(lock_2.slot_ids[-1].usercode)
        self.assertEqual(len(lock_3.slot_ids), 3)
        self.assertFalse(lock_3.slot_ids[-1].usercode)
        self.assertEqual(len(lock_4.slot_ids), 30)
        self.assertTrue(all(slot and slot.usercode for slot in lock_4.slot_ids))
        self.assertEqual(len(lock_5.slot_ids), 2)
        self.assertFalse(lock_5.slot_ids[-1].usercode)

        self.room._clear_lock('40000030')
        self.assertEqual(len(lock_4.slot_ids), 30)
        self.assertFalse(lock_4.slot_ids[-1].usercode)
        self.assertTrue(all(slot and slot.usercode for slot in lock_4.slot_ids[:-1]))
