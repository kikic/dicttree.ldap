import ldap

from itertools import chain
from unittest import TestCase

from dicttree.ldap import Connection
from dicttree.ldap import Node

from dicttree.ldap.tests import fixtures


@fixtures.slapd
class TestLdapConnectivity(TestCase):
    """A simple test to ensure ldap is running and binding works
    """
    def test_connectivity(self):
        self.slapd.con.bind_s('cn=root,o=o', 'secret')
        self.assertEqual(self.slapd.con.whoami_s(), 'dn:cn=root,o=o')


@fixtures.slapd
class TestLDAPConnection(TestCase):
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

    @classmethod
    def setUpClass(self):
        self.ldap = self.slapd.con
        self.con = Connection(uri='ldapi://var%2Frun%2Fldapi',
                              base_dn='o=o',
                              bind_dn='cn=root,o=o',
                              pw='secret')

    def setUp(self):
        """Setup entries for this test case
        """
        for id in [self.ldap.add(dn, self.ENTRIES[dn]) for dn in self.ENTRIES]:
            self.ldap.result(id)

    def tearDown(self):
        """Remove all entries of this test case
        """
        for id in [self.ldap.delete(dn) for dn in
                   chain(self.ENTRIES, self.ADDITIONAL)]:
            try:
                self.ldap.result(id)
            except ldap.NO_SUCH_OBJECT:
                pass

    def test_attrlist_and_attrsonly(self):
        """understanding what theses two are exactly doing
        """
        # attrlist=None, [], and ['*'] fetch all normal attributes,
        # so-called user-attributes
        self.assertEqual(
            [('o=o', {'objectClass': ['organization'], 'o': ['o']})],
            self.ldap.search_s('o=o', ldap.SCOPE_BASE))
        self.assertEqual(
            [('o=o', {'objectClass': ['organization'], 'o': ['o']})],
            self.ldap.search_s('o=o', ldap.SCOPE_BASE, attrlist=[]))
        self.assertEqual(
            [('o=o', {'objectClass': ['organization'], 'o': ['o']})],
            self.ldap.search_s('o=o', ldap.SCOPE_BASE, attrlist=['*']))

        # attrlist=['+'] fetches internal attributes, attrsonly=True
        # skips the values
        self.assertEqual(
            [('o=o', {'createTimestamp': [],
                      'creatorsName': [],
                      'entryCSN': [],
                      'entryDN': [],
                      'entryUUID': [],
                      'hasSubordinates': [],
                      'modifiersName': [],
                      'modifyTimestamp': [],
                      'structuralObjectClass': [],
                      'subschemaSubentry': []})],
            self.ldap.search_s('o=o', ldap.SCOPE_BASE, attrlist=['+'], attrsonly=True))

        # attrlist=[''] skips all attributes
        self.assertEqual(
            [('o=o', {})],
            self.ldap.search_s('o=o', ldap.SCOPE_BASE, attrlist=['']))

    def test_contains(self):
        self.assertTrue('cn=cn0,o=o' in self.con)
        self.assertFalse('cn=fail,o=o' in self.con)

    def test_getitem(self):
        def get_nonexistent():
            self.con['cn=fail,o=o']

        dn = 'cn=cn0,o=o'
        self.assertEqual(self.con[dn], self.con[dn])
        self.assertEqual(dn, self.con[dn].name)
        # (currently) order is not preserved, see dicttree.ldap.Node
        #self.assertEqual(self.ENTRIES[dn], tuple(self.con[dn].attrs.items()))
        self.assertItemsEqual(self.ENTRIES[dn], self.con[dn].attrs.items())
        self.assertRaises(KeyError, get_nonexistent)

    def test_setitem(self):
        dn = 'cn=cn2,o=o'
        node = Node(name=dn, attrs=self.ADDITIONAL[dn])
        def addnode():
            self.con[dn] = node

        addnode()
        self.assertRaises(KeyError, addnode)
        self.assertEquals(node, self.con[dn])

    def test_delitem(self):
        def delete():
            del self.con['cn=cn0,o=o']

        def search_deleted():
            self.ldap.search_s('cn=cn0,o=o', ldap.SCOPE_BASE)

        delete()
        self.assertRaises(KeyError, delete)
        self.assertRaises(ldap.NO_SUCH_OBJECT, search_deleted)

    def test_iter(self):
        self.assertItemsEqual(self.ENTRIES.keys(), self.con)

    def test_keys(self):
        self.assertItemsEqual(self.ENTRIES.keys(), self.con.keys())

    def test_values(self):
        self.assertItemsEqual(self.ENTRIES.keys(),
                              (node.name for node in self.con.values()))

    def test_items(self):
        self.assertItemsEqual(((dn, dn) for dn in self.ENTRIES.keys()),
                              ((dn, node.name) for dn, node in self.con.items()))
