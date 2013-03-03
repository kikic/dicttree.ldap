import ldap
import os
import time

from itertools import chain
from ldap.ldapobject import LDAPObject
from subprocess import Popen, PIPE
from unittest import TestCase

from dicttree.ldap import Connection
from dicttree.ldap import Node


def setUpModule():
    """setup global SLAPD process and LDAP connection

    ldap data dir is wiped and a fresh base dn added. In case of
    errors the SLAPD process is supposed to be killed.
    """
    global SLAPD, LDAP

    # ensure ldap dirs exist
    datadir = 'var/openldap-data'
    for x in (datadir, 'var/log', 'var/run'):
        if not os.path.exists(x):
            os.makedirs(x)

    # wipe ldap data dir and empty logfile (enable tailf)
    dbfiles = os.listdir(datadir)
    for x in dbfiles:
        os.unlink(datadir + '/' + x)
    with open('var/log/slapd.log', 'w') as f:
        f.truncate(0)

    # start ldap server
    # loglevels for -d
    # 1      (0x1 trace) trace function calls
    # 2      (0x2 packets) debug packet handling
    # 4      (0x4 args) heavy trace debugging (function args)
    # 8      (0x8 conns) connection management
    # 16     (0x10 BER) print out packets sent and received
    # 32     (0x20 filter) search filter processing
    # 64     (0x40 config) configuration file processing
    # 128    (0x80 ACL) access control list processing
    # 256    (0x100 stats) connections, LDAP operations, results (recommended)
    # 512    (0x200 stats2) stats log entries sent
    # 1024   (0x400 shell) print communication with shell backends
    # 2048   (0x800 parse) entry parsing
    SLAPD = Popen(["nixenv/libexec/slapd",
                   "-f", "etc/openldap/slapd.conf",
                   "-d", "stats",
                   "-s", "0",
                   "-h", "ldapi://var%2Frun%2Fldapi"], stdout=PIPE, stderr=PIPE)

    # wait for ldap to appear
    waited = 0
    while True:
        try:
            LDAP = LDAPObject('ldapi://var%2Frun%2Fldapi')
            LDAP.bind_s('cn=root,o=o', 'secret')
        except:
            if waited > 10:
                tearDownModule()
                raise
            time.sleep(0.1)
            waited = waited + 1
        else:
            break

    # add base dn
    try:
        LDAP.add_s('o=o', (('o', 'o'),
                           ('objectClass', 'organization'),))
    except:
        tearDownModule()
        raise


def tearDownModule():
    """make sure ldap is killed before we return
    """
    global SLAPD
    SLAPD.kill()
    SLAPD.wait()


class TestLdapConnectivity(TestCase):
    """A simple test to ensure ldap is running and binding works
    """
    def test_connectivity(self):
        global LDAP
        LDAP.bind_s('cn=root,o=o', 'secret')
        self.assertEqual(LDAP.whoami_s(), 'dn:cn=root,o=o')


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
        global LDAP
        self.ldap = LDAP
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
            except ldap.LDAPError:
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
        self.assertEqual(sorted((self.con[dn] for dn in self.ENTRIES),
                                key=lambda x: x.name),
                         sorted(self.con.values(),
                                key=lambda x: x.name))

    def test_items(self):
        self.assertEqual(sorted((dn, self.con[dn]) for dn in self.ENTRIES),
                         sorted(self.con.items()))
