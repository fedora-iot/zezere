try:
    import libvirt
except ImportError:
    libvirt = None
import os
import requests
from unittest import TestCase, skipUnless


TEST_NETWORK_UUID = "5494736a-7424-4e58-8ef7-089c8debc51f"
TEST_NETWORK = """
<network xmlns:dnsmasq='http://libvirt.org/schemas/network/dnsmasq/1.0'>
  <name>zezere-integration</name>
  <uuid>5494736a-7424-4e58-8ef7-089c8debc51f</uuid>
  <forward mode='nat'>
    <nat>
      <port start='1024' end='65535'/>
    </nat>
  </forward>
  <bridge name='virbr-zezere' stp='off' delay='0'/>
  <mac address='52:54:00:70:42:24'/>
  <dns>
    <host ip='%(bootserv_ip)s'>
      <hostname>bootserv</hostname>
    </host>
  </dns>
  <ip address='192.168.42.1' netmask='255.255.255.0'>
    <dhcp>
      <range start='192.168.42.2' end='192.168.42.254'/>
    </dhcp>
  </ip>
  <ip family='ipv6' address='2001:db8:ca2:6::1' prefix='64'>
    <dhcp>
      <range start='2001:db8:ca2:6:1::10' end='2001:db8:ca2:6:1::ff'/>
    </dhcp>
  </ip>
  <dnsmasq:options>
    <dnsmasq:option value='dhcp-option=option:vendor-class,HTTPClient'/>
    <dnsmasq:option
      value='dhcp-option=option:bootfile-name,http://bootserv:8080/netboot/x86_64/initial'/>
  </dnsmasq:options>
</network>
"""

VM = """
<domain type='kvm'>
  <name>%(name)s</name>
  <uuid>%(uuid)s</uuid>
  <metadata>
    <libosinfo:libosinfo xmlns:libosinfo="http://libosinfo.org/xmlns/libvirt/domain/1.0">
      <libosinfo:os id="http://fedoraproject.org/fedora/31"/>
    </libosinfo:libosinfo>
  </metadata>
  <memory unit='KiB'>2097152</memory>
  <currentMemory unit='KiB'>2097152</currentMemory>
  <vcpu placement='static'>2</vcpu>
  <os>
    <type arch='x86_64' machine='pc-q35-4.2'>hvm</type>
    <loader readonly='yes'
            secure='yes'
            type='pflash'>/usr/share/edk2/ovmf/OVMF_CODE.secboot.fd</loader>
    <nvram>/usr/share/edk2/ovmf/OVMF_VARS.secboot.fd</nvram>
  </os>
  <features>
    <acpi/>
    <apic/>
    <vmport state='off'/>
    <smm state='on'/>
  </features>
  <cpu mode='host-model' check='partial'/>
  <clock offset='utc'>
    <timer name='rtc' tickpolicy='catchup'/>
    <timer name='pit' tickpolicy='delay'/>
    <timer name='hpet' present='no'/>
  </clock>
  <on_poweroff>destroy</on_poweroff>
  <on_reboot>restart</on_reboot>
  <on_crash>destroy</on_crash>
  <pm>
    <suspend-to-mem enabled='no'/>
    <suspend-to-disk enabled='no'/>
  </pm>
  <devices>
    <emulator>/usr/bin/qemu-system-x86_64</emulator>
    <disk type='file' device='disk'>
      <driver name='qemu' type='qcow2'/>
      <source file='/var/lib/libvirt/images/fedora31.qcow2'/>
      <target dev='vda' bus='virtio'/>
      <address type='pci' domain='0x0000' bus='0x04' slot='0x00' function='0x0'/>
    </disk>
    <controller type='usb' index='0' model='qemu-xhci' ports='15'>
      <address type='pci' domain='0x0000' bus='0x02' slot='0x00' function='0x0'/>
    </controller>
    <controller type='pci' index='0' model='pcie-root'/>
    <controller type='pci' index='1' model='pcie-root-port'>
      <model name='pcie-root-port'/>
      <target chassis='1' port='0x10'/>
      <address type='pci'
               domain='0x0000'
               bus='0x00'
               slot='0x02'
               function='0x0'
               multifunction='on'/>
    </controller>
    <controller type='pci' index='2' model='pcie-root-port'>
      <model name='pcie-root-port'/>
      <target chassis='2' port='0x11'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x02' function='0x1'/>
    </controller>
    <controller type='pci' index='3' model='pcie-root-port'>
      <model name='pcie-root-port'/>
      <target chassis='3' port='0x12'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x02' function='0x2'/>
    </controller>
    <controller type='pci' index='4' model='pcie-root-port'>
      <model name='pcie-root-port'/>
      <target chassis='4' port='0x13'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x02' function='0x3'/>
    </controller>
    <controller type='pci' index='5' model='pcie-root-port'>
      <model name='pcie-root-port'/>
      <target chassis='5' port='0x14'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x02' function='0x4'/>
    </controller>
    <controller type='pci' index='6' model='pcie-root-port'>
      <model name='pcie-root-port'/>
      <target chassis='6' port='0x15'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x02' function='0x5'/>
    </controller>
    <controller type='pci' index='7' model='pcie-root-port'>
      <model name='pcie-root-port'/>
      <target chassis='7' port='0x16'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x02' function='0x6'/>
    </controller>
    <controller type='virtio-serial' index='0'>
      <address type='pci' domain='0x0000' bus='0x03' slot='0x00' function='0x0'/>
    </controller>
    <controller type='sata' index='0'>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x1f' function='0x2'/>
    </controller>
    <interface type='network'>
      <mac address='52:54:00:42:c2:43'/>
      <source network='zezere-integration'/>
      <model type='virtio'/>
      <boot order='1'/>
      <address type='pci' domain='0x0000' bus='0x01' slot='0x00' function='0x0'/>
    </interface>
    <serial type='pty'>
      <target type='isa-serial' port='0'>
        <model name='isa-serial'/>
      </target>
    </serial>
    <console type='pty'>
      <target type='serial' port='0'/>
    </console>
    <channel type='unix'>
      <target type='virtio' name='org.qemu.guest_agent.0'/>
      <address type='virtio-serial' controller='0' bus='0' port='1'/>
    </channel>
    <input type='mouse' bus='ps2'/>
    <input type='keyboard' bus='ps2'/>
    <memballoon model='virtio'>
      <address type='pci' domain='0x0000' bus='0x05' slot='0x00' function='0x0'/>
    </memballoon>
    <rng model='virtio'>
      <backend model='random'>/dev/urandom</backend>
      <address type='pci' domain='0x0000' bus='0x06' slot='0x00' function='0x0'/>
    </rng>
  </devices>
</domain>
"""


class IntegrationTest(TestCase):
    libvirt_conn = None
    libvirt_net = None

    @classmethod
    @skipUnless(
        os.environ.get("ZEZERE_RUN_INTEGRATION_TEST"), "Not running integration suite"
    )
    def setUpClass(cls):
        if not libvirt:
            raise Exception("Integration tests require libvirt python bindings")

        bootserv_ip = os.getenv("BOOTSERV_IP")
        if not bootserv_ip:
            raise Exception("Integration tests require BOOTSERV_IP")

        # Just checking that the server is available
        resp = requests.get(
            "http://%s:8080/" % bootserv_ip, headers={"Host": "bootserv"}
        )
        resp.raise_for_status()

        # Connect to libvirt
        lvconn = libvirt.open(None)

        # Set up network
        try:
            lvconn.networkLookupByUUIDString(TEST_NETWORK_UUID)
        except libvirt.libvirtError:
            lvconn.networkDefineXML(TEST_NETWORK % {"bootserv_ip": bootserv_ip})
        net = lvconn.networkLookupByUUIDString(TEST_NETWORK_UUID)
        if not net.isActive():
            # Start the network
            net.create()

        # TODO: Build the rest

        # Set class variables for teardown
        cls.libvirt_conn = lvconn
        cls.libvirt_net = net

    @classmethod
    def tearDownClass(cls):
        cls.libvirt_net.destroy()
        cls.libvirt_net.undefine()
        cls.libvirt_conn.close()
        cls.libvirt_conn = None

    def test_foo(self):
        print("Connection: %s" % self.libvirt_conn)
