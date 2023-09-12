# FolderSync
This program periodically synchronizes uni-directionally two folders: source and replica.

Compiled in python3.11
Requires checksumdir to be installed:
  pip install checksumdir

Program usage: python main.py [source folder path] [replica folder path] [synchronization interval in seconds] [log file path]
Example:

python main.py c:/Source c:/Replica 10 c:/Logs/Logfile


Current code limitations:

1: moving items to another directory is not detected as a rename
2: if a directory is renamed, and a subfile is changed, the whole directory and its contents will be deleted and then copied to replica
