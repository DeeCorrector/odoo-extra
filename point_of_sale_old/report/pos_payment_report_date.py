# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import time
from report import report_sxw


class pos_payment_report_date(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(pos_payment_report_date, self).__init__(cr, uid, name, context)
        self.total = 0.0
        self.localcontext.update({
                'time': time,
                'pos_payment_date': self.__pos_payment_date__,
                'pos_payment_date_total':self.__pos_payment_date__total__,
                })

    def __pos_payment_date__(self,form):
        dt1 = form['date_start'] + ' 00:00:00'
        dt2 = form['date_end'] + ' 23:59:59'
        data={}
        self.cr.execute ("select pt.name,pol.qty,pol.discount,pol.price_unit, " \
                         "(pol.price_unit * pol.qty * (1 - (pol.discount) / 100.0)) as total  " \
                         "from pos_order as po,pos_order_line as pol,product_product as pp,product_template as pt " \
                         "where pt.id=pp.product_tmpl_id and pp.id=pol.product_id and po.id = pol.order_id  " \
                         "and po.state in ('paid','invoiced') and po.date_order  >= %s and po.date_order <= %s and po.user_id in %s " \
                         ,(dt1,dt2,tuple(form['user_id'][0][-1])))
        data=self.cr.dictfetchall()
        return data

    def __pos_payment_date__total__(self,form):
        dt1 = form['date_start'] + ' 00:00:00'
        dt2 = form['date_end'] + ' 23:59:59'
        res=[]
        self.cr.execute ("select sum(pol.price_unit * pol.qty * (1 - (pol.discount) / 100.0)) " \
                         "from pos_order as po,pos_order_line as pol,product_product as pp,product_template as pt " \
                         "where pt.id=pp.product_tmpl_id and pp.id=pol.product_id and po.id = pol.order_id " \
                         "and po.state in ('paid','invoiced') and po.date_order  >= %s and po.date_order <= %s and po.user_id in %s " \
                         ,(dt1,dt2,tuple(form['user_id'][0][-1])))
        res=self.cr.fetchone()[0]
        return res


report_sxw.report_sxw('report.pos.payment.report.date', 'pos.order', 'addons/point_of_sale/report/pos_payment_report_date.rml', parser=pos_payment_report_date)








