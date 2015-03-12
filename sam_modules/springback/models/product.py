# -*- coding: utf-8 -*-

from openerp import fields, models

class product_template(models.Model):
    _inherit = 'product.template'

    vol_per_plt = fields.Integer("Volume per Pallet", default=1)
    npi_ok = fields.Boolean('Is NPI', help="Specify if the product is NPI/Springback.")
