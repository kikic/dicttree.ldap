import ldap

from ldap import SCOPE_BASE
from ldap import SCOPE_ONELEVEL
from ldap import SCOPE_SUBTREE
from ldap.ldapobject import LDAPObject

import copy
import random

class Attributes(object):
    def __init__(self, node=None):
        if node is not None:
            self.node = node


class Node(object):
    def __init__(self, name=None, attrs=()):
        self.name = name
        # python-ldap uses (unordered) dicts to return attributes. I
        # am under the impression that openldap preserves attribute
        # order from an ldif file, which would mean patching
        # python-ldap would give us order. Needs to be investigated.
        #self.attrs = OrderedDict(attrs)
        self.attrs = dict(attrs)

    def __eq__(self, other):
        return self is other or \
            self.name == other.name and \
            self.attrs == other.attrs

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return '<ldap node dn="%s">' % (self.name,)


class Directory(object):
    """XXX: this could be without base_dn, not supporting iteration
    """
    def __init__(self, uri, base_dn, bind_dn, pw):
        self.base_dn = base_dn
        self._ldap = LDAPObject(uri)
        self._ldap.bind_s(bind_dn, pw)

    def __contains__(self, dn):
        try:
            return dn == self._ldap.search_s(dn, SCOPE_BASE,
                                             attrlist=[''])[0][0]
        except ldap.NO_SUCH_OBJECT:
            return False

    def __getitem__(self, dn):
        try:
            entry = self._ldap.search_s(dn, SCOPE_BASE)[0]
        except ldap.NO_SUCH_OBJECT:
            raise KeyError(dn)
        node = Node(name=dn, attrs=entry[1])
        return node

    def __setitem__(self, dn, node):
        addlist = node.attrs.items()
        try:
            self._ldap.add_s(dn, addlist)
        except ldap.ALREADY_EXISTS:
            raise KeyError(dn)

    def __delitem__(self, dn):
        try:
            self._ldap.delete_s(dn)
        except ldap.NO_SUCH_OBJECT:
            raise KeyError(dn)

    def __iter__(self):
        return (x[0][0] for x in
                self._search(self.base_dn, SCOPE_SUBTREE)
                if x[0][0] != self.base_dn)

    def _search(self, base, scope, filterstr='(objectClass=*)', attrlist=None,
                timeout=-1):
        """asynchronous ldap search returning a generator
        """
        msgid = self._ldap.search(base, scope, filterstr=filterstr, attrlist=attrlist)
        rtype = ldap.RES_SEARCH_ENTRY
        while rtype is ldap.RES_SEARCH_ENTRY:
            # Fetch results single file, the final result (usually)
            # has an empty field. <sigh>
            (rtype, data) = self._ldap.result(msgid=msgid, all=0, timeout=timeout)
            if rtype is ldap.RES_SEARCH_ENTRY or data:
                yield data

    def items(self):
        return ItemsView(directory=self)

    def keys(self):
        return KeysView(directory=self)

    def values(self):
        return ValuesView(directory=self)

    def __len__(self):
	return sum(1 for i in iter(self))
               
    def clear(self):
	for k in self.keys():
	    del self[k]
	    
    def copy(self):
	new_copy = copy.copy(self)
	return new_copy
     
    def get(self, key, default=None):
	try:
            entry = self._ldap.search_s(key, SCOPE_BASE)[0]
        except ldap.NO_SUCH_OBJECT:
            return default
        node = Node(name=key, attrs=entry[1])
        return node

    def pop(self, key, default=None):
        try:
            entry = self._ldap.search_s(key, SCOPE_BASE)[0]
        except ldap.NO_SUCH_OBJECT:
	    if default is None:
		raise KeyError(key)
            return default
        node = Node(name=key, attrs=entry[1])
        self.__delitem__(key)    
        return node        
        
    def popitem(self):
	if not self:
	  raise KeyError
	keys_view = self.keys()
	keys_enum = enumerate(iter(keys_view))
	random_keys = random.shuffle(keys_enum)
	random_key = random_keys[0]
	node = self.get(random_key)
	self.__delitem__(node.name)
	return node
	
    def setdefault(self, key, default=None):
	try:
            entry = self._ldap.search_s(key, SCOPE_BASE)[0]    
        except ldap.NO_SUCH_OBJECT:
	    if default is not None and type(default) is Node:
		self.__setitem__(default.name, default)
		return default
	    else:
		return None
	node = Node(name=key, attrs=entry[1])
	return node
	    
    def update(self, *args, **kwargs):
	if type(args[0]) is Node:
	    return True
	else:
	    return False
	addlist = node.attrs.items()
        try:
            self._ldap.add_s(dn, addlist)
        except ldap.ALREADY_EXISTS:
            raise KeyError(dn)
	return None
	
	
	
class DictView(object):
    def __init__(self, directory):
        self.directory = directory


class ItemsView(DictView):
    def __iter__(self):
        return ((node.name, node) for node in ValuesView(self.directory))


class KeysView(DictView):
    def __iter__(self):
        return iter(self.directory)


class ValuesView(DictView):
    def __iter__(self):
        directory = self.directory
        return (Node(name=x[0][0], attrs=x[0][1]) for x in
                directory._search(directory.base_dn,
                                   ldap.SCOPE_SUBTREE, attrlist=[''])
                if x[0][0] != directory.base_dn)
