
# implement chunking for mass post send (like when first evalutating a page) 
# less suited to the club context
# heres a good vibecoded example I edited
def _chunks(items: List[Dict[str, Any]], size: int) -> Iterable[List[Dict[str, Any]]]:
    """
    Yield successive chunks from a list.

    Teaching note:
    - Chunking lets us control request size (context + cost).
    - We chunk the *posts* list; the raw file layout stays per run/day.
    """
    for i in range(0, len(items), size):
        # analogous to multiple return where the function state is paused at each yield
        yield items[i : i + size]

# then use in main function with             out_path = out_dir / f"summary_{idx:03d}.json"
# idx and chunk from the enumerate object