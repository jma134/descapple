# -*- coding: utf-8 -*-

from openerp.osv import osv
from openerp.osv import fields
from openerp.tools.translate import _

class mywizard(osv.osv_memory):
    _name = 'transport.mywizard'
    _description = 'Wizard with step'    
    _columns = { 
               'name1': fields.char('Name 1',),
               'name2': fields.char('Name 2',),
               'state': fields.selection([('step1', 'step1'),('step2', 'step2')])  
               } 

    def action_next(self, cr, uid, ids, context=None):
        #your treatment to click  button next 
        #...
        # update state to  step2
        self.write(cr, uid, ids, {'state': 'step2',}, context=context)
        #return view
        return {
              'type': 'ir.actions.act_window',
              'res_model': 'transport.mywizard',
              'view_mode': 'form',
              'view_type': 'form',
              'res_id': this.id,
              'views': [(False, 'form')],
              'target': 'new',
               }

    def action_previous(self, cr, uid, ids, context=None):
        #your treatment to click  button previous 
        #...
        # update state to  step1
        self.write(cr, uid, ids, {'state': 'step1',}, context=context)
        #return view
        return {
              'type': 'ir.actions.act_window',
              'res_model': 'transport.mywizard',
              'view_mode': 'form',
              'view_type': 'form',
              'res_id': this.id,
              'views': [(False, 'form')],
              'target': 'new',
               }
      
      