import io, struct

class ArrayBufferSlice:
    def __init__(self, array, offset = 0, length = -1):
        self.__array = array
        self.__offset = offset
        self.__length = length if length != -1 else len(array) - offset

    def slice(self, offset, length = -1):
        if length == -1:
            length = self.__length - offset
        else:
            length = min(length, self.__length - offset)

        assert offset >= 0, "Offset is negative!"
        assert offset < self.__length, "Offset is past bounds of array!"
        assert length > 0, "Array length is not positive!"

        return ArrayBufferSlice(self.__array,
                                self.__offset + offset,
                                length)

    def __len__(self):
        return self.__length

    def __getitem__(self, index):
        if isinstance(index, slice):
            return self.slice(index.start, index.stop - index.start)

        assert index >= 0, "Index is negative!"
        assert index < self.__length, "Index is past bounds of array!"

        return self.__array[self.__offset + index]

    def decode(self, format):
        return self.__array[self.__offset:self.__offset+self.__length].decode(format)

    def unpack(self, format):
        return struct.unpack(format, self.__array[self.__offset:self.__offset+self.__length])

    def toStream(self):
        return io.BytesIO(self.__array[self.__offset:self.__offset+self.__length])
