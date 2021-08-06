from .array_buffer_slice import ArrayBufferSlice

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
        with open(filePath, "rb") as f:
            bytes = ArrayBufferSlice(f.read())

        self.header = Zar.ZarHeader(bytes)
        self.filetypesSection = Zar.FiletypesSection(bytes, self.header)

        self.files = []
        for filetype in self.filetypesSection.filetypes:
            for fileInFiletypeIndex in range(filetype.fileCount):
                fileIndexOffset = filetype.fileListOffset + 4 * fileInFiletypeIndex
                fileIndexBytes = bytes[fileIndexOffset:fileIndexOffset+4]
                (fileIndex,) = fileIndexBytes.unpack("I")

                fileMetadataOffset = self.header.fileMetadataOffset + 8 * fileIndex
                fileMetadataBytes = bytes[fileMetadataOffset:fileMetadataOffset+8]
                (
                    fileSize,
                    filenameOffset,
                ) = fileMetadataBytes.unpack("II")

                filename = readNullTerminatedString(bytes, filenameOffset)

                fileOffsetOffset = self.header.dataOffset + 4 * fileIndex
                fileOffsetBytes = bytes[fileOffsetOffset:fileOffsetOffset+4]
                (fileOffset,) = fileOffsetBytes.unpack("I")

                fileBytes = bytes.slice(fileOffset, fileSize)

                file = Zar.File(filename, fileBytes)

                self.files.append(file)
                filetype.files.append(file)

    def getFiles(self, typeName):
        for filetype in self.filetypesSection.filetypes:
            if typeName == filetype.typeName:
                return filetype.files

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
            ) = bytes.slice(4, 20).unpack("IHHIII")

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
            ) = filetypeBytes.unpack("III")

            self.typeName = readNullTerminatedString(bytes, self.typeNameOffset)
            self.files = []

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
            self.bytes = fileBytes

        def __str__(self):
            return '\n'.join([
                "===",
                "File \"" + self.filename + "\":",
                str(len(self.bytes)) + " bytes",
                "===",
            ])


if __name__ == "__main__":
    #zar = Zar("R:/Documents/PythonWorkspace/OoT3D-Importer/romfs/actor/zelda_sa.zar")
    zar = Zar("R:/Documents/PythonWorkspace/OoT3D-Importer/romfs/scene/kakariko_home3.zar")
    print(zar)
