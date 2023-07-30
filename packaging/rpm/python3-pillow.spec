%global debug_package %{nil}
%define _disable_source_fetch 0
%global srcname pillow

%if "%{getenv:PYTHON3}" == ""
%global python3 python3
%define package_prefix python3-
%else
%global python3 %{getenv:PYTHON3}
%define package_prefix %{python3}-
%undefine __pythondist_requires
%undefine __python_requires
%define python3_sitearch %(%{python3} -Ic "from sysconfig import get_path; print(get_path('platlib').replace('/usr/local/', '/usr/'))" 2> /dev/null)
%endif


Name:           %{package_prefix}%{srcname}
Version:        10.0.0
Release:        1%{?dist}
Summary:        Python image processing library

# License: see http://www.pythonware.com/products/pil/license.htm
License:        MIT
URL:            http://python-pillow.github.io/
Source0:        https://github.com/python-pillow/Pillow/archive/%{version}/Pillow-%{version}.tar.gz

BuildRequires:  freetype-devel
BuildRequires:  gcc
BuildRequires:  lcms2-devel
BuildRequires:  libimagequant-devel
BuildRequires:  libjpeg-devel
BuildRequires:  libwebp-devel
BuildRequires:  zlib-devel

BuildRequires:  %{package_prefix}devel
BuildRequires:  %{package_prefix}setuptools


%global __provides_exclude_from ^%{python3_sitearch}/PIL/.*\\.so$

%description
Python image processing library, fork of the Python Imaging Library (PIL)

This library provides extensive file format support, an efficient
internal representation, and powerful image processing capabilities.


%package -n %{package_prefix}%{srcname}
Summary:        Python 3 image processing library
%{?python_provide:%python_provide %{package_prefix}%{srcname}}
Provides:       %{package_prefix}imaging = %{version}-%{release}

%description -n %{package_prefix}%{srcname}
Python image processing library, fork of the Python Imaging Library (PIL)

This library provides extensive file format support, an efficient
internal representation, and powerful image processing capabilities.

There are four subpackages: tk (tk interface), qt (PIL image wrapper for Qt),
devel (development) and doc (documentation).


%prep
sha256=`sha256sum %{SOURCE0} | awk '{print $1}'`
if [ "${sha256}" != "535d17e830427bec163027114ded1def9ab0350c99bf1d8cb10535032967f3a5" ]; then
	echo "invalid checksum for %{SOURCE0}"
	exit 1
fi
%autosetup -n Pillow-%{version}

%build
CFLAGS="$RPM_OPT_FLAGS" %{python3} setup.py build

%install
%{python3} setup.py install -O1 --skip-build --root %{buildroot}

%files -n %{package_prefix}%{srcname}
%doc README.md CHANGES.rst
%license docs/COPYING
%{python3_sitearch}/PIL/
%{python3_sitearch}/Pillow-%{version}-py*.egg-info
# simplified build does not shi these:
%exclude %{python3_sitearch}/PIL/_imagingtk*
%exclude %{python3_sitearch}/PIL/ImageTk*
%exclude %{python3_sitearch}/PIL/SpiderImagePlugin*
%exclude %{python3_sitearch}/PIL/ImageQt*
%exclude %{python3_sitearch}/PIL/__pycache__/ImageTk*
%exclude %{python3_sitearch}/PIL/__pycache__/SpiderImagePlugin*
%exclude %{python3_sitearch}/PIL/__pycache__/ImageQt*

%changelog
* Sun Jul 30 2023 Antoine Martin <antoine@xpra.org> - 10.0.0-1
- initial packaging for python prefixed builds
