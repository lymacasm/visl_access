import difflib

def get_closest_match(search_item: str, options: list[str], function=str.title):
    # Cover trivial case
    if search_item in options:
        return search_item

    # Use difflib to find closest match
    cutoff = 0.1
    while cutoff <= 1.0001:
        matches = difflib.get_close_matches(search_item, options, cutoff=cutoff)
        if len(matches) == 0:
            if function is None or not callable(function):
                return

            next_function = {
                str.title: str.capitalize,
                str.capitalize: str.upper,
                str.upper: str.lower,
            }
            return get_closest_match(function(search_item), options, function=next_function.get(function))
        if len(matches) > 1:
            cutoff += 0.1
            continue

        return matches[0]