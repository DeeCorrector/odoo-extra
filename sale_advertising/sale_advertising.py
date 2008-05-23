
##############################################################################
#
# Copyright (c) 2008 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from osv import fields,osv
from osv import orm

class one2many_mod_advert(fields.one2many):
#this class is used to display crm.case with fields ref or ref2 which are related to the current object

	def get(self, cr, obj, ids, name, user=None, offset=0, context=None, values=None):
		if not context:
			context = {}
		if not values:
				values = {}
		res = {}
		for id in ids:
			res[id] = []
		for id in ids:
			temp = 'sale.order,'+str(id)
			query = "select id from crm_case where ref = '%s' or ref2 = '%s'" %(temp,temp)
			cr.execute(query)
			case_ids = [ x[0] for x in cr.fetchall()]
			ids2 = obj.pool.get('crm.case').search(cr, user, [(self._fields_id,'in',case_ids)], limit=self._limit)
			for r in obj.pool.get(self._obj)._read_flat(cr, user, ids2, [self._fields_id], context=context, load='_classic_write'):
				res[id].append( r['id'] )
		return res

class sale_order(osv.osv):
	_inherit = "sale.order"

	_columns = {
		'published_customer': fields.many2one('res.partner','Published Customer'),
		'adverstising_agency': fields.many2one('res.partner','Advertising Agency'),
		'case_ids': one2many_mod_advert('crm.case', 'id', "Related Cases"),
	}

	def onchange_published_customer(self, cursor, user, ids ,published_customer):
		data = {'adverstising_agency':published_customer,'partner_id':published_customer,'partner_invoice_id': False, 'partner_shipping_id':False, 'partner_order_id':False}
		if published_customer:
			address = self.onchange_partner_id(cursor, user, ids, published_customer)
			data.update(address['value'])
		return {'value' : data}

sale_order()

class sale_advertising_issue(osv.osv):
	_name = "sale.advertising.issue"
	_description="Sale Advertising Issue"
	_columns = {
		'name': fields.char('Name', size=32),
		'issue_date': fields.datetime('Issue Date'),
		'medium': fields.many2one('product.category','Medium'),
		'state': fields.selection([('open','Open'),('close','Close')], 'State'),
		'default_note': fields.text('Default Note'),
	}
sale_advertising_issue()

class sale_order_line(osv.osv):
	_inherit = "sale.order.line"
	_columns = {
		'layout_remark': fields.text('Layout Remark'),
		'adv_issue': fields.many2one('sale.advertising.issue','Advertising Issue'),
		'page_reference': fields.char('Reference of the Page', size=32),
		'from_date': fields.datetime('Start of Validity'),
		'to_date': fields.datetime('End of Validity'),
	}
sale_order_line()

class product_product(osv.osv):
	_inherit = "product.product"
	_columns = {
		'equivalency_in_A4': fields.float('A4 Equivalency'),
	}
product_product()

class sale_advertising_proof(osv.osv):
	_name = "sale.advertising.proof"
	_description="Sale Advertising Proof"
	_columns = {
		'name': fields.char('Name', size=32),
		'address_id':fields.many2one('res.partner.address','Delivery Address'),
		'number': fields.integer('Number of Copies'),
		'target_id': fields.many2one('sale.order.line','Target'),
	}
sale_advertising_proof()

