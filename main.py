import sys, os, gc
import time

import operations

#Current code limitations:
#
# 1: moving items to another directory is not detected as a rename
# 2: if a directory is renamed, and a subfile is changed, the whole directory and its contents will be deleted and then copied to replica


def invalidArguments(argument, index):
    print("Invalid parameter for " + argument + " - It cannot be '" + sys.argv[index] + "'")
    exit()


def argumentsValidation():

    if len(sys.argv) < 5:
        print("Program usage: python main.py [source folder path] [replica folder path] [synchronization interval in seconds] [log file path]")
        exit()

    if os.path.isdir(sys.argv[1]):
        sourceRoot = sys.argv[1]
    else:
        invalidArguments("source folder path", 1)

    if os.path.isdir(sys.argv[2]):
        replicaRoot = sys.argv[2]
    else:
        invalidArguments("replica folder path", 2)

    try:
        if (int(sys.argv[3])) > 0:
            syncInterval = int(sys.argv[3])
        else:
            raise ValueError('integer must be positive')
    except Exception as error:
        print("Exception thrown reading argument 3: " + repr(error))
        invalidArguments("synchronization interval in seconds", 3)

    try:
        logFile = open(sys.argv[4], "a")
    except Exception as error:
        print("Exception thrown reading argument 4: " + repr(error))
        invalidArguments("log file path", 4)
    else:
        operations.writeLogs(logFile, "start", None, None)

    return sourceRoot, replicaRoot, syncInterval, logFile


def cleanAndWait(directoriesComparison, logFile, syncInterval):
    
    del directoriesComparison
    gc.collect()
    logFile.close()
    time.sleep(syncInterval)
    try:
        return open(sys.argv[4], "a")
    except Exception as error:
        print("Exception thrown opening log file: " + repr(error))


def main():

    sourceRoot, replicaRoot, syncInterval, logFile = argumentsValidation()

    while True:
        directoriesComparison = operations.compareDirectories(sourceRoot, replicaRoot)
        operations.syncDirs(directoriesComparison, logFile)
        logFile = cleanAndWait(directoriesComparison, logFile, syncInterval)


if __name__ == "__main__":
    main()