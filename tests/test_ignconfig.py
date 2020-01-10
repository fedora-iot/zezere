from . import TestCase

from zezere import ignconfig


class IgnConfigTest(TestCase):
    def test_filecontents_init_both_sources(self):
        with self.assertRaises(ValueError) as ex:
            ignconfig.FileContents(
                sourceURL="foo", digest=None, contents=b"foo", compression=None
            )
        self.assertEqual(ex.exception.args[0], "Instantiating with source and contents")

    def test_filecontents_init_sourceurl_http_no_digest(self):
        with self.assertRaises(ValueError) as ex:
            ignconfig.FileContents(
                sourceURL="http://foo", digest=None, contents=None, compression=None
            )
        self.assertEqual(ex.exception.args[0], "HTTP URL included without verification")

    def test_filecontents_init_sourceurl_invalid_scheme(self):
        with self.assertRaises(ValueError) as ex:
            ignconfig.FileContents(
                sourceURL="nobody://foo", digest=None, contents=None, compression=None
            )
        self.assertEqual(ex.exception.args[0], "Source has unsupported scheme")

    def test_filecontents_init_compression_non_gzip(self):
        with self.assertRaises(ValueError) as ex:
            ignconfig.FileContents(
                sourceURL="https://foo", digest=None, contents=None, compression="null"
            )
        self.assertEqual(
            ex.exception.args[0], "Not-allowed compression method provided"
        )

    def test_filecontents_init_compression_s3(self):
        with self.assertRaises(ValueError) as ex:
            ignconfig.FileContents(
                sourceURL="s3://foo", digest=None, contents=None, compression="gzip"
            )
        self.assertEqual(
            ex.exception.args[0], "Compression is not allowed with s3 source"
        )

    def test_filecontents_init_contents_invalid_digest(self):
        with self.assertRaises(ValueError) as ex:
            ignconfig.FileContents(
                sourceURL=None, digest="bar", contents=b"foo", compression=None
            )
        self.assertEqual(
            ex.exception.args[0], "Digest does not match recomputed digest"
        )

    def test_filecontents_init_no_source_or_contents(self):
        with self.assertRaises(ValueError) as ex:
            ignconfig.FileContents(
                sourceURL=None, digest=None, contents=None, compression=None
            )
        self.assertEqual(
            ex.exception.args[0], "Instantiating without source and contents"
        )

    def test_filecontents_init_contents(self):
        ctsobj = ignconfig.FileContents(
            sourceURL=None, digest=None, contents=b"foo", compression=None
        )
        self.assertIsNotNone(ctsobj)
        self.assertIsNone(ctsobj.compression)
        self.assertEqual(ctsobj.source, "data:text/plain;charset=utf-8;base64,Zm9v")
        self.assertEqual(
            ctsobj.digest,
            "f7fbba6e0636f890e56fbbf3283e524c6fa3204ae298382d624741d0dc663832"
            "6e282c41be5e4254d8820772c5518a2c5a8c0c7f7eda19594a7eb539453e1ed7",
        )
        self.assertEqual(
            ctsobj.generate_config(),
            {
                "source": "data:text/plain;charset=utf-8;base64,Zm9v",
                "verification": {
                    "hash": "sha512-f7fbba6e0636f890e56fbbf3283e524c6fa3204ae298"
                    "382d624741d0dc6638326e282c41be5e4254d8820772c5518a2"
                    "c5a8c0c7f7eda19594a7eb539453e1ed7"
                },
            },
        )

    def test_filecontents_init_sourceurl(self):
        ctsobj = ignconfig.FileContents(
            sourceURL="https://nowhere.foo",
            digest=None,
            contents=None,
            compression="gzip",
        )
        self.assertIsNotNone(ctsobj)
        self.assertEqual(ctsobj.compression, "gzip")
        self.assertEqual(ctsobj.source, "https://nowhere.foo")
        self.assertIsNone(ctsobj.digest)
        self.assertEqual(
            ctsobj.generate_config(),
            {"compression": "gzip", "source": "https://nowhere.foo"},
        )

    def test_passwd_user_init(self):
        obj = ignconfig.PasswdUser("myusername")
        self.assertIsNotNone(obj)
        self.assertEqual(obj.generate_config(), {"name": "myusername"})

    def test_passwd_user_attributes(self):
        obj = ignconfig.PasswdUser("myusername")
        self.assertIsNotNone(obj)
        obj.uid = 50
        obj.gecos = "My users name"
        obj.noCreateHome = True
        self.assertEqual(
            obj.generate_config(),
            {
                "name": "myusername",
                "uid": 50,
                "gecos": "My users name",
                "noCreateHome": True,
            },
        )

    def test_passwd_group_init(self):
        obj = ignconfig.PasswdGroup("mygroup")
        self.assertIsNotNone(obj)
        self.assertEqual(obj.generate_config(), {"name": "mygroup"})

    def test_systemd_unit_dropin_init(self):
        obj = ignconfig.SystemdUnitDropin("dropinname", "[Service]")
        self.assertIsNotNone(obj)
        self.assertEqual(
            obj.generate_config(), {"name": "dropinname", "contents": "[Service]"}
        )

    def test_systemd_unit_init(self):
        obj = ignconfig.SystemdUnit("unitname")
        self.assertIsNotNone(obj)
        self.assertEqual(obj.generate_config(), {"name": "unitname", "dropins": []})

    def test_systemd_unit_with_dropins(self):
        dropin1 = ignconfig.SystemdUnitDropin("dropin1", "[Service]Contents1")
        dropin2 = ignconfig.SystemdUnitDropin("dropin2", "[Service]Contents2")
        obj = ignconfig.SystemdUnit("testunit")
        self.assertIsNotNone(obj)
        obj.add_dropin(dropin1)
        obj.add_dropin(dropin2)
        self.assertEqual(
            obj.generate_config(),
            {
                "name": "testunit",
                "dropins": [
                    {"name": "dropin1", "contents": "[Service]Contents1"},
                    {"name": "dropin2", "contents": "[Service]Contents2"},
                ],
            },
        )

    def test_ignition_config_init(self):
        obj = ignconfig.IgnitionConfig()
        self.assertIsNotNone(obj)
        self.assertEqual(
            obj.generate_config(),
            {
                "ignition": {
                    "version": ignconfig.IgnitionConfig.CFGVERSION,
                    "config": {"merges": []},
                },
                "systemd": {"units": []},
                "passwd": {"users": [], "groups": []},
            },
        )

    def test_ignition_config_full(self):
        obj = ignconfig.IgnitionConfig()
        self.assertIsNotNone(obj)

        tuser1 = ignconfig.PasswdUser("testuser1")
        tuser1.uid = 50
        tuser1.gecos = "Testing User One"
        obj.add_user(tuser1)

        tuser2 = ignconfig.PasswdUser("testuser2")
        tuser2.groups = ["group1", "group2"]
        tuser2.noUserGroup = True
        obj.add_user(tuser2)

        tgroup1 = ignconfig.PasswdGroup("testgroup1")
        tgroup1.gid = 42
        obj.add_group(tgroup1)

        tgroup2 = ignconfig.PasswdGroup("testgroup2")
        tgroup2.system = True
        obj.add_group(tgroup2)

        unit1 = ignconfig.SystemdUnit("firstunit")
        unit1.enabled = True
        unit1.contents = "units contents"
        unit1.add_dropin(
            ignconfig.SystemdUnitDropin("unit1dropin1", "First dropins contents")
        )
        unit1.add_dropin(
            ignconfig.SystemdUnitDropin("unit1dropin2", "Second dropins contents")
        )
        obj.add_unit(unit1)

        unit2 = ignconfig.SystemdUnit("secondunit")
        unit2.mask = True
        unit2.enabled = False
        obj.add_unit(unit2)

        cfgref = ignconfig.FileContents("https://myconfig.json")
        obj.add_config_merge(cfgref)

        cfgcts = ignconfig.FileContents(contents=b"foo")
        obj.add_config_merge(cfgcts)

        self.maxDiff = None
        self.assertEqual(
            obj.generate_config(),
            {
                "ignition": {
                    "version": ignconfig.IgnitionConfig.CFGVERSION,
                    "config": {
                        "merges": [
                            {"source": "https://myconfig.json"},
                            {
                                "source": "data:text/plain;charset=utf-8;"
                                "base64,Zm9v",
                                "verification": {
                                    "hash": "sha512-f7fbba6e0636f890e56fbbf3283e5"
                                    "24c6fa3204ae298382d624741d0dc6638326"
                                    "e282c41be5e4254d8820772c5518a2c5a8c0"
                                    "c7f7eda19594a7eb539453e1ed7"
                                },
                            },
                        ]
                    },
                },
                "systemd": {
                    "units": [
                        {
                            "name": "firstunit",
                            "enabled": True,
                            "contents": "units contents",
                            "dropins": [
                                {
                                    "name": "unit1dropin1",
                                    "contents": "First dropins contents",
                                },
                                {
                                    "name": "unit1dropin2",
                                    "contents": "Second dropins contents",
                                },
                            ],
                        },
                        {
                            "name": "secondunit",
                            "mask": True,
                            "enabled": False,
                            "dropins": [],
                        },
                    ]
                },
                "passwd": {
                    "users": [
                        {"name": "testuser1", "uid": 50, "gecos": "Testing User One"},
                        {
                            "name": "testuser2",
                            "groups": ["group1", "group2"],
                            "noUserGroup": True,
                        },
                    ],
                    "groups": [
                        {"name": "testgroup1", "gid": 42},
                        {"name": "testgroup2", "system": True},
                    ],
                },
            },
        )
