#
# spec file for package matrix-mautrix-telegram
#
# Copyright (c) 2026 Tomáš Čech
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself unless
# otherwise agreed upon.
#

%global bridge_user matrix-mautrix-telegram
%global bridge_datadir %{_localstatedir}/lib/matrix-mautrix-telegram
%global bridge_confdir %{_sysconfdir}/matrix-mautrix-telegram
%global bridge_logdir %{_localstatedir}/log/matrix-mautrix-telegram
%global goipath go.mau.fi/mautrix-telegram

Name:           matrix-mautrix-telegram
Version:        26.08
Release:        0
Summary:        A Matrix-Telegram puppeting bridge
License:        AGPL-3.0-only
Group:          Productivity/Networking/Chat
URL:            https://github.com/mautrix/telegram
Source0:        https://github.com/mautrix/telegram/archive/refs/tags/v0.2608.0.tar.gz#/mautrix-telegram-%{version}.tar.gz
Source1:        %{name}.service
Source2:        %{name}.sysusers
Source3:        %{name}.tmpfiles
Source4:        vendor.tar.zst
# Security fix: bump golang.org/x/crypto past GO-2026-6354 / GO-2026-6355
# (SSH-channel DoS in x/crypto/ssh; mautrix-telegram doesn't use SSH itself,
# but this closes the dependency-scanner finding at build time).
# Audit performed with govulncheck 1.8.0 + osv-scanner 2.5.1, see
# audit/govulncheck-v26.08.txt and audit/osv-scanner-v26.08.txt in the
# packaging git repository for the full report.
Patch0:         0001-bump-x-crypto-0.56.0-security.patch
BuildRequires:  go1.27
BuildRequires:  olm-devel
BuildRequires:  sysuser-tools
BuildRequires:  zstd
BuildRequires:  gcc-c++
BuildRequires:  libstdc++-devel
%sysusers_requires
%systemd_requires
Requires:       libolm3
Requires:       %{name}-config = %{version}

%description
mautrix-telegram is a Matrix-Telegram puppeting bridge, allowing Matrix and
Telegram users to talk to each other seamlessly, as if they were on the
same platform. It is written in Go using the bridgev2 architecture.

This package builds and runs the bridge as a native systemd service instead
of the upstream Docker container, under a dedicated unprivileged system
user, with configuration and persistent data kept in standard FHS
locations.

%package config
Summary:        Default configuration package for %{name}
Group:          Productivity/Networking/Chat
BuildArch:      noarch

%description config
Placeholder subpackage that owns %{_sysconfdir}/matrix-mautrix-telegram so
the main package can depend on configuration being present without forcing
a specific config generator. The actual config.yaml/registration.yaml are
generated on first start by the bridge binary itself (see README).

%prep
%autosetup -p1 -n mautrix-telegram-%{version} -a4

%build
export GOFLAGS="-mod=vendor -buildmode=pie"
export CGO_ENABLED=1
export GOPATH=%{_builddir}/go
LDFLAGS="-linkmode=external"
LDFLAGS="$LDFLAGS -X main.Tag=v0.2608.0"
LDFLAGS="$LDFLAGS -X main.Commit=3df4c4ae87cab0a590ec0aaa139e0c1361460028"
LDFLAGS="$LDFLAGS -X main.BuildTime=$(date -u +%%Y-%%m-%%dT%%H:%%M:%%SZ)"
go build -mod=vendor -ldflags="$LDFLAGS" -o mautrix-telegram ./cmd/mautrix-telegram

%install
install -D -m 0755 mautrix-telegram %{buildroot}%{_bindir}/matrix-mautrix-telegram
install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/%{name}.service
install -D -m 0644 %{SOURCE2} %{buildroot}%{_sysusersdir}/%{name}.conf
install -D -m 0644 %{SOURCE3} %{buildroot}%{_tmpfilesdir}/%{name}.conf
install -d -m 0750 %{buildroot}%{bridge_confdir}
install -d -m 0750 %{buildroot}%{bridge_datadir}
install -d -m 0750 %{buildroot}%{bridge_logdir}
install -D -m 0644 pkg/connector/example-config.yaml %{buildroot}%{_datadir}/%{name}/example-config.yaml
%sysusers_generate_pre %{SOURCE2} %{bridge_user} %{name}.conf

%pre -f %{bridge_user}.pre
%service_add_pre %{name}.service

%post
%service_add_post %{name}.service
%tmpfiles_create %{_tmpfilesdir}/%{name}.conf

%preun
%service_del_preun %{name}.service

%postun
%service_del_postun %{name}.service

%files
%license LICENSE
%doc CHANGELOG.md ROADMAP.md
%{_bindir}/matrix-mautrix-telegram
%{_unitdir}/%{name}.service
%{_sysusersdir}/%{name}.conf
%{_tmpfilesdir}/%{name}.conf
%dir %attr(0750,%{bridge_user},%{bridge_user}) %{bridge_datadir}
%dir %attr(0750,%{bridge_user},%{bridge_user}) %{bridge_logdir}
%{_datadir}/%{name}/example-config.yaml

%files config
%dir %attr(0750,%{bridge_user},%{bridge_user}) %{bridge_confdir}

%changelog
