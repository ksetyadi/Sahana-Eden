# -*- coding: utf-8 -*-

from gluon.tools import Service
service = Service(globals())

# Reusable timestamp fields
timestamp = db.Table(None, 'timestamp',
            Field('created_on', 'datetime',
                          readable=False,
                          writable=False,
                          default=request.utcnow),
            Field('modified_on', 'datetime',
                          readable=False,
                          writable=False,
                          default=request.utcnow,
                          update=request.utcnow)
            )

# Reusable author fields, TODO: make a better represent!
authorstamp = db.Table(None, 'authorstamp',
            Field('created_by', db.auth_user,
                          readable=False, # Enable when needed, not by default
                          writable=False,
                          default=session.auth.user.id if auth.is_logged_in() else 0,
                          represent = lambda id: (id and [db(db.auth_user.id==id).select()[0].first_name] or ["None"])[0],
                          ondelete='RESTRICT'),
            Field('modified_by', db.auth_user,
                          readable=False, # Enable when needed, not by default
                          writable=False,
                          default=session.auth.user.id if auth.is_logged_in() else 0,
                          update=session.auth.user.id if auth.is_logged_in() else 0,
                          represent = lambda id: (id and [db(db.auth_user.id==id).select()[0].first_name] or ["None"])[0],
                          ondelete='RESTRICT')
            )

# Reusable UUID field (needed as part of database synchronization)
import uuid
from gluon.sql import SQLCustomType
s3uuid = SQLCustomType(
                type ='string',
                native ='VARCHAR(64)',
                encoder = (lambda x: "'%s'" % (uuid.uuid4() if x=="" else str(x).replace("'","''"))),
                decoder = (lambda x: x)
            )

uuidstamp = db.Table(None, 'uuidstamp',
                     Field('uuid',
                          type=s3uuid,
                          length=64,
                          notnull=True,
                          unique=True,
                          readable=False,
                          writable=False,
                          default=""))

# Reusable Deletion status field (needed as part of database synchronization)
# Q: Will this be moved to a separate table? (Simpler for module writers but a performance penalty)
deletion_status = db.Table(None, 'deletion_status',
            Field('deleted', 'boolean',
                          readable=False,
                          writable=False,
                          default=False))

# Reusable Admin field
admin_id = db.Table(None, 'admin_id',
            Field('admin', db.auth_group,
                requires = IS_NULL_OR(IS_ONE_OF(db, 'auth_group.id', '%(role)s')),
                represent = lambda id: (id and [db(db.auth_group.id==id).select()[0].role] or ["None"])[0],
                comment = DIV(A(T('Add Role'), _class='thickbox', _href=URL(r=request, c='admin', f='group', args='create', vars=dict(format='popup', KeepThis='true'))+"&TB_iframe=true", _target='top', _title=T('Add Role')), A(SPAN("[Help]"), _class="tooltip", _title=T("Admin|The Group whose members can edit data in this record."))),
                ondelete='RESTRICT'
                ))

# Reusable Document field
document = db.Table(None, 'document',
            Field('document', 'upload', autodelete = True,
                label=T('Scanned File'),
                #comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Scanned File|The scanned copy of this document.")),
                ))

from gluon.storage import Storage
# Keep all S3 framework-level elements stored off here, so as to avoid polluting global namespace & to make it clear which part of the framework is being interacted with
# Avoid using this where a method parameter could be used: http://en.wikipedia.org/wiki/Anti_pattern#Programming_anti-patterns
s3 = Storage()

s3.crud_strings = Storage()
s3.crud_strings.title_create = T('Add Record')
s3.crud_strings.title_display = T('Record Details')
s3.crud_strings.title_list = T('List Records')
s3.crud_strings.title_update = T('Edit Record')
s3.crud_strings.title_search = T('Search Records')
s3.crud_strings.subtitle_create = T('Add New Record')
s3.crud_strings.subtitle_list = T('Available Records')
s3.crud_strings.label_list_button = T('List Records')
s3.crud_strings.label_create_button = T('Add Record')
s3.crud_strings.msg_record_created = T('Record added')
s3.crud_strings.msg_record_modified = T('Record updated')
s3.crud_strings.msg_record_deleted = T('Record deleted')
s3.crud_strings.msg_list_empty = T('No Records currently available')

s3.display = Storage()

module = 'admin'
resource = 'theme'
table = module + '_' + resource
db.define_table(table,
                Field('name'),
                Field('logo'),
                Field('footer'),
                Field('text_direction'),
                Field('col_background'),
                Field('col_txt'),
                Field('col_txt_background'),
                Field('col_txt_border'),
                Field('col_txt_underline'),
                Field('col_menu'),
                Field('col_highlight'),
                Field('col_input'),
                Field('col_border_btn_out'),
                Field('col_border_btn_in'),
                Field('col_btn_hover'),
                migrate=migrate)

module = 's3'
# Auditing
# ToDo: consider using native Web2Py log to auth_events
resource = 'audit'
table = module + '_' + resource
db.define_table(table,timestamp,
                Field('person', db.auth_user, ondelete='RESTRICT'),
                Field('operation'),
                Field('representation'),
                Field('module'),
                Field('resource'),
                Field('record', 'integer'),
                Field('old_value'),
                Field('new_value'),
                migrate=migrate)
db[table].operation.requires = IS_IN_SET(['create', 'read', 'update', 'delete', 'list', 'search'])

# Settings - systemwide
s3_setting_security_policy_opts = {
    1:T('simple'),
    2:T('full')
    }
resource = 'setting'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
                Field('admin_name'),
                Field('admin_email'),
                Field('admin_tel'),
                Field('theme', db.admin_theme),
                Field('debug', 'boolean', default=False),
                Field('self_registration', 'boolean', default=True),
                Field('security_policy', 'integer', default=1),
                Field('archive_not_delete', 'boolean', default=True),
                Field('audit_read', 'boolean', default=False),
                Field('audit_write', 'boolean', default=False),
                migrate=migrate)
db[table].security_policy.requires = IS_IN_SET(s3_setting_security_policy_opts)
db[table].security_policy.represent = lambda opt: opt and s3_setting_security_policy_opts[opt]
db[table].security_policy.label = T('Security Policy')
db[table].security_policy.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Security Policy|The simple policy allows anonymous users to Read & registered users to Edit. The full security policy allows the administrator to set permissions on individual tables or records - see models/zzz.py."))
db[table].theme.label = T('Theme')
db[table].theme.requires = IS_IN_DB(db, 'admin_theme.id', 'admin_theme.name')
db[table].theme.represent = lambda name: db(db.admin_theme.id==name).select()[0].name
db[table].theme.comment = DIV(A(T('Add Theme'), _class='thickbox', _href=URL(r=request, c='admin', f='theme', args='create', vars=dict(format='popup', KeepThis='true'))+"&TB_iframe=true", _target='top', _title=T('Add Theme'))),
db[table].debug.label = T('Debug')
db[table].debug.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Debug|Switch this on to use individual CSS/Javascript files for diagnostics during development."))
db[table].self_registration.label = T('Self Registration')
db[table].self_registration.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Self-registration|Can users register themselves for authenticated login access?"))
db[table].archive_not_delete.label = T('Archive not Delete')
db[table].archive_not_delete.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Archive not Delete|If this setting is enabled then all deleted records are just flagged as deleted instead of being really deleted. They will appear in the raw database access but won't be visible to normal users."))
db[table].audit_read.label = T('Audit Read')
db[table].audit_read.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Audit Read|If enabled then a log is maintained of all records a user accesses. If disabled then it can still be enabled on a per-module basis."))
db[table].audit_write.label = T('Audit Write')
db[table].audit_write.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Audit Write|If enabled then a log is maintained of all records a user edits. If disabled then it can still be enabled on a per-module basis."))
# Define CRUD strings (NB These apply to all Modules' 'settings' too)
title_create = T('Add Setting')
title_display = T('Setting Details')
title_list = T('List Settings')
title_update = T('Edit Setting')
title_search = T('Search Settings')
subtitle_create = T('Add New Setting')
subtitle_list = T('Settings')
label_list_button = T('List Settings')
label_create_button = T('Add Setting')
msg_record_created = T('Setting added')
msg_record_modified = T('Setting updated')
msg_record_deleted = T('Setting deleted')
msg_list_empty = T('No Settings currently defined')
s3.crud_strings[resource] = Storage(title_create=title_create, title_display=title_display, title_list=title_list, title_update=title_update, subtitle_create=subtitle_create, subtitle_list=subtitle_list, label_list_button=label_list_button, label_create_button=label_create_button, msg_record_created=msg_record_created, msg_record_modified=msg_record_modified, msg_record_deleted=msg_record_deleted, msg_list_empty=msg_list_empty)

# Settings - appadmin
module = 'appadmin'
resource = 'setting'
table = module + '_' + resource
db.define_table(table,
                Field('audit_read', 'boolean'),
                Field('audit_write', 'boolean'),
                migrate=migrate)