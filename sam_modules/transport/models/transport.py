# -*- coding: utf-8 -*-

from openerp.osv import osv
from openerp.osv import fields as FD

from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp import tools
import time
import logging
_logger = logging.getLogger(__name__)

from openerp import models, fields, api, exceptions
from datetime import timedelta


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
        if is_test:
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
    partner_id = fields.Many2one('res.partner', 'Customer', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, 
                                 domain=['|', ('instructor', '=', True),('category_id.name', 'ilike', "Teacher")])    
    partner_name = fields.Char("Customer Name", size=64,help='The name of the future partner company that will be created while converting the lead into opportunity', select=1)
    qty = fields.Integer('Dlvy Qty')
    plt_qty = fields.Integer('Plt Qty')
    hawb = fields.Char('HAWB', size=23, states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, copy=False)
    trackno = fields.Char('Tracking No.', size=23, select=True, states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, copy=False)
    pickupdate = fields.Datetime('Pickup Date', help="Pickup Date, usually the time DESC pickup @ SLC", select=True, states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    eta = fields.Date('ETA', compute='_eta')  
    description = fields.Text('Notes')
    state = fields.Selection(STATE_SELECTION, 'Status', readonly=True,
                                  help="The status of the transport order. "
                                       "A request for quotation is a purchase order in a 'Draft' status. "
                                       "Then the order has to be confirmed by the user, the status switch "
                                       "to 'Confirmed'. Then the supplier must confirm the order to change "
                                       "the status to 'Approved'. When the purchase order is paid and "
                                       "received, the status becomes 'Done'. If a cancel action occurs in "
                                       "the invoice or in the receipt of goods, the status becomes "
                                       "in exception.",
                                  select=True, copy=False)
     
     
    @api.one
    def _eta(self):
        self.eta = fields.datetime.now()
    
    @api.one
    def action_confirm(self):
        self.state = 'confirmed'
    
#     partner_id = fields.Many2one('res.partner', 'Partner', ondelete='set null', track_visibility='onchange',
#             select=True, help="Linked partner (optional). Usually created when converting the lead.")
#     contact_name = fields.Char('Contact Name', size=64)
#     partner_name = fields.Char("Customer Name", size=64,help='The name of the future partner company that will be created while converting the lead into opportunity', select=1)
#     
#     org = fields.Char(string="Origin", required=True, size=4)
#     dst = fields.Char(string="Destination", required=True, size=4)
#     itinerary = fields.Char(string="Itinerary", compute='_itinerary')
#     dstprovince = fields.Char(string="Province", size=30)
#     tt = fields.Float(string="Transit Time", digits=(5, 1), help="Transit Time in days")
#     is_test = fields.Boolean('Is a Test', help="Check if the contact is a company, otherwise it is a person")
#     
#     eta = fields.function(get_eta_date, multi="min_max_date", fnct_inv=_set_min_date,
#                  store={'stock.move': (_get_pickings, ['date_expected', 'picking_id'], 20)}, type='datetime', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, string='ETA', select=True, help="Scheduled time for Arrival")
#                  
#     _columns = {
#         'name': fields.char('Reference', select=True, states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, copy=False),
#         'origin': fields.char('Source Document', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, help="Reference of the document", select=True),
#         'backorder_id': fields.many2one('stock.picking', 'Back Order of', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, help="If this shipment was split, then this field links to the shipment which contains the already processed part.", select=True, copy=False),
#         'note': fields.text('Notes', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}),
#         'move_type': fields.selection([('direct', 'Partial'), ('one', 'All at once')], 'Delivery Method', required=True, states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, help="It specifies goods to be deliver partially or all at once"),
#         'state': fields.function(_state_get, type="selection", copy=False,
#             store={
#                 'stock.picking': (lambda self, cr, uid, ids, ctx: ids, ['move_type'], 20),
#                 'stock.move': (_get_pickings, ['state', 'picking_id', 'partially_available'], 20)},
#             selection=[
#                 ('draft', 'Draft'),
#                 ('cancel', 'Cancelled'),
#                 ('waiting', 'Waiting Another Operation'),
#                 ('confirmed', 'Waiting Availability'),
#                 ('partially_available', 'Partially Available'),
#                 ('assigned', 'Ready to Transfer'),
#                 ('done', 'Transferred'),
#                 ], string='Status', readonly=True, select=True, track_visibility='onchange',
#             help="""
#                 * Draft: not confirmed yet and will not be scheduled until confirmed\n
#                 * Waiting Another Operation: waiting for another move to proceed before it becomes automatically available (e.g. in Make-To-Order flows)\n
#                 * Waiting Availability: still waiting for the availability of products\n
#                 * Partially Available: some products are available and reserved\n
#                 * Ready to Transfer: products reserved, simply waiting for confirmation.\n
#                 * Transferred: has been processed, can't be modified or cancelled anymore\n
#                 * Cancelled: has been cancelled, can't be confirmed anymore"""
#         ),
#         'priority': fields.function(get_min_max_date, multi="min_max_date", fnct_inv=_set_priority, type='selection', selection=procurement.PROCUREMENT_PRIORITIES, string='Priority',
#                                     store={'stock.move': (_get_pickings, ['priority', 'picking_id'], 20)}, states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, select=1, help="Priority for this picking. Setting manually a value here would set it as priority for all the moves",
#                                     track_visibility='onchange', required=True),
#         'min_date': fields.function(get_min_max_date, multi="min_max_date", fnct_inv=_set_min_date,
#                  store={'stock.move': (_get_pickings, ['date_expected', 'picking_id'], 20)}, type='datetime', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, string='Scheduled Date', select=1, help="Scheduled time for the first part of the shipment to be processed. Setting manually a value here would set it as expected date for all the stock moves.", track_visibility='onchange'),
#         'max_date': fields.function(get_min_max_date, multi="min_max_date",
#                  store={'stock.move': (_get_pickings, ['date_expected', 'picking_id'], 20)}, type='datetime', string='Max. Expected Date', select=2, help="Scheduled time for the last part of the shipment to be processed"),
#         'date': fields.datetime('Creation Date', help="Creation Date, usually the time of the order", select=True, states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, track_visibility='onchange'),
#         'date_done': fields.datetime('Date of Transfer', help="Date of Completion", states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, copy=False),
#         'move_lines': fields.one2many('stock.move', 'picking_id', 'Internal Moves', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, copy=True),
#         'quant_reserved_exist': fields.function(_get_quant_reserved_exist, type='boolean', string='Quant already reserved ?', help='technical field used to know if there is already at least one quant reserved on moves of a given picking'),
#         'partner_id': fields.many2one('res.partner', 'Partner', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}),
#         'company_id': fields.many2one('res.company', 'Company', required=True, select=True, states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}),
#         'pack_operation_ids': fields.one2many('stock.pack.operation', 'picking_id', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, string='Related Packing Operations'),
#         'pack_operation_exist': fields.function(_get_pack_operation_exist, type='boolean', string='Pack Operation Exists?', help='technical field for attrs in view'),
#         'picking_type_id': fields.many2one('stock.picking.type', 'Picking Type', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, required=True),
#         'picking_type_code': fields.related('picking_type_id', 'code', type='char', string='Picking Type Code', help="Technical field used to display the correct label on print button in the picking view"),
# 
#         'owner_id': fields.many2one('res.partner', 'Owner', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, help="Default Owner"),
#         # Used to search on pickings
#         'product_id': fields.related('move_lines', 'product_id', type='many2one', relation='product.product', string='Product'),
#         'recompute_pack_op': fields.boolean('Recompute pack operation?', help='True if reserved quants changed, which mean we might need to recompute the package operations', copy=False),
#         'location_id': fields.related('move_lines', 'location_id', type='many2one', relation='stock.location', string='Location', readonly=True),
#         'location_dest_id': fields.related('move_lines', 'location_dest_id', type='many2one', relation='stock.location', string='Destination Location', readonly=True),
#         'group_id': fields.related('move_lines', 'group_id', type='many2one', relation='procurement.group', string='Procurement Group', readonly=True,
#               store={
#                   'stock.picking': (lambda self, cr, uid, ids, ctx: ids, ['move_lines'], 10),
#                   'stock.move': (_get_pickings, ['group_id', 'picking_id'], 10),
#               }),
#     }
# 
#     _defaults = {
#         'name': '/',
#         'state': 'draft',
#         'move_type': 'direct',
#         'priority': '1',  # normal
#         'date': fields.datetime.now,
#         'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid, 'stock.picking', context=c),
#         'recompute_pack_op': True,
#     }
#     _sql_constraints = [
#         ('name_uniq', 'unique(name, company_id)', 'Reference must be unique per company!'),
#     ]
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
