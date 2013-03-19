import ldap
import unittest

from itertools import chain

from dicttree.ldap import Directory
from dicttree.ldap import Node
from dicttree.ldap.tests import mixins


class TestLdapConnectivity(mixins.Slapd, unittest.TestCase):
    """A simple test to ensure ldap is running and binding works
    """
    def test_connectivity(self):
        self.ldap.bind_s('cn=root,o=o', 'secret')
        self.assertEqual(self.ldap.whoami_s(), 'dn:cn=root,o=o')


class TestLDAPDirectory(mixins.Slapd, unittest.TestCase):
    ENTRIES = {
        'cn=cn0,o=o': (('cn', ['cn0']),
                       ('objectClass', ['organizationalRole'])),
        'cn=cn1,o=o': (('cn', 'cn1'),
                       ('objectClass', ['organizationalRole'])),
        }
    ADDITIONAL = {
        'cn=cn2,o=o': (('cn', ['cn2']),
                       ('objectClass', ['organizationalRole'])),
        }

    def test_contains(self):
        self.assertTrue('cn=cn0,o=o' in self.dir)
        self.assertFalse('cn=fail,o=o' in self.dir)

    def test_getitem(self):
        def get_nonexistent():
            self.dir['cn=fail,o=o']

        dn = 'cn=cn0,o=o'
        self.assertEqual(self.dir[dn], self.dir[dn])
        self.assertEqual(dn, self.dir[dn].name)
        # (currently) order is not preserved, see dicttree.ldap.Node
        #self.assertEqual(self.ENTRIES[dn], tuple(self.dir[dn].attrs.items()))
        self.assertItemsEqual(self.ENTRIES[dn], self.dir[dn].attrs.items())
        self.assertRaises(KeyError, get_nonexistent)

    def test_setitem(self):
        dn = 'cn=cn2,o=o'
        node = Node(name=dn, attrs=self.ADDITIONAL[dn])
        def addnode():
            self.dir[dn] = node

        addnode()
        self.assertRaises(KeyError, addnode)
        self.assertEquals(node, self.dir[dn])

    def test_delitem(self):
        def delete():
            del self.dir['cn=cn0,o=o']

        def search_deleted():
            self.ldap.search_s('cn=cn0,o=o', ldap.SCOPE_BASE)

        delete()
        self.assertRaises(KeyError, delete)
        self.assertRaises(ldap.NO_SUCH_OBJECT, search_deleted)

    def test_iter(self):
        self.assertItemsEqual(self.ENTRIES.keys(), self.dir)

    def test_keys(self):
        self.assertItemsEqual(self.ENTRIES.keys(), self.dir.keys())

    def test_values(self):
        self.assertItemsEqual(self.ENTRIES.keys(),
                              (node.name for node in self.dir.values()))

    def test_items(self):
        self.assertItemsEqual(((dn, dn) for dn in self.ENTRIES.keys()),
                              ((dn, node.name) for dn, node in self.dir.items()))

    def test_len(self):
	def delete():
            del self.dir['cn=cn0,o=o']
	
	dn1 = 'cn=cn0,o=o'
        node1 = Node(name=dn1, attrs=self.ENTRIES[dn1])
        def addnode1():
            self.dir[dn1] = node1

        dn2 = 'cn=cn2,o=o'
        node2 = Node(name=dn2, attrs=self.ADDITIONAL[dn2])
        def addnode2():
            self.dir[dn2] = node2

	self.assertEqual(len(self.ENTRIES), len(self.dir))
	delete()
	self.assertTrue(len(self.ENTRIES) > len(self.dir))
        addnode1()
        addnode2()
        self.assertTrue(len(self.ENTRIES) < len(self.dir))
      
    def test_clear(self):
	self.assertItemsEqual(self.ENTRIES.keys(), self.dir)
	self.dir.clear()
	self.assertEqual(0, len(self.dir))
	self.assertEqual([('o=o', {})], self.ldap.search_s('o=o', ldap.SCOPE_BASE, attrlist=['']))
      
    def test_copy(self):
	self.assertItemsEqual(self.ENTRIES.keys(), self.dir.copy())
	self.assertItemsEqual(self.dir, self.dir.copy())
      
    def test_getkeydefault(self):
	dn = 'cn=cn0,o=o'
	fail = 'cn=fail,o=o'
	default = 'HubbaBubba'

        self.assertEqual(self.dir[dn], self.dir.get(dn))
	self.assertEqual(None, self.dir.get(fail))
	self.assertEqual(default, self.dir.get(fail, default))
      
    def test_popkeydefault(self):
	dn = 'cn=cn0,o=o'
	node = Node(name=dn, attrs=self.ENTRIES[dn])
	fail = 'cn=fail,o=o'
	default = 'HubbaBubba'
	
	self.assertEqual(node, self.dir.pop(dn))
	self.assertFalse(dn in self.dir)
	""" if default value is set to None, KeyError is raised, check if this is ok! """
	self.assertEqual(default, self.dir.pop(fail, default))
	""" lambda turns lookup into a callable object. """
	self.assertRaises(KeyError, lambda: self.dir.pop(fail))
      
      
    #def test_popitem(self):
	#node = self.dir.popitem()
	#self.assertTrue(node.name in self.ENTRIES.keys())
	#node = self.dir.popitem()
	#self.assertTrue(node.name in self.ENTRIES.keys())
	#self.assertRaises(KeyError, lambda: self.dir.popitem())
         
      
    def test_setdefault(self):
	dn = 'cn=cn0,o=o'
	node = Node(name=dn, attrs=self.ENTRIES[dn])
	dn2 = 'cn=cn2,o=o'
	node2 = Node(name=dn2, attrs=self.ADDITIONAL[dn2])
	fail = 'cn=fail,o=o'
	
	self.assertEqual(node, self.dir.setdefault(dn))
	""" how to insert a None value??? """
	self.assertEqual(None, self.dir.setdefault(fail))
	""" default has to be node.attr.items """
	self.assertEqual(node2, self.dir.setdefault(fail, node2))
      
    def test_update(self):
	dn = 'cn=cn0,o=o'	
	val = {'objectClass': ['organizationalRole'], 'cn': ['cn3']}
	node = Node(name=dn, attrs=val)
	
	self.assertTrue(self.dir.update(node))
    	#self.assertEqual(val, self.dir.update(dn, val))