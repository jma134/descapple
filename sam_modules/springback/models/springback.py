# -*- coding: utf-8 -*-

from openerp import tools
#import time
import logging
#from win32con import DST_BITMAP
_logger = logging.getLogger(__name__)

from openerp import models, fields, api, exceptions
from datetime import timedelta
import math

# 1. NPI 銆丼pringback瑕佸尯鍒紑
# 2. OEM,SLC,DC H/O date锛岃鏈塒lanned鍜孉ctual 
# 3. Unit锛�pcs/pallet, 鑷姩璁＄畻Pallet
# 4. Volume锛氬垎瀹為檯鍜岄浼�
# 5. Category 鍔犲湪鏄庣粏閲�
# 6. 濡傞噷鏄疪etail鐨勮揣锛屾槑缁嗚鍔犱釜DC H/O Date
# 7. Marketing, direct/hub

#----------------------------------------------------------
# springback order 
#----------------------------------------------------------
class springback_order(models.Model):
    _name = "springback.order"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = "springback Order"
    _order = 'cnee_id, product_id, id'
#     _rec_name = 'name'
    
    STATE_SELECTION = [
        ('draft', 'TBA'),
        ('shipping', 'Shipping'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ]
    
        
    name = fields.Char('Order Reference', required=True, select=True, copy=False,
                            help="Unique number of the NPI/Springback order, "
                                 "computed automatically when the order is created.", default='/')
    product_id = fields.Many2one('product.template', 'Material', required=True, select=True, domain=[('npi_ok', '=', 'True')], states={'done': [('readonly', True)]})
#     cnee_name = fields.Char('Name1', size=128)            domain=[('type', '<>', 'service')], 
#     sales_doc = fields.Char('Sales Doc', size=10)
#     pono = fields.Char('Purchase Order#', size=32)       
    cnee_id = fields.Many2one('res.partner', 'OEM', required=True, states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, 
                                 domain=['|', ('instructor', '=', True),('category_id.name', 'ilike', "OEM")])    
#     shpr_pt = fields.Char('ShPt', size=4)
#     shpr_id = fields.Many2one('res.partner', 'Shipper', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, 
#                                  domain=['|', ('instructor', '=', True),('category_id.name', 'ilike', "OEM")])
#     partner_name = fields.Char("Customer Name", size=64,help='The name of the future partner company that will be created while converting the lead into opportunity', select=1)
#     org = fields.Char("Orig", compute='_org_get')
#     dst = fields.Char("Dest", compute='_dst_get')
#     tt = fields.Float("Transit Time", compute='_tt_get', help="Transit Time in days")
    customer = fields.Selection([
                        ('reseller', 'Reseller'),
                        ('retail', 'Retail'),
                        ('online', 'Online'),
                        ('market1', 'Marketing Direct'),
                        ('market2', 'Marketing Hub')],
                'Customer',
                help="""* this field representing the customer type                      
                       \n* for products delivery
                      """, select=True)
    itinerary = fields.Many2one('springback.itinerary', 'Itinerary', required=True)
    security = fields.Selection([
                        ('std', 'Standard'),
                        ('med', 'Mediate'),
                        ('max', 'Max.'),
                        ],
                'Security Level')
    total_qty_plan = fields.Integer('Planned Volume')
    total_qty = fields.Integer('Volume')
    volperplt = fields.Integer("Volume per Pallet", compute='_volperplt_get')
    #qty = fields.Integer('Volume Subtotal', compute='_qty_all', help="The shipped Quantity of this order", multi="sums")    
    total_plt = fields.Integer('Pallet', compute='_calc_plt')
    #plt = fields.Integer('Pallet Subtotal', compute='_qty_all', help="The shipped Pallet of this order", multi="sums")
    taken_qty = fields.Float(string="Taken Volume", compute='_taken_qty')
#     order_line = fields.One2many('springback.order.line', 'order_id', 'Order Lines',
#                                       states={'picking':[('readonly',True)],
#                                               'done':[('readonly',True)]},
#                                       copy=True)    
    oem_date = fields.Date('OEM H/O Planned', default=fields.datetime.now())
    oem_date_actual = fields.Date('OEM H/O Actual', default=fields.datetime.now()) 
#     slc_date = fields.Date('SLC H/O Planned')
#     slc_date_actual = fields.Date('SLC H/O Actual')
#     dc_date = fields.Date('DC H/O Planned')
#     dc_date_actual = fields.Date('DC H/O Acutal')
    planned_date = fields.Date('H/O Planned', required=True, default=fields.datetime.now())
    actual_date = fields.Date('H/O Actual')
    fm_oem = fields.Boolean('From OEM', compute='_chk_itinerary')
#     eta = fields.Date('Ending Date', compute='_eta')
    
    description = fields.Text('Handling Security')
    remark = fields.Text('Remark')
    
    state = fields.Selection(STATE_SELECTION, 'Status', readonly=True, default=lambda *args: 'draft',
                                  help=' * The \'Draft\' status is set automatically when purchase order in draft status. \
                                   \n* The \'Confirmed\' status is set automatically as confirm when purchase order in confirm status. \
                                   \n* The \'Done\' status is set automatically when purchase order is set as done. \
                                   \n* The \'Cancelled\' status is set automatically when user cancel purchase order.',
                                  select=True, copy=False)
    
    def create(self, cr, uid, vals, context=None):
        print vals
        if vals.get('name','/')=='/':
            print "mmm"
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'springback.order') or '/'
        #context = dict(context or {}, mail_create_nolog=True)
        order =  super(springback_order, self).create(cr, uid, vals, context=context)
        print vals
        #self.message_post(cr, uid, [order], body=_("RFQ created"), context=context)
        return order
        
    
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
    def confirm_order(self):
        self.state = 'confirmed'
        
               
    @api.one
    @api.depends('total_qty', 'total_qty_plan')
    def _taken_qty(self):
        if not self.total_qty_plan:
            self.taken_qty = 0.0
        else:
            self.taken_qty = 100.0 * self.total_qty / self.total_qty_plan          
          
        
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
            self.total_plt = math.ceil(self.total_qty * 1.0 / self.volperplt)
            #print math.ceil(self.total_qty / self.volperplt)
        else:
            self.total_plt = ""

    @api.one
    @api.depends('itinerary')
    def _chk_itinerary(self):
        self.fm_oem = False
        
        if self.itinerary:
            #print self.itinerary.name[:3]
            if self.itinerary.name[:3] == 'OEM':
                self.fm_oem = True              


#     @api.one
#     @api.depends('order_line')
#     def _qty_all(self):
#         qty = 0
#         #plt = 0
#         if self.order_line:       
#             for line in self.order_line:
#                 if line.pickup_point == "slc":
#                     qty += line.product_qty
#                 
#             
#         self.qty = qty
#         #self.plt = plt
#            
#     @api.one
#     @api.depends('order_line')
#     def _eta(self):
#         if self.order_line:
#             self.eta = self.order_line[0].date_shipped
#
#     @api.one
#     @api.constrains('slc_date', 'oem_date', 'dc_date')
#     def _check_value(self):
#         if self.slc_date and self.oem_date:
#             if self.slc_date < self.oem_date:
#                 raise exceptions.ValidationError("SLC H/O date should be larger than OEM H/O date!")            
#         if self.slc_date and self.dc_date:
#             if self.dc_date < self.slc_date:
#                 raise exceptions.ValidationError("DC H/O date should be larger than SLC H/O date!")

#----------------------------------------------------------
# springback order line
#----------------------------------------------------------
# class springback_order_line(models.Model):
#     _table = 'springback_order_line'
#     _name = 'springback.order.line'
#     _description = 'springback Order Line'
#     
#     
#     pickup_point= fields.Selection([
#                         ('slc', 'SLC'),
#                         ('dc', 'HUB')],
#                 'Pickup Point', required=True,
#                 help="""* this field representing the location
#                        \n* where DHL pickup products
#                       """, select=True)
#     product_qty = fields.Integer('Volume', required=True, default=lambda *a: 1.0)
#     #product_plt = fields.Integer('Pallet', required=True, default=lambda *a: 1.0)
#     pickup_time = fields.Datetime('Pickup Datetime', required=True, select=True)
#     delivery_time = fields.Datetime('Delivery Datetime')
#     remark = fields.Text('Remark')
#     order_id = fields.Many2one('springback.order', 'Order Reference', select=True, required=True, ondelete='cascade')
#     state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed'), ('done', 'Done'), ('cancel', 'Cancelled')],
#                               'Status', required=True, readonly=True, copy=False, default=lambda *args: 'draft',
#                               help=' * The \'Draft\' status is set automatically when purchase order in draft status. \
#                                    \n* The \'Confirmed\' status is set automatically as confirm when purchase order in confirm status. \
#                                    \n* The \'Done\' status is set automatically when purchase order is set as done. \
#                                    \n* The \'Cancelled\' status is set automatically when user cancel purchase order.')

 
 #----------------------------------------------------------
# Springback Itinerary 
#----------------------------------------------------------
class springback_itinerary(models.Model):
    _name = 'springback.itinerary'
    _description = 'NPI/Springback Itinerary'
    
    name = fields.Char(string='Itinerary Name', compute='_itinerary', required=True)
    org = fields.Char(string="Origin", required=True, size=4)
    dst = fields.Char(string="Destination", required=True, size=4)
    itinerary = fields.Char(string="Itinerary", compute='_itinerary')
    
    _defaults = {
        'name': "/",
    }

    _sql_constraints = [
        ('itinerary_name_uniq',
         'UNIQUE(name)',
         "The itinerary name must be unique"),
    ]
        
    @api.one
    @api.depends('org', 'dst')
    def _itinerary(self):
#         s1 = self.org and self.org or ''
#         if self.dst:
#             s2 = self.dst
#         else:
#             s2 = ''
        
        if self.org and self.dst:
            self.name = str(self.org).upper() + '>' + str(self.dst).upper()  
        
        #self.itinerary = self.org and self.org or '' + self.dst and self.dst or ''
        
