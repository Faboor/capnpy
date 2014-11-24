import struct

class Blob(object):

    PTR_STRUCT = 0
    PTR_LIST = 1

    def __init__(self, buf, offset):
        self._buf = buf
        self._offset = offset

    def _read_int64(self, offset):
        """
        Read an int64 at the given offset
        """
        return struct.unpack_from('=q', self._buf, self._offset+offset)[0]

    def _read_struct(self, offset, cls):
        """
        Read and dereference a struct pointer at the given offset.  It returns an
        instance of ``cls`` pointing to the dereferenced struct.
        """
        struct_offset = self._deref_ptrstruct(offset)
        return cls(self._buf, self._offset+struct_offset)

    def _unpack_ptrstruct(self, offset):
        ## lsb                      struct pointer                       msb
        ## +-+-----------------------------+---------------+---------------+
        ## |A|             B               |       C       |       D       |
        ## +-+-----------------------------+---------------+---------------+
        ##
        ## A (2 bits) = 0, to indicate that this is a struct pointer.
        ## B (30 bits) = Offset, in words, from the end of the pointer to the
        ##     start of the struct's data section.  Signed.
        ## C (16 bits) = Size of the struct's data section, in words.
        ## D (16 bits) = Size of the struct's pointer section, in words.
        ptr = self._read_int64(offset)
        ptr_kind  = ptr & 0x3
        ptr_offset = ptr>>2 & 0x3fffffff
        data_size = ptr>>32 & 0xffff
        ptrs_size = ptr>>48 & 0xffff
        assert ptr_kind == self.PTR_STRUCT
        return ptr_offset, data_size, ptrs_size

    def _deref_ptrstruct(self, offset):
        # we partially replicate the logic of _unpack_ptrstruct, because in
        # the common case it's not needed to decode data_size and ptrs_size
        ptr = self._read_int64(offset)
        ptr_kind  = ptr & 0x3
        ptr_offset = ptr>>2 & 0x3fffffff
        assert ptr_kind == self.PTR_STRUCT
        # the +1 is needed because the offset is measured from the end of the
        # pointer itself
        offset = offset + (ptr_offset+1)*8
        return offset

    def _unpack_ptrlist(self, offset):
        ## lsb                       list pointer                        msb
        ## +-+-----------------------------+--+----------------------------+
        ## |A|             B               |C |             D              |
        ## +-+-----------------------------+--+----------------------------+
        ##
        ## A (2 bits) = 1, to indicate that this is a list pointer.
        ## B (30 bits) = Offset, in words, from the end of the pointer to the
        ##     start of the first element of the list.  Signed.
        ## C (3 bits) = Size of each element:
        ##     0 = 0 (e.g. List(Void))
        ##     1 = 1 bit
        ##     2 = 1 byte
        ##     3 = 2 bytes
        ##     4 = 4 bytes
        ##     5 = 8 bytes (non-pointer)
        ##     6 = 8 bytes (pointer)
        ##     7 = composite (see below)
        ## D (29 bits) = Number of elements in the list, except when C is 7
        ptr = self._read_int64(offset)
        ptr_kind  = ptr & 0x3
        ptr_offset = ptr>>2 & 0x3fffffff
        item_size = ptr>>32 & 0x7
        item_count = ptr>>35
        assert ptr_kind == self.PTR_LIST
        #offset = offset + (ptr_offset+1)*8
        return offset, item_size, item_count