from odoo.tools.misc import mute_logger
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase
from psycopg2 import IntegrityError


class TestPmsLock(TransactionCase):

    def setUp(self):
        super().setUp()
        self.pms_lock_slot = self.env['pms.lock.slot']
        self.lock = self.env['pms.lock'].create({
            'name': 'Test Lock',
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
