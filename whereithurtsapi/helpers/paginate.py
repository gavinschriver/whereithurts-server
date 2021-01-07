def paginate(collection, page, page_size):
    try:
        page = int(page)
    except ValueError:
        page = 1

    try:
        page_size = int(page_size)
    except ValueError:
        page_size = 10

    page = page - 1
    start_index = (page * page_size)
    end_index = ((page + 1) * page_size)
    return collection[start_index:end_index]