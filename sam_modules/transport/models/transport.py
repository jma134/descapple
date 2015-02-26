# -*- coding: utf-8 -*-

from openerp.osv import osv
from openerp.osv import fields as FD

from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp import tools
import time
import logging
#from win32con import DST_BITMAP
_logger = logging.getLogger(__name__)

from openerp import models, fields, api, exceptions
from datetime import timedelta

import random


#----------------------------------------------------------
# Transport Course 
#----------------------------------------------------------
class transport_course(osv.osv):
    _name = 'transport.course'

    _columns = {
        'name': FD.char(string="Title", required=True),
        'description': FD.text(string="description"),
        
        'responsible_id': FD.many2one('res.users',ondelete='set null', string="Responsible", index=True),
        'session_ids': FD.one2many('transport.session', 'course_id', string="Sessions"),
        'attendee_ids': FD.many2many('res.partner', string="Attendees"),
    }
    
    @api.one
    def copy(self, default=None):
        default = dict(default or {})
        print "mmm"
        print default
        
        copied_count = self.search_count(
            [('name', '=like', u"Copy of {}%".format(self.name))])
        if not copied_count:
            new_name = u"Copy of {}".format(self.name)
        else:
            new_name = u"Copy of {} ({})".format(self.name, copied_count)

        default['name'] = new_name
        default['description'] = 'DHL Supply Chain'
        return super(transport_course, self).copy(default)
    
    _sql_constraints = [
        ('name_description_check',
         'CHECK(name != description)',
         "The title of the course should not be the description"),

        ('name_unique',
         'UNIQUE(name)',
         "The course title must be unique"),
    ]
    
class transport_session(osv.osv):
    _name = 'transport.session'

    _columns = {
        'name': FD.char(string="Session", required=True),
        'start_date': FD.date(string="start_date"),
        'duration': FD.float(string="duration", digits=(6, 2), help="Duration in days"),
        'seats': FD.integer(string="Number of seats"),
        'active': FD.boolean(string="Active", default=True), 
        'color': FD.integer(),
        
        'instructor_id': FD.many2one('res.partner', string="Instructor", domain=['|', ('instructor', '=', True),
                     ('category_id.name', 'ilike', "Teacher")]),
        'course_id': FD.many2one('transport.course',ondelete='cascade', string="Course", required=True),
        'attendee_ids': FD.many2many('res.partner', string="Attendees"),
        
        'taken_seats': FD.float(string="Taken seats", compute='_taken_seats'),
        'end_date': FD.date(string="End Date", store=True, compute='_get_end_date', inverse='_set_end_date'),
        'hours': FD.float(string="Duration in hours", compute='_get_hours', inverse='_set_hours'),
        
        'attendees_count': FD.integer(string="Attendees count", compute='_get_attendees_count', store=True),
        'state': FD.selection([('draft', "Draft"),
                                   ('confirmed', "Confirmed"),
                                   ('done', "Done"),
                                   ]),
    }
    
    org = fields.Char(string="Origin", required=True, size=4)
    dst = fields.Char(string="Destination", required=True, size=4)
    itinerary = fields.Char(string="Itinerary", compute='_itinerary')
    

    @api.one
    @api.depends('org', 'dst')
    def _itinerary(self):
        print self.org
#         if self.org:
#             s1 = self.org
#         else:
#             s1 = ''
        s1 = self.org and self.org or ''
        if self.dst:
            s2 = self.dst
        else:
            s2 = ''
         
        self.itinerary = s1 + s2
            
    @api.one
    def action_draft(self):
        self.state = 'draft'
        
    @api.one
    def action_confirm(self):
        self.state = 'confirmed'
        
    @api.one
    def action_done(self):
        self.state = 'done'
        
        
    
    @api.one
    @api.depends('start_date', 'duration')
    def _get_end_date(self):
        if not (self.start_date and self.duration):
            self.end_date = self.start_date
            return

        # Add duration to start_date, but: Monday + 5 days = Saturday, so
        # subtract one second to get on Friday instead
        start = FD.Datetime.from_string(self.start_date)
        duration = timedelta(days=self.duration, seconds=-1)
        self.end_date = start + duration
        
    @api.one
    def _set_end_date(self):
        if not (self.start_date and self.end_date):
            return

        # Compute the difference between dates, but: Friday - Monday = 4 days,
        # so add one day to get 5 days instead
        start_date = FD.Datetime.from_string(self.start_date)
        end_date = FD.Datetime.from_string(self.end_date)
        self.duration = (end_date - start_date).days + 1
        
    @api.one
    @api.depends('duration')
    def _get_hours(self):
        self.hours = self.duration * 24
        
    @api.one
    def _set_hours(self):
        self.duration = self.hours / 24
        
    @api.one
    @api.depends('attendee_ids')
    def _get_attendees_count(self):
        self.attendees_count = len(self.attendee_ids)
        
    @api.one
    @api.depends('seats', 'attendee_ids')
    def _taken_seats(self):
        if not self.seats:
            self.taken_seats = 0.0
        else:
            self.taken_seats = 100.0 * len(self.attendee_ids) / self.seats
            
    @api.onchange('seats', 'attendee_ids')
    def _verify_valid_seats(self):
        if self.seats < 0:
            return {
                'warning': {
                    'title': "Incorrect 'seats' value",
                    'message': "The number of available seats may not be negative",
                },
            }
        if self.seats < len(self.attendee_ids):
            return {
                'warning': {
                    'title': "Too many attendees",
                    'message': "Increase seats or remove excess attendees",
                },
            }
    
    @api.one
    @api.constrains('instructor_id', 'attendee_ids')
    def _check_instructor_not_in_attendees(self):
        if self.instructor_id and self.instructor_id in self.attendee_ids:
            raise exceptions.ValidationError("A session's instructor can't be an attendee")   
            
#----------------------------------------------------------
# Transport EDI 
#----------------------------------------------------------
class transport_edi(osv.osv):
    _name = "transport.edi"
    _description = "Transport EDI"
    _order = "id desc"
     

    _columns = {
        'name': FD.char('BizNo', size=16, select=True, readonly=True),
        'category': FD.char('EDI', size=6, select=True, readonly=True),
        'msgid': FD.char('MsgID', size=50, readonly=True),
        'fname': FD.char('FileName', size=100, readonly=True),
        'isa': FD.char('ISA#', size=9, select=True, readonly=True),
        'recvtime': FD.datetime('ReceiveTime', help="DHL Link EDI Receive Time", readonly=True),
        'sendtime': FD.datetime('SendTime', help="DHL Link EDI Send Time", readonly=True),
        'exception': FD.char('ExceptionID', size=10, readonly=True),        
        'email': FD.char('Email', size=30, readonly=True),        
        'remark': FD.char('Remark', size=200, readonly=True),        
        'hawb': FD.char('HAWB', size=50, readonly=True),
        'eventcd': FD.char('EventCode', size=3, readonly=True),
        'eventdate': FD.char('EventDate', size=16, readonly=True),
        'city': FD.char('City', size=32, readonly=True),
        'gweight': FD.float('G.Weight', digits_compute=dp.get_precision('Product Unit of Measure'), readonly=True),
        'partno': FD.char('Part#', size=16, readonly=True),
        'qty': FD.float('Qty', digits_compute=dp.get_precision('Product Unit of Measure'), readonly=True),        
        'gentime': FD.datetime('GenTime', select=True, readonly=True),
        'state': FD.selection([('draft', 'New'),
                                   ('done', 'Done'),
                                   ], 'Status', readonly=True, select=True,
                 help= "* New: When the EDI is created and not yet confirmed.\n"\
                       "* Done: When the EDI is completed & arichived, the state is \'Done\'."),          
        'note': FD.text('Notes'),
    }
    _defaults = {
        'state': 'draft',
        'gentime': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
    }   
    
    _log_access = False
    

#----------------------------------------------------------
# Transport SLD 
#----------------------------------------------------------
class transport_sld(models.Model):
    _name = 'transport.sld'
    _inherit = ['mail.thread']

#     def _default_sessions(self):
#         return self.env['transport.session'].browse(self._context.get('active_ids'))
#     
    partner_id = fields.Many2one('res.partner', 'Partner', ondelete='set null', track_visibility='onchange',
            select=True, help="Linked partner (optional). Usually created when converting the lead.")
    contact_name = fields.Char('Contact Name', size=64)
    partner_name = fields.Char("Customer Name", size=64,help='The name of the future partner company that will be created while converting the lead into opportunity', select=1)
    
    org = fields.Char(string="Origin", required=True, size=4)
    dst = fields.Char(string="Destination", required=True, size=4)
    itinerary = fields.Char(string="Itinerary", compute='_itinerary')
    dstprovince = fields.Char(string="Province", size=30)
    tt = fields.Float(string="Transit Time", digits=(5, 1), help="Transit Time in days")
    is_test = fields.Boolean('Is a Test', help="Check if the contact is a company, otherwise it is a person")

    
    _defaults = {
        'itinerary': "SHA",
    }
#     attendee_ids = fields.Many2many('res.partner', string="Attendees")

    @api.multi
    def onchange_type(self, is_company):        
        if self.is_test:
            domain = {'title': [('domain', '=', 'partner')]}
        else:
            domain = {'title': [('domain', '=', 'contact')]}
        return {'domain': domain}
    
    
    def on_change_partner_id(self, cr, uid, ids, partner_id, context=None):
        values = {}
        print partner_id
        
        if partner_id:
            partner = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context)
            values = {
                'partner_name': partner.parent_id.name if partner.parent_id else partner.name,
                'contact_name': partner.name if partner.parent_id else False,
            }
        return {'value': values}
        
    @api.one
    @api.depends('org', 'dst')
    def _itinerary(self):
        s1 = self.org and self.org or ''
        if self.dst:
            s2 = self.dst
        else:
            s2 = ''
         
        self.itinerary = s1 + s2
        #self.itinerary = self.org and self.org or '' + self.dst and self.dst or ''


#----------------------------------------------------------
# Transport order 
#----------------------------------------------------------
class transport_order(models.Model):
    _name = "transport.order"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = "Transport Order"
    _order = 'id desc'
    
    STATE_SELECTION = [
        ('draft', 'Draft'),
        ('sent', 'PreAlert'),
#         ('confirmed', 'Confirmed'),
#         ('approved', 'Purchase Confirmed'),
        ('picking', 'Shipping'),
        ('pod', 'POD'),
        ('invoiced', 'Invoiced'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ]
        
    dn = fields.Char('Delivery No.', size=10, select=True, required=True, states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, copy=False)
    product_id = fields.Many2one('product.product', 'Material', required=True, select=True, domain=[('type', '<>', 'service')], states={'done': [('readonly', True)]})
    cnee_name = fields.Char('Name1', size=128)
    sales_doc = fields.Char('Sales Doc', size=10)
    pono = fields.Char('Purchase Order#', size=32)       
    cnee_id = fields.Many2one('res.partner', 'Consignee', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, 
                                 domain=['|', ('instructor', '=', True),('category_id.name', 'ilike', "Teacher")])    
    shpr_pt = fields.Char('ShPt', size=4)
    shpr_id = fields.Many2one('res.partner', 'Shipper', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, 
                                 domain=['|', ('instructor', '=', True),('category_id.name', 'ilike', "OEM")])
    partner_name = fields.Char("Customer Name", size=64,help='The name of the future partner company that will be created while converting the lead into opportunity', select=1)
    org = fields.Char("Orig", compute='_org_get')
    dst = fields.Char("Dest", compute='_dst_get')
    tt = fields.Float("Transit Time", compute='_tt_get', help="Transit Time in days")
    qty = fields.Integer('Dlvy Qty')
    plt_qty = fields.Integer('Plt Qty')
    order_line = fields.One2many('transport.order.line', 'order_id', 'Order Lines',
                                      states={'picking':[('readonly',True)],
                                              'done':[('readonly',True)]},
                                      copy=True)
    hawb = fields.Char('HAWB', size=23, states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, copy=False)
    trackno = fields.Char('Tracking No.', size=23, select=True, states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, copy=False)
    pickupdate = fields.Datetime('Pickup Date', help="Pickup Date, usually the time DESC pickup @ SLC", select=True, states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    eta = fields.Date('ETA', compute='_eta')
    remark = fields.Char('Remark', size=64)  
    description = fields.Text('Notes')
    
    state = fields.Selection(STATE_SELECTION, 'Status', readonly=True,
                                  help=' * The \'Draft\' status is set automatically when purchase order in draft status. \
                                   \n* The \'Confirmed\' status is set automatically as confirm when purchase order in confirm status. \
                                   \n* The \'Done\' status is set automatically when purchase order is set as done. \
                                   \n* The \'Cancelled\' status is set automatically when user cancel purchase order.',
                                  select=True, copy=False)
     
     
    @api.one
    def _eta(self):
        self.eta = fields.datetime.now()
    
    @api.one
    def confirm_order(self):
        self.state = 'confirmed'
        
    @api.one
    @api.depends('shpr_id')
    def _org_get(self):
        if not (self.shpr_id):            
            return
        
        self.org = self.shpr_id.city
    
    @api.one
    @api.depends('cnee_id')
    def _dst_get(self):
        if not (self.cnee_id):            
            return
        
        self.dst = self.cnee_id.city
        

    @api.one
    @api.depends('org', 'dst')
    def _tt_get(self):
        if self.org and self.dst:            
            self.tt = random.randint(1, 10)
        else:
            self.tt = 0                  
          

#----------------------------------------------------------
# Transport order_line
#----------------------------------------------------------
class transport_order_line(models.Model):
    _table = 'transport_order_line'
    _name = 'transport.order.line'
    _description = 'Purchase Order Line'
    
    def _amount_line(self, cr, uid, ids, prop, arg, context=None):
        res = {}
#         cur_obj=self.pool.get('res.currency')
#         tax_obj = self.pool.get('account.tax')
        for line in self.browse(cr, uid, ids, context=context):
#             taxes = tax_obj.compute_all(cr, uid, line.taxes_id, line.price_unit, line.product_qty, line.product_id, line.order_id.partner_id)
#             cur = line.order_id.pricelist_id.currency_id
#             res[line.id] = cur_obj.round(cr, uid, cur, taxes['total'])
            res[line.id] = random.randint(11, 99)
        return res
    
    def _get_uom_id(self, cr, uid, context=None):
        try:
            proxy = self.pool.get('ir.model.data')
            result = proxy.get_object_reference(cr, uid, 'product', 'product_uom_unit')
            return result[1]
        except Exception, ex:
            return False
            
    name = fields.Text('Description', required=True)
    product_qty = fields.Float('Quantity', digits_compute=dp.get_precision('Product Unit of Measure'), required=True)
#     'taxes_id': fields.many2many('account.tax', 'purchase_order_taxe', 'ord_id', 'tax_id', 'Taxes')
    product_uom = fields.Many2one('product.uom', 'Product Unit of Measure', required=True)
    product_id = fields.Many2one('product.product', 'Product', domain=[('purchase_ok','=',True)], change_default=True)        
    price_unit = fields.Float('Unit Price', required=True, digits_compute= dp.get_precision('Product Price'))
    price_subtotal = fields.Float(compute='_amount_line', string='Subtotal', digits_compute= dp.get_precision('Account'))
    order_id = fields.Many2one('transport.order', 'Order Reference', select=True, required=True, ondelete='cascade')        
#         'company_id': fields.related('order_id','company_id',type='many2one',relation='res.company',string='Company', store=True, readonly=True),
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed'), ('done', 'Done'), ('cancel', 'Cancelled')],
                              'Status', required=True, readonly=True, copy=False,
                              help=' * The \'Draft\' status is set automatically when purchase order in draft status. \
                                   \n* The \'Confirmed\' status is set automatically as confirm when purchase order in confirm status. \
                                   \n* The \'Done\' status is set automatically when purchase order is set as done. \
                                   \n* The \'Cancelled\' status is set automatically when user cancel purchase order.')
    
#         'invoice_lines': fields.many2many('account.invoice.line', 'purchase_order_line_invoice_rel',
#                                           'order_line_id', 'invoice_id', 'Invoice Lines',
#                                           readonly=True, copy=False),
#         'invoiced': fields.boolean('Invoiced', readonly=True, copy=False),

#     partner_id = fields.Related('order_id', 'partner_id', string='Partner', readonly=True, type="many2one", relation="res.partner", store=True)
#     date_order = fields.Related('order_id', 'date_order', string='Order Date', readonly=True, type="datetime")        
    
    
#     http://odoo-new-api-guide-line.readthedocs.org/en/latest/fields.html







                        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
