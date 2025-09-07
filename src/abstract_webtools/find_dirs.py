import os
def get_dir_size(path):
    """Calculate the total size of a directory in bytes."""
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(file_path)
                except (OSError, PermissionError) as e:
                    #print(f"Error accessing {file_path}: {e}")
                    pass
    except (OSError, PermissionError) as e:
        print(f"Error accessing {path}: {e}")
    return total_size

def compare_dirs(dir1_path, dir2_path):
    """Compare the sizes of two directories."""
    dir1_size = get_dir_size(dir1_path)
    dir2_size = get_dir_size(dir2_path)
    
    print(f"Size of {dir1_path}: {dir1_size} bytes")
    print(f"Size of {dir2_path}: {dir2_size} bytes")
    
    if dir1_size > dir2_size:
        print(f"{dir1_path} is larger than {dir2_path}")
    elif dir2_size > dir1_size:
        print(f"{dir2_path} is larger than {dir1_path}")
    else:
        print("Both directories are the same size")
twentyfourT = """/mnt/24T/evo_970
/mnt/24T/main_drive
/mnt/24T/nvmeHeatSync-new
/mnt/24T/PNY_1T
/mnt/24T/serverBack
/mnt/24T/solcatcher_backup
/mnt/24T/transferDrive
/mnt/24T/wd_black
/mnt/24T/wd_black_980_home
/mnt/24T/wdBlack_970_evo
/mnt/24T/wd_main_980
/mnt/24T/wd_nvm
/mnt/24T/.Trash-1000
/mnt/24T/testfile.txt"""


sixteenT = """/mnt/16T/24T/24T/evo980-new
/mnt/16T/24T/24T/500Gb_pny
/mnt/16T/24T/24T/wdBlack_970_evo
/mnt/16T/24T/24T/wd_nvm
/mnt/16T/24T/24T/wd_main_980
/mnt/16T/24T/24T/nvmeHeatSync-new
/mnt/16T/24T/24T/PNY_1T
/mnt/16T/24T/24T/serverBack
/mnt/16T/24T/24T/transferDrive
/mnt/16T/24T/24T/.Trash-1000
/mnt/16T/24T/24T/solcatcher_backup
/mnt/16T/24T/24T/wd_black_980_home
/mnt/16T/24T/24T/abstract_images-0.0.0.5-py3-none-any
/mnt/16T/24T/24T/evo_970
/mnt/16T/24T/24T/main_drive
/mnt/16T/24T/24T/wd_black
/mnt/16T/24T/24T/testfile.txtt"""
sixteenT = sixteenT.split('\n')
twentyfourT = twentyfourT.split('\n')
def is_dirname_in_sixteenT(dirname):
    basenames = [directory for directory in sixteenT if os.path.basename(directory) == dirname]
    if basenames:
        return basenames[0]
for directory in twentyfourT:
    dirname = os.path.basename(directory)
    
    size1 = get_dir_size(directory))
    sixteenT_dir = is_dirname_in_sixteenT(dirname)
    size2 = get_dir_size(sixteenT_dir))
    print(directory)
    print(f"size == {size1}")
    print(sixteenT_dir)
    input(f"size == {size2}")
    input(compare_dirs(directory, sixteenT_dir))
