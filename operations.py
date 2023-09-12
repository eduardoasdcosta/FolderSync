import os, shutil, filecmp
import checksumdir 
import datetime

def writeLogs(logFile, event, type, item):

    try:
        if event == "start":
            string = "=================================================================\n" + str(datetime.datetime.now()) + " - Starting program."
            logFile.writelines(string + "\n")
            print(string)

        elif event == "delete":
            
            string = str(datetime.datetime.now()) + " - Deleted " + type + " '" + item + "'."
            logFile.writelines(string + "\n")
            print(string)

        elif event == "copy":
            
            string = str(datetime.datetime.now()) + " - Copied " + type + " '" + item + "'."
            logFile.writelines(string + "\n")
            print(string)

        elif event == "error":

            logFile.writelines(item + "\n")
            print(item)

        elif event == "rename":

            string = str(datetime.datetime.now()) + " - Renamed " + type + " '" + item + "'."
            logFile.writelines(string + "\n")
            print(string)
    
    except Exception as error:
        print("Exception thrown writing logs: " + repr(error))


def getFilePathsRecursively(source):

    filePaths = []

    for path, _, files in os.walk(source):
        for name in files:
            filePaths.append(os.path.join(path, name))

    return filePaths


def copyFile(source, target, logFile):

    try:
        shutil.copy(source, target)
    except Exception as error:
        writeLogs(logFile, "error", None, "Exception thrown copying file: " + repr(error))  
    else:
        writeLogs(logFile, "copy", "file", source)


def copyDirectory(source, target, logFile):

    try:
        shutil.copytree(source, target)
    except Exception as error:
        writeLogs(logFile, "error", None, "Exception thrown copying directory: " + repr(error))   
    else:
        writeLogs(logFile, "copy", "dir", source)
        copiedFiles = getFilePathsRecursively(source)
        for file in copiedFiles:
            writeLogs(logFile, "copy", "file", file)


def copyItem(itemPath, targetPath, item, logFile):

    if os.path.isfile(itemPath):
        copyFile(itemPath, targetPath, logFile)
    else:
        copyDirectory(itemPath, targetPath + "/" + item, logFile)


def deleteFile(file, logFile):
    
    try:
        os.remove(file)
    except Exception as error:
        writeLogs(logFile, "error", None, "Exception thrown deleting file: " + repr(error))  
    else:
        writeLogs(logFile, "delete", "file", file)


def deleteDirectory(dir, logFile):

    copiedFiles = getFilePathsRecursively(dir)

    try:
        shutil.rmtree(dir)
    except Exception as error:
        writeLogs(logFile, "error", None, "Exception thrown deleting directory: " + repr(error))  
    else:
        writeLogs(logFile, "delete", "dir", dir)
        for file in copiedFiles:
            writeLogs(logFile, "delete", "file", file)


def deleteItem(itemPath, logFile):

    if os.path.isfile(itemPath):
        deleteFile(itemPath, logFile)
    else:
        deleteDirectory(itemPath, logFile)


def checkFileRename(sourcePath, sourceList, replicaPath, replicaList, sourceFile, replicaFile, logFile):

    oldName = replicaPath + '/' + replicaFile
    newName = replicaPath + '/' + sourceFile

    if filecmp.cmp(sourcePath + '/' + sourceFile, replicaPath + '/' + replicaFile, True):
        try:
            os.rename(oldName, newName)

        except Exception as error:
            writeLogs(logFile, "error", None, "Exception thrown renaming file: " + repr(error))  
        
        else:
            writeLogs(logFile, "rename", "file", oldName + "' to '" + newName)
            sourceList.remove(sourceFile)
            replicaList.remove(replicaFile)


def checkDirRename(sourcePath, replicaPath, sourceDirectory, sourceDirectories, replicaDirectory, replicaDirectories, logFile):
    if checksumdir.dirhash(sourcePath + '/' + sourceDirectory) == checksumdir.dirhash(replicaPath + '/' + replicaDirectory):

        oldName = replicaPath + '/' + replicaDirectory
        newName = replicaPath + '/' + sourceDirectory

        try:
            os.rename(oldName, newName)

        except Exception as error:
            writeLogs(logFile, "error", None, "Exception thrown renaming directory: " + repr(error)) 

        else:
            writeLogs(logFile, "rename", "dir", oldName + "' to '" + newName)
            sourceDirectories.remove(sourceDirectory)
            replicaDirectories.remove(replicaDirectory)
            
            #this is required for the specific case that a file contained in this directory is also renamed
            subDirectoriesComparison = compareDirectories(sourcePath, replicaPath)
            syncDirs(subDirectoriesComparison, logFile)


def checkIfDirectory(item, itemPath, itemList, dirList):
    if os.path.isdir(itemPath + '/' + item):
        dirList.append(item)
        itemList.remove(item)      


def detectItemRename(sourcePath, sourceList, replicaPath, replicaList, subDirs, logFile):

    sourceDirectories = []
    replicaDirectories = []

    for sourceItem in sourceList[:]:
        checkIfDirectory(sourceItem, sourcePath, sourceList, sourceDirectories)
    
    for replicaItem in replicaList[:]:
        checkIfDirectory(replicaItem, replicaPath, replicaList, replicaDirectories)

    for sourceFile in sourceList[:]:
        for replicaFile in replicaList[:]:
            checkFileRename(sourcePath, sourceList, replicaPath, replicaList, sourceFile, replicaFile, logFile)

    for sourceDirectory in sourceDirectories[:]:
        for replicaDirectory in replicaDirectories[:]:
            checkDirRename(sourcePath, replicaPath, sourceDirectory, sourceDirectories, replicaDirectory, replicaDirectories, subDirs, logFile)

    #add back to original lists the directories that weren't renamed
    sourceList.extend(sourceDirectories)
    replicaList.extend(replicaDirectories)


def syncDirs(comparison, logFile):
    
    #if an item was renamed, there is no need to delete and copy it
    detectItemRename(comparison.left, comparison.left_only, comparison.right, comparison.right_only, comparison.subdirs.values(), logFile)

    for diffFile in comparison.diff_files:
        copyItem(comparison.left + '/' + diffFile, comparison.right, diffFile, logFile)

    for sourceItem in comparison.left_only:
        copyItem(comparison.left + '/' + sourceItem, comparison.right, sourceItem, logFile)
    
    for replicaItem in comparison.right_only:
        deleteItem(comparison.right + '/' + replicaItem, logFile)

    for funnyItem in comparison.common_funny:
        deleteItem(comparison.right + '/' + funnyItem, logFile)
        copyItem(comparison.left + '/' + funnyItem, comparison.right, funnyItem, logFile)

    #go to subdirectories recursively
    for dir in comparison.subdirs.values():
        syncDirs(dir, logFile)
        

def compareDirectories(source, replica):
    return filecmp.dircmp(source, replica)