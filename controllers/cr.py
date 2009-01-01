module='cr'
# Current Module (for sidebar title)
module_name=db(db.module.name==module).select()[0].name_nice
# List Modules (from which to build Menu of Modules)
modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
# List Options (from which to build Menu for this Module)
options=db(db['%s_menu_option' % module].enabled=='Yes').select(db['%s_menu_option' % module].ALL,orderby=db['%s_menu_option' % module].priority)

# T2 framework functions
def login():
	response.view='login.html'
	return dict(form=t2.login(),module_name=module_name,modules=modules,options=options)
def logout(): t2.logout(next='login')
def register():
	response.view='register.html'
	t2.messages.record_created=T("You have been successfully registered")
	return dict(form=t2.register())
def profile(): t2.profile()

# S3 framework functions
def index():
    "Module's Home Page"
    return dict(module_name=module_name,modules=modules,options=options)
def open_option():
    "Select Option from Module Menu"
    id=request.vars.id
    options=db(db['%s_menu_option' % module].id==id).select()
    if not len(options):
        redirect(URL(r=request,f='index'))
    option=options[0].function
    redirect(URL(r=request,f=option))

def shelter():
    """RESTful controller function.
    Anonymous users can Read.
    Authentication required for Create/Update/Delete."""
    resource='shelter'
    table=db['%s_%s' % (module,resource)]
    if request.args:
        method=request.args[0]
        try:
            # 1st argument is ID not method => display
            id = int(method)
            item=t2.display(table)
            response.view='display.html'
            title=T('Shelter Details')
            edit=A(T("Edit"),_href=t2.action(resource,['update',t2.id]))
            list_btn=A(T("List Shelters"),_href=t2.action(resource))
            return dict(module_name=module_name,modules=modules,options=options,item=item,title=title,edit=edit,list_btn=list_btn)
        except:
            if method=="create":
                if t2.logged_in:
                    t2.messages.record_created=T("Shelter added")
                    form=t2.create(table)
                    response.view='create.html'
                    title=T('Add Shelter')
                    list_btn=A(T("List Shelters"),_href=t2.action(resource))
                    return dict(module_name=module_name,modules=modules,options=options,form=form,title=title,list_btn=list_btn)
                else:
                    t2.redirect('login',vars={'_destination':'%s/create' % resource})
            elif method=="display":
                t2.redirect(resource,args=t2.id)
            elif method=="update":
                if t2.logged_in:
                    t2.messages.record_modified=T("Shelter updated")
                    form=t2.update(table)
                    response.view='update.html'
                    title=T('Edit Shelter')
                    list_btn=A(T("List Shelters"),_href=t2.action(resource))
                    return dict(module_name=module_name,modules=modules,options=options,form=form,title=title,list_btn=list_btn)
                else:
                    t2.redirect('login',vars={'_destination':'%s/update/%i' % (resource,t2.id)})
            elif method=="delete":
                if t2.logged_in:
                    t2.messages.record_deleted=T("Shelter deleted")
                    t2.delete(table,next=resource)
                    return
                else:
                    t2.redirect('login',vars={'_destination':'%s/delete/%i' % (resource,t2.id)})
            else:
                # Invalid!
                return
    else:
        # No arguments => default to list
        list=t2.itemize(table)
        if list=="No data":
            list="No Shelters currently registered."
        title=T('List Shelters')
        subtitle=T('Shelters')
        if t2.logged_in:
            form=t2.create(table)
            response.view='list_create.html'
            addtitle=T('Add New Shelter')
            return dict(module_name=module_name,modules=modules,options=options,list=list,form=form,title=title,subtitle=subtitle,addtitle=addtitle)
        else:
            add_btn=A(T("Add Shelter"),_href=t2.action(resource,'create'))
            response.view='list.html'
            return dict(module_name=module_name,modules=modules,options=options,list=list,title=title,subtitle=subtitle,add_btn=add_btn)
