from capnpy import ptr

def copy_from_list(builder, pos, item_type, lst):
    item_length, size_tag = item_type.get_item_length()
    item_count = len(lst)
    body_length = item_length * item_count
    if size_tag == ptr.LIST_SIZE_COMPOSITE:
        # alloc the list and write the tag
        struct_item_type = item_type
        data_size = struct_item_type.static_data_size
        ptrs_size = struct_item_type.static_ptrs_size
        total_words = (data_size+ptrs_size) * item_count
        pos = builder.alloc_list(pos, size_tag, total_words,
                                 body_length + 8) # +8 is for the tag
        tag = ptr.new_struct(item_count, data_size, ptrs_size)
        builder.write_int64(pos, tag)
        pos += 8
    else:
        # alloc the list, no tag
        pos = builder.alloc_list(pos, size_tag, item_count, body_length)
    #
    for item in lst:
        item_type.write_item(builder, pos, item)
        pos += item_length
