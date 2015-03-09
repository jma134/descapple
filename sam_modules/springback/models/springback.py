# -*- coding: utf-8 -*-

from openerp import tools
#import time
import logging
#from win32con import DST_BITMAP
_logger = logging.getLogger(__name__)

from openerp import models, fields, api, exceptions
from datetime import timedelta

# 1. NPI 、Springback要区别开
# 2. OEM,SLC,DC H/O date，要有Planned和Actual 
# 3. Unit： pcs/pallet, 自动计算Pallet
# 4. Volume：分实际和预估
# 5. Category 加在明细里
# 6. 如里是Retail的货，明细要加个DC H/O Date
# 7. Marketing, direct/hub

#----------------------------------------------------------
# springback order 
#----------------------------------------------------------
class springback_order(models.Model):
    _name = "springback.order"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = "springback Order"
    _order = 'id desc'
    
    STATE_SELECTION = [
        ('draft', 'Draft'),
        ('picking', 'Picking'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ]
    
    @api.one
    @api.depends('order_line')
    def _qty_all(self):
        qty = 0
        plt = 0
        if self.order_line:       
            for line in self.order_line:
               qty += line.product_qty
               plt += line.product_plt
            
        self.qty = qty
        self.plt = plt
        
    
    product_id = fields.Many2one('product.product', 'Material', required=True, select=True, domain=[('type', '<>', 'service')], states={'done': [('readonly', True)]})
#     cnee_name = fields.Char('Name1', size=128)
#     sales_doc = fields.Char('Sales Doc', size=10)
#     pono = fields.Char('Purchase Order#', size=32)       
    cnee_id = fields.Many2one('res.partner', 'OEM', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, 
                                 domain=['|', ('instructor', '=', True),('category_id.name', 'ilike', "Teacher")])    
#     shpr_pt = fields.Char('ShPt', size=4)
#     shpr_id = fields.Many2one('res.partner', 'Shipper', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, 
#                                  domain=['|', ('instructor', '=', True),('category_id.name', 'ilike', "OEM")])
#     partner_name = fields.Char("Customer Name", size=64,help='The name of the future partner company that will be created while converting the lead into opportunity', select=1)
#     org = fields.Char("Orig", compute='_org_get')
#     dst = fields.Char("Dest", compute='_dst_get')
#     tt = fields.Float("Transit Time", compute='_tt_get', help="Transit Time in days")
    total_qty = fields.Integer('Total Volume', required=True)
    qty = fields.Integer('Volume Subtotal', compute='_qty_all', help="The shipped Quantity of this order", multi="sums")    
    total_plt = fields.Integer('Total Pallet', required=True)
    plt = fields.Integer('Pallet Subtotal', compute='_qty_all', help="The shipped Pallet of this order", multi="sums")
    taken_plt = fields.Float(string="Taken Pallets", compute='_taken_plt')
    order_line = fields.One2many('springback.order.line', 'order_id', 'Order Lines',
                                      states={'picking':[('readonly',True)],
                                              'done':[('readonly',True)]},
                                      copy=True)    
    ho_date = fields.Date('OEM H/O', default=fields.datetime.now())
    end_date = fields.Date('Ending Date')
    slc_date = fields.Date('SLC Date')
    eta = fields.Date('Ending Date', compute='_eta')
    
    description = fields.Text('Handling Security')
    remark = fields.Text('Remark')      
    
    state = fields.Selection(STATE_SELECTION, 'Status', readonly=True,
                                  help=' * The \'Draft\' status is set automatically when purchase order in draft status. \
                                   \n* The \'Confirmed\' status is set automatically as confirm when purchase order in confirm status. \
                                   \n* The \'Done\' status is set automatically when purchase order is set as done. \
                                   \n* The \'Cancelled\' status is set automatically when user cancel purchase order.',
                                  select=True, copy=False)
     
     
    @api.one
    @api.depends('order_line')
    def _eta(self):
        if self.order_line:
            self.eta = self.order_line[0].date_shipped
        
    
    @api.one
    def confirm_order(self):
        self.state = 'confirmed'
               
    @api.one
    @api.depends('total_plt', 'plt')
    def _taken_plt(self):
        if not self.total_plt:
            self.taken_plt = 0.0
        else:
            self.taken_plt = 100.0 * self.plt / self.total_plt


#----------------------------------------------------------
# springback order line
#----------------------------------------------------------
class springback_order_line(models.Model):
    _table = 'springback_order_line'
    _name = 'springback.order.line'
    _description = 'springback Order Line'
    

    product_qty = fields.Integer('Volume', required=True, default=lambda *a: 1.0)
    product_plt = fields.Integer('Pallet', required=True, default=lambda *a: 1.0)    
    date_shipped = fields.Date('Shipped Date', required=True, select=True)
    order_id = fields.Many2one('springback.order', 'Order Reference', select=True, required=True, ondelete='cascade')
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed'), ('done', 'Done'), ('cancel', 'Cancelled')],
                              'Status', required=True, readonly=True, copy=False, default=lambda *args: 'draft',
                              help=' * The \'Draft\' status is set automatically when purchase order in draft status. \
                                   \n* The \'Confirmed\' status is set automatically as confirm when purchase order in confirm status. \
                                   \n* The \'Done\' status is set automatically when purchase order is set as done. \
                                   \n* The \'Cancelled\' status is set automatically when user cancel purchase order.')

 