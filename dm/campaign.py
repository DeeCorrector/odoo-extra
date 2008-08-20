# -*- encoding: utf-8 -*-
import time
import datetime
import offer

from osv import fields
from osv import osv


class dm_campaign_group(osv.osv):
    _name = "dm.campaign.group"
    _columns = {
        'name': fields.char('Campaign group name', size=64, required=True),
        'project_id' : fields.many2one('project.project', 'Project', readonly=True),
        'campaign_ids': fields.one2many('dm.campaign', 'campaign_group_id', 'Campaigns', domain=[('campaign_group_id','=',False)]),
    }
dm_campaign_group()


class dm_campaign_type(osv.osv):
    _name = "dm.campaign.type"

    _columns = {
        'name': fields.char('Description', size=64, required=True),
        'code': fields.char('Code', size=16, required=True),
    }
dm_campaign_type()

class dm_campaign(osv.osv):
    _name = "dm.campaign"
    _inherits = {'account.analytic.account': 'analytic_account_id'}
    _rec_name = 'name'

    def dtp_making_time_get(self, cr, uid, ids, name, arg, context={}):
        return name
    
    def _campaign_code(self, cr, uid, ids, name, args, context={}):
        result ={}
        for id in ids:
            camp = self.browse(cr,uid,[id])[0]
            offer_code = camp.offer_id and camp.offer_id.code or ''
            trademark_code = camp.trademark_id and camp.trademark_id.ref or ''
            dealer_code =camp.dealer_id and camp.dealer_id.ref or ''
            date_start = camp.date_start or ''
            country_code = camp.country_id.code or ''
            date = date_start.split('-')
            year = month = ''
            if len(date)==3:
                year = date[0][2:] 
                month = date[1]
            final_date=month+year
            code1='-'.join([offer_code ,dealer_code ,trademark_code ,final_date ,country_code])
            result[id]=code1
        return result

    def _get_campaign_type(self,cr,uid,context={}):
        campaign_type = self.pool.get('dm.campaign.type')
        type_ids = campaign_type.search(cr,uid,[])
        type = campaign_type.browse(cr,uid,type_ids)
        return map(lambda x : [x.code,x.name],type)

    _columns = {
        'code1' : fields.function(_campaign_code,string='Code',type="char",method=True,readonly=True),
        'offer_id' : fields.many2one('dm.offer', 'Offer',domain=[('state','=','open'),('type','in',['new','standart','rewrite'])]),
        'country_id' : fields.many2one('res.country', 'Country',required=True),
        'lang_id' : fields.many2one('res.lang', 'Language'),
        'trademark_id' : fields.many2one('dm.trademark', 'Trademark'),
        'project_id' : fields.many2one('project.project', 'Project', readonly=True),
        'campaign_group_id' : fields.many2one('dm.campaign.group', 'Campaign group'),
        'notes' : fields.text('Notes'),
        'campaign_stat_ids' : fields.one2many('dm.campaign.statistics','camp_id','Statistics'),
        'proposition_ids' : fields.one2many('dm.campaign.proposition', 'camp_id', 'Proposition'),
        'campaign_type' : fields.selection(_get_campaign_type,'Type',required=True),
        'analytic_account_id' : fields.many2one('account.analytic.account','Analytic Account', ondelete='cascade'),
        'planning_state' : fields.selection([('pending','Pending'),('inprogress','In Progress'),('done','Done')], 'Planning Status'),
        'manufacturing_state' : fields.selection([('pending','Pending'),('inprogress','In Progress'),('done','Done')], 'Manufacturing Status'),
        'dealer_id' : fields.many2one('res.partner', 'Dealer',domain=[('category_id','ilike','Dealer')]),
#
#                        desktop publication
#
        'theorical_dtp_request_date' :fields.date('Theorical Request Date'),
        'reviewed_dtp_request_date' :fields.date('Reviewed Request Date'),
        'real_dtp_request_date' :fields.date('Real Request Date'),
        'theorical_translation_delivery_date' :fields.date('Theorical Translation Delivery Date'),
        'reviewed_translation_delivery_date' :fields.date('Reviewed Translation Delivery Date'),
        'real_translation_delivery_date' :fields.date('Real Translation Date'), 
        'theorical_translation_rereading_date' : fields.date('Theorical Translation Rereading Date'),
        'reviewed_translation_rereading_date' :fields.date('Reviewed Translation Rereading Date'),
        'real_translation_rereading_date' :fields.date('Real Translation Rereading Date'),
        'theorical_draft_delivery_date' :fields.date('Theorical Draft Delivery Date'),
        'reviewed_draft_delivery_date' : fields.date('Reviewed Draft Delivery Date'),
        'real_draft_delivery_date' : fields.date('Real Draft Delivery Date'),
        'theorical_fcp_validation_date' : fields.date('Theorical Fcp Validation Date'),
        'reviewed_fcp_validation_date' : fields.date('Reviewed Fcp Validation Date'),
        'real_fcp_validation_date' : fields.date('Real Fcp Validation Date'),
        'theorical_dtp_sup_delivery_date' : fields.date('Theorical Dtp Sup Delivery Date'),
        'reviewed_dtp_sup_delivery_date' : fields.date('Reviewed Dtp Sup Delivery Date'),
        'real_dtp_sup_delivery_date' : fields.date('Real Dtp Sup Delivery Date'),
        'responsible_id' : fields.many2one('res.users','Responsible'),
        'dtp_making_time' : fields.function(dtp_making_time_get, method=True, type='float', string='Making Time'),
        'deduplicator_id' : fields.many2one('res.partner','Deduplicator',domain=[('category_id','ilike','Deduplicator')]),
        'dedup_order_date' : fields.date('Order Date'),
        'dedup_validity_date' : fields.date('Validity Date'),
        'dedup_delivery_date' : fields.date('Delivery Date'),
        'currency_id' : fields.many2one('res.currency','Currency',ondelete='cascade'),      
    }

    _defaults = {
        'state': lambda *a: 'draft',
        'planning_state': lambda *a: 'pending',
        'manufacturing_state': lambda *a: 'pending',
        'campaign_type': lambda *a: 'general',
        'responsible_id' : lambda obj, cr, uid, context: uid,
    }

    def onchange_offer(self, cr, uid, ids, offer_id,country_id):
        if not country_id:
            raise osv.except_osv("Error!!","Country can't be empty ,First select Country")
        value = {}
        country = self.pool.get('res.country').browse(cr,uid,[country_id])[0]
        value['lang_id'] =  country.main_language.id
        value['currency_id'] = country.main_currency.id
        if not offer_id:
            res = {'trademark_id':0}
            return {'value':value}
        else:
            id = self.pool.get('dm.offer').read(cr, uid, [offer_id])
            if id:
                value = {'trademark_id':id[0]['recommended_trademark']}
            return {'value':value}
                    
        forbidden_state_ids = map(lambda x:x.country_id.id ,res.forbidden_state_ids)
        forbidden_country_ids = map(lambda x:x.id ,res.forbidden_country_ids)
        forbidden_country_ids.extend(forbidden_state_ids)
        if country_id in forbidden_country_ids:
            raise osv.except_osv("Error!!","You cannot use this offer in this country")
        value['name']=res.name
        return {'value':value}

    def state_draft_set(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {'state':'draft'})
        return True  

    def state_close_set(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {'state':'close'})
        return True  

    def state_pending_set(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {'state':'pending'})
        return True

    def state_open_set(self, cr, uid, ids, *args):
        camp = self.browse(cr,uid,ids)[0]
        forbidden_state_ids = [state_id.country_id.id for state_id in camp.offer_id.forbidden_state_ids]
        forbidden_country_ids = [country_id.id for country_id in camp.offer_id.forbidden_country_ids]
        forbidden_country_ids.extend(forbidden_state_ids)
        if camp.offer_id.forbidden_country_ids and camp.country_id.id  in  forbidden_country_ids :
            raise osv.except_osv("Error!!","This offer is not valid in this country")
        if not camp.date_start or not camp.dealer_id or not camp.trademark_id :
            raise osv.except_osv("Error!!","Informations are missing.Check Date Start, Dealer and Trademark")
        self.write(cr, uid, ids, {'state':'open'})
        return True
    
    def create(self,cr,uid,vals,context={}):
        if context.has_key('campaign_type') and context['campaign_type']=='model':
            vals['campaign_type']='model'
        id_camp = super(dm_campaign,self).create(cr,uid,vals,context)
        data_cam = self.browse(cr, uid, id_camp)
        if (data_cam.date_start) and (not data_cam.date):
            time_format = "%Y-%m-%d"
            d = time.strptime(data_cam.date_start,time_format)
            d = datetime.date(d[0], d[1], d[2])
            date_end = d + datetime.timedelta(days=365)
            self.write(cr, uid, id_camp, {'date':date_end})
        return id_camp

    def fields_view_get(self, cr, user, view_id=None, view_type='form', context=None, toolbar=False):
        result = super(dm_campaign,self).fields_view_get(cr, user, view_id, view_type, context, toolbar)
        if context.has_key('campaign_type'):
            if context['campaign_type'] == 'model' :
                if result.has_key('toolbar'):
                    result['toolbar']['action'] =[]
        return result

    def copy_campaign(self,cr, uid, ids, *args):
        camp = self.browse(cr,uid,ids)[0]
        default={}
        default['name']='New campaign from model %s' % camp.name
        default['campaign_type'] = 'recruiting'
        default['responsible_id'] = uid
        self.copy(cr,uid,ids[0],default)
        return True
        
dm_campaign()

#Postgres view
class dm_campaign_statistics(osv.osv):
    _name = "dm.campaign.statistics"
    _columns = {
        'kind' : fields.char('Kind', size=16),
        'qty' : fields.integer('Quantity'),
        'rate' : fields.float('Rate', digits=(16,2)),
        'camp_id' : fields.many2one('dm.campaign', 'Campaign')
    }
dm_campaign_statistics()


#class dm_campaign_pricelist(osv.osv):
#    _name = "dm.campaign.pricelist"
#    _description = "Pricelist"
#    _columns = {
#        'name': fields.char('Name',size=64, required=True),
#        'active': fields.boolean('Active'),
#        'type': fields.selection([('customer','Customer'),('requirer','Requirer')], 'Pricelist Type', required=True),
#        'currency_id': fields.many2one('res.currency', 'Currency', required=True),
#    }
#
#    _defaults = {
#        'active': lambda *a: 1,
#    }
#dm_campaign_pricelist()

class dm_campaign_proposition(osv.osv):
    _name = "dm.campaign.proposition"
    _inherits = {'account.analytic.account': 'analytic_account_id'}
    
    def onchange_date(self, cr, uid, ids, camp_id):
        res = {} 
        if camp_id:
            id = self.pool.get('dm.campaign').read(cr, uid, [camp_id])
            if id:
                res = {'date_start':id[0]['date_start']}
            
        else:
           res = {'date_start':0}   
        return {'value': res}
    
    def create(self, cr, user, vals, context=None):
        
       if 'keep_segments' in  vals  and vals['keep_segments'] == False :
            vals['segment_ids'] = []
       return super(dm_campaign_proposition,self).create(cr, user, vals, context=None)
       

    def _proposition_code(self, cr, uid, ids, name, args, context={}):
        result ={}
        for id in ids:

            pro = self.browse(cr,uid,[id])[0]
            offer_code = pro.camp_id.offer_id and pro.camp_id.offer_id.code or ''
            trademark_code = pro.camp_id.trademark_id and pro.camp_id.trademark_id.name or ''
            dealer_code =pro.camp_id.dealer_id and pro.camp_id.dealer_id.ref or ''
            date_start = pro.date_start or ''
            date = date_start.split('-')
            year = month = ''
            if len(date)==3:
                year = date[0][2:] 
                month = date[1]
            country_code = pro.camp_id.country_id.code or '' 
            seq = '%%0%sd' % 2 % id
            final_date = month+year
            code1='-'.join([offer_code, dealer_code ,trademark_code ,final_date ,country_code ,seq])
            result[id]=code1
        return result

    _columns = {
        'code1' : fields.function(_proposition_code,string='Code',type="char",method=True,readonly=True),
        'camp_id' : fields.many2one('dm.campaign','Campaign',ondelete = 'cascade',required=True),
        'delay_ids' : fields.one2many('dm.campaign.delay', 'proposition_id', 'Delays', ondelete='cascade'),
        'sale_rate' : fields.float('Sale Rate', digits=(16,2)),
        'proposition_type' : fields.selection([('init','Initial'),('relaunching','Relauching'),('split','Split')],"Type"),
        'initial_proposition_id': fields.many2one('dm.campaign.proposition', 'Initial proposition'),
        'segment_ids' : fields.one2many('dm.campaign.proposition.segment','proposition_id','Segment', ondelete='cascade'),
        'starting_mail_price' : fields.float('Starting Mail Price',digits=(16,2)),
        'customer_pricelist_id':fields.many2one('product.pricelist','Items Pricelist', required=False),
        'forwarding_charges' : fields.float('Forwarding Charges', digits=(16,2)),
        'notes':fields.text('Notes'),
        'analytic_account_id' : fields.many2one('account.analytic.account','Analytic Account', ondelete='cascade'),
        'product_ids' : fields.one2many('dm.product', 'proposition_id', 'Catalogue'),
#        'product_ids' : fields.many2many('dm.product', 'proposition_product_rel', 'proposition_id', 'product_id', 'Catalogue'),
        'payment_methods' : fields.many2many('account.journal','campaign_payment_method_rel','proposition_id','journal_id','Payment Methods',domain=[('type','=','cash')]),
        'keep_segments' : fields.boolean('Keep Segments'),
#        'prices_prog_id' : fields.many2one('dm.campaign.proposition.prices_progression', 'Prices Progression'),
    }

    _defaults = {
        'proposition_type' : lambda *a : 'init',
    }

    def _check(self, cr, uid, ids=False, context={}):
        '''
        Function called by the scheduler to create workitem from the segments of propositions.
        '''
        ids = self.search(cr,uid,[('date_start','=',time.strftime('%Y-%m-%d %H:%M:%S'))])
        for id in ids:
            res = self.browse(cr,uid,[id])[0]
            offer_step_id = self.pool.get('dm.offer.step').search(cr,uid,[('offer_id','=',res.camp_id.offer_id.id),('flow_start','=',True)])
            if offer_step_id :
                for segment in res.segment_ids:
                    vals = {'step_id':offer_step_id[0],'segment_id':segment.id}
                    new_id = self.pool.get('dm.offer.step.workitem').create(cr,uid,vals)
        return True

dm_campaign_proposition()

class dm_campaign_proposition_segment(osv.osv):

    _name = "dm.campaign.proposition.segment"
    _inherits = {'account.analytic.account': 'analytic_account_id'}
    _description = "Segment"

    def _check_char(self, cr, uid, ids):
        segment = self.browse(cr,uid,ids)[0]
        if not segment.quantity_add:
            return True
        return segment.quantity_add.isdigit() or segment.quantity_add=='AAA'
    _columns = {
#        'action_code': fields.char('Code',size=16, required=True),
        'proposition_id' : fields.many2one('dm.campaign.proposition','Proposition', required=True, ondelete='cascade'),
        'file_id': fields.many2one('dm.customer.file','Files'),
        'qty': fields.integer('Qty'),
        'quantity_add' : fields.char('Quantity',size=16),
        'split_id' : fields.many2one('dm.campaign.proposition.segment','Split'),
        'start_census' :fields.integer('Start Census'),
        'end_census' : fields.integer('End Census'),
        'deduplication_level' : fields.integer('Deduplication Level'),
        'active' : fields.boolean('Active'),
        'raw_quantity' : fields.integer('Raw Quantity'),
        'reuse_id' : fields.many2one('dm.campaign.proposition.segment','Reuse'),
        'analytic_account_id' : fields.many2one('account.analytic.account','Analytic Account', ondelete='cascade'),
        'note' : fields.text('Notes'),
#        'sequence' : fields.integer('Sequence'),
    }
    _order = 'deduplication_level'

    _constraints = [
        (_check_char, "Error ! Quantity of segment can only be integer or 'AAA'", ['quantity_add'])
    ]

dm_campaign_proposition_segment()

class dm_campaign_delay(osv.osv):
    _name = "dm.campaign.delay"
    _columns = {
        'name' : fields.char('Name', size=64, required=True),
        'value' : fields.integer('Value'),
        'proposition_id' : fields.many2one('dm.campaign.proposition', 'Proposition')
    }

dm_campaign_delay()

class Country(osv.osv):
    _name = 'res.country'
    _inherit = 'res.country'
    _columns = {
                'main_language' : fields.many2one('res.lang','Main Language',ondelete='cascade',),
                'main_currency' : fields.many2one('res.currency','Main Currency',ondelete='cascade'),
    }
Country()

class dm_campaign_proposition_prices_progression(osv.osv):
    _name = 'dm.campaign.proposition.prices_progression'
    _columns = {
        'name' : fields.char('Name', size=64, required=True),
        'fixed_prog' : fields.float('Fixed Prices Progression', digits=(16,2)),
        'percent_prog' : fields.float('Percentage Prices Progression', digits=(16,2)),
    }
dm_campaign_proposition_prices_progression()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


