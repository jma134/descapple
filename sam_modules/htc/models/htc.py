# -*- coding: utf-8 -*-

from openerp.osv import osv, fields
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp import tools
import time
import logging
_logger = logging.getLogger(__name__)

#----------------------------------------------------------
# HTC EDI 
#----------------------------------------------------------
class htc_master(osv.osv):
    _name = "htc.master"
    _description = "HTC Master Overview"
    _order = "id desc"     

    _columns = {
        'filename': fields.char('Filename', size=50, select=True, readonly=True),
        'md5checksum': fields.char('md5checksum', size=32, select=True, readonly=True),
        'filesize': fields.integer('Filesize', readonly=True),        
        'category': fields.char('Category', size=1, select=True, readonly=True),        
        'direction': fields.char('Direction', size=3, select=True, readonly=True),
        
        'modifytime': fields.datetime('File Modified', help="EDI Modified timestamp", readonly=True),
        'createtime': fields.datetime('File Created', help="EDI Received time", readonly=True),       
        'gentime': fields.datetime('GenTime', select=True, readonly=True),    
    }
    _defaults = {
        'gentime': fields.datetime.now()
    } 
        
    _log_access = False
    
    
    
class htc_customer(osv.osv):
    _name = "htc.customer"
    _description = "HTC Customer EDI"
    _order = "id desc"     

    _columns = {
        'customer_id': fields.char('Code', size=7, select=True, readonly=True),
        'customer_name': fields.char('Name', size=20, readonly=True),
        'customer_contact_person': fields.char('Contact Person', size=20, readonly=True),        
        'customer_addr_code': fields.char('Addr Code', size=10, select=True, readonly=True),        
        'customer_addr': fields.char('Address', size=200, readonly=True),
        'customer_contact_name': fields.char('Contact Name', size=200, readonly=True),
        'customer_tel': fields.char('Tel', size=100, readonly=True),
        
        'mdftime': fields.datetime('Modified', help="DHL Link EDI Receive Time", readonly=True),    
        'gentime': fields.datetime('GenTime', select=True, readonly=True),
    }
    _defaults = {
        'gentime': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
    }   
    
    _log_access = False


class htc_customer_comp(osv.osv):
    _name = "htc.customer.comp"
    _description = "HTC Customer COMP EDI"
    _order = "id desc"     

    _columns = {
        'customer_id': fields.char('Code', size=7, select=True, readonly=True),
        'customer_name': fields.char('customer_name', size=20, readonly=True),
        'customer_contact_person': fields.char('Contact Person', size=20, readonly=True),        
        'customer_addr_code': fields.char('customer_addr_code', size=10, select=True, readonly=True),        
        'customer_addr': fields.char('customer_addr', size=200, readonly=True),
        'customer_contact_name': fields.char('customer_contact_name', size=200, readonly=True),
        'customer_tel': fields.char('customer_tel', size=100, readonly=True),
        
        'mdftime': fields.datetime('Modify Time', help="DHL Link EDI Receive Time", readonly=True),    
        'gentime': fields.datetime('GenTime', select=True, readonly=True),
    }
    _defaults = {
        'gentime': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
    }   
    
    _log_access = False


class htc_item(osv.osv):
    _name = "htc.item"
    _description = "HTC Item EDI"
    _order = "id desc"     

    _columns = {
        'htcpartno': fields.char('PartNo', size=12, select=True, readonly=True),
        'partdescription': fields.char('Description', size=100, readonly=True),
        'modelname': fields.char('Model Name', size=50, readonly=True),        
        'color': fields.char('Color', size=20, readonly=True),        
        'packdefinition': fields.integer('Pack Definition',  readonly=True),
        'palletdefinition': fields.integer('Pallet Definition', readonly=True),
            
        'mdftime': fields.datetime('Modified', help="DHL Link EDI Receive Time", readonly=True),    
        'gentime': fields.datetime('GenTime', select=True, readonly=True),
    }
    _defaults = {
        'gentime': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
    }   
    
    _log_access = False    
    

class htc_item_comp(osv.osv):
    _name = "htc.item.comp"
    _description = "HTC Item COMP EDI"
    _order = "id desc"     

    _columns = {
        'htcpartno': fields.char('PartNo', size=12, select=True, readonly=True),
        'partdescription': fields.char('Description', size=100, readonly=True),
        'modelname': fields.char('Model Name', size=50, readonly=True),        
        'color': fields.char('Color', size=20, readonly=True),        
        'packdefinition': fields.integer('Pack Definition',  readonly=True),
        'palletdefinition': fields.integer('Pallet Definition', readonly=True),
            
        'mdftime': fields.datetime('Modified', help="DHL Link EDI Receive Time", readonly=True),    
        'gentime': fields.datetime('GenTime', select=True, readonly=True),
    }
    _defaults = {
        'gentime': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
    }   
    
    _log_access = False   
    
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
