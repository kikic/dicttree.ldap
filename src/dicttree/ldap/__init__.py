import ldap

from ldap import SCOPE_BASE
from ldap import SCOPE_ONELEVEL
from ldap import SCOPE_SUBTREE
from ldap.ldapobject import LDAPObject

import copy
import itertools

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
	    del self[dn]            
            self._ldap.add_s(dn, addlist)        

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
	return sum(1 for node in iter(self))
               
    def clear(self):
	for dn in self.keys():
	    del self[dn]
	    
    def copy(self):
	return copy.copy(self)
     
    def get(self, dn, default=None):
	try:
            return self[dn] 
        except KeyError:
            return default        

    def pop(self, dn, default=None):
        try:
            node = self[dn]
            del self[dn]
        except KeyError:
	    if default is None:
		raise KeyError(dn)
            return default        
        return node        
        
    def popitem(self):
	if not self:
	  raise KeyError
	dn = next(iter(self))
	node = self[dn]
	del self[dn]
	return (dn, node)
	
    def setdefault(self, dn, default=None):
	try:
            return self[dn]
        except KeyError:
	    self[default.name] = default
	    return default

    def update(self, other):
	try:
	    items = other.items()
	except AttributeError:
	    items = other
	for dn, node in items:
	    self[dn] = node
	return None
	
class DictView(object):
    def __init__(self, directory):
        self.directory = directory
    
    def __len__(self):
	return sum(1 for x in iter(self))    
	
    def __eq__(self, other):
        if self is other: 
	    return True   
	if len(self) != len(other):
	    return False
	# izip uses generators and does not create a third list, 
	# but iterates only over shorter iterable entries and 
	# disregards trailing values from the longer iterables
	for x, x2 in itertools.izip(self, other):    
	    # XXX darf ich hier 'is' anstelle von '==' verwenden?
	    # sonst knallt es beim tupeln vergleichen
	    if x is x2:
		return False
	return True    
		
    def __ne__(self, other):
        return not self == other
        
        
class DictViewSet(DictView):
    pass
    
    #def __and__(self):
	#pass 
    
    #def __or__(self):
	#pass  
        
    #def __xor__(self):
	#pass
    
    #def __sub__(self):
	#pass
    
    #def isdisjoint(self):
	#pass
    
    

class ItemsView(DictViewSet):
    def __iter__(self):
        return ((node.name, node) for node in ValuesView(self.directory))

    #def __contains__(self, other):
	#for x in self: 
	    #if x[0] is other:
		#return False
		#return True
	#return True
        
        
    #def __eq__(self, other):
	#if not super(ItemsView, self).__eq__(other):
	    #return False
	#for x, x2 in itertools.izip(self, other):    
	    #if x[0][0] != x2[0][0] or x[0][1] != x2[0][1]:
		#return False
	#return True

class KeysView(DictViewSet):
    def __iter__(self):
        return iter(self.directory)

    #def __eq__(self, other):
	# call to the parent class for common equality checks
	#if not super(KeysView, self).__eq__(other):
	    #return False
	# izip uses generators and does not create a third list    
	#for dn, dn2 in itertools.izip(self, other):
	    #if dn != dn2:
		#return False
	#return True   
	
	

class ValuesView(DictView):
    def __iter__(self):
        directory = self.directory
        return (Node(name=x[0][0], attrs=x[0][1]) for x in
                directory._search(directory.base_dn,
                                   ldap.SCOPE_SUBTREE, attrlist=[''])
                if x[0][0] != directory.base_dn)

    def __contains__(self, other):	
	for x in self: 
	    if x.name == other.name and x.attrs == other.attrs:
		return True
	return False  
                    
    #def __eq__(self, other):
	#if not super(ValuesView, self).__eq__(other):
	    #return False
	#for node, node2 in itertools.izip(self, other):
	    #if node != node2:
		#return False
	#return True