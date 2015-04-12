# -*- coding: utf-8 -*-

from openerp import fields, models

class partner(models.Model):
    _inherit = 'res.partner'

    recipients_ids = fields.Many2many('res.partner', 'oem_res_partner_rel',
            'parnter_id', 'partner_id', string='Additional Contacts')
