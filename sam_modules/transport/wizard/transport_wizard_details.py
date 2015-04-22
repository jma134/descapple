# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from datetime import datetime


class transport_wizard_details(models.TransientModel):
    _name = 'transport.wizard_details'
    _description = 'wizard_details'

    session_id = fields.Many2one('transport.session', 'SessionN')
    item_ids = fields.One2many('transport.wizard_details_items', 'transfer_id', 'Items', domain=[('product_id', '!=', False)])
#     packop_ids = fields.One2many('stock.transfer_details_items', 'transfer_id', 'Packs', domain=[('product_id', '=', False)])
#     picking_source_location_id = fields.Many2one('stock.location', string="Head source location", related='picking_id.location_id', store=False, readonly=True)
#     picking_destination_location_id = fields.Many2one('stock.location', string="Head destination location", related='picking_id.location_dest_id', store=False, readonly=True)
