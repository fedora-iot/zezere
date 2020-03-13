Name:          zezere
Version:       0.1
Release:       2%{?dist}
Summary:       A provisioning service for Fedora IoT
License:       MIT
URL:           https://github.com/fedora-iot/zezere
Source0:       https://github.com/fedora-iot/zezere/archive/v%{version}.tar.gz#/%{name}-%{version}.tar.gz

BuildArch: noarch
BuildRequires: python3-devel
BuildRequires: python3-setuptools
BuildRequires: systemd


%description
Zezere is a provisioning service for Fedora IoT. It can be used for deploying
Fedora IoT to devices without needing a physical console.

%package ignition
Summary: Ignition client for Zezere
Requires: python3-setuptools
Requires: ignition

%description ignition
An Ignition client for Zezere managed systems.

%prep
%autosetup -p1

%build
%py3_build

%install
%py3_install
install zezere_ignition/__init__.py %{buildroot}/usr/bin/zezere-ignition
chmod +x %{buildroot}/usr/bin/zezere-ignition
mkdir -p %{buildroot}%{_unitdir}
install zezere_ignition/zezere_ignition.* %{buildroot}%{_unitdir}/
mkdir -p %{buildroot}%{_sharedstatedir}/zezere

%files
%license LICENSE
%{_sharedstatedir}/zezere
%{_bindir}/zezere-manage
%{python3_sitelib}/zezere/
%{python3_sitelib}/zezere-*

%files ignition
%{_bindir}/zezere-ignition
%{_unitdir}/*

%changelog
* Thu Dec  5 2019 Peter Robinson <pbrobinson@fedoraproject.org> 0.1-2
- Review fixes and updates

* Thu Dec  5 2019 Peter Robinson <pbrobinson@fedoraproject.org> 0.1-1
- Initial package
