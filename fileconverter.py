import shutil
import os
import glob
import datetime
from logging import getLogger, StreamHandler, DEBUG

logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(DEBUG)
logger.setLevel(DEBUG)
logger.addHandler(handler)
logger.propagate = False


def _file_name(full_path):
    return full_path[full_path.rfind("/") + 1:]


def _year_of_file(full_path):
    return full_path[full_path.rfind("/") + 1:full_path.rfind("/") + 5]


def copy_and_convert_files(original_folder, target_folder):
    # load file names
    original_files = glob.glob(original_folder + "*.markdown")
    # loop file names
    for file in original_files:
        logger.debug("filename:[" + file + "]")
        # get year from file name: 4 chars from file name
        file_name = _file_name(file)
        year = _year_of_file(file)
        logger.debug(year)
        # mkdir year folder if not exist
        if not os.path.exists(target_folder + "post/" + year):
            os.makedirs(target_folder + "post/" + year)
        # move file to folder
        #shutil.copy(file, target_folder + year + "/" + file_name)
        convert_file_to_hugo(file, target_folder + "post/" + year + "/" + file_name.replace(".markdown", ".md"))
        #break

def convert_file_to_hugo(original_file, target_file):
    logger.debug("start convert_to_hugo")
    ## See https://gam0022.net/blog/2016/09/25/migrated-from-octopress-to-hugo/
    # read line from file? or using reg exp?
    original_fp = open(original_file)
    target_fp = open(target_file, 'w')
    for line in original_fp:
        if line.startswith("title:"):
            line = append_slug(line, original_file)
            line = append_author(line)
        if line.startswith("date:"):
            line = convert_date(line)
        if "'''" in line:
            line = convert_code_block(line)
        if "categories:" in line:
            line = convert_categories(line)
        if "{%" in line:
            line = convert_image_tag(line)
        target_fp.write(line)
    original_fp.close()
    target_fp.close()
    logger.debug("finish convert_to_hugo")


def convert_date(line):
    if "+" in line:
        date = datetime.datetime.strptime(line, "date: %Y-%m-%d %H:%M:%S %z\n")
        line = date.strftime("date: %Y-%m-%dT%H:%M:%S+09:00\n")
    else:
        date = datetime.datetime.strptime(line, "date: %Y-%m-%d %H:%M\n")
        line = date.strftime("date: %Y-%m-%dT%H:%M:%S+09:00\n")
    return line


def append_author(line):
    return line + "author: johtani\n"


def append_slug(line, original_file):
    return line + "slug: " + _file_name(original_file)[11:].replace(".markdown", "") + "\n"


def convert_image_tag(line):
    tmp_line = line.replace("{% img ", "").replace("%}", "").strip()
    logger.debug(tmp_line)
    image_path = ""
    options = ""
    if " " in tmp_line:
        words = tmp_line.split(" ")
        image_path = words.pop(0)
        word = words.pop(0)
        if word.isnumeric():
            options = options + ' width="' + word + '"'
        else:
            words.insert(0, word)
            options = options + ' title="' + " ".join(words) + '"'
    else:
        image_path = tmp_line
    line = '{{< figure src="' + image_path + '"'
    if len(options) > 0:
        line = line + options
    line = line + " >}}\n"
    return line


def convert_categories(line):
    return line.replace("categories:", "tags:")


def convert_code_block(line):
    # no need to convert > v0.60.0
    return line


def main():
    logger.info("start main")
    original_folder = "/Users/johtani/projects/blog/octopress/source/_posts/"
    target_folder = "/Users/johtani/projects/blog/hugo/blog_generator/content/"
    copy_and_convert_files(original_folder, target_folder)
    logger.info("finish!")


if __name__ == '__main__':
    main()
