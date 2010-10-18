# -*- coding: utf-8 -*-

""" S3XRC Resource Framework - Model Extensions

    @version: 2.1.7

    @see: U{B{I{S3XRC}} <http://eden.sahanafoundation.org/wiki/S3XRC>} on Eden wiki

    @author: nursix
    @contact: dominic AT nursix DOT org
    @copyright: 2009-2010 (c) Sahana Software Foundation
    @license: MIT

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.

"""

__all__ = ["S3SuperEntity",
           "S3ResourceComponent",
           "S3ResourceModel",
           "S3ResourceLinker"]

from gluon.storage import Storage

# *****************************************************************************
class S3SuperEntity(object):

    """ Super Entity class

        @todo 2.2: implement

    """

    def __init__(self):

        pass


# *****************************************************************************
class S3ResourceComponent(object):

    """ Class to represent component relations between resources """

    # -------------------------------------------------------------------------
    def __init__(self, db, prefix, name, **attr):

        """ Constructor

            @param db: the database (DAL)
            @param prefix: prefix of the resource name (=module name)
            @param name: name of the resource (=without prefix)
            @param attr: attributes

        """

        self.db = db
        self.prefix = prefix
        self.name = name

        self.tablename = "%s_%s" % (prefix, name)
        self.table = self.db.get(self.tablename, None)
        if not self.table:
            raise SyntaxError("Table must exist in the database.")

        self.attr = Storage(attr)
        if not "multiple" in self.attr:
            self.attr.multiple = True
        if not "deletable" in self.attr:
            self.attr.deletable = True
        if not "editable" in self.attr:
            self.attr.editable = True


    # Configuration ===========================================================

    def set_attr(self, name, value):

        """ Sets an attribute for a component

            @param name: attribute name
            @param value: attribute value

        """

        self.attr[name] = value


    # -------------------------------------------------------------------------
    def get_attr(self, name):

        """ Reads an attribute of the component

            @param name: attribute name

        """

        if name in self.attr:
            return self.attr[name]
        else:
            return None


# *****************************************************************************
class S3ResourceModel(object):


    """ Class to handle the compound resources model """


    # -------------------------------------------------------------------------
    def __init__(self, db):

        """ Constructor

            @param db: the database (DAL)

        """

        self.db = db
        self.components = {}
        self.config = Storage()
        self.methods = {}
        self.cmethods = {}

        # Initialize super entities
        self.super_entity = Storage()


    # Configuration ===========================================================

    def configure(self, table, **attr):

        """ Update the extra configuration of a table

            @param table: the table
            @param attr: dict of attributes to update

        """

        cfg = self.config.get(table._tablename, Storage())
        cfg.update(attr)
        self.config[table._tablename] = cfg


    # -------------------------------------------------------------------------
    def get_config(self, table, key):

        """ Reads a configuration attribute of a resource

            @param table: the resource DB table
            @param key: the key (name) of the attribute

        """

        if table._tablename in self.config:
            return self.config[table._tablename].get(key, None)
        else:
            return None


    # -------------------------------------------------------------------------
    def clear_config(self, table, *keys):

        """ Removes configuration attributes of a resource

            @param table: the resource DB table
            @param keys: keys of attributes to remove (maybe multiple)

        """

        if not keys:
            if table._tablename in self.config:
                del self.config[table._tablename]
        else:
            if table._tablename in self.config:
                for k in keys:
                    if k in self.config[table._tablename]:
                        del self.config[table._tablename][k]


    # -------------------------------------------------------------------------
    def add_component(self, prefix, name, **attr):

        """ Adds a component to the model

            @param prefix: prefix of the component name (=module name)
            @param name: name of the component (=without prefix)

        """

        joinby = attr.get("joinby", None)
        if joinby:
            component = S3ResourceComponent(self.db, prefix, name, **attr)
            hook = self.components.get(name, Storage())
            if isinstance(joinby, dict):
                for tablename in joinby:
                    hook[tablename] = Storage(
                        _joinby = ("id", joinby[tablename]),
                        _component = component)
            elif isinstance(joinby, str):
                hook._joinby=joinby
                hook._component=component
            else:
                raise SyntaxError("Invalid join key(s)")
            self.components[name] = hook
            return component
        else:
            raise SyntaxError("Join key(s) must be defined.")


    # -------------------------------------------------------------------------
    def get_component(self, prefix, name, component_name):

        """ Retrieves a component of a resource

            @param prefix: prefix of the resource name (=module name)
            @param name: name of the resource (=without prefix)
            @param component_name: name of the component (=without prefix)

        """

        tablename = "%s_%s" % (prefix, name)
        table = self.db.get(tablename, None)

        hook = self.components.get(component_name, None)
        if table and hook:
            h = hook.get(tablename, None)
            if h:
                pkey, fkey = h._joinby
                component = h._component
                return (hook[tablename]._component, pkey, fkey)
            else:
                nkey = hook._joinby
                component = hook._component
                if nkey and nkey in table.fields:
                    return (component, nkey, nkey)

        return (None, None, None)


    # -------------------------------------------------------------------------
    def get_components(self, prefix, name):

        """ Retrieves all components related to a resource

            @param prefix: prefix of the resource name (=module name)
            @param name: name of the resource (=without prefix)

        """

        tablename = "%s_%s" % (prefix, name)
        table = self.db.get(tablename, None)

        components = []
        if table:
            for hook in self.components.values():
                if tablename in hook:
                    h = hook[tablename]
                    pkey, fkey = h._joinby
                    component = h._component
                    components.append((component, pkey, fkey))
                else:
                    nkey = hook._joinby
                    component = hook._component
                    if nkey and nkey in table.fields:
                        components.append((component, nkey, nkey))

        return components


    # -------------------------------------------------------------------------
    def has_components(self, prefix, name):

        """ Check whether the specified resource has components

            @param prefix: prefix of the resource name (=module name)
            @param name: name of the resource (=without prefix)

        """

        tablename = "%s_%s" % (prefix, name)
        table = self.db.get(tablename, None)

        h = self.components.get(name, None)
        if h and h._component and h._component.tablename == tablename:
            k = h._joinby
        else:
            k = None

        if table:
            for hook in self.components.values():
                if tablename in hook:
                    return True
                else:
                    nkey = hook._joinby
                    if nkey and nkey in table.fields and nkey != k:
                        return True

        return False


    # -------------------------------------------------------------------------
    def set_method(self, prefix, name,
                   component_name=None,
                   method=None,
                   action=None):

        """ Adds a custom method for a resource or component

            @param prefix: prefix of the resource name (=module name)
            @param name: name of the resource (=without prefix)
            @param component_name: name of the component (=without prefix)
            @param method: name of the method
            @param action: function to invoke for this method

        """

        if not method:
            raise SyntaxError("No method specified")

        tablename = "%s_%s" % (prefix, name)

        if not component_name:
            if method not in self.methods:
                self.methods[method] = {}
            self.methods[method][tablename] = action
        else:
            component = self.get_component(prefix, name, component_name)[0]
            if component:
                if method not in self.cmethods:
                    self.cmethods[method] = {}
                if component.tablename not in self.cmethods[method]:
                    self.cmethods[method][component.tablename] = {}
                self.cmethods[method][component.tablename][tablename] = action


    # -------------------------------------------------------------------------
    def get_method(self, prefix, name, component_name=None, method=None):

        """ Retrieves a custom method for a resource or component

            @param prefix: prefix of the resource name (=module name)
            @param name: name of the resource (=without prefix)
            @param component_name: name of the component (=without prefix)
            @param method: name of the method

            @todo 2.2: fix docstring

        """

        if not method:
            return None

        tablename = "%s_%s" % (prefix, name)

        if not component_name:
            if method in self.methods and tablename in self.methods[method]:
                return self.methods[method][tablename]
            else:
                return None
        else:
            component = self.get_component(prefix, name, component_name)[0]
            if component and \
               method in self.cmethods and \
               component.tablename in self.cmethods[method] and \
               tablename in self.cmethods[method][component.tablename]:
                return self.cmethods[method][component.tablename][tablename]
            else:
                return None


    # -------------------------------------------------------------------------
    def set_attr(self, component_name, name, value):

        """ Sets an attribute for a component

            @param component_name: name of the component (without prefix)
            @param name: name of the attribute
            @param value: value for the attribute

        """

        return self.components[component_name].set_attr(name, value)


    # -------------------------------------------------------------------------
    def get_attr(self, component_name, name):

        """ Retrieves an attribute value of a component

            @param component_name: name of the component (without prefix)
            @param name: name of the attribute

            @todo 2.2: fix docstring

        """

        return self.components[component_name].get_attr(name)


# *****************************************************************************
class S3ResourceLinker(object):

    """ Resource Linker

        @todo 2.2: implement

    """

    def __init__(self):

        pass


# *****************************************************************************