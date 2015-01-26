# -*- coding: utf-8 -*-

from openerp.osv import osv, fields
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp import tools
import time
import logging
_logger = logging.getLogger(__name__)

from openerp import models, api, exceptions

#----------------------------------------------------------
# Transport Course 
#----------------------------------------------------------
class transport_course(osv.osv):
    _name = 'transport.course'

    _columns = {
        'name': fields.char(string="Title", required=True),
        'description': fields.text(string="description"),
        
        'responsible_id': fields.many2one('res.users',ondelete='set null', string="Responsible", index=True),
        'session_ids': fields.one2many('transport.session', 'course_id', string="Sessions"),
        'attendee_ids': fields.many2many('res.partner', string="Attendees"),
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
        'name': fields.char(string="Session", required=True),
        'start_date': fields.date(string="start_date"),
        'duration': fields.float(string="duration", digits=(6, 2), help="Duration in days"),
        'seats': fields.integer(string="Number of seats"),
        'active': fields.boolean(string="Active", default=True), 
        
        'instructor_id': fields.many2one('res.partner', string="Instructor", domain=['|', ('instructor', '=', True),
                     ('category_id.name', 'ilike', "Teacher")]),
        'course_id': fields.many2one('transport.course',ondelete='cascade', string="Course", required=True),
        'attendee_ids': fields.many2many('res.partner', string="Attendees"),
        
        'taken_seats': fields.float(string="Taken seats", compute='_taken_seats'),
        
    }
    
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
        'name': fields.char('BizNo', size=16, select=True, readonly=True),
        'category': fields.char('EDI', size=6, select=True, readonly=True),
        'msgid': fields.char('MsgID', size=50, readonly=True),
        'fname': fields.char('FileName', size=100, readonly=True),
        'isa': fields.char('ISA#', size=9, select=True, readonly=True),
        'recvtime': fields.datetime('ReceiveTime', help="DHL Link EDI Receive Time", readonly=True),
        'sendtime': fields.datetime('SendTime', help="DHL Link EDI Send Time", readonly=True),
        'exception': fields.char('ExceptionID', size=10, readonly=True),        
        'email': fields.char('Email', size=30, readonly=True),        
        'remark': fields.char('Remark', size=200, readonly=True),        
        'hawb': fields.char('HAWB', size=50, readonly=True),
        'eventcd': fields.char('EventCode', size=3, readonly=True),
        'eventdate': fields.char('EventDate', size=16, readonly=True),
        'city': fields.char('City', size=32, readonly=True),
        'gweight': fields.float('G.Weight', digits_compute=dp.get_precision('Product Unit of Measure'), readonly=True),
        'partno': fields.char('Part#', size=16, readonly=True),
        'qty': fields.float('Qty', digits_compute=dp.get_precision('Product Unit of Measure'), readonly=True),        
        'gentime': fields.datetime('GenTime', select=True, readonly=True),
        'state': fields.selection([('draft', 'New'),
                                   ('done', 'Done'),
                                   ], 'Status', readonly=True, select=True,
                 help= "* New: When the EDI is created and not yet confirmed.\n"\
                       "* Done: When the EDI is completed & arichived, the state is \'Done\'."),          
        'note': fields.text('Notes'),
    }
    _defaults = {
        'state': 'draft',
        'gentime': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
    }   
    
    _log_access = False
    


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
