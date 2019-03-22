#!/bin/bash

cd ./vnd.microsoft-apps/
zip -0 vnd.microsoft-apps.zip mimetype
zip -r vnd.microsoft-apps.zip *
cd ..

mv ./vnd.microsoft-apps/vnd.microsoft-apps.zip ../oneDriveOOo/vnd.microsoft-apps.odb
