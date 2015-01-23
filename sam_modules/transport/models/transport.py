# -*- coding: utf-8 -*-

from openerp.osv import osv, fields
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp import tools
import time
import logging
_logger = logging.getLogger(__name__)

from openerp import models, api

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
    
class transport_session(osv.osv):
    _name = 'transport.session'

    _columns = {
        'name': fields.char(string="Session", required=True),
        'start_date': fields.date(string="start_date"),
        'duration': fields.float(string="duration", digits=(6, 2), help="Duration in days"),
        'seats': fields.integer(string="Number of seats"),
        
        'instructor_id': fields.many2one('res.partner', string="Instructor"),
        'course_id': fields.many2one('transport.course',ondelete='cascade', string="Course", required=True),
        'attendee_ids': fields.many2many('res.partner', string="Attendees"),
    }
    
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
