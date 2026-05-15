%global debug_package %{nil}
%global __spec_install_post %{lua: print(""); }

Name:           FFConverter
Version:        1.0
Release:        1%{?dist}
Summary:        Simple Video, Audio, and Image Converter for Linux

License:        GPL-3.0-or-later
URL:            https://github.com/963arc/FFConverter
Source0:        /home/x/rpmbuild/SOURCES/FFConverter-1.0.tar.gz

Requires:       python3
Requires:       python3-pip
Requires:       python3-tkinter
Requires:       python3-pystray
Requires:       python3-pillow
Requires:       python3-six
Requires:       python3-gobject
Requires:       libappindicator-gtk3
Recommends:     ffmpeg

BuildRequires:  make

%description
FFConverter is a simple, portable video, audio, and image converter for Linux.
Built with Python and FFmpeg, it provides an easy-to-use graphical interface
for converting between various media formats.

%prep
%setup -q

%build
# No compilation needed for Python

%install
# Create directories
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_mandir}/man1
mkdir -p %{buildroot}%{_datadir}/ffconverter
mkdir -p %{buildroot}%{_datadir}/applications
mkdir -p %{buildroot}%{_datadir}/icons/hicolor/256x256/apps
mkdir -p %{buildroot}%{_datadir}/licenses/FFConverter

# Install main script to share directory (for tray icon access)
install -m 755 ffc.py %{buildroot}%{_datadir}/ffconverter/
install -m 755 run.sh %{buildroot}%{_datadir}/ffconverter/
install -m 644 ffconverter.png %{buildroot}%{_datadir}/ffconverter/

# Create wrapper in bin
echo '#!/bin/bash' > %{buildroot}%{_bindir}/FFConverter
echo 'python3 %{_datadir}/ffconverter/ffc.py "$@"' >> %{buildroot}%{_bindir}/FFConverter
chmod +x %{buildroot}%{_bindir}/FFConverter

# Install desktop file
install -m 644 usr/share/applications/ffconverter.desktop %{buildroot}%{_datadir}/applications/

# Install icon
install -m 644 usr/share/icons/hicolor/256x256/ffconverter.png %{buildroot}%{_datadir}/icons/hicolor/256x256/apps/ffconverter.png

# Install license
install -m 644 LICENSE %{buildroot}%{_datadir}/licenses/FFConverter/

%files
%{_bindir}/FFConverter
%{_datadir}/ffconverter/ffc.py
%{_datadir}/ffconverter/run.sh
%{_datadir}/ffconverter/ffconverter.png
%{_datadir}/applications/ffconverter.desktop
%{_datadir}/icons/hicolor/256x256/apps/ffconverter.png
%{_datadir}/licenses/FFConverter/LICENSE

%changelog
* Thu May 15 2026 369ARC <email@369arc.com> - 1.0-1
- Initial RPM package
- Added ffmpeg as Recommends (optional dependency)