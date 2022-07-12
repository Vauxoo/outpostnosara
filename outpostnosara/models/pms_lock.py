# Copyright 2021 Vauxoo
# License LGPL-3 or later (http://www.gnu.org/licenses/lgpl).
import json
import os


from requests import post

from odoo import fields, models, _
from odoo.exceptions import UserError


class PmsLock(models.Model):
    _name = 'pms.lock'
    _description = 'PMS Lock door connected to Home Assistant'

    name = fields.Char(
        required=True,
        help="""Identifier of the lock in Home Assistant, you can set this from the device's configuration in HA."""
    )
    slot_ids = fields.One2many('pms.lock.slot', 'lock_id', help="Memory slots where the keys are saved in the lock.")
    max_slots = fields.Integer(default=30, help="Max number of slots that the lock can save.")
    room_id = fields.Many2one('pms.room', help="Room on which the lock is installed on.")

    def action_set_user_code(self, slot_name, usercode):
        self.ensure_one()
        slot = self.slot_ids.filtered(lambda s: s.name == slot_name)
        if not slot:
            slot = slot.create({
                'lock_id': self.id,
                'name': slot_name,
            })
        return slot._set_user_code(usercode=usercode)

    def action_clear_user_code(self, slot_name):
        self.ensure_one()
        slot = self.slot_ids.filtered(lambda s: s.name == slot_name)
        if not slot:
            return False
        return slot._clear_user_code()


class PmsLockSlot(models.Model):
    _name = 'pms.lock.slot'
    _description = 'PMS Lock slot or memory position where the user codes will be saved.'

    lock_id = fields.Many2one('pms.lock', required=True)
    name = fields.Integer(required=True, help="Slot number, it is an integer between 1 and 30.")
    usercode = fields.Char(size=8, help="Pin Code between 4 and 8")

    def _get_connection_parameters(self):
        hostname = self.sudo().env['ir.config_parameter'].get_param('pms.locks_hostname')
        auth_token = self.sudo().env['ir.config_parameter'].get_param('pms.locks_auth_token')
        if not hostname:
            raise UserError(_("Please set the key pms.locks_hostname in the configuration parameters."))
        if not auth_token:
            raise UserError(_("Please set the key pms.locks_auth_token in the configuration parameters."))
        return {
            'hostname': hostname,
            'auth_token': auth_token
        }

    def _set_user_code(self, usercode=None):
        if os.environ.get('ODOO_STAGE', False) != 'production':
            self.write({'usercode': usercode})
            return True
        parameters = self._get_connection_parameters()
        usercode = usercode or self.usercode
        payload = {
            'entity_id': self.lock_id.name,
            'code_slot': self.name,
            'usercode': usercode
        }
        url = "%s/api/services/zwave_js/set_lock_usercode" % parameters['hostname']
        headers = {
            "Authorization": "Bearer %s" % parameters['auth_token'],
            "content-type": "application/json"
        }
        try:
            response = post(url, headers=headers, data=json.dumps(payload), timeout=10)
        except BaseException as error:
            raise UserError(_('Error setting code %s in slot: %s from lock: %s\n\n%s') % (
                usercode, self.name, self.lock_id.name, error))
        self.write({'usercode': usercode})
        return response

    def _clear_user_code(self):
        if os.environ.get('ODOO_STAGE', False) != 'production':
            self.write({'usercode': False})
            return True
        parameters = self._get_connection_parameters()
        payload = {
            'entity_id': self.lock_id.name,
            'code_slot': self.name,
        }
        url = "%s/api/services/zwave_js/clear_lock_usercode" % parameters['hostname']
        headers = {
            "Authorization": "Bearer %s" % parameters['auth_token'],
            "content-type": "application/json"
        }
        try:
            response = post(url, headers=headers, data=json.dumps(payload), timeout=10)
        except BaseException as error:
            raise UserError(_('Error clearing slot: %s from lock: %s\n\n%s') % (self.name, self.lock_id.name, error))
        self.write({'usercode': False})
        return response

    def action_set_user_code(self, usercode=None):
        self.ensure_one()
        return self._set_user_code(usercode or self.usercode)

    def action_clear_user_code(self):
        self.ensure_one()
        return self._clear_user_code()

    _sql_constraints = [
        ('lock_code_uniq', 'unique(lock_id, name)', 'The name of the slot in a lock must be unique.')
    ]
