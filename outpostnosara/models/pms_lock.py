# Copyright 2021 Vauxoo
# License LGPL-3 or later (http://www.gnu.org/licenses/lgpl).
import json
from requests import post

from odoo import fields, models, _
from odoo.exceptions import UserError


class PmsLock(models.Model):
    _name = 'pms.lock'
    _description = 'PMS Lock door connected to a homeassitant'

    name = fields.Char(
        required=True,
        help="""Identifier of the lock in the home assistant, you need to get this from that configuration"""
    )
    slot_ids = fields.One2many('pms.lock.slot', 'lock_id', help="Memory slots where the keys are saved")

    def action_set_user_code(self, slot_name, usercode):
        self.ensure_one()
        slot = self.slot_ids.mapped(lambda s: s.name == slot_name)
        if not slot:
            slot = slot.create({
                'lock_id': self.id,
                'slot': slot_name,
            })
        return slot._set_user_code(usercode=usercode)

    def action_clear_user_code(self, slot_name):
        self.ensure_one()
        slot = self.slot_ids.mapped(lambda s: s.name == slot_name)
        if not slot:
            return False
        return slot._clear_user_code()


class PmsLockSlot(models.Model):
    _name = 'pms.lock.slot'
    _description = 'PMS Lock Slot or memory position where the keys of the lock key  will be saved'

    lock_id = fields.Many2one('pms.lock', required=True)
    name = fields.Integer(required=True, help="Slot position or memory position")
    usercode = fields.Char(size=8, help="Pin Code between 4 and 8")

    def _get_connection_parameters(self):
        hostname = self.sudo().env['ir.config_parameter'].get_param('pms.locks_hostname')
        auth_token = self.sudo().env['ir.config_parameter'].get_param('pms.locks_auth_token')
        if not hostname:
            raise UserError(_("Set the key pms.locks_hostname on the parameters, None found"))
        if not auth_token:
            raise UserError(_("Set the key pms.locks_auth_token on the parameters, None found"))
        return {
            'hostname': hostname,
            'auth_token': auth_token
        }

    def _set_user_code(self, usercode=None):
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
            response = post(url, headers=headers, data=json.dumps(payload))
        except BaseException as error:
            raise UserError(_('Error setting code %s in slot: %s from lock: %s\n\n%s') % (
                usercode, self.name, self.lock_id.name, error))
        self.write({'usercode': usercode})
        return response

    def _clear_user_code(self):
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
            response = post(url, headers=headers, data=json.dumps(payload))
        except BaseException as error:
            raise UserError(_('Error clearing slot: %s from lock: %s\n\n%s') % (self.name, self.lock_id.name, error))
        self.write({'usercode': False})
        return response

    def action_set_user_code(self, usercode):
        self.ensure_one()
        return self._set_user_code(usercode)

    def action_clear_user_code(self):
        self.ensure_one()
        return self._clear_user_code()

    _sql_constraints = [
        ('lock_code_uniq', 'unique(lock_id, name)', 'The name of the slot must be unique by lock!')
    ]
