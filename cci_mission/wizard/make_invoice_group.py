import wizard
import netsvc
import pooler
import create_invoice_carnet
import create_invoice_embassy
import create_invoice

from osv import fields, osv

form = """<?xml version="1.0"?>
<form string="Inovoice Grouped">
    <separator string="Invoices Grouped for Following Partners." colspan="4" />
    <newline/>
    <field name="message" nolabel="1" colspan="5"/>
</form>
"""
fields = {
      'message': {'string':'', 'type':'text', 'readonly':True, 'size':'500'},
}

def _group_invoice(self, cr, uid, data, context):
    pool_obj=pooler.get_pool(cr.dbname)
    obj_inv=pool_obj.get('account.invoice')
    dict_info=[]
    models=['cci_missions.certificate','cci_missions.legalization','cci_missions.embassy_folder','cci_missions.ata_carnet']

    for model in models:
        model_ids=pool_obj.get(model).search(cr,uid,[('state','=','draft')])

        if model_ids:
            read_ids=pool_obj.get(model).read(cr,uid,model_ids,['partner_id','order_partner_id'])

            for element in read_ids:
                part_info={}

                if ('partner_id' in element) and element['partner_id']:
                    part_info['partner_id']=element['partner_id'][0]
                    part_info['id']=element['id']
                    part_info['model']=model
                if ('order_partner_id' in element) and element['order_partner_id']:
                    part_info['partner_id']=element['order_partner_id'][0]
                    part_info['id']=element['id']
                    part_info['model']=model

                if part_info:
                    dict_info.append(part_info)

    if not dict_info:
        data['form']['invoice_ids']=[]
        data['form']['message']="No invoices grouped  because no invoices for Embassy Folder, Legalizations, Certifications and ATA Carnet are in 'Draft' state."
        return data['form']

    partner_ids = list(set([x['partner_id'] for x in dict_info]))
    partner_ids.sort()
    disp_msg=''

    list_invoice=[]
    for partner_id in partner_ids:

        partner=pool_obj.get('res.partner').browse(cr, uid,partner_id)
        models=[]
        list_invoice_ids=[]

        for element in dict_info:

            if element['partner_id']==partner_id:
                data={'model':element['model'],'form':{},'id':element['id'],'ids':[element['id']],'report_type': 'pdf'}

                if element['model']=='cci_missions.ata_carnet':
                    result=create_invoice_carnet._createInvoices(self,cr,uid,data,context)

                    if result['inv_rejected']>0 and result['inv_rej_reason']:
                        disp_msg +='\nFor Partner '+ partner.name +' On ATA Carnet with ' + result['inv_rej_reason']
                    if result['invoice_ids']:
                        list_invoice_ids.append(result['invoice_ids'][0])

                if element['model']=='cci_missions.embassy_folder':
                    pool_obj.get(element['model']).write(cr, uid, [element['id']], {'state':'open',})
#                    pool_obj.get(element['model'])._history(cr, uid, [pool_obj.get(element['model']).browse(cr, uid,element['id'])], 'Got Back', history=True)
                    result=create_invoice_embassy._createInvoices(self,cr,uid,data,context)

                    if result['inv_rejected']>0 and result['inv_rej_reason']:
                        disp_msg +='\nFor Partner '+ partner.name +' On Embassy Folder with ' + result['inv_rej_reason']
                    if result['invoice_ids']:
                        list_invoice_ids.append(result['invoice_ids'][0])

                if element['model'] in ('cci_missions.certificate','cci_missions.legalization'):
                    result=create_invoice._createInvoices(self,cr,uid,data,context)

                    if result['inv_rejected']>0 and result['inv_rej_reason']:
                        disp_msg +='\nFor Partner '+ partner.name +' On Certificate or Legalization with ' + result['inv_rej_reason']
                    if result['invoice_ids']:
                        list_invoice_ids.append(result['invoice_ids'][0])

        count=0
        list_inv_lines=[]
        customer_ref = ''
        line_obj = pool_obj.get('account.invoice.line')
        id_note=line_obj.create(cr,uid,{'name':customer_ref,'state':'text','sequence':count})
        count=count+1
        list_inv_lines.append(id_note)
        data_inv=obj_inv.browse(cr,uid,list_invoice_ids)
        notes = ''
        for invoice in data_inv:

            if invoice.reference:
                customer_ref = customer_ref +' ' + invoice.reference
            if invoice.comment:
                notes = (notes + invoice.comment)

            for line in invoice.invoice_line:
                if invoice.name:
                    name = invoice.name +' '+ line.name
                else:
                    name = line.name
                #pool_obj.get('account.invoice.line').write(cr,uid,line.id,{'name':name,'sequence':count})
                inv_line = line_obj.create(cr, uid, {'name': name,'account_id':line.account_id.id,'price_unit': line.price_unit,'quantity': line.quantity,'discount': False,'uos_id': line.uos_id.id,'product_id':line.product_id.id,'invoice_line_tax_id': [(6,0,line.invoice_line_tax_id)],'note':False,'sequence' : count})
                count=count+1
                list_inv_lines.append(inv_line)
#            If we want to cancel ==> obj_inv.write(cr,uid,invoice.id,{'state':'cancel'}) here
#            If we want to delete ==> obj_inv.unlink(cr,uid,list_invoice_ids) after new invoice creation.


        line_obj.write(cr,uid,id_note,{'name':customer_ref})
        id_note1=line_obj.create(cr,uid,{'name':notes,'state':'text','sequence':count})# a new line of type 'note' with all the old invoice note
        count=count+1
        list_inv_lines.append(id_note1)
        id_linee=line_obj.create(cr,uid,{'state':'line','sequence':count}) #a new line of type 'line'
        count=count+1
        list_inv_lines.append(id_linee)
        id_stotal=line_obj.create(cr,uid,{'name':'Subtotal','state':'subtotal','sequence':count})#a new line of type 'subtotal'
        count=count+1
        list_inv_lines.append(id_stotal)
        inv = {
                'name': 'Grouped Invoice - ' + partner.name,
                'origin': 'Grouped Invoice',
                'type': 'out_invoice',
                'reference': False,
                'account_id': invoice.account_id.id,
                'partner_id': invoice.partner_id.id,
                'address_invoice_id':invoice.address_invoice_id.id,
                'address_contact_id':invoice.address_contact_id.id,
                'invoice_line': [(6,0,list_inv_lines)],
                'currency_id' :invoice.currency_id.id,# 1
                'comment': "",
                'payment_term':invoice.payment_term.id,
            }
        inv_id = obj_inv.create(cr, uid, inv)
        disp_msg +='\n'+ partner.name + ': '+ str(len(data_inv)) +' Invoice(s) Grouped.'
        list_invoice.append(inv_id)
        obj_inv.unlink(cr,uid,list_invoice_ids)
    data['form']['invoice_ids']=list_invoice
    data['form']['message']=disp_msg

    return data['form']

class mission_group_invoice(wizard.interface):
    def _list_invoice(self, cr, uid, data, context):
        pool_obj = pooler.get_pool(cr.dbname)
        model_data_ids = pool_obj.get('ir.model.data').search(cr,uid,[('model','=','ir.ui.view'),('name','=','invoice_form')])
        resource_id = pool_obj.get('ir.model.data').read(cr,uid,model_data_ids,fields=['res_id'])[0]['res_id']
        return {
            'domain': "[('id','in', ["+','.join(map(str,data['form']['invoice_ids']))+"])]",
            'name': 'Invoices',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.invoice',
            'views': [(False,'tree'),(resource_id,'form')],
            'context': "{'type':'out_invoice'}",
            'type': 'ir.actions.act_window'
        }
    states = {
        'init' : {
               'actions' : [_group_invoice],
               'result': {'type': 'form', 'arch': form, 'fields': fields, 'state':[('end','Ok'),('open','Open')]}
            },
        'open': {
            'actions': [],
            'result': {'type':'action', 'action':_list_invoice, 'state':'end'}
            }
    }
mission_group_invoice("cci_missions.make_invoice_common")