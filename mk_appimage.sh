#!/bin/bash

set -e # abort on error

# python3-venv is needed to avoid an error message:
# The virtual environment was not created successfully because ensurepip is not
# available.  On Debian/Ubuntu systems, you need to install the python3-venv
apt install python3-venv

# desktop-file-validate is needed by appimagetool
apt install desktop-file-utils

buildroot=/tmp/appim$$
MyApp=OcisImport
yourscript=ocis-import.py
mkdir -p $buildroot/AppImageKit/$MyApp.AppDir/usr/bin
cd $buildroot
wget https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage
chmod a+x appimagetool-x86_64.AppImage

# install python dependencies
python3 -m venv $buildroot/python-appimage-env
source $buildroot/python-appimage-env/bin/activate
pip install msgpack
deactivate
pylibdir=$(cd python-appimage-env; echo lib/python*)
mkdir -p $buildroot/AppImageKit/$MyApp.AppDir/usr/$pylibdir/site-packages
cp -r $buildroot/python-appimage-env/$pylibdir/site-packages/* $buildroot/AppImageKit/$MyApp.AppDir/usr/$pylibdir/site-packages/

# install python tool
git clone https://github.com/esgarov/Daten-Import-in-Ocis
cp $buildroot/Daten-Import-in-Ocis/$yourscript AppImageKit/$MyApp.AppDir/usr/bin/
chmod a+x AppImageKit/$MyApp.AppDir/usr/bin/$yourscript

cat << EOF > $buildroot/AppImageKit/$MyApp.AppDir/myApp.desktop
[Desktop Entry]
Type=Application
Name=$MyApp
Exec=AppRun
Icon=myapp-icon
Categories=Utility;
EOF
cat << EOF > $buildroot/AppImageKit/$MyApp.AppDir/AppRun
#!/bin/bash
HERE="\$(dirname "\$(readlink -f "\${0}")")"
export PYTHONPATH=\${HERE}/usr/$pylibdir/site-packages
python3 \${HERE}/usr/bin/$yourscript "\$@"
EOF
chmod a+x $buildroot/AppImageKit/$MyApp.AppDir/AppRun

# create myapp-icon.png
wget -O $buildroot/AppImageKit/$MyApp.AppDir/myapp-icon.png https://www.iconpacks.net/icons/1/free-cloud-icon-1168-thumb.png
ARCH=x86_64 ./appimagetool-x86_64.AppImage $buildroot/AppImageKit/$MyApp.AppDir
chmod a+x $MyApp-x86_64.AppImage
echo "AppImage created here:"
ls -la $buildroot/$MyApp-x86_64.AppImage
echo ""
echo "Please copy this to a permanent location, and then remove $buildroot"

