#!/bin/bash

cd ./oneDriveOOo/
zip -0 oneDriveOOo.zip mimetype
zip -r oneDriveOOo.zip *
cd ..

mv ./oneDriveOOo/oneDriveOOo.zip ./oneDriveOOo.oxt
