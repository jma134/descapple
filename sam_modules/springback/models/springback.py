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
        ('shipping', 'Shipping'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ]
    
    @api.one
    @api.depends('order_line')
    def _qty_all(self):
        qty = 0
        #plt = 0
        if self.order_line:       
            for line in self.order_line:
               qty += line.product_qty
               #plt += line.product_plt
            
        self.qty = qty
        #self.plt = plt
        
    
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
    total_qty_plan = fields.Integer('Planned Volume', required=True)
    total_qty = fields.Integer('Volume', required=True)
    volperplt = fields.Integer("Volume per Pallet", compute='_volperplt_get')
    qty = fields.Integer('Volume Subtotal', compute='_qty_all', help="The shipped Quantity of this order", multi="sums")    
    total_plt = fields.Integer('Pallet', compute='_calc_plt')
    plt = fields.Integer('Pallet Subtotal', compute='_qty_all', help="The shipped Pallet of this order", multi="sums")
    taken_qty = fields.Float(string="Taken Volume", compute='_taken_qty')
    order_line = fields.One2many('springback.order.line', 'order_id', 'Order Lines',
                                      states={'picking':[('readonly',True)],
                                              'done':[('readonly',True)]},
                                      copy=True)    
    oem_date = fields.Date('OEM H/O Planned', default=fields.datetime.now())
    oem_date_actual = fields.Date('OEM H/O Actual', default=fields.datetime.now()) 
    slc_date = fields.Date('SLC H/O Planned')
    slc_date_actual = fields.Date('SLC H/O Actual')
    dc_date = fields.Date('DC H/O Planned')
    dc_date_actual = fields.Date('DC H/O Acutal')
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
    def action_draft(self):
        self.state = 'draft'
        
    @api.one
    def action_shipping(self):
        self.state = 'shipping'
        
    @api.one
    def action_done(self):
        self.state = 'done'

    @api.one
    def action_cancel(self):
        self.state = 'cancel'
        
                 
    @api.one
    @api.depends('order_line')
    def _eta(self):
        if self.order_line:
            self.eta = self.order_line[0].date_shipped
        
    
    @api.one
    def confirm_order(self):
        self.state = 'confirmed'
               
    @api.one
    @api.depends('total_qty', 'qty')
    def _taken_qty(self):
        if not self.total_qty:
            self.taken_qty = 0.0
        else:
            self.taken_qty = 100.0 * self.qty / self.total_qty
            
    @api.one
    @api.constrains('slc_date', 'oem_date', 'dc_date')
    def _check_value(self):
        if self.slc_date and self.oem_date:
            if self.slc_date < self.oem_date:
                raise exceptions.ValidationError("SLC H/O date should be larger than OEM H/O date!")            
        if self.slc_date and self.dc_date:
            if self.dc_date < self.slc_date:
                raise exceptions.ValidationError("DC H/O date should be larger than SLC H/O date!")
            
        
    @api.one
    @api.depends('product_id')
    def _volperplt_get(self):
        if not (self.product_id):            
            return
        
        self.volperplt = self.product_id.vol_per_plt

    @api.one
    @api.depends('total_qty', 'volperplt')
    def _calc_plt(self):
        if self.total_qty and self.volperplt:
            self.total_plt = round(self.total_qty / self.volperplt)
        else:
            self.total_plt = ""
            

#----------------------------------------------------------
# springback order line
#----------------------------------------------------------
class springback_order_line(models.Model):
    _table = 'springback_order_line'
    _name = 'springback.order.line'
    _description = 'springback Order Line'
    
    category = fields.Selection([
                        ('reseller', 'Reseller'),
                        ('retail', 'Retail'),
                        ('online', 'Online'),
                        ('market1', 'Marketing Direct'),
                        ('market2', 'Marketing Hub')],
                'Customer Type', required=True,
                help="""* this field representing the customer type                      
                       \n* for products delivery
                      """, select=True)
    product_qty = fields.Integer('Volume', required=True, default=lambda *a: 1.0)
    #product_plt = fields.Integer('Pallet', required=True, default=lambda *a: 1.0)
    date_shipped = fields.Date('Shipped Date', required=True, select=True)
    dc_date = fields.Date('Marketing DC Shipped Date')  
    order_id = fields.Many2one('springback.order', 'Order Reference', select=True, required=True, ondelete='cascade')
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed'), ('done', 'Done'), ('cancel', 'Cancelled')],
                              'Status', required=True, readonly=True, copy=False, default=lambda *args: 'draft',
                              help=' * The \'Draft\' status is set automatically when purchase order in draft status. \
                                   \n* The \'Confirmed\' status is set automatically as confirm when purchase order in confirm status. \
                                   \n* The \'Done\' status is set automatically when purchase order is set as done. \
                                   \n* The \'Cancelled\' status is set automatically when user cancel purchase order.')

 