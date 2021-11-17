
from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    housekeeping_task = fields.Integer(string='Housekeeping Tasks', compute='_compute_housekeeping_task')
    maintenance_task = fields.Integer(string='Maintenance Tasks', compute='_compute_maintenance_task')

    def _compute_housekeeping_task(self):
        for rec in self:
            housekeeping_task = self.env['pms.housekeeping'].search_count([('employee_id', '=', rec.id)])
            rec.housekeeping_task = housekeeping_task

    def _compute_maintenance_task(self):
        for rec in self:
            maintenance_task = self.env['maintenance.request'].search_count([('user_id', '=', rec.user_id.id)])
            rec.maintenance_task = maintenance_task

    def activities_housekeeping(self):
        action = self.env["ir.actions.act_window"]._for_xml_id("pms_housekeeping.action_pms_house_keeping_view_form")
        action['domain'] = [('employee_id', '=', self.id)]
        return action

    def activities_maintenance(self):
        action = self.env["ir.actions.act_window"]._for_xml_id("maintenance.hr_equipment_request_action")
        action['domain'] = [('user_id', '=', self.user_id.id)]
        return action
