@echo off
taskkill /IM sshd.exe /T
ping 127.0.0.1 /n 3 > NUL 2> NUL
taskkill /IM sshd.exe /F
