from osv import fields, osv
from osv import orm
import os

class res_partner(osv.osv):
    _inherit = 'res.partner'

    def create(self, cr, uid, vals, *args, **kwargs):
        list_lang = []
        ids_lang = self.pool.get('res.lang').search(cr, uid, [])
        lang = self.pool.get('res.lang').browse(cr, uid, ids_lang)
        for l in lang:
            list_lang.append(l.code)
        d= {}
        if 'lang' in vals and not vals['lang'] in list_lang:
            d['lang']=''
            vals.update(d)
        return super(res_partner,self).create(cr, uid, vals, *args, **kwargs)

res_partner()


class config_bob_import(osv.osv_memory):
    _name = 'config.bob.import'
    _columns = {
        'company_id':fields.many2one('res.company','Company', required=True),
        'path':fields.char('Path for BOB Folder',required=True,size=200),
    }

    def action_create(self, cr, uid,ids, context=None):
        ids=self.search(cr, uid, [])
        path=self.read(cr, uid, [ids[len(ids)-1]], ['path'], context)
        path_bob=path[-1]['path']

        if not os.path.exists(path_bob):
            raise osv.except_osv(_('User Error'), _('The Path "%s" doesn''t exist.Please provide a valid one.') % path[-1]['path'] )

        if 'bob.exe' not in os.listdir(path_bob):
            raise osv.except_osv(_('User Error'), _('The Path "%s" is not a valid BOB Folder.It doesn''t have bob.exe.') % path[-1]['path'] )

        return {
            'view_type': 'form',
            "view_mode": 'form',
            'res_model': 'config.path.folder',
            'type': 'ir.actions.act_window',
            'target':'new',
        }
config_bob_import()

def _folders_get(self, cr, uid, context={}):
    acc_type_obj = self.pool.get('config.bob.import')
    ids = acc_type_obj.search(cr, uid, [])
    path=[]
    res=[(0,'')]
    seq=0
    if ids:
        path=acc_type_obj.read(cr, uid, [ids[len(ids)-1]], ['path'], context)
        list_folders=os.listdir(path[-1]['path'])

        # under developmnt
        if path[-1]['path']=='temp':
            res=[{'name':'jay','j':'vora'},{'name':'Non-jay','j':'non-Vora'}]
            res=[(r['j'], r['name']) for r in res]
        else:
            res=[(0,'')]

    return res
#    return [(r['j'], r['name']) for r in res]

class config_path_folder(osv.osv_memory):
    _name="config.path.folder"
    _columns ={
        'folder': fields.selection(_folders_get,'Folder'),
    }

    def action_back(self,cr,uid,ids,conect=None):
        return {
                'view_type': 'form',
                "view_mode": 'form',
                'res_model': 'config.bob.import',
                'type': 'ir.actions.act_window',
                'target':'new',
        }

config_path_folder()

