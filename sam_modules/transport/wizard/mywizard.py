# -*- coding: utf-8 -*-

from openerp import models, api
from openerp.osv import osv
from openerp.osv import fields
from openerp.tools.translate import _
import random

random.seed()

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
      



class test_partners_wizard(models.TransientModel):
    _name = "test.partners.wizard"
    _description = "Testing tree_but_open for context durability"
    _columns = {
    }
    _defaults = {
    }
    def test_partners_open_window(self, cr, uid, ids, context=None):
        mod_obj = self.pool.get('ir.model.data')
        
        if context is None:
            context = {}
#         result = mod_obj.get_object_reference(cr, uid, 'test_but_open', 'action_partners_game_tree_1')
        result = mod_obj.get_object_reference(cr, uid, 'transport', 'action_partners_game_tree_1')
        id = result and result[1] or False
        print id
        
        act_obj = self.pool.get('ir.actions.act_window')
        result = act_obj.read(cr, uid, [id], context=context)[0]
        print result
        important_value = random.randint(1,100)
        print '[step1] IMPORTANT_VALUE: %s' %important_value # print the important_vaule...        xtx = 

        result['context'] = str({'important_value': important_value, 'persist_values': [ 'important_value' ] })
        print result
        return result
    
    @api.multi
    def test_partners_open_next_wizard(self, context=None):
        if not context:
            context= {}
        print 'mmm', context
        
        result = self.env['ir.model.data'].get_object_reference('transport', 'view_test_next_level')
        print result
        id = result and result[1] or False
        
        ctx = dict(context)
        ctx.update({
            'myname': 'Sam',
        })
        print ctx
        
        return {
            'name': 'Next Level',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
#             'res_model': 'test.partners.wizard',
            'res_model': 'test.partners.level.wizard',            
            'views': [(id, 'form')],
            'view_id': id,
            'target': 'new',
#             'context': context.update({'author': 'samma'})
            'context': ctx,
        }

test_partners_wizard()

class test_partners_level_wizard(osv.osv_memory):
        _name = "test.partners.level.wizard"
        _description = "Move game to next level"
        _columns = {
        }
        _defaults = {
        }
        def next_level_mmm(self, cr, uid, ids, context=None):
            if context == None:
                context = {} 
            print context
            
            print '[step2] IMPORTANT_VALUE: %s' %context.get('important_value',False) # Now it prints: "[step2] IMPORTANT_VALUE: <same number as in the previous print (step1)>", i.e. the important_value is preserved, because it was listed in 'persist_values' list. of course it's possible to put more then one key to persist in the list and all these keys will be persisted through multiple tree_but_open actions.
            # ....

test_partners_level_wizard()

#
# ....then Wizard3 and stuff like that
# 

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:      