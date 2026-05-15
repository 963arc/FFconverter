Name:           FFConverter
Version:        1.0
Release:        1%{?dist}
Summary:        Simple Video, Audio, and Image Converter for Linux

License:        GPL-3.0-or-later
URL:            https://github.com/963arc/FFConverter
Source0:        %{name}-%{version}.tar.gz

Requires:       python3
Requires:       python3-pip
Requires:       python3-tkinter
Requires:       python3-pystray
Requires:       python3-pillow
Requires:       python3-six
Recommends:     ffmpeg

BuildRequires:  /bin/true

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
mkdir -p %{buildroot}%{_datadir}/applications
mkdir -p %{buildroot}%{_datadir}/icons/hicolor/256x256/apps
mkdir -p %{buildroot}%{_datadir}/licenses/FFConverter

# Install main script
install -m 755 ffc.py %{buildroot}%{_bindir}/FFConverter
install -m 755 run.sh %{buildroot}%{_bindir}/ffconverter-run

# Install desktop file
install -m 644 usr/share/applications/ffconverter.desktop %{buildroot}%{_datadir}/applications/

# Install icon
install -m 644 usr/share/icons/hicolor/256x256/ffconverter.png %{buildroot}%{_datadir}/icons/hicolor/256x256/apps/ffconverter.png

# Install license
install -m 644 LICENSE %{buildroot}%{_datadir}/licenses/FFConverter/

%files
%{_bindir}/FFConverter
%{_bindir}/ffconverter-run
%{_datadir}/applications/ffconverter.desktop
%{_datadir}/icons/hicolor/256x256/apps/ffconverter.png
%{_datadir}/licenses/FFConverter/LICENSE

%changelog
* Thu May 15 2026 369ARC <email@369arc.com> - 1.0-1
- Initial RPM package
- Added ffmpeg as Recommends (optional dependency)