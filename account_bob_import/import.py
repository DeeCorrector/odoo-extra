#!/usr/bin/python
# -*- coding: utf8
import csv


#TODO:
##genere chart with parents :( => create a root with code = 0 then create the tree structure
##change it in order to run it server side
##remove close_method when mra's work is pushed

account_map = {
#   'id': lambda x: 'account_'+x['AID,A,10'], # will have to be uncomment for server side import
    'id': lambda z:'',
    'code': lambda x: x['AID,A,10'],
    'name': lambda x: x['HEADING1,A,40'],
    'note': lambda x: x['AMEMO,M,11'],
    'type': lambda x: {
        'LIABILIT': 'cash',
        'ASSETS': 'asset',
        'FXASSETS': 'asset',
        'INCOME': 'income',
        'DISCINC': 'income',
        'EXPENSE': 'expense',
        'DISCEXP': 'expense',
        '': 'view',
        'UNDEF': 'view',
    }[x['ABALANCE,A,10']],
    'sign': lambda x: 1,
#   'company_id': lambda x: "Tiny sprl", #will be replaced by id of main company
    'parent_id:id': lambda a: ''#'account_bob_import.account_bob_0'
    #'close_method': lambda x: 'balance', #will be removed
}


#this dict is used to know the header of each column
account_headers = {
    'id':'id',
    'code':'code', #'Code',
    'name':'name',# 'Name',
    'note': 'note',#'Note',
    'type': 'type',#'Account Type',
    'sign': 'sign', #'Sign',
#   'company_id': 'Company',
    'parent_id:id':'parent_id:id'
    #'close_method': 'Deferral Method',
    }

journals_map = {
    'code': lambda x: x['DBID,A,4'],
    'name': lambda x: x['HEADING1,A,30'],
    'view_id:id': lambda x: 'account.account_journal_view', # journal view for all except the ones that are of type cash => cash journal view
    'currency:id': lambda x: x['DBCURRENCY,A,3'],#to be check
    'sequence_id:id': lambda x: 'account.sequence_journal', #entry journal for all
    'type': lambda x: {
        'PUR': 'purchase',
        'PUC': 'purchase',
        'SAL': 'sale',
        'SAC': 'sale',
        'CAS': 'cash',
        'ISB': 'general',#default
        'PRI': 'general',#default
        'ISD': 'general',#default
        'ICO': 'general',#default
        'ISO': 'general',#default
        'PRO': 'general',#default
        'COP': 'general',#default
        'ISI': 'general',#default
        'ISM': 'general',#default
        'IDN': 'general',#default
        'ICE': 'general'#default
        #else should be of 'general' type

    }[x['DBTYPE,A,3']],
    'default_debit_account_id:id':lambda x: x['DBACCOUNT,A,10'], #should be filled with the id of the account_account with code = x['DBACCOUNT,A,10'],
    'default_credit_account_id:id':lambda x: x['DBACCOUNT,A,10'] ,#should be filled with the id of the account_account with code =
}

#this dict is used to know the header of each column
journals_headers = {
    'code': 'code',
    'name': 'name',
    'view_id:id': 'view_id:id', # journal view for all except the ones that are of type cash => cash journal view
    'currency:id': 'currency:id',
    'sequence_id:id': 'sequence_id:id', #entry journal for all
    'type': 'type',
    'default_debit_account_id:id':'default_debit_account_id:id', #should be filled with the id of the account_account with code = x['DBACCOUNT,A,10'],
    'default_credit_account_id:id': 'default_credit_account_id:id' ,#should be filled with the id of the account_account with code =['DBACCOUNT,A,10'],
    }

def convert2utf(row):
    if row:
        retRow = {}
        for k,v in row.items():
            retRow[k] = v.decode('latin1').encode('utf8').strip()
        return retRow
    return row
def convert(reader, writer, mapping, column_headers):
    record = {}
    for key, column_name in column_headers.items():
        record[key] = column_name
    writer.writerow(record)
    temp_dict = {}
    list_ids = []
    for row in reader:
        record = {}
        for key,fnct in mapping.items():
            record[key] = fnct(convert2utf(row))
        temp_dict[record['code']]=record
        list_ids.append(record['code'])
        record['id'] = 'id' + record['code']
        #if len(record['code'])>1:
            #l = len(record['code'])
            #aa = range(l+1)
            #aa.reverse()#[0,1,2,3,4,5]
            #aa.pop()
            #for i in aa:
                #if record['code'][0:i-1] in list_ids:
                    #record['parent_id:id'] = 'id' + str(record['code'][0:i-1])
                    #break
        #else:
            #record['parent_id:id'] = 'account_bob_import.account_bob_0'
        #writer.writerow(record)
    temp_keys = map(lambda x: int(x),temp_dict.keys())
    temp_keys.sort()
    temp_str_keys = map(lambda x: str(x),temp_keys)
    for t in temp_str_keys:
        if len(t)>1:
            l = len(temp_dict[t]['code'])
            aa = range(l+1)
            aa.reverse()
            aa.pop()
            for i in aa:
                if temp_dict[t]['code'][0:i-1] in list_ids:
                    temp_dict[t]['parent_id:id'] = 'id' + str(temp_dict[t]['code'][0:i-1])
                    break
        else:
            temp_dict[t]['parent_id:id'] = 'account_bob_import.account_bob_0'
        writer.writerow(temp_dict[t])
    return True

def import_journal(reader_journal, writer_journal, journals_map, journals_headers):
    record = {}
    for key, column_name in journals_headers.items():
        record[key] = column_name
    writer_journal.writerow(record)
    for row in reader_journal:
        record = {}
        for key,fnct in journals_map.items():
            record[key] = fnct(convert2utf(row))
        
        if record['default_debit_account_id:id']:
            record['default_debit_account_id:id'] = 'id' + str(record['default_debit_account_id:id'])
        if record['default_credit_account_id:id']:
            record['default_credit_account_id:id'] = 'id' + str(record['default_credit_account_id:id'])
        if record['type']=='cash':
            record['view_id:id']='account.account_journal_bank_view'
        writer_journal.writerow(record)
    return True

reader = csv.DictReader(file('accounts.csv','rb'))
writer = csv.DictWriter(file('account_bob/account.account.csv', 'wb'), account_map.keys())
reader_journal = csv.DictReader(file('journals.csv','rb'))
writer_journal = csv.DictWriter(file('account_bob/account.journal.csv', 'wb'), journals_map.keys())
convert(reader, writer, account_map, account_headers)
import_journal(reader_journal, writer_journal, journals_map, journals_headers)

move_map = {
    'id': lambda x: 'move_'+x['MID,A,40'],
    'account_id:id': lambda x: 'account_'+x['AID']
}

#TODO:
#   Minimal Account Chart & Properties: Demo Only
#   Create Objects:
#       account.account.template
#           idem a account.account + champ selection property
#       account.tax.template
#       account.journal.template
#   Wizard:
#       Prend un template -> genere un vrai plan
#           - Societe -
#           - Template -
#       Cree properties
#   Changer l10n_be et l10n_fr, l10n_ch

#~ Problemes:
    #~ Minimal Account Chart : Demo Only
    #~ Creer une nouvelle societe (nvx plan de compte)
        #~ -> dupliquer un plan de compte si meme pays
        #~ -> si pas meme pays: installer l10n_XXX


#~ if __name__=='__main__':
    #~ pass

