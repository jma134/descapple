# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.tools.translate import _

class transport_prealert(models.TransientModel):
    _name = 'transport.prealert'

    def _default_sessions(self):
        return self.env['transport.order'].browse(self._context.get('active_ids'))

    session_ids = fields.Many2many('transport.order',
        string="Orders", default=_default_sessions)
#     attendee_ids = fields.Many2many('res.partner', string="Attendees")

    @api.multi
    def subscribe(self, context=None):        
        for session in self.session_ids:
#             session.attendee_ids |= self.attendee_ids
            print session.cnee_id
        
        try:        
            template_ids  = self.env['email.template'].search([('name', '=', 'Pre-Alert - Send by Email')])
        except ValueError:
            template_ids = False
        
        email = self.env['email.template'].browse(template_ids[0])
        email[0].subject = 'asdf'
            
        
        #email.write(template_ids[0], {'subject': 'subject123'})
        #self.pool.get('email.template').write(template_ids[0], {'subject': 'subject123'})
        #self.env['email.template'].write(template_ids[0], {'subject': 'subject~~'})
#         email.write({ 'subject': 'spam & eggs'})
        
        #ir_model_data = self.pool.get('ir.model.data')
        template_id = self.env['ir.model.data'].get_object_reference('transport', 'email_template_transport_prealert')[1]
        print template_id, template_ids
        print self.ids[0], self.session_ids.ids[0]
        
        try:
            compose_form_id = self.env['ir.model.data'].get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        
        if not context:
            context= {}
                
        ctx = dict(context)
        ctx.update({
            'default_model': 'transport.order',
            'default_res_id': self.session_ids.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
        })
#         return {}
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }
        

        
        
class transport_wizardtest(models.TransientModel):
    _name = 'transport.wizardtest'


    period_from = fields.Datetime('Start period')
    period_to = fields.Datetime('End period')
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                         ('all', 'All Entries'),
                                        ], 'Target Moves')

    def transport_wizardtest_open_window(self, cr, uid, ids, context=None):
        print "Pre-Alert"
        data = self.read(cr, uid, ids, context=context)
        print data #[{'create_uid': (1, u'Administrator'), 'create_date': '2015-04-17 07:30:31', '__last_update': '2015-04-17 07:30:31', 'period_to': '2015-04-22 07:29:37', 'write_uid': (1, u'Administrator'), 'period_from': '2015-04-17 07:29:32', 'write_date': '2015-04-17 07:30:31', 'display_name': u'transport.prealert,4', 'id': 4, 'target_move': u'posted'}]
        print data[0] #get the first record {'x': 'AF', 'asdf', 332}
        return {}        