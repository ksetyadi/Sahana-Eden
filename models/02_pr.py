# -*- coding: utf-8 -*-

#
# Sahanapy VITA - Part 02_pr: Person Tracking and Tracing
#
# created 2009-07-15 by nursix
#
# This part defines:
#       - PersonEntity (pentity)    - a person entity
#       - Person (person)           - an individual person
#       - Group (group)             - a group of persons
#       - Network (network)         - a social network layer of a person

module = 'pr'

# *****************************************************************************
# Settings
#
resource = 'setting'
table = module + '_' + resource
db.define_table(table,
                Field('audit_read', 'boolean'),
                Field('audit_write', 'boolean'),
                migrate=migrate)
# Populate table with Default options
# - deployments can change these live via appadmin
if not len(db().select(db[table].ALL)): 
   db[table].insert(
        # If Disabled at the Global Level then can still Enable just for this Module here
        audit_read = False,
        audit_write = False
    )

# *****************************************************************************
# PersonEntity (pentity)
#

#
# PersonEntity classes --------------------------------------------------------
#
pr_pentity_class_opts = {
    1:T('Person'),                  # used in VITA - don't change
    2:T('Group'),                   # used in VITA - don't change
    3:T('Body'),
    4:T('Object')
    }

opt_pr_pentity_class = SQLTable(None, 'opt_pr_pentity_class',
                    db.Field('opt_pr_pentity_class','integer',
                    requires = IS_IN_SET(pr_pentity_class_opts),
                    default = 1,
                    label = T('Entity Class'),
                    represent = lambda opt: opt and pr_pentity_class_opts[opt]))

#
# shn_pentity_represent -------------------------------------------------------
#
def shn_pentity_represent(pentity):
    """
        Represent a Person Entity in option fields or list views
    """

    default = "None"

    try:
        if not pentity: return default

        if isinstance(pentity,dict):
            if 'pr_pe_id' in pentity:
                pentity_id = pentity.pr_pe_id
                pe_record = db((db.pr_pentity.id==pentity_id) & (db.pr_pentity.deleted==False)).select()[0]
            else:
                pentity_id = pentity.id
                pe_record = pentity
        else:
            pentity_id = pentity
            pe_record = db((db.pr_pentity.id==pentity_id) & (db.pr_pentity.deleted==False)).select()[0]

        if pe_record and pe_record.opt_pr_pentity_class==1:
            subentity_record=db(db.pr_person.pr_pe_id==pe_record.id).select()[0]
            if subentity_record:
                pentity_str = '%s %s [%s] (%s %s)' % (
                    subentity_record.first_name,
                    subentity_record.last_name or '',
                    subentity_record.pr_pe_label or 'no label',
                    pr_pentity_class_opts[1],
                    subentity_record.id
                )
            else:
                pentity_str = '[%s] (%s PE=%s)' % (
                    pe_record.label or 'no label',
                    pr_pentity_class_opts[1],
                    pe_record.id
                )

        elif pe_record and pe_record.opt_pr_pentity_class==2:
            subentity_record=db(db.pr_group.pr_pe_id==pe_record.id).select()[0]
            if subentity_record:
                pentity_str = '%s (%s %s)' % (
                    subentity_record.group_name,
                    pr_pentity_class_opts[2],
                    subentity_record.id
                )
            else:
                pentity_str = '(%s PE=%s)' % (
                    pr_pentity_class_opts[2],
                    pe_record.id
                )

        elif pe_record and pe_record.opt_pr_pentity_class==3:
            subentity_record=db(db.hrm_body.pr_pe_id==pe_record.id).select()[0]
            if subentity_record:
                pentity_str = '[%s] (%s %s)' % (
                    subentity_record.pr_pe_label or 'no label',
                    pr_pentity_class_opts[3],
                    subentity_record.id
                )
            else:
                pentity_str = '[%s] (%s PE=%s)' % (
                    pe_record.label or 'no label',
                    pr_pentity_class_opts[3],
                    pe_record.id
                )
        elif pe_record:
            pentity_str = '[%s] (%s PE=%s)' % (
                pe_record.label or 'no label',
                pr_pentity_class_opts[pe_record.opt_pr_pentity_class],
                pe_record.id
            )

        else: return default

        return pentity_str

    except:
        # No such record
        return default

#
# pentity table ---------------------------------------------------------------
#
resource = 'pentity'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                Field('parent'),                    # Parent Entity
                opt_pr_pentity_class,               # Entity class
                Field('label', unique=True),        # Recognition Label
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].label.requires = IS_NULL_OR(IS_NOT_IN_DB(db, 'pr_pentity.label'))
db[table].parent.requires = IS_NULL_OR(IS_ONE_OF(db, 'pr_pentity.id', shn_pentity_represent))
db[table].parent.label = T('belongs to')
db[table].deleted.readable = True

#
# Reusable field for other tables to reference --------------------------------
#
pr_pe_id = SQLTable(None, 'pe_id',
                Field('pr_pe_id', db.pr_pentity,
                requires =  IS_NULL_OR(IS_ONE_OF(db, 'pr_pentity.id', shn_pentity_represent)),
                represent = lambda id: (id and [shn_pentity_represent(id)] or ["None"])[0],
                ondelete = 'RESTRICT',
                label = T('ID')
                ))

#
# Person Entity Field Set -----------------------------------------------------
#
pr_pe_fieldset = SQLTable(None, 'pe_fieldset',
                    Field('pr_pe_id', db.pr_pentity,
                    requires = IS_NULL_OR(IS_ONE_OF(db, 'pr_pentity.id', shn_pentity_represent)),
                    represent = lambda id: (id and [shn_pentity_represent(id)] or ["None"])[0],
                    ondelete = 'RESTRICT',
                    readable = False,   # should be invisible in (most) forms
                    writable = False    # should be invisible in (most) forms
                    ),
                    Field('pr_pe_parent', db.pr_pentity,
                    requires =  IS_NULL_OR(IS_ONE_OF(db, 'pr_pentity.id', shn_pentity_represent)),
                    represent = lambda id: (id and [shn_pentity_represent(id)] or ["None"])[0],
                    ondelete = 'RESTRICT',
                    label = T('belongs to'),
                    readable = False,   # should be invisible in (most) forms
                    writable = False    # should be invisible in (most) forms
                    ),
                    Field('pr_pe_label',
                    label = T('ID Label'),
                    requires = IS_NULL_OR(IS_NOT_IN_DB(db, 'pr_pentity.label'))
                    ))

# *****************************************************************************
# Person (person)
#

#
# Gender ----------------------------------------------------------------------
#
pr_person_gender_opts = {
    1:T('unknown'),
    2:T('female'),
    3:T('male')
    }

opt_pr_gender = SQLTable(None, 'opt_pr_gender',
                    db.Field('opt_pr_gender','integer',
                    requires = IS_IN_SET(pr_person_gender_opts),
                    default = 1,
                    label = T('Gender'),
                    represent = lambda opt: opt and pr_person_gender_opts[opt]))

#
# Age Group -------------------------------------------------------------------
#
pr_person_age_group_opts = {
    1:T('unknown'),
    2:T('Infant (0-1)'),
    3:T('Child (2-11)'),
    4:T('Adolescent (12-20)'),
    5:T('Adult (21-50)'),
    6:T('Senior (50+)')
    }

opt_pr_age_group = SQLTable(None, 'opt_pr_age_group',
                    db.Field('opt_pr_age_group','integer',
                    requires = IS_IN_SET(pr_person_age_group_opts),
                    default = 1,
                    label = T('Age Group'),
                    represent = lambda opt: opt and pr_person_age_group_opts[opt]))

#
# Marital Status --------------------------------------------------------------
#
pr_marital_status_opts = {
    1:T('unknown'),
    2:T('single'),
    3:T('married'),
    4:T('separated'),
    5:T('divorced'),
    6:T('widowed'),
    99:T('other')
}

opt_pr_marital_status = SQLTable(None, 'opt_pr_marital_status',
                        db.Field('opt_pr_marital_status','integer',
                        requires = IS_IN_SET(pr_marital_status_opts),
                        default = 1,
                        label = T('Marital Status'),
                        represent = lambda opt: opt and pr_marital_status_opts[opt]))

#
# Religion --------------------------------------------------------------------
#
pr_religion_opts = {
    1:T('none'),
    2:T('Christian'),
    3:T('Muslim'),
    4:T('Jew'),
    5:T('Bhuddist'),
    6:T('Hindu'),
    99:T('other')
    }

opt_pr_religion = SQLTable(None, 'opt_pr_religion',
                    db.Field('opt_pr_religion','integer',
                    requires = IS_IN_SET(pr_religion_opts),
                    default = 1,
                    label = T('Religion'),
                    represent = lambda opt: opt and pr_religion_opts[opt]))

#
# Nationality and Country of Residence ----------------------------------------
#
pr_nationality_opts = shn_list_of_nations

opt_pr_nationality = SQLTable(None, 'opt_pr_nationality',
                        db.Field('opt_pr_nationality','integer',
                        requires = IS_IN_SET(pr_nationality_opts),
                        default = 999, # unknown
                        label = T('Nationality'),
                        represent = lambda opt: opt and pr_nationality_opts[opt]))

opt_pr_country = SQLTable(None, 'opt_pr_country',
                        db.Field('opt_pr_country','integer',
                        requires = IS_IN_SET(pr_nationality_opts),
                        default = 999, # unknown
                        label = T('Country of Residence'),
                        represent = lambda opt: opt and pr_nationality_opts[opt]))

#
# person table ----------------------------------------------------------------
#
resource = 'person'
table = module + '_' + resource
db.define_table(table, timestamp, deletion_status,
                pr_pe_fieldset,                         # Person Entity Field Set
#                Field('name_unknown', 'boolean', default=False),
                Field('first_name', notnull=True),      # first or only name
                Field('middle_name'),                   # middle name
                Field('last_name'),                     # last name
                Field('preferred_name'),                # how the person uses to be called
                Field('local_name'),                    # name in local language and script, Sahana legacy
                opt_pr_gender,
                opt_pr_age_group,
                Field('email', unique=True),            # Needed for AAA (change this!)
                Field('mobile_phone','integer'),        # Needed for SMS (change this!)
                # Person Details
                Field('date_of_birth','date'),          # Sahana legacy
                opt_pr_nationality,                     # Nationality
                opt_pr_country,                         # Country of residence
#                Field('town'),                          # Town of Origin, Sahana legacy
#                Field('race'),                          # Sahana legacy
#                Field('ethnicity'),                     # by nursix - TODO: add option field
                opt_pr_religion,                        # Sahana legacy
                opt_pr_marital_status,                  # Sahana legacy
                Field('occupation'),                    # Sahana legacy
                Field('comment'),                       # comment
                migrate=migrate)

db[table].pr_pe_label.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("ID Label|Number or Label on the identification tag this person is wearing (if any)."))
#db[table].name_unknown.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Name unknown|Please tag here if the name of the person is unknown (e.g. due to unconsciousness), and repeat the ID label or enter a placeholder (e.g. [unknown]) into the first name field."))

db[table].opt_pr_gender.label = T('Gender')
db[table].opt_pr_age_group.label = T('Age group')

db[table].date_of_birth.requires = IS_NULL_OR(IS_DATE())

db[table].first_name.requires = IS_NOT_EMPTY()   # People don't have to have unique names, some just have a single name
db[table].first_name.comment = SPAN(SPAN("*", _class="req"),A(SPAN("[Help]"), _class="tooltip", _title=T("First name|The first or only name of the person (mandatory).")))

db[table].preferred_name.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Preferred Name|The name to be used when calling for or directly addressing the person (optional)."))
db[table].local_name.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Local Name|Name of the person in local language and script (optional)."))

db[table].email.requires = IS_NOT_IN_DB(db, '%s.email' % table)     # Needs to be unique as used for AAA
db[table].email.requires = IS_NULL_OR(IS_EMAIL())
db[table].email.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Email|This gets used both for signing-in to the system & for receiving alerts/updates."))
db[table].mobile_phone.requires = IS_NULL_OR(IS_NOT_IN_DB(db, '%s.mobile_phone' % table))   # Needs to be unique as used for AAA
db[table].mobile_phone.label = T("Mobile Phone #")
db[table].mobile_phone.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Mobile Phone No|This gets used both for signing-in to the system & for receiving alerts/updates."))

db[table].opt_pr_nationality.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Nationality|Nationality of the person."))
db[table].opt_pr_country.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Country of Residence|The country the person usually lives in."))

title_create = T('Add Person')
title_display = T('Person Details')
title_list = T('List Persons')
title_update = T('Edit Person')
title_search = T('Search Persons')
subtitle_create = T('Add New Person')
subtitle_list = T('Persons')
label_list_button = T('List Persons')
label_create_button = T('Add Person')
msg_record_created = T('Person added')
msg_record_modified = T('Person updated')
msg_record_deleted = T('Person deleted')
msg_list_empty = T('No Persons currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

#
# person_id: reusable field for other tables to reference ---------------------
#
person_id = SQLTable(None, 'person_id',
                Field('person_id', db.pr_person,
                requires = IS_NULL_OR(IS_IN_DB(db, 'pr_person.id', '%(id)s: %(first_name)s %(last_name)s')),
                represent = lambda id: (id and [db(db.pr_person.id==id).select()[0].first_name] or ["None"])[0],
                comment = DIV(A(T('Add Person'), _class='popup', _href=URL(r=request, c='pr', f='person', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Create Person Entry|Create a person entry in the registry."))),
                ondelete = 'RESTRICT'
                ))

# *****************************************************************************
# Group (group)
#

#
# Group types -----------------------------------------------------------------
#
pr_group_type_opts = {
    1:T('Family'),
    2:T('Tourist Group'),
    3:T('Relief Team'),
    4:T('other')
    }

opt_pr_group_type = SQLTable(None, 'opt_pr_group_type',
                    db.Field('opt_pr_group_type','integer',
                    requires = IS_IN_SET(pr_group_type_opts),
                    default = 4,
                    label = T('Group Type'),
                    represent = lambda opt: opt and pr_group_type_opts[opt]))

#
# group table -----------------------------------------------------------------
#
resource = 'group'
table = module + '_' + resource
db.define_table(table, timestamp, deletion_status,
                pr_pe_fieldset,                                 # Person Entity Field Set
                opt_pr_group_type,                              # group type
                Field('system','boolean',default=False),        # System internal? (e.g. users?)
                Field('group_name'),                            # Group name (optional? => No!)
                Field('group_description'),                     # Group short description
#                Field('group_head'),                           # Sahana legacy
#                Field('no_of_adult_males','integer'),           # Sahana legacy
#                Field('no_of_adult_females','integer'),         # Sahana legacy
#                Field('no_of_children', 'integer'),            # Sahana legacy
#                Field('no_of_children_males','integer'),        # by Khushbu
#                Field('no_of_children_females','integer'),      # by Khushbu
#                Field('no_of_displaced', 'integer'),           # Sahana legacy
#                Field('no_of_missing', 'integer'),             # Sahana legacy
#                Field('no_of_dead', 'integer'),                # Sahana legacy
#                Field('no_of_rehabilitated', 'integer'),       # Sahana legacy
#                Field('checklist', 'text'),                    # Sahana legacy
#                Field('description', 'text'),                  # Sahana legacy
                Field('comment'),                               # optional comment
                migrate=migrate)

db[table].pr_pe_label.readable=False
db[table].pr_pe_label.writable=False

db[table].opt_pr_group_type.label = T("Group type")

db[table].group_name.label = T("Group name")
db[table].group_description.label = T("Group description")
title_create = T('Add Group')
title_display = T('Group Details')
title_list = T('List Groups')
title_update = T('Edit Group')
title_search = T('Search Groups')
subtitle_create = T('Add New Group')
subtitle_list = T('Groups')
label_list_button = T('List Groups')
label_create_button = T('Add Group')
msg_record_created = T('Group added')
msg_record_modified = T('Group updated')
msg_record_deleted = T('Group deleted')
msg_list_empty = T('No Groups currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

#
# group_id: reusable field for other tables to reference ----------------------
#
group_id = SQLTable(None, 'group_id',
                Field('group_id', db.pr_group,
                requires = IS_NULL_OR(IS_IN_DB(db, 'pr_group.id', '%(id)s: %(group_name)s')),
                represent = lambda id: (id and [db(db.pr_group.id==id).select()[0].group_name] or ["None"])[0],
                comment = DIV(A(T('Add Group'), _class='popup', _href=URL(r=request, c='pr', f='group', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Create Group Entry|Create a group entry in the registry."))),
                ondelete = 'RESTRICT'
                ))

# *****************************************************************************
# Network (network)
#
pr_network_type_opts = {
    1:T('Family'),
    2:T('Friends'),
    3:T('Colleagues'),
    99:T('other')
    }

opt_pr_network_type = SQLTable(None, 'opt_pr_network_type',
                    db.Field('opt_pr_network_type','integer',
                    requires = IS_IN_SET(pr_network_type_opts),
                    default = 99,
                    label = T('Network Type'),
                    represent = lambda opt: opt and pr_network_type_opts[opt]))
#
# network table ---------------------------------------------------------------
#
resource = 'network'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                person_id,                          # Reference to person (owner)
                opt_pr_network_type,                # Network type
                Field('comment'),                   # a comment (optional)
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)

#
# network_id: reusable field for other tables to reference ----------------------
#
network_id = SQLTable(None, 'network_id',
                Field('network_id', db.pr_network,
                requires = IS_NULL_OR(IS_IN_DB(db, 'pr_network.id', '%(id)s')),
                represent = lambda id: (id and [db(db.pr_network.id==id).select()[0].id] or ["None"])[0],
                comment = DIV(A(T('Add Network'), _class='popup', _href=URL(r=request, c='pr', f='network', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Create Network|Create a social network layer for a person."))),
                ondelete = 'RESTRICT'
                ))

# *****************************************************************************
# Functions:
#

#
# shn_pentity_ondelete --------------------------------------------------------
#
def shn_pentity_ondelete(record):
    """
    VITA function:
    Minimalistic callback function for CRUD controller, deletes a pentity record
    when the corresponding subclass record gets deleted.
     
    Use as setting in the calling controller:
    
    crud.settings.delete_onvalidation=shn_pentity_ondelete

    Also called by the shn_pentity_onvalidation function on deletion from update form
    """
    if request.vars.format:
        representation = str.lower(request.vars.format)
    else:
        representation = "html"

    if 'pr_pe_id' in record:
        pr_pe_id = record.pr_pe_id
        shn_delete('pr_pentity', 'pentity', pr_pe_id, representation)
    return

#
# shn_pentity_onvalidation ----------------------------------------------------
#
def shn_pentity_onvalidation(form, table=None, entity_class=1):
    """
    VITA function:
    Callback function for RESTlike CRUD controller, creates or updates a pentity
    record when the corresponding subclass record gets created/updated.
     
    Passed to shn_rest_controller as:
    
    onvalidation=lambda form: shn_pentity_onvalidation(form, table='pr_person', entity_class=1)

    form            : the current form containing pr_pe_id and pr_pe_label (from pr_pe_fieldset)
    table           : the table containing the subclass entity
    entity_class    : the class of pentity to be created (from pr_pentity_class_opts)
    """
    if form.vars:
        if (len(request.args) == 0 or request.args[0] == 'create') and entity_class in pr_pentity_class_opts.keys():
            # this is a create action either directly or from list view
            subentity_label = form.vars.get('pr_pe_label')
            pr_pe_id = db['pr_pentity'].insert(opt_pr_pentity_class=entity_class,label=subentity_label)
            if pr_pe_id: form.vars.pr_pe_id = pr_pe_id
        elif len(request.args) > 1 and request.args[0] == 'update' and form.vars.delete_this_record and table:
            # this is a delete action from update
            subentity_id = request.args[1]
            shn_pentity_ondelete(db[table][subentity_id])
        elif len(request.args) > 1 and request.args[0] == 'update' and table:
            # this is an update action
            subentity_id = request.args[1]
            subentity_record=db[table][subentity_id]
            if subentity_record and subentity_record.pr_pe_id:
                db(db.pr_pentity.id==subentity_record.pr_pe_id).update(label=form.vars.get('pr_pe_label'))
    return

#
# shn_pr_get_person_id --------------------------------------------------------
#
def shn_pr_get_person_id(label, fields=None, filterby=None):
    """
        Finds a person by any name and/or tag label
    """

    if fields and isinstance(fields, (list,tuple)):
        search_fields = []
        for f in fields:
            if db.pr_person.has_key(f):     # TODO: check for field type?
                search_fields.append(f)
        if not len(search_fields):
            # Error: none of the specified search fields exists
            return None
    else:
        # No search fields specified at all => fallback
        search_fields = ['pr_pe_label','first_name','middle_name','last_name']

    if label and isinstance(label,str):
        labels = label.split()
        results = []
        query = None
        for l in labels:
            # build query
            for f in search_fields:
                if query:
                    query = (db.pr_person[f].like(l)) | query
                else:
                    query = (db.pr_person[f].like(l))
            # undeleted records only
            query = (db.pr_person.deleted==False) & (query)
            # restrict to prior results (AND)
            if len(results):
                query = (db.pr_person.id.belongs(results)) & query
            if filterby:
                query = (filterby) & (query)
            records = db(query).select(db.pr_person.id)
            # rebuild result list
            results = [r.id for r in records]
            # any results left?
            if not len(results):
                return None
        return results
    else:
        # no label given or wrong parameter type
        return None
#
# shn_pr_select_person --------------------------------------------------------
#
def shn_pr_select_person(id):

    if id:
        # Clear selection
        if 'pr_person' in session:
            del session['pr_person']
        if isinstance(id,int) or (isinstance(id,str) and id.isdigit()):
            record_id = id
        else:
            record_id = None
    else:
        if 'pr_person' in session:
            record_id = session.pr_person
        else:
            record_id = None

    if record_id:
        query = ((db.pr_person.deleted==False) | (db.pr_person.deleted==None))
        query = (db.pr_person.id==record_id) & query
        records = db(query).select(db.pr_person.id)
        if records:
            session.pr_person = records[0].id
        else:
            if 'pr_person' in session:
                del session['pr_person']

    return

#
# shn_pr_person_header --------------------------------------------------------
#
def shn_pr_person_header(id, next=None):
    if id and isinstance(id,int):
        try:
            record = db(db.pr_person.id==id).select()[0]
        except:
            return None

        if next: request.vars.next=next

        redirect = { "_next" : "%s" % URL(r=request, args=request.args, vars=request.vars)}

        pheader = TABLE(
            TR(
                TH("Name: "),
                "%s %s %s" % (
                    record.first_name,
                    record.middle_name or '',
                    record.last_name or ''
                    ),
                TH("ID Label: "),
                "%(pr_pe_label)s" % record,
                TH(A("Clear Selection", _href=URL(r=request, c='pr', f='person', args='clear', vars=request.vars)))
                ),
            TR(
                TH("Date of Birth: "),
                "%s" % (record.date_of_birth or 'unknown'),
                TH("Gender: "),
                "%s" % pr_person_gender_opts[record.opt_pr_gender],
                "",
                ),
            TR(
                TH("Nationality"),
                "%s" % pr_nationality_opts[record.opt_pr_nationality],
                TH("Age Group: "),
                "%s" % pr_person_age_group_opts[record.opt_pr_age_group],
                TH(A("Edit Person", _href=URL(r=request, c='pr', f='person', args='update/%s' % id, vars=redirect)))
                )
        )
        return pheader
    else:
        return None

#
# shn_pr_person_sublist -------------------------------------------------------
#
def shn_pr_person_sublist_linkto(field):
    return URL(r=request, f=request.args[0], args="update/%s" % field, vars=dict(_next=URL(r=request, args=request.args, vars=request.vars)))

def shn_pr_person_sublist(request, subentity, person_id, fields=None, representation='html', orderby=None):

    subresource = "%s_%s" % (module, subentity)
    subtable = db[subresource]

    output = dict(items=None)

    # Check for authorization
    if shn_has_permission('read',db.pr_person) & shn_has_permission('read',subtable):
        query = (db.pr_person.id==person_id)
        if 'pr_pe_id' in subtable.fields:
            query = ((db.pr_person.pr_pe_id==subtable.pr_pe_id) & query)
        elif 'person_id' in subtable.fields:
            query = ((db.pr_person.id==subtable.person_id) & query)

        query = ((db.pr_person.deleted==False) & (subtable.deleted==False)) & query

        # Audit
        shn_audit_read(operation='list', resource=subresource, representation=representation)

        # Pagination
        if 'page' in request.vars:
            # Pagination at server-side (since no JS available)
            page = int(request.vars.page)
            start_record = (page - 1) * ROWSPERPAGE
            end_record = start_record + ROWSPERPAGE
            limitby = start_record, end_record
            totalpages = (db(query).count() / ROWSPERPAGE) + 1 # Fails on GAE
            label_search_button = T('Search')
            search_btn = A(label_search_button, _href=URL(r=request, f=resource, args='search'), _id='search-btn')
            output.update(dict(page=page, totalpages=totalpages, search_btn=search_btn))
        else:
            # No Pagination server-side (to allow it to be done client-side)
            limitby = ''
            # Redirect to a paginated version if JS not-enabled
            request.vars['page'] = 1
            response.refresh = '<noscript><meta http-equiv="refresh" content="0; url=' + URL(r=request, args=request.args, vars=request.vars) + '" /></noscript>'

        if not fields:
            fields = [subtable[f] for f in subtable.fields if subtable[f].readable]

        # Column labels
        headers = {}
        for field in fields:
            # Use custom or prettified label
            headers[str(field)] = field.label
    
        if shn_has_permission('update',subtable):
            linkto=shn_pr_person_sublist_linkto
        else:
            linkto=None

        items = crud.select(
            subtable,
            query=query,
            fields=fields,
            limitby=limitby,
            headers=headers,
            truncate=48,
            linkto=linkto,
            orderby=orderby,
            _id='list', _class='display')

    else:
        session.error = UNAUTHORISED
        redirect(URL(r=request, c='default', f='user', args='login', vars={'_next':URL(r=request, args=request.args, vars=request.vars)}))

    if not items:
        items = T('None')

    output.update(items=items)

    return output

#
#
# END
# *****************************************************************************
