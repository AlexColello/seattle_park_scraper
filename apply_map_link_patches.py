lines = []
with open("google_maps_links.txt", "r") as f:
    lines = f.readlines()

with open("lines_to_remove.txt", "r") as f:
    for line in f.readlines():
        lines.remove(line)

with open("lines_to_add.txt", "r") as f:
    lines = f.readlines() + lines

with open("patched_google_maps_links.txt", "w") as f:
    f.writelines(lines)
