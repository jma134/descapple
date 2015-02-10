# -*- coding: utf-8 -*-

from openerp import fields, models

class partner(models.Model):
    _inherit = 'res.partner'

    # Add a new column to the res.partner model, by default partners are not
    # instructors
    instructor = fields.Boolean("Instructor", default=False)
    soldtopt = fields.Integer("Sold-to pt", default=0)
    shiptopt = fields.Integer("Ship-to pt", default=0)
