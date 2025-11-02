import os

def print_tree(startpath, prefix=""):
    files = os.listdir(startpath)
    files.sort()
    for i, name in enumerate(files):
        path = os.path.join(startpath, name)
        connector = "└── " if i == len(files) - 1 else "├── "
        print(prefix + connector + name)
        if os.path.isdir(path):
            extension = "    " if i == len(files) - 1 else "│   "
            print_tree(path, prefix + extension)

if __name__ == "__main__":
    # Change '.' to any folder path you want to print
    print_tree(".")