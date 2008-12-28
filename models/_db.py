# This scaffolding model makes your app work on Google App Engine too   #
#try:
#    from gluon.contrib.gql import *         # if running on Google App Engine
#except:
db=SQLDB('sqlite://storage.db')         # if not, use SQLite or other DB
#else:
#    db=GQLDB()                              # connect to Google BigTable
#    session.connect(request,response,db=db) # and store sessions there

# Define 'now'
# 'modified_on' fields used by T2 to do edit conflict-detection & by DBSync to check which is more recent
import datetime; now=datetime.datetime.today()

# We need UUIds for database synchronization
import uuid

# Use T2 plugin for AAA & CRUD
# At top of file rather than usual bottom as we refer to it within our tables
#from applications.sahana.modules.t2 import T2
#t2=T2(request,response,session,cache,T,db)

# Custom classes which extend default T2
from applications.sahana.modules.sahana import T2SAHANA
t2=T2SAHANA(request,response,session,cache,T,db)

# Custom validators
from applications.sahana.modules.validators import *

#
# Core Framework
#

# Modules
db.define_table('module',
                SQLField('name'),
                SQLField('name_nice'),
                SQLField('menu_priority','integer'),
                SQLField('description',length=256),
                SQLField('enabled','boolean',default='True'))
db.module.name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'module.name')]
db.module.name_nice.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'module.name_nice')]
db.module.menu_priority.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'module.menu_priority')]

# Home Menu Options
db.define_table('default_menu_option',
                SQLField('name'),
                SQLField('function'),
                SQLField('description',length=256),
                SQLField('priority','integer'),
                SQLField('enabled','boolean',default='True'))
db.default_menu_option.name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'default_menu_option.name')]
db.default_menu_option.function.requires=IS_NOT_EMPTY()
db.default_menu_option.priority.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'default_menu_option.priority')]

# Field options meta table
# Give a custom list of options for each field in this schema 
# prefixed with opt_. This is customizable then at deployment
# See the field_options.py for default customizations
# Modules: cr
# Actually for S3 we have a per-module table for 'config'
#db.define_table('field_option',
#                SQLField('field_name'),
#                SQLField('option_code',length=20),
#                SQLField('option_description',length=50))
#db.field_option.field_name.requires=IS_NOT_EMPTY()
#db.field_option.option_code.requires=IS_NOT_EMPTY()
#db.field_option.option_description.requires=IS_NOT_EMPTY()

# System Config
db.define_table('system_config',
				SQLField('setting'),
				SQLField('description',length=256),
				SQLField('value'))
# We want a THIS_NOT_IN_DB here: admin_name, admin_email, admin_tel
db.system_config.setting.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'system_config.setting')]
