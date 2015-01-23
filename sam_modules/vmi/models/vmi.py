# -*- coding: utf-8 -*-

from openerp.osv import osv, fields
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
import time
import logging
_logger = logging.getLogger(__name__)

#----------------------------------------------------------
# 852 Recon
#----------------------------------------------------------
class vmi_recon(osv.osv):
    _name = "vmi.recon"
    _description = "852 Recon"
    _columns = {
        'name': fields.char('EDI', size=32, required=True, help="from_partner of EDI"),
        'hub': fields.char('Hub', size=32, required=True, help="from_partner of EDI"),
        'partner': fields.char('Partner', size=32, required=True, help="Code for to_partner"),
        'isano': fields.char('ISA#', size=10, required=True, help="ISA# of EDI"),
        'docno': fields.char('Doc#', size=32, required=True, help="Doc#"),
        'edidate': fields.char('edidate', size=16),
        'editime': fields.char('editime', size=16),
        'partno': fields.char('Part#', size=16),
        'lot': fields.char('lot', size=16),
        'qty': fields.float('Qty', digits_compute=dp.get_precision('Product Unit of Measure')),
        'date_recorded': fields.datetime('Datetime', select=True),
    }
    _defaults = {
        'date_recorded': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
    }


#----------------------------------------------------------
# vmi envstat
#----------------------------------------------------------
class vmi_envstat(osv.osv):
    _name = "vmi.envstat"
    _inherit = ['mail.thread']
    _description = "Hub Temperature & Humidity"
    _order = "id desc"
    
#    def message_post(self, *args, **kwargs):
#        """Post the message on stock.picking to be able to see it in the form view when using the chatter"""
#        return self.pool.get('vmi.envstat').message_post(*args, **kwargs)
#
#    def message_subscribe(self, *args, **kwargs):
#        """Send the subscribe action on stock.picking model as it uses _name in request"""
#        return self.pool.get('vmi.envstat').message_subscribe(*args, **kwargs)
#
#    def message_unsubscribe(self, *args, **kwargs):
#        """Send the unsubscribe action on stock.picking model to match with subscribe"""
#        return self.pool.get('vmi.envstat').message_unsubscribe(*args, **kwargs)


    _columns = {
        'name': fields.char('Reference', size=64, select=True, states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
        'hub': fields.char('Hub', size=3, select=True),
        'date_recorded': fields.datetime('Datetime', help="the time of the Stat.", select=True, states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
        'humidity': fields.float('Humidity', digits_compute=dp.get_precision('Product Unit of Measure'), states={'done': [('readonly', True)]}),
        'temperature': fields.float('Temperature', digits_compute=dp.get_precision('Product Unit of Measure'), states={'done': [('readonly', True)]}),
        'state': fields.selection([('draft', 'New'),
                                   ('cancel', 'Cancelled'),
                                   ('waiting', 'Waiting Another Move'),
                                   ('confirmed', 'Waiting Availability'),
                                   ('assigned', 'Available'),
                                   ('done', 'Done'),
                                   ], 'Status', readonly=True, select=True,
                 help= "* New: When the stock move is created and not yet confirmed.\n"\
                       "* Waiting Another Move: This state can be seen when a move is waiting for another one, for example in a chained flow.\n"\
                       "* Waiting Availability: This state is reached when the procurement resolution is not straight forward. It may need the scheduler to run, a component to me manufactured...\n"\
                       "* Available: When products are reserved, it is set to \'Available\'.\n"\
                       "* Done: When the shipment is processed, the state is \'Done\'."),        
        'note': fields.text('Notes'),
    }
    _defaults = {
        'state': 'draft',
        'hub': 'SHA',
        'date_recorded': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
    }
    
    
#----------------------------------------------------------
# vmi POD
#----------------------------------------------------------
class vmi_pod(osv.osv):
    _name = "vmi.pod"
    _description = "Hub POD Status"
    _order = "id desc"


    _columns = {
        'etd': fields.datetime('ETD', help="Estimated Time of Departure", select=True, states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
#       'product_id': fields.related('move_lines', 'product_id', type='many2one', relation='product.product', string='Product'),
        'product_id': fields.many2one('product.product', 'Item', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'dn': fields.char('DN#', size=10, readonly=True, states={'draft': [('readonly', False)]}),
        'product_qty': fields.integer('Qty', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'partner_id': fields.many2one('res.partner', 'OEM', readonly=True, states={'draft':[('readonly',False)]}, required=True, change_default=True, select=True, track_visibility='always'),
        'hawb': fields.char('HAWB', size=10, readonly=True, states={'draft': [('readonly', False)]}),
        'date_updated': fields.datetime('Update Date', select=True, readonly=False),
        'tat': fields.integer('TAT', readonly=True), 
        #fields.float('TAT',digits=(2,1)),
        'date_closed': fields.datetime('Close Date', select=True, readonly=False),
        'state': fields.selection([('draft', 'New'),
                                   ('cancel', 'Cancelled'),
                                   ('waiting', 'Waiting Another Move'),
                                   ('confirmed', 'Waiting Availability'),
                                   ('assigned', 'Available'),
                                   ('done', 'Done'),
                                   ], 'Status', readonly=True, select=True),
        'hub': fields.char('Hub', size=3, select=True),                                
        'note': fields.text('Notes'),
    }
    _defaults = {
        'state': 'draft',
        'hub': 'SHA',
    } 
    
    def draft_force_assign(self, cr, uid, ids, *args):
        """ Confirms picking directly from draft state.
        @return: True
        """
        for pick in self.browse(cr, uid, ids):
            if not pick.product_qty > 5:
                raise osv.except_osv(_('Error!'),_('You cannot process when Qty > 5.'))
            self.signal_button_confirm(cr, uid, [pick.id])
        return True    

#----------------------------------------------------------
# vmi Inventory
#----------------------------------------------------------
class vmi_inventory(osv.osv):
    _name = "vmi.inventory"
    _description = "Hub Inventory"
    _order = "id desc"


    _columns = {
        'plant': fields.char('Plant', size=4),
        'location': fields.char('Location', size=7),
        'loc_status': fields.char('Loc_Status', size=8),
        'owner': fields.char('Owner', size=3),
        'item': fields.char('Item', size=10),
        'qty': fields.integer('Qty', size=4),
        'containerid': fields.char('ContainerId', size=17),
        'recvdate': fields.datetime('RecvDate', select=True),
        'lot': fields.char('Lot', size=16),
        'itemdesc': fields.char('ItemDesc', size=100),
        'palletId': fields.char('ItemDesc', size=16),
        'state': fields.selection([('draft', 'New'),
                                   ('waiting', 'Waiting'),
                                   ('assigned', 'Assigned'),
                                   ('done', 'Done'),
                                   ], 'Status', readonly=True, select=True),
        'hub': fields.char('Hub', size=3, select=True),                                
    }
    _defaults = {
        'state': 'draft',
        'hub': 'SHA',
    } 
    
class vmi_inventory_rpt(osv.osv):
    _name = "vmi.inventory.rpt"
    _inherit = "vmi.inventory"
    _table = "vmi_inventory"
    _description = "Inventory View1"
    
    
                                  

#    def create(self, cr, uid, data, context=None):
#        if not context:
#            context = {}
#        context.update({'mail_create_nolog': True})
#        vehicle_id = super(vmi_envstat, self).create(cr, uid, data, context=context)
#        vehicle = self.browse(cr, uid, vehicle_id, context=context)
#        self.message_post(cr, uid, [vehicle_id], body=_('%s %s has been added to the stat!') % (vehicle.name,vehicle.humidity), context=context)
#        return vehicle_id


#class vmi_(osv.Model):
#    _name = 'idea.idea'
#    _columns = {
#        'name': fields.char('Title', size=64, required=True, translate=True),
#        'state': fields.selection([('draft','Draft'),
#                                   ('confirmed','Confirmed')],'State',required=True,readonly=True),
#        # Description is read-only when not draft!
#        'description': fields.text('Description', readonly=True,
#        states={'draft': [('readonly', False)]} ),
#                    'active': fields.boolean('Active'),
#                    'invent_date': fields.date('Invent date'),
#        # by convention, many2one fields end with '_id'
#            'inventor_id': fields.many2one('res.partner','Inventor'),
#            'inventor_country_id': fields.related('inventor_id','country',
#        readonly=True, type='many2one',
#        relation='res.country', string='Country'),
#        # by convention, *2many fields end with '_ids'
#        'vote_ids': fields.one2many('idea.vote','idea_id','Votes'),
#        'sponsor_ids': fields.many2many('res.partner','idea_sponsor_rel',
#        'idea_id','sponsor_id','Sponsors'),
#        'score': fields.float('Score',digits=(2,1)),
#        'category_id' = many2one('idea.category', 'Category'),
#    }
#    _defaults = {
#        'active': True, # ideas are active by default
#        'state': 'draft', # ideas are in draft state by default
#        }
#def _check_name(self,cr,uid,ids):
#    for idea in self.browse(cr, uid, ids):
#        if 'spam' in idea.name: return False # Can't create ideas with spam!
#        return True
#_sql_constraints = [('name_uniq','unique(name)', 'Ideas must be unique!')]
#_constraints = [(_check_name, 'Please avoid spam in ideas !', ['name'])]



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
