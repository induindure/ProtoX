def build_file_tree(files: list) -> dict:
    """
    Converts flat list of file paths into a nested dict tree.
    Example:
      ["src/App.jsx", "src/components/Navbar.jsx"]
    becomes:
      { "src": { "App.jsx": None, "components": { "Navbar.jsx": None } } }
    """
    tree = {}

    for file in files:
        parts = file["path"].split("/")
        current = tree
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = None  # None means it's a file, not a folder

    return tree