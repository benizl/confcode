#! /usr/bin/env python

import requests
import json
import re

from bs4 import BeautifulSoup, CData

headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}

def conf_get(endpoint, **params):
    resp = requests.get(base + endpoint, auth=(user, token), headers=headers, params=params)
    return json.loads(resp.text)

def conf_put(endpoint, data, **params):
    resp = requests.put(base + endpoint, auth=(user, token), data=data, headers=headers, params=params)
    return json.loads(resp.text)


# We look for headings that have a code macro before the next heading (i.e. they are the heading
# most closely preceding the code macro). We don't have a way to mark code macros as "do not touch",
# not least of all because at the moment the lxml parser nukes the CDATA tag containing their old
# body before we even get here.
def _tag_is_code_macro(tag):
    return tag.name == 'ac:structured-macro' and tag.attrs.get('ac:name', None) == 'code'

def _matched_heading(tag):
    if not re.search(r"h[1-9]", tag.name):
        return False
    
    for sibling in tag.next_siblings:
        if re.search(r"h[1-9]", sibling.name):
            return False
        
        if _tag_is_code_macro(sibling):
            return True
    
    return False


def process_page(title, files):
    page_set = conf_get("content",
        spaceKey=space_key,
        title=title,
        expand="body.storage,version")

    page = page_set['results'][0]
    body = page['body']['storage']['value']


    # Really should use an XML parser here because this default HTML one inserts bollocks HTML
    # and BODY tags. I don't though because the Confluence storage format doesn't explicitly
    # declare its entities so XML parsers choke on e.g. &lsquo; . In the future it might be worth
    # inserting some DOCTYPE metadata that resolves the entities so the XML parser works, but for
    # now all this means is that I need to strip the stupid extra tags below
    soup = BeautifulSoup(body, "lxml")

    headings = soup.find_all(_matched_heading)

    for heading in headings:
        file_hdr = heading.string
        code_macro = [sibling for sibling in heading.next_siblings if _tag_is_code_macro(sibling) ][0]
        code_el = code_macro.find('ac:plain-text-body')
        
        # If the code macro is empty, it won't even have the plain-text-body to insert in to.
        if code_el is None:
            code_el = soup.new_tag('ac:plain-text-body')
            code_macro.append(code_el)

        if file_hdr not in files:
            print(f"  Unmatched header {file_hdr}")
            continue

        try:
            fname = files[file_hdr]
            print(f"  Heading \"{file_hdr}\" matched to file {fname}")

            with open(fname) as f:
                data = CData(f.read())
                code_el.append(data)
        except Exception as e:
            print(f"  Can't find file '{files[file_hdr]}' for heading '{file_hdr}' ({e})")


    # Clean up the page structure, keeping only the keys we want and incrementing the version number
    page_id = page['id']
    required_keys = ['id', 'title', 'type', 'status', 'body']
    new_page = { key: page[key] for key in required_keys }

    # Intentionally swap out the dict here not just increment in-place as the original version dict
    # carries a bunch of cruft
    new_page['version'] = {'number': page['version']['number'] + 1}

    # There must be a better way to strip the body tags from this string?
    new_page['body']['storage']['value'] = str(soup.body)[6:-7]

    # Upload!
    result = conf_put(f"content/{page_id}", data=json.dumps(new_page))
    if 'success' in result and not result['success']:
        raise Exception(str(result))

    print(f"  Success. New version is {result['version']['number']}")



if __name__ == '__main__':
    conf = json.load(open('conf-code.json'))
    user, token, base = conf['user'], conf['token'], conf['base']
    pages = conf['pages']

    spaces = conf_get("space")['results']

    name_to_key = { sp['name']: sp['key'] for sp in spaces }
    space_key = name_to_key[conf['space']]

    for title, files in pages.items():
        print(f"Processing page \"{title}\" ({len(files)} file(s))")
        process_page(title, files)

    print(f"Done.")
