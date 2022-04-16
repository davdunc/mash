%global pkgname mash

Name:		%{pkgname}
Summary:	 A set of Python3 service based processes for Image Release automation
Version:	 11.2.0
Release: 	 1
License:	 GPLv3
URL:		 https://github.com/SUSE-Enceladus/%{name}
Source0:	 %{url}/archive/v%{version}/%{srcname}-%{version}.tar.gz
BuildArch:	 noarch

BuildRequires: python3-devel

%description
MASH provides a set of Python3 service based processes for Image Release automation into the Public Cloud Frameworks. Amazon EC2, Google Compute Engine and Microsoft Azure are currently supported.

%prep
%setup -q -n %{name}-%{version}

%build

%install
rm -rf $RPM_BUILD_ROOT

%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%license LICENSE
%doc README.md


%changelog
* Fri Apr 15 2022 Duncan <davdunc@3c06303f730c.ant.amazon.com> -
- Initial build.
