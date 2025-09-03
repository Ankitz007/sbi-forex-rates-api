import importlib.metadata
import os
import sys


def main():
    # Find the site-packages directory for the informational message
    try:
        site_packages = next(p for p in sys.path if "site-packages" in p)
        print(f"📦 Checking packages in: {site_packages}\n")
    except StopIteration:
        print("Could not find the site-packages directory.")
        return

    total_size = 0
    sizes = []

    # Iterate through all installed packages
    for dist in importlib.metadata.distributions():
        name = dist.metadata["Name"]
        size = 0

        # The most reliable method is to iterate over the files listed in the
        # package's RECORD metadata file. dist.files provides this list.
        if dist.files:
            for file in dist.files:
                try:
                    # dist.locate_file() resolves the file's path to an
                    # absolute path on your disk.
                    path = dist.locate_file(file)
                    size += os.path.getsize(str(path))
                except FileNotFoundError:
                    # The RECORD file can sometimes list files that don't exist
                    # (e.g., in editable installs), so we safely skip them.
                    pass

        sizes.append((name, size))
        total_size += size

    # Sort packages by size in descending order
    sizes.sort(key=lambda x: x[1], reverse=True)

    # Print the results
    print(f"{'Package':<20} {'Size'}")
    print(f"{'-'*20} {'-'*10}")
    for name, size in sizes:
        # Only print packages that have a measurable size
        if size > 0:
            print(f"{name:<20} {size/1024/1024:.2f} MB")

    print("\n🔹 Total installed packages size: " f"{total_size/1024/1024:.2f} MB")


if __name__ == "__main__":
    main()
