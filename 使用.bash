{\rtf1\ansi\ansicpg936\cocoartf2709
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;\f1\fnil\fcharset134 PingFangSC-Regular;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural\partightenfactor0

\f0\fs24 \cf0 @echo off\
\
echo 
\f1 \'bc\'ec\'b2\'e9
\f0 Python
\f1 \'ca\'c7\'b7\'f1\'d2\'d1\'b0\'b2\'d7\'b0
\f0 ...\
where python >nul 2>nul\
if errorlevel 1 (\
    echo 
\f1 \'d5\'fd\'d4\'da\'b0\'b2\'d7\'b0
\f0 Python...\
    powershell -Command "Invoke-WebRequest https://www.python.org/ftp/python/3.9.7/python-3.9.7-amd64.exe -OutFile python-installer.exe"\
    python-installer.exe /quiet InstallAllUsers=1 PrependPath=1\
    del python-installer.exe\
) else (\
    echo Python
\f1 \'d2\'d1\'b0\'b2\'d7\'b0
\f0 \
)\
\
echo 
\f1 \'bc\'ec\'b2\'e9\'cb\'f9\'d0\'e8\'bf\'e2\'ca\'c7\'b7\'f1\'d2\'d1\'b0\'b2\'d7\'b0
\f0 ...\
python -m pip freeze > installed_libraries.txt\
findstr /L /I /G:requirements.txt installed_libraries.txt >nul\
if errorlevel 1 (\
    echo 
\f1 \'d5\'fd\'d4\'da\'b0\'b2\'d7\'b0\'cb\'f9\'d0\'e8\'b5\'c4\'bf\'e2
\f0 ...\
    python -m pip install -r requirements.txt\
) else (\
    echo 
\f1 \'cb\'f9\'d0\'e8\'bf\'e2\'d2\'d1\'b0\'b2\'d7\'b0
\f0 \
)\
\
echo 
\f1 \'b0\'b2\'d7\'b0\'cd\'ea\'b3\'c9\'a3\'ac\'d5\'fd\'d4\'da\'d4\'cb\'d0\'d0
\f0  gui.py\
python gui.py\
exit}