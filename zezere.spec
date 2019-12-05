Name:          zezere
Version:       0.1
Release:       2%{?dist}
Summary:       A provisioning service for Fedora IoT
License:       MIT
URL:           https://github.com/fedora-iot/zezere
Source0:       https://github.com/fedora-iot/zezere/archive/v%{version}.tar.gz#/%{name}-%{version}.tar.gz
Patch0:        0001-add-setup.py.patch

BuildArch: noarch
BuildRequires: python3-devel
BuildRequires: python3-setuptools

%description
Zezere is a provisioning service for Fedora IoT. It can be used for deploying
Fedora IoT to devices without needing a physical console.

%prep
%autosetup -p1

%build
%py3_build

%install
%py3_install

%files
%license LICENSE
%{python3_sitelib}/zezere/
%{python3_sitelib}/zezere-*

%changelog
* Thu Dec  5 2019 Peter Robinson <pbrobinson@fedoraproject.org> 0.1-2
- Review fixes and updates

* Thu Dec  5 2019 Peter Robinson <pbrobinson@fedoraproject.org> 0.1-1
- Initial package
