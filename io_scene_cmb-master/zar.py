import struct

def readNullTerminatedString(bytes, offset):
    chars = []
    for i in range(offset, len(bytes)):
        c = bytes[i]
        if c == 0:
            return bytearray(chars).decode('utf-8')
        chars.append(c)

# Class representing a Zar archive.
class Zar:
    def __init__(self, filePath):
        fileHandle = open(filePath, "rb")
        bytes = fileHandle.read()

        self.header = Zar.ZarHeader(bytes)
        self.filetypesSection = Zar.FiletypesSection(bytes, self.header)

        fileIndex = 0
        self.files = []
        for filetype in self.filetypesSection.filetypes:
            for fileInFiletypeIndex in range(filetype.fileCount):
                fileMetadataOffset = self.header.fileMetadataOffset + 8 * fileIndex
                fileMetadataBytes = bytes[fileMetadataOffset:fileMetadataOffset+8]
                (
                    fileSize,
                    filenameOffset,
                ) = struct.unpack("II", fileMetadataBytes)

                filename = readNullTerminatedString(bytes, filenameOffset)

                fileOffsetOffset = filetype.fileListOffset + 4 * fileInFiletypeIndex
                fileOffsetBytes = bytes[fileOffsetOffset:fileOffsetOffset+4]
                (fileOffset,) = struct.unpack("I", fileOffsetBytes)
                fileBytes = bytes[fileOffset:fileOffset+fileSize]

                self.files.append(Zar.File(filename, fileBytes))

                fileIndex += 1


    def __str__(self):
        return '\n\n\n'.join([
            str(self.header),
            str(self.filetypesSection),
            '\n\n'.join(map(lambda file: str(file), self.files))
        ])


    # Helper class for fetching the Zar header from a file.
    class ZarHeader:
        def __init__(self, bytes):
            magicText = bytes[0:4].decode("utf-8")
            assert magicText == "ZAR\1", "Invalid magic text!"

            (
                self.size,
                self.filetypeCount,
                self.fileCount,
                self.filetypesOffset,
                self.fileMetadataOffset,
                self.dataOffset
            ) = struct.unpack("IHHIII", bytes[4:24])

        def __str__(self):
            return '\n'.join([
                "###",
                "ZAR archive header:",
                str(self.size) + " bytes",
                str(self.filetypeCount) + " types",
                str(self.fileCount) + " files",
                "filetypes @ " + str(self.filetypesOffset),
                "file metadata @ " + str(self.fileMetadataOffset),
                "data @ " + str(self.dataOffset),
                "###",
            ])


    # Helper class for fetching the list of filetypes and their associated files.
    class FiletypesSection:
        def __init__(self, bytes, header):
            self.filetypes = []

            filetypesOffset = header.filetypesOffset
            for i in range(header.filetypeCount):
                currentFiletypeOffset = filetypesOffset + 16 * i
                self.filetypes.append(Zar.Filetype(bytes, currentFiletypeOffset))

        def __str__(self):
            return '\n\n'.join(map(lambda filetype: str(filetype), self.filetypes))

    class Filetype:
        def __init__(self, bytes, filetypeOffset):
            filetypeBytes = bytes[filetypeOffset:filetypeOffset+12]
            (
                self.fileCount,
                self.fileListOffset,
                self.typeNameOffset,
            ) = struct.unpack("III", filetypeBytes)

            self.typeName = readNullTerminatedString(bytes, self.typeNameOffset)

        def __str__(self):
            return '\n'.join([
                "===",
                "Filetype \"" + self.typeName + "\":",
                str(self.fileCount) + " files",
                "file list @ " + str(self.fileListOffset),
                "filetype name @ " + str(self.typeNameOffset),
                "===",
            ])

    # Helper class that represents a specific file
    class File:
        def __init__(self, filename, fileBytes):
            self.filename = filename
            self.fileBytes = fileBytes

        def __str__(self):
            return '\n'.join([
                "===",
                "File \"" + self.filename + "\":",
                str(len(self.fileBytes)) + " bytes",
                "===",
            ])


if __name__ == "__main__":
    zar = Zar("R:/Documents/PythonWorkspace/OoT3D-Importer/romfs/actor/zelda_sa.zar")
    print(zar)
