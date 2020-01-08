import rules


# Rules and predicates for Devices
@rules.predicate
def is_device_owner(user, device):
    return device.owner == user


@rules.predicate
def is_owned_device(user, device):
    return device.owner is not None


owns_device = rules.is_authenticated & is_device_owner
can_claim = rules.is_authenticated & ~is_owned_device


# Rules and predicates for SSHKeys
@rules.predicate
def is_sshkey_owner(user, sshkey):
    return sshkey.owner == user


owns_sshkey = rules.is_authenticated & is_sshkey_owner
