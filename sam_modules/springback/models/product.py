# -*- coding: utf-8 -*-

from openerp import fields, models

class product_template(models.Model):
    _inherit = 'product.template'

    vol_per_plt = fields.Integer("Volume per Pallet", default=1)
