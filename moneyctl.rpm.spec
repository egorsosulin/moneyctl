Name:           moneyctl
Version:        0.1.0
Release:        1%{?dist}
License:        GPL
Summary:        CLI finance management application based on Beancount

%description
CLI finance management application based on Beancount

%define _build_id_links none

%install
mkdir -p %{buildroot}%{_bindir}
install -m 755 %{name} %{buildroot}%{_bindir}/%{name}


%files
%{_bindir}/%{name}
