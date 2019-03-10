
cd .\vnd.microsoft-apps

..\..\zip.exe -0 vnd.microsoft-apps.zip mimetype

..\..\zip.exe -r vnd.microsoft-apps.zip *

cd ..

move /Y .\vnd.microsoft-apps\vnd.microsoft-apps.zip ..\gDriveOOo\vnd.microsoft-apps.odb
