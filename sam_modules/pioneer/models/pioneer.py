# -*- coding: utf-8 -*-


from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp import tools
import time
import logging
#from win32con import DST_BITMAP
_logger = logging.getLogger(__name__)

from openerp import models, fields, api, exceptions
from datetime import timedelta


from geopy import geocoders
from geopy.exc import GeocoderTimedOut
g_api_key = 'AIzaSyDmIYy2HIVH1wSd622gPTZ8sFAvOEwuUPU'
#import random


#----------------------------------------------------------
# pioneer order 
#----------------------------------------------------------
class pioneer_order(models.Model):
    _name = "pioneer.order"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = "pioneer Order"
    _rec_name = 'dn'
    _order = 'id desc'
    
    
    STATE_SELECTION = [
        ('draft', 'Draft'),
#         ('sent', 'PreAlert'),
#         ('confirmed', 'Confirmed'),
#         ('approved', 'Purchase Confirmed'),
        ('shipping', 'Shipping'),
        ('pod', 'POD'),
#         ('invoiced', 'Invoiced'),
        ('done', 'Done'),
#         ('cancel', 'Cancelled'),
    ]
    
    @api.one
    @api.depends('order_line')
    def _qty_all(self):
        val = 0 
        for line in self.order_line:
           val += line.product_qty
        
        self.qty = val
        
    dn = fields.Char('Delivery No.', size=10, select=True, required=True, states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, copy=False)
    #product_id = fields.Many2one('product.product', 'Material', required=True, select=True, domain=[('type', '<>', 'service')], states={'done': [('readonly', True)]})
    
    state_id = fields.Many2one("res.country.state", 'State', ondelete='restrict')
    city = fields.Char('City')
    district = fields.Char('district')
    street =  fields.Char('Street')
    street2 = fields.Char('Street2')
    zip = fields.Char('Zip', size=24, change_default=True)    
#     'country_id': fields.many2one('res.country', 'Country', ondelete='restrict'),
    email = fields.Char('Email')
    phone = fields.Char('Phone')
    mobile = fields.Char('Mobile')
    partner_latitude = fields.Float('Geo Latitude', digits=(16, 6))
    partner_longitude = fields.Float('Geo Longitude', digits=(16, 6))
    formatted_address = fields.Char('Formatted Address', readonly=True)
    date_localization = fields.Date('Geo Localization Date')
    
    cnee_name = fields.Char('Name', size=128)
    sales_doc = fields.Char('Sales Doc', size=10)
    pono = fields.Char('Purchase Order', size=32)       
    cnee_id = fields.Many2one('res.partner', 'Consignee', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, 
                                 domain=['|', ('instructor', '=', True),('category_id.name', 'ilike', "Teacher")])    
    shpr_pt = fields.Char('ShPt', size=4)
    shpr_id = fields.Many2one('res.partner', 'Shipper', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, 
                                 domain=['|', ('instructor', '=', True),('category_id.name', 'ilike', "OEM")])
    partner_name = fields.Char("Customer Name", size=64,help='The name of the future partner company that will be created while converting the lead into opportunity', select=1)
#     org = fields.Char("Orig", compute='_org_get')
#     dst = fields.Char("Dest", compute='_dst_get')
    org = fields.Many2one('pioneer.city', 'Org', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    dst = fields.Many2one('pioneer.city', 'Dest', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    poe = fields.Char("POE", size=4)
#     tt = fields.Float("Transit Time", compute='_tt_get', help="Transit Time in days")
    qty = fields.Integer('Dlvy Qty', compute='_qty_all', help="The Total Quantity of this DN", multi="sums")    
    plt_qty = fields.Integer('Plt Qty', default=1)
    order_line = fields.One2many('pioneer.order.line', 'order_id', 'Order Lines',
                                      states={'picking':[('readonly',True)],
                                              'done':[('readonly',True)]},
                                      copy=True)
    hawb = fields.Char('HAWB', size=23, states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, copy=False)
    trackno = fields.Char('Tracking No.', size=23, select=True, states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, copy=False)
    pickupdate = fields.Datetime('Pickup Date', help="Pickup Date, usually the time DESC pickup @ SLC", select=True, states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
#     eta = fields.Date('ETA', compute='_eta')
    eta = fields.Datetime('ETA', help="Estimated Time of Arrival.", select=True, states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    remark = fields.Char('Remark', size=64)  
    description = fields.Text('Notes')
#     taken_event = fields.Integer('Taken Events', compute='_taken_event')
    state = fields.Selection(STATE_SELECTION, 'Status', readonly=True,
                                  help=' * The \'Draft\' status is set automatically when purchase order in draft status. \
                                   \n* The \'Confirmed\' status is set automatically as confirm when purchase order in confirm status. \
                                   \n* The \'Done\' status is set automatically when purchase order is set as done. \
                                   \n* The \'Cancelled\' status is set automatically when user cancel purchase order.',
                                  select=True, copy=False)
     
    _defaults = {
        'state': 'draft',
    }
        
    _sql_constraints = [
        ('order_dn_unique',
         'UNIQUE(dn)',
         "The DN# must be unique"),
    ]
    
    
    @api.model
    def _address_as_string(self):
        addr = []
        if self.state_id:
            addr.append(self.state_id.name)
        if self.city:
            addr.append(self.city)
        if self.district:
            addr.append(self.district)                                            
        if self.street:
            addr.append(self.street)
        if self.street2:
            addr.append(self.street2)
#         if self.zip:
#             addr.append(self.zip)            
        if not addr:
            raise Warning(
                _("Address missing on Order: '%s'.") % self.name)
        address = ' '.join(addr)
        return address
    
    @api.one
    def geocode_address(self):
        """Get the latitude and longitude by requesting "mapquestapi"
        see http://open.mapquestapi.com/geocoding/
        """
#         url = 'http://nominatim.openstreetmap.org/search'
#         pay_load = {
#             'limit': 1,
#             'format': 'json',
#             'street': self.street or '',
#             'postalCode': self.zip or '',
#             'city': self.city or '',
#             'state':  self.state_id and self.state_id.name or '',
# #             'country': self.country_id and self.country_id.name or '',
# #             'countryCodes': self.country_id and self.country_id.code or ''
#             }
# 
#         request_result = requests.get(url, params=pay_load)
#         try:
#             request_result.raise_for_status()
#         except Exception as e:
#             _logger.exception('Geocoding error')
#             raise exceptions.Warning(_(
#                 'Geocoding error. \n %s') % e.message)
#         a = tools.ustr(', '.join(filter(None, [self.state, self.street, ("%s %s" % (self.city or '', self.zip or '')).strip(),'China'])))
#         print a
        g = geocoders.GoogleV3(g_api_key)
        try:
            result = g.geocode(self._address_as_string(), exactly_one=False, language='zh-cn')          
#         except (ValueError, GQueryError, GeocoderResultError,GBadKeyError, GTooManyQueriesError, GeocoderTimedOut):
        except Exception as e:
            _logger.exception('Geocoding error')
            raise exceptions.Warning(_(
                'Geocoding error. \n %s') % e.message)
            
        if result:
            place, (lat, lng) = list(result)[0]
            self.write({
                'partner_latitude': lat,
                'partner_longitude': lng,
                'formatted_address': place,
                'date_localization': fields.Date.today()})        
             
    @api.one
    def geo_localize(self):
        print "geo_localize called."
        self.geocode_address()
        return True
    
    @api.one
    def action_draft(self):
        print '2222223  33333333333333333333'
        self.state = 'draft'  
        
    @api.one
    def action_shipping(self):
        print '444444444444444444444444444444 '
        self.state = 'shipping'

    @api.one
    def action_pod(self):
        self.state = 'pod'
                
    @api.one
    def action_done(self):
        self.state = 'done'


    
#     @api.one
#     @api.depends('edi_detail')
#     def _taken_event(self):
#         print 11111111111111111111111111111
#         if self.edi_detail:
#             if self.state == 'draft' and self.taken_event <> 1:
#                 print "mmmmmmmmmmmmmmmmmmmmmmmmmmmm"
#                 for cd in self.edi_detail:
#                     print cd.eventcd
#                     if cd.eventcd == 'AF':
#                         print self.state
#                         self.state = 'shipping'
#                         self.taken_event = 1                        
#                         break
                    
          

#----------------------------------------------------------
# pioneer order line
#----------------------------------------------------------
class pioneer_order_line(models.Model):
#     _table = 'pioneer_order_line'
    _name = 'pioneer.order.line'
    _description = 'pioneer Order Line'
    
    def _amount_line(self, cr, uid, ids, prop, arg, context=None):
        res = {}
        cur_obj=self.pool.get('res.currency')
        #tax_obj = self.pool.get('account.tax')
        for line in self.browse(cr, uid, ids, context=context):
            #taxes = tax_obj.compute_all(cr, uid, line.taxes_id, line.price_unit, line.product_qty, line.product_id, line.order_id.partner_id)
            cur = line.order_id.pricelist_id.currency_id
            res[line.id] = cur_obj.round(cr, uid, cur, taxes['total'])
        return res


    name = fields.Text('Description', required=True)
    #product_qty = fields.Float('Quantity', digits_compute=dp.get_precision('Product Unit of Measure'), required=True, default=lambda *a: 1.0)
    product_qty = fields.Integer('Quantity', required=True, default=lambda *a: 1.0)
    #'date_planned': fields.date('Scheduled Date', required=True, select=True),
    #'taxes_id': fields.many2many('account.tax', 'purchase_order_taxe', 'ord_id', 'tax_id', 'Taxes'),
    product_uom = fields.Many2one('product.uom', 'Product Unit of Measure', required=True)
    product_id = fields.Many2one('product.product', 'Material', required=True, select=True, domain=[('type', '<>', 'service')], states={'done': [('readonly', True)]})
    #'move_ids': fields.one2many('stock.move', 'purchase_line_id', 'Reservation', readonly=True, ondelete='set null'),
    price_unit = fields.Float('Unit Price', required=True, digits_compute= dp.get_precision('Product Price'))
    #price_subtotal = fields.Float(compute='_amount_line', string='Subtotal')
    order_id = fields.Many2one('pioneer.order', 'Order Reference', select=True, required=True, ondelete='cascade')
    #'account_analytic_id':fields.many2one('account.analytic.account', 'Analytic Account',),
    #'company_id': fields.related('order_id','company_id',type='many2one',relation='res.company',string='Company', store=True, readonly=True),
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed'), ('done', 'Done'), ('cancel', 'Cancelled')],
                              'Status', required=True, readonly=True, copy=False, default=lambda *args: 'draft',
                              help=' * The \'Draft\' status is set automatically when purchase order in draft status. \
                                   \n* The \'Confirmed\' status is set automatically as confirm when purchase order in confirm status. \
                                   \n* The \'Done\' status is set automatically when purchase order is set as done. \
                                   \n* The \'Cancelled\' status is set automatically when user cancel purchase order.')
                                                       


#(parent.pricelist_id,product_id,0,False,parent.partner_id, parent.date_order,parent.fiscal_position,date_planned,name,False,parent.state,context)"
    def onchange_product_id(self, cr, uid, ids, product_id, qty, uom_id,
            partner_id, 
            name=False, state='draft', context=None):
        """
        onchange handler of product_id.
        """
        if context is None:
            context = {}

        res = {'value': {'name': name or '', 'product_uom' : uom_id or False}}
        if not product_id:
            return res

        product_product = self.pool.get('product.product')
        product_uom = self.pool.get('product.uom')
        res_partner = self.pool.get('res.partner')
        #product_pricelist = self.pool.get('product.pricelist')
        #account_fiscal_position = self.pool.get('account.fiscal.position')
        #account_tax = self.pool.get('account.tax')

        # - check for the presence of partner_id and pricelist_id
        #if not partner_id:
        #    raise osv.except_osv(_('No Partner!'), _('Select a partner in purchase order to choose a product.'))
        #if not pricelist_id:
        #    raise osv.except_osv(_('No Pricelist !'), _('Select a price list in the purchase order form before choosing a product.'))

        # - determine name and notes based on product in partner lang.
        context_partner = context.copy()
        if partner_id:
            lang = res_partner.browse(cr, uid, partner_id).lang
            context_partner.update( {'lang': lang, 'partner_id': partner_id} )
        product = product_product.browse(cr, uid, product_id, context=context_partner)
        #call name_get() with partner in the context to eventually match name and description in the seller_ids field
        dummy, name = product_product.name_get(cr, uid, product_id, context=context_partner)[0]
        if product.description_purchase:
            name += '\n' + product.description_purchase
        res['value'].update({'name': name})

        # - set a domain on product_uom
        res['domain'] = {'product_uom': [('category_id','=',product.uom_id.category_id.id)]}

        # - check that uom and product uom belong to the same category
        product_uom_po_id = product.uom_po_id.id
        if not uom_id:
            uom_id = product_uom_po_id

        if product.uom_id.category_id.id != product_uom.browse(cr, uid, uom_id, context=context).category_id.id:
            if context.get('purchase_uom_check') and self._check_product_uom_group(cr, uid, context=context):
                res['warning'] = {'title': _('Warning!'), 'message': _('Selected Unit of Measure does not belong to the same category as the product Unit of Measure.')}
            uom_id = product_uom_po_id

        res['value'].update({'product_uom': uom_id})

#         # - determine product_qty and date_planned based on seller info
#         if not date_order:
#             date_order = fields.datetime.now()


#         supplierinfo = False
#         precision = self.pool.get('decimal.precision').precision_get(cr, uid, 'Product Unit of Measure')
#         for supplier in product.seller_ids:
#             if partner_id and (supplier.name.id == partner_id):
#                 supplierinfo = supplier
#                 if supplierinfo.product_uom.id != uom_id:
#                     res['warning'] = {'title': _('Warning!'), 'message': _('The selected supplier only sells this product by %s') % supplierinfo.product_uom.name }
#                 min_qty = product_uom._compute_qty(cr, uid, supplierinfo.product_uom.id, supplierinfo.min_qty, to_uom_id=uom_id)
#                 if float_compare(min_qty , qty, precision_digits=precision) == 1: # If the supplier quantity is greater than entered from user, set minimal.
#                     if qty:
#                         res['warning'] = {'title': _('Warning!'), 'message': _('The selected supplier has a minimal quantity set to %s %s, you should not purchase less.') % (supplierinfo.min_qty, supplierinfo.product_uom.name)}
#                     qty = min_qty
#         dt = self._get_date_planned(cr, uid, supplierinfo, date_order, context=context).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        qty = qty or 1.0
#         res['value'].update({'date_planned': date_planned or dt})
        if qty:
            res['value'].update({'product_qty': qty})

#         price = price_unit
#         if price_unit is False or price_unit is None:
#             # - determine price_unit and taxes_id
#             if pricelist_id:
#                 date_order_str = datetime.strptime(date_order, DEFAULT_SERVER_DATETIME_FORMAT).strftime(DEFAULT_SERVER_DATE_FORMAT)
#                 price = product_pricelist.price_get(cr, uid, [pricelist_id],
#                         product.id, qty or 1.0, partner_id or False, {'uom': uom_id, 'date': date_order_str})[pricelist_id]
#             else:
#                 price = product.standard_price
# 
#         taxes = account_tax.browse(cr, uid, map(lambda x: x.id, product.supplier_taxes_id))
#         fpos = fiscal_position_id and account_fiscal_position.browse(cr, uid, fiscal_position_id, context=context) or False
#         taxes_ids = account_fiscal_position.map_tax(cr, uid, fpos, taxes)
#         res['value'].update({'price_unit': price, 'taxes_id': taxes_ids})

        return res                

#----------------------------------------------------------
# Pioneer City 
#----------------------------------------------------------
class pioneer_city(models.Model):
    _name = 'pioneer.city'
     
    name = fields.Char('City Code', required=True, size=4) 
    cityname = fields.Char('City Name', size=32)
    province = fields.Char('Province', size=32)
    province_cn = fields.Char('Proince CN', size=16)
    province_sn = fields.Char('Proince ShortName', size=1)
    
    _sql_constraints = [
        ('cityname_unique',
         'UNIQUE(name)',
         "The City Code must be unique"),
    ]  
        
    
#     http://odoo-new-api-guide-line.readthedocs.org/en/latest/fields.html


                        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
