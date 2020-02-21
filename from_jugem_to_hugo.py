import xml.etree.ElementTree as ET
import glob
import datetime
import os
import re
import urllib
from googletrans import Translator
from logging import getLogger, StreamHandler, DEBUG

logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(DEBUG)
logger.setLevel(DEBUG)
logger.addHandler(handler)
logger.propagate = False


def translate_title(title):
    # FIXME 使用制限がある
    # translator = Translator()
    # translations = translator.translate(title, dest='en', src='ja')
    # title = translations.text
    return title.replace(' ', '-') \
        .replace('/', '-') \
        .replace(',', '-') \
        .replace('.', '-') \
        .replace('&', '-') \
        .replace('#', '-') \
        .replace('(', '-') \
        .replace(')', '-') \
        .replace('"', '') \
        .replace("'", '-') \
        .replace("?", '') \
        .replace("@", '-') \
        .lower()


def convert_date(date):
    date_obj = datetime.datetime.strptime(date, "%Y/%m/%d %H:%M:%S")
    formatted = date_obj.strftime("%Y-%m-%dT%H:%M:%S+09:00")
    return formatted


def convert_description(description, target, filename):
    return convert_pre_tag(
        convert_span_tag(
            convert_ul_ol(
                convert_a_tag(
                    convert_review_tag(
                        description, target
                    ), target, filename
                )
            )
        )
    ) \
        .replace('<del>', '~~') \
        .replace('</del>', '~~') \
        .replace('<strong>', '**') \
        .replace('</strong>', '**') \
        .replace('<h2>', '##') \
        .replace('</h2>', '') \
        .replace('<h3>', '###') \
        .replace('</h3>', '') \
        .replace('<h4>', '####') \
        .replace('</h4>', '') \
        .replace('<br/>', '') \
        .replace('<br>', '') \
        .replace('<hr/>', '___') \
        .replace('&#36;', '$') \
        .replace('&#123;', '{') \
        .replace('&#125;', '}') \
        .replace('&#8211;', '–') \
        .replace('&lt;', '<') \
        .replace('&#36;', '$') \
        .replace('&#36;', '$') \
        .replace('&#36;', '$') \
        .replace('<pre>', '```') \
        .replace('</pre>', '```')


def convert_span_tag(description):
    description = re.sub(r'<strong><span style="font-size:large;">(.*?)</span></strong>', '## \\1', description)
    description = re.sub(r'<strong><span style="font-size:medium;">(.*?)</span></strong>', '### \\1', description)
    description = re.sub(r'<strong><span style="font-size:small;">(.*?)</span></strong>', '#### \\1', description)
    description = re.sub(r'<span style="font-size:large;">(.*?)</span>', '## \\1', description)
    description = re.sub(r'<span style="font-size:medium;">(.*?)</span>', '### \\1', description)
    description = re.sub(r'<span style="font-size:small;">(.*?)</span>', '#### \\1', description)
    description = re.sub(r'<span style="font-size:x-small;">(.*?)</span>', '##### \\1', description)
    return description



def convert_review_tag(description, target_dir):
    matches = list(re.finditer('<div class="jugem_review">((.|\\s)*?)<br />\n</div>', description,
                               flags=(re.MULTILINE | re.DOTALL)))
    if len(matches) > 0:
        # logger.debug("Match!! " + str(len(matches)))
        asin = ""
        for match in matches:
            div_str = match.group()
            asin_match = re.search(r'/ASIN/(.*?)/johtani.*? title="(.*?)">', div_str)
            if asin_match is not None:
                asin = asin_match.group(1)
                with open(target_dir + "amazon.txt", mode='a') as f:
                    f.write('"' + asin_match.group(1) + '":\n')
                    f.write('  "title": "' + asin_match.group(2) + '"\n')
        description = re.sub(r'<div class="jugem_review">((.|\\s)*?)<br />\n</div>', '{{< amazon "' + asin + '" >}}',
                             description, flags=(re.MULTILINE | re.DOTALL))
    return description


def convert_a_tag(description, target_dir, filename):
    # extract src and text
    converted_description = ""
    for line in description.splitlines():
        if "<a href=" in line:
            if "<img " in line:
                # print("------")
                line = convert_images(line, target_dir, filename)
            else:
                line = convert_href(line)
        converted_description += line + "\n"
    return converted_description


def convert_href(line):
    return re.sub(r'<a href="(.*?)".*?>(.*?)</a>', '[\\2](\\1)', line)


def convert_images(line, target_dir, filename):
    # extract src
    match = re.search('<img src="(.*?)".*? alt="(.*?)".*?/>', line)
    image_file = match.group(1)[match.group(1).rfind("/") + 1:].replace("_t", "")
    image_title = match.group(2)
    date = filename[0:10].replace("-", "")
    image_dir = make_img_dir(target_dir, date)
    base_url = "http://img-cdn.jg.jugem.jp/1b8/2091685/"
    #download_images(base_url, image_dir, image_file)
    # print(matches.groups())
    line = re.sub(r'<a href=.*?</a>', '{{< figure src="' + image_dir.replace(target_dir + "static",
                                                                             "") + image_file + '" alt="' + image_title + '" >}}',
                  line)
    return line


def download_images(base_url, image_dir, image_file):
    try:
        with urllib.request.urlopen(base_url + image_file) as web_file:
            data = web_file.read()
            with open(image_dir + image_file, mode='wb') as local_file:
                local_file.write(data)
    except urllib.error.URLError as e:
        print(image_file)
        print(e)


def convert_pre_tag(description):
    return re.sub(r'<pre.*>', '```\n', description)


def convert_ul_ol(description):
    matches = list(re.finditer('<(ul|ol)>((.|\\s)*?)</(ul|ol)>', description,
                               flags=(re.MULTILINE | re.DOTALL)))
    if len(matches) > 0:
        for match in matches:
            ul_ol_str = match.group()
            if "<ul>" in ul_ol_str:
                description = description.replace(ul_ol_str, convert_ul(ul_ol_str))
            else:
                description = description.replace(ul_ol_str, convert_ol(ul_ol_str))
    return description


def convert_ul(ul_str):
    converted_ul = ""
    for line in ul_str.splitlines():
        if "<li>" in line:
            converted_ul += line.replace("<li>", "* ").replace("</li>", "") + "\n"
    return converted_ul


def convert_ol(ol_str):
    converted_ol = ""
    for line in ol_str.splitlines():
        if "<li>" in line:
            converted_ol += line.replace("<li>", "1. ").replace("</li>", "") + "\n"
    return converted_ol


def make_img_dir(target, date):
    dir_name = target + "static/images/entries/" + date
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    return dir_name + "/"


def make_dir(target, year):
    dir_name = target + "post/" + year
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    return dir_name + "/"


def output_markdown(target_dir, title, author, category, date, description):
    date_str = convert_date(date)
    dir_name = make_dir(target_dir, date_str[0:4])
    filename = date_str[0:10] + '-' + translate_title(title) + ".md"
    logger.info(filename)
    target_fp = open(dir_name + filename, 'w')
    target_fp.write('---\n')
    target_fp.write('layout: post\n')
    target_fp.write('title: "' + title + '(Jugemより移植)"\n')
    target_fp.write('slug: ' + filename[11:].replace('.md', '') + '\n')
    target_fp.write('author: ' + author + '\n')
    target_fp.write('date: ' + date_str + '\n')
    target_fp.write('comments: true\n')
    target_fp.write('tags: [' + category + ']\n')
    target_fp.write('---\n')
    target_fp.write(convert_description(description, target_dir, filename))
    target_fp.close()


def make_markdown(target, elem):
    title = elem.findtext('title')
    author = elem.findtext('author')
    category = elem.findtext('category')
    date = elem.findtext('date')
    description = elem.findtext('description') + elem.findtext('sequel')
    output_markdown(target, title, author, category, date, description)


def convert_to_hugo(original, target):
    original_files = glob.glob(original + "*.xml")
    for file in original_files:
        logger.debug("filename:[" + file + "]")
        context = ET.iterparse(file, events=('start', 'end'))
        event, root = next(context)
        for event, elem in context:
            if event == 'end' and elem.tag == 'entry':
                make_markdown(target, elem)
                root.clear()


def main():
    logger.info("convert start")
    original_folder = "original/"
    target_forlder = "converted/"
    convert_to_hugo(original_folder, target_forlder)
    logger.info("finish!")


if __name__ == '__main__':
    main()
