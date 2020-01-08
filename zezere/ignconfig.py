from typing import Union, Mapping, List, Optional, Any, Dict

from abc import ABC, abstractmethod
import base64
import hashlib


# Used for type assertions
# https://github.com/python/typing/issues/182
JSON = Union[str, int, float, bool, None,
             Mapping[str, Any], List[Any]]


# Helper
class IgnitionConfigObjectType(ABC):
    @abstractmethod
    def generate_config(self) -> JSON:
        pass  # pragma: no cover

    def recursive_generate_config(self, value):
        return list(
            map(
                lambda x: x.generate_config(),
                value,
            )
        )


class AttributeIgnitionConfigObjectType(IgnitionConfigObjectType):
    def generate_config(self) -> JSON:
        cfg = {}
        for attr in dir(self):
            if attr.startswith('_'):
                continue
            val = getattr(self, attr)
            if callable(val):
                continue
            if val is None:
                continue
            if (isinstance(val, list)
                    and len(val) > 0
                    and isinstance(val[0], IgnitionConfigObjectType)):
                val = [elem.generate_config() for elem in val]
            cfg[attr] = val
        return cfg


class FileContents(IgnitionConfigObjectType):
    source: str
    digest: Optional[str] = None
    compression: Optional[str] = None

    SOURCE_SCHEMES = ('http://', 'https://', 's3:', 'tftp://')

    def __init__(self,
                 sourceURL: Optional[str] = None,
                 digest: Optional[str] = None,
                 contents: Optional[bytes] = None,
                 compression: Optional[str] = None):
        if sourceURL is not None and contents is not None:
            raise ValueError("Instantiating with source and contents")
        if sourceURL is not None:
            if sourceURL.startswith("http://") and digest is None:
                raise ValueError("HTTP URL included without verification")
            if not sourceURL.startswith(FileContents.SOURCE_SCHEMES):
                raise ValueError("Source has unsupported scheme")
        if compression is not None:
            if compression != "gzip":
                raise ValueError("Not-allowed compression method provided")
            if sourceURL is not None and sourceURL.startswith("s3:"):
                raise ValueError("Compression is not allowed with s3 source")
            self.compression = compression
        if contents is not None:
            computed_digest = hashlib.sha512(contents).hexdigest()
            if digest is not None and digest != computed_digest:
                raise ValueError("Digest does not match recomputed digest")
            contents = base64.b64encode(contents)
            self.source = \
                f"data:text/plain;charset=utf-8;base64,{contents.decode()}"
            self.digest = computed_digest
        elif sourceURL is not None:
            self.source = sourceURL
            self.digest = digest
        else:
            raise ValueError("Instantiating without source and contents")

    def generate_config(self) -> JSON:
        cfg: Dict[str, Any] = {
            "source": self.source,
        }
        if self.compression is not None:
            cfg["compression"] = self.compression
        if self.digest is not None:
            cfg['verification'] = {
                "hash": f"sha512-{self.digest}"
            }
        return cfg


class PasswdUser(AttributeIgnitionConfigObjectType):
    name: str
    sshAuthorizedKeys: Optional[List[str]] = None
    uid: Optional[int] = None
    gecos: Optional[str] = None
    homeDir: Optional[str] = None
    noCreateHome: Optional[bool] = None
    primaryGroup: Optional[str] = None
    groups: Optional[List[str]] = None
    noUserGroup: Optional[bool] = None
    shell: Optional[str] = None
    system: Optional[bool] = None

    def __init__(self, name: str):
        self.name = name


class PasswdGroup(AttributeIgnitionConfigObjectType):
    name: str
    gid: Optional[int] = None
    system: Optional[bool] = None

    def __init__(self, name: str):
        self.name = name


class SystemdUnitDropin(AttributeIgnitionConfigObjectType):
    name: str
    contents: str

    def __init__(self, name: str, contents: str):
        self.name = name
        self.contents = contents


class SystemdUnit(AttributeIgnitionConfigObjectType):
    name: str
    enabled: Optional[bool] = None
    mask: Optional[bool] = None
    contents: Optional[str] = None
    dropins: List[SystemdUnitDropin]

    def __init__(self, name: str):
        self.name = name
        self.dropins = []

    def add_dropin(self, dropin: SystemdUnitDropin):
        self.dropins.append(dropin)


# Top-level
class IgnitionConfig(IgnitionConfigObjectType):
    CFGVERSION = "3.0.0"

    units: List[SystemdUnit]
    users: List[PasswdUser]
    groups: List[PasswdGroup]
    config_merges: List[FileContents]

    def __init__(self):
        super()
        self.units = []
        self.users = []
        self.groups = []
        self.config_merges = []

    def add_unit(self, unit: SystemdUnit):
        self.units.append(unit)

    def add_user(self, user: PasswdUser):
        self.users.append(user)

    def add_group(self, group: PasswdGroup):
        self.groups.append(group)

    def add_config_merge(self, config: FileContents):
        self.config_merges.append(config)

    def generate_config(self) -> JSON:
        return {
            "ignition": {
                "version": IgnitionConfig.CFGVERSION,
                "config": {
                    "merges": self.recursive_generate_config(
                        self.config_merges),
                },
            },
            "systemd": {
                "units": self.recursive_generate_config(self.units),
            },
            "passwd": {
                "users": self.recursive_generate_config(self.users),
                "groups": self.recursive_generate_config(self.groups),
            },
        }
