
rem cd .\make_odb
rem call .\make_odb.bat
rem cd ..

cd .\oneDriveOOo
..\zip.exe -0 oneDriveOOo.zip mimetype
..\zip.exe -r oneDriveOOo.zip *
cd ..

move /Y .\oneDriveOOo\oneDriveOOo.zip .\oneDriveOOo.oxt
