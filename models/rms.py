# -*- coding: utf-8 -*-

module = 'rms'

# Settings
resource = 'setting'
table = module + '_' + resource
db.define_table(table,
                Field('audit_read', 'boolean'),
                Field('audit_write', 'boolean'),
                migrate=migrate)

# -------------------------------
# Load lists/dictionaries for drop down menus

rms_priority_opts = {
    3:T('High'),
    2:T('Medium'),
    1:T('Low')
}

rms_status_opts = {
    1:T('Pledged'),
    2:T('In Transit'),
    3:T('Delivered'),
    }

rms_type_opts = {
    1:T('Food'),
    2:T('Find'),
    3:T('Water'),
    4:T('Medicine'),
    5:T('Shelter'),
    6:T('Report'),
    }

rms_req_source_type = { 1 : 'Manual',
                        2 : 'SMS',
                        3 : 'Tweet' }

# -----------------
# Requests table (Combined SMS, Tweets & Manual entry)

def shn_req_aid_represent(id):
    return  A(T('Make Pledge'), _href=URL(r=request, f='req', args=[id, 'pledge']))

resource = 'req'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
   Field("message", "text"),
   location_id,
   Field("timestamp", "datetime"),
   Field("type", "integer"),
   Field("priority", "integer"),
   Field("verified", "boolean"),
   Field("city", "string"),
   Field("completion_status", "boolean"),
   Field("source_type", "integer"),
   Field("source_id", "integer"),
   Field("actionable", "boolean"),
    migrate=migrate)

db.rms_req.id.represent = lambda id: shn_req_aid_represent(id)

#label the fields for the view
db[table].timestamp.label = T('Date & Time')

#Hide fields from user:
db[table].verified.readable = db[table].verified.writable = False
db[table].source_id.writable = db[table].source_id.readable = False
db[table].completion_status.writable = db[table].completion_status.readable = False
db[table].actionable.writable = db[table].actionable.readable = False
db[table].source_type.writable = db[table].source_type.readable = False

#set default values
db[table].actionable.default = 1
db[table].source_type.default = 1

db[table].message.requires = IS_NOT_EMPTY()
db[table].message.comment = SPAN("*", _class="req")

db[table].timestamp.requires = IS_NOT_EMPTY()
db[table].timestamp.comment = SPAN("*", _class="req")


db[table].priority.requires = IS_NULL_OR(IS_IN_SET(rms_priority_opts))
#db[table].priority.represent = lambda prior: prior and rms_priority_opts[prior]
db[table].priority.represent = lambda id: (id and [DIV(IMG(_src='/%s/static/img/priority/priority_%d.gif' % (request.application,id,), _height=12))] or [DIV(IMG(_src='/%s/static/img/priority/priority_4.gif' % request.application), _height=12)])
db[table].priority.label = T('Priority Level')

db[table].type.requires = IS_NULL_OR(IS_IN_SET(rms_type_opts))
db[table].type.represent = lambda type: type and rms_type_opts[type]
db[table].type.label = T('Request Type')

db[table].source_type.requires = IS_NULL_OR(IS_IN_SET(rms_req_source_type))
db[table].source_type.represent = lambda stype: stype and rms_req_source_type[stype]
db[table].source_type.label = T(' Source Type')

ADD_AID_REQUEST = T('Add Aid Request')

s3.crud_strings[table] = Storage(title_create        = ADD_AID_REQUEST,
                                 title_display       = "Aid Request Details",
                                 title_list          = "List Aid Requests",
                                 title_update        = "Edit Aid Request",
                                 title_search        = "Search Aid Requests",
                                 subtitle_create     = "Add New Aid Request",
                                 subtitle_list       = "Aid Requests",
                                 label_list_button   = "List Aid Requests",
                                 label_create_button = ADD_AID_REQUEST,
                                 msg_record_created  = "Aid request added",
                                 msg_record_modified = "Aid request updated",
                                 msg_record_deleted  = "Aid request deleted",
                                 msg_list_empty      = "No aid requests currently available")

#Reusable field for other tables
request_id = SQLTable(None, 'req_id',
            FieldS3('req_id', db.rms_req, sortby='message',
                requires = IS_NULL_OR(IS_ONE_OF(db, 'rms_req.id', '%(message)s')),
                represent = lambda id: (id and [db(db.rms_req.id==id).select().first().updated] or ["None"])[0],
                label = T('Aid Request'),
                comment = DIV(A(ADD_AID_REQUEST, _class='thickbox', _href=URL(r=request, c='rms', f='req', args='create', vars=dict(format='popup', KeepThis='true'))+"&TB_iframe=true", _target='top', _title=ADD_AID_REQUEST), A(SPAN("[Help]"), _class="tooltip", _title=T("ADD Request|The Request this record is associated with."))),
                ondelete = 'RESTRICT'
                ))


# shn_rms_get_req --------------------------------------------------------
# copied from pr.py
def shn_rms_get_req(label, fields=None, filterby=None):
    """
        Finds a request by Message string
    """

    if fields and isinstance(fields, (list,tuple)):
        search_fields = []
        for f in fields:
            if db.rms_req.has_key(f):     # TODO: check for field type?
                search_fields.append(f)
        if not len(search_fields):
            # Error: none of the specified search fields exists
            return None
    else:
        # No search fields specified at all => fallback
        search_fields = ['message']

    if label and isinstance(label, str):
        labels = label.split()
        results = []
        query = None
        # TODO: make a more sophisticated search function (levenshtein?)
        for l in labels:

            # append wildcards
            wc = "%"
            _l = "%s%s%s" % (wc, l, wc)

            # build query
            for f in search_fields:
                if query:
                    query = (db.rms_req[f].like(_l)) | query
                else:
                    query = (db.rms_req[f].like(_l))

            # undeleted records only
            query = (db.rms_req.deleted==False) & (query)
            # restrict to prior results (AND)
            if len(results):
                query = (db.rms_req.id.belongs(results)) & query
            if filterby:
                query = (filterby) & (query)
            records = db(query).select(db.rms_req.id)
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
# shn_rms_req_search_simple -------------------------------------------------
# copied from pr.py
def shn_rms_req_search_simple(xrequest, **attr):
    """
        Simple search form for persons
    """

    if attr is None:
        attr = {}

    onvalidation = attr.get('onvalidation', None)
    onaccept = attr.get('onaccept', None)

    if not shn_has_permission('read', db.rms_req):
        session.error = UNAUTHORISED
        redirect(URL(r=request, c='default', f='user', args='login', vars={'_next':URL(r=request, args='search_simple', vars=request.vars)}))

    if xrequest.representation=="html":
        # Check for redirection
        if request.vars._next:
            next = str.lower(request.vars._next)
        else:
            next = str.lower(URL(r=request, f='req', args='[id]'))

        # Custom view
        response.view = '%s/req_search.html' % xrequest.prefix

        # Title and subtitle
        title = T('Search for a Request')
        subtitle = T('Matching Records')

        # Select form
        form = FORM(TABLE(
                TR(T('Text in Message: '),
                   INPUT(_type="text", _name="label", _size="40"),
                   A(SPAN("[Help]"), _class="tooltip", _title=T("Text in Message|To search for a request, enter some of the text that you are looking for. You may use % as wildcard. Press 'Search' without input to list all requests."))),
                TR("", INPUT(_type="submit", _value="Search"))
                ))

        output = dict(title=title, subtitle=subtitle, form=form, vars=form.vars)

        # Accept action
        items = None
        if form.accepts(request.vars, session):

            if form.vars.label == "":
                form.vars.label = "%"

            results = shn_rms_get_req(form.vars.label)

            if results and len(results):
                rows = db(db.rms_req.id.belongs(results)).select()
            else:
                rows = None

            # Build table rows from matching records
            if rows:
                records = []
                for row in rows:
                    href = next.replace('%5bid%5d', '%s' % row.id)
                    records.append(TR(
                        row.completion_status,
                        row.message,
                        row.timestamp,
                        row.location_id and shn_gis_location_represent(row.location_id) or 'unknown',
                        ))
                items=DIV(TABLE(THEAD(TR(
                    TH("Completion Status"),
                    TH("Message"),
                    TH("Time"),
                    TH("Location"),
                    )),
                    TBODY(records), _id='list', _class="display"))
            else:
                items = T('None')

        try:
            label_create_button = s3.crud_strings['rms_req'].label_create_button
        except:
            label_create_button = s3.crud_strings.label_create_button

        add_btn = A(label_create_button, _href=URL(r=request, f='req', args='create'), _id='add-btn')

        output.update(dict(items=items, add_btn=add_btn))
        return output

    else:
        session.error = BADFORMAT
        redirect(URL(r=request))

# Plug into REST controller
s3xrc.model.set_method(module, resource, method='search_simple', action=shn_rms_req_search_simple )

# ------------------
# Create pledge table

def shn_req_pledge_represent(id):
#    return  A(T('Edit Pledge'), _href=URL(r=request, f='pledge', args=[id, 'pledge']))
    return  A(T('Edit Pledge'), _href=URL(r=request, f='pledge', args=[id]))


resource = 'pledge'
table = module + '_' + resource
db.define_table(table, timestamp, authorstamp, uuidstamp, deletion_status,
   Field('submitted_on', 'datetime'),
   Field("req_id", db.rms_req),
   Field("status", "integer"),
   organisation_id,
   person_id,
#   Field('submitted_by', db.auth_user), # replaced by authorstamp
#   location_id,
#   Field('comment_id', db.comment),
   migrate=migrate)

db.rms_pledge.id.represent = lambda id: shn_req_pledge_represent(id)

# hide unnecessary fields
db[table].req_id.writable = db[table].req_id.readable = False

# set pledge default
db[table].status.default = 1

# auto fill posted_on field and make it readonly
db[table].submitted_on.default = request.now
db[table].submitted_on.writable = False

db[table].status.requires = IS_IN_SET(rms_status_opts)
db[table].status.represent = lambda status: status and rms_status_opts[status]
db[table].status.label = T('Pledge Status')

# Pledges as a component of requests
s3xrc.model.add_component(module, resource,
    multiple=True,
    joinby=dict(rms_req = 'req_id'),
    deletable=True,
    editable=True,
    list_fields = ['id', 'organisation_id', 'person_id', 'submitted_on', 'status'])

s3.crud_strings[table] = Storage(title_create        = "Add Pledge",
                                 title_display       = "Pledge Details",
                                 title_list          = "List Pledges",
                                 title_update        = "Edit Pledge",
                                 title_search        = "Search Pledges",
                                 subtitle_create     = "Add New Pledge",
                                 subtitle_list       = "Pledges",
                                 label_list_button   = "List Pledges",
                                 label_create_button = "Add Pledge",
                                 msg_record_created  = "Pledge added",
                                 msg_record_modified = "Pledge updated",
                                 msg_record_deleted  = "Pledge deleted",
                                 msg_list_empty      = "No Pledges currently available")



# ------------------
# Create the table for request_detail for requests with arbitrary keys
resource = 'req_detail'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
    request_id,
    Field("request_key", "string"),
    Field("value", "string"),
    migrate=migrate)

s3xrc.model.add_component(module, resource,
    multiple=True,
    joinby=dict(rms_req='req_id'),
    deletable=True,
    editable=True,
    main='request_key', extra='value',
    list_fields = ['id', 'req_id', 'request_key', 'value'])

# Make some fields invisible:
db[table].req_id.writable = db[table].req_id.readable = False

# make all fields read only
#db[table].tweet_request_id.writable = db[table].tweet_request_id.readable = False
#db[table].request_key.writable = False
#db[table].value.writable = False

ADD_REQUEST_DETAIL = T('Add Request Detail')
s3.crud_strings[table] = Storage( title_create        = ADD_REQUEST_DETAIL,
                                  title_display       = "Request Detail",
                                  title_list          = "List Request Details",
                                  title_update        = "Edit Request Details",
                                  title_search        = "Search Request Details",
                                  subtitle_create     = "Add New Request Detail",
                                  subtitle_list       = "Request Details",
                                  label_list_button   = "List Request Details",
                                  label_create_button = ADD_REQUEST_DETAIL,
                                  msg_record_created  = "Request detail added",
                                  msg_record_modified = "Request detail updated",
                                  msg_record_deleted  = "Request detail deleted",
                                  msg_list_empty      = "No request details currently available")


#Reusable field for other tables
req_detail_id = SQLTable(None, 'req_detail_id',
            FieldS3('req_detail_id', db.rms_req_detail, sortby='request_key',
                requires = IS_NULL_OR(IS_ONE_OF(db, 'rms_req_detail.id', '%( request_key)s')),
                represent = lambda id: (id and [db(db.rms_req_detail.id==id).select().first().updated] or ["None"])[0],
                label = T('Request Detail'),
                comment = DIV(A(ADD_REQUEST_DETAIL, _class='thickbox', _href=URL(r=request, c='rms', f='req_detail', args='create', vars=dict(format='popup', KeepThis='true'))+"&TB_iframe=true", _target='top', _title=ADD_REQUEST_DETAIL), A(SPAN("[Help]"), _class="tooltip", _title=T("ADD Request|The Request this record is associated with."))),
                ondelete = 'RESTRICT'
                ))
