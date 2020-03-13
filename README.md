# conf/code
conf/code is a simple script that can push files from your repo into `code` macros in Atlassian Confluence. Confluence plugins exist that can pull code from your git repo, though few work on cloud-hosted Confluence instances and fewer still work with generic git repos rather than e.g. GitHub.

conf/code takes a different approach, pushing to Confluence rather than having Confluence pull from your repo. It is a single script file plus a config file, designed to be copied in to your repo and invoked as part of your `git push`, either through git hooks or your CI/CD pipeline.

# Usage
conf/code is very simple, it looks for code macros on a page and captures the nearest preceding header. The text of that header is used to look up which file should be loaded into the macro.

To Use:
1. Set up a new page in Confluence with a series of headers and empty code macros. Set up the macro's syntax highlighting if you wish.

1. Establish the mapping between header text and filenames in the config file (see below). For example, the following page might go with the config file below.
    ```
    # A heading
    Intro text
    {code}{code}

    ## Lower heading
    Explination of the above code

    # Second heading
    {code}{code}
    Outro text
    ```

1. For your build, all you need is `conf_code.py` and `conf_code.json` in the same directory; typically the root of your project. Run the script as part of your build/deploy process (or manually) and you're done.

## Config
The config file must be named `conf_code.json` and be in the same folder as the Python script.
```
{
    "user": "user@company.com",
    "token": "<api token>",
    "base": "https://<company>.atlassian.net/wiki/rest/api/",
    "space": "My Space",
    "pages" : {
        "Some Page Name": {
            "A heading": "path/to/file.json",
            "Second heading": "another/file.py"
        }
    }
}
```
- `user`: Username of the Confluence user who will make the change, often just their email address
- `token`: Generated REST token, see https://id.atlassian.com/manage/api-tokens
- `base`: The base URL of the REST endpoint
- `space`: Target Confluence Space
- `title`: The title of the target page in that space
- `pages`: A dictionary mapping page names to their headings/files. The inner dictionary here matches heading text to the file path to insert in to that heading's matching code tag.

# Known Issues
This is mostly a hobby project so there are plenty of rough edges. Like this document. And:

1. All code macros on the page have to be managed by conf/code, you can't selectively replace some segments and not others. Note this means that if you enter contents in to a macro yourself it will be lost when you run the script! Confluence page history can help you here :-)
1. Config file name and path isn't configurable
1. Error messages aren't pretty, especially things like when it can't find the `space` or the page title.
1. Only supports "New Editor" pages. I think. Certainly only tested on them.