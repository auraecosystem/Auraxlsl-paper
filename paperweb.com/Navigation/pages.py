import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os, re, base64
from queue import Queue

def encode_file_to_base64(url):
    try:
        data = requests.get(url).content
        ext = url.split(".")[-1].lower()
        if ext in ["woff2", "woff", "ttf", "otf"]:
            mime_type = f"font/{ext}"
        elif ext in ["png", "jpg", "jpeg", "gif", "svg"]:
            mime_type = f"image/{ext if ext != 'jpg' else 'jpeg'}"
        elif ext in ["mp4", "webm", "ogg"]:
            mime_type = f"video/{ext}"
        else:
            mime_type = "application/octet-stream"
        return f"data:{mime_type};base64,{base64.b64encode(data).decode()}"
    except Exception as e:
        print(f"Failed to encode {url}: {e}")
        return url

def sanitize_filename(url):
    parsed = urlparse(url)
    path = parsed.path.strip("/").replace("/", "_") or "index"
    if not path.endswith(".html"):
        path += ".html"
    return path

def embed_resources(soup, page_url):
    # Images
    for img in soup.find_all("img"):
        src = img.get("src")
        if src:
            img["src"] = encode_file_to_base64(urljoin(page_url, src))

    # CSS
    for link in soup.find_all("link", rel="stylesheet"):
        href = link.get("href")
        if href:
            css_url = urljoin(page_url, href)
            try:
                css_data = requests.get(css_url).text
                # Embed fonts in CSS
                def font_replacer(match):
                    font_url = urljoin(css_url, match.group(1))
                    return f"url({encode_file_to_base64(font_url)})"
                css_data = re.sub(r'url\(([^)]+)\)', font_replacer, css_data)
                style_tag = soup.new_tag("style")
                style_tag.string = css_data
                link.replace_with(style_tag)
            except Exception as e:
                print(f"Failed to embed CSS {css_url}: {e}")

    # JS
    for script in soup.find_all("script", src=True):
        js_url = urljoin(page_url, script["src"])
        try:
            js_data = requests.get(js_url).text
            script.attrs.pop("src", None)
            script.string = js_data
        except Exception as e:
            print(f"Failed to embed JS {js_url}: {e}")

    # Inline styles with background images
    for tag in soup.find_all(style=True):
        style_content = tag["style"]
        urls = re.findall(r'url\(([^)]+)\)', style_content)
        for u in urls:
            clean_url = u.strip(' "\'')
            full_url = urljoin(page_url, clean_url)
            style_content = style_content.replace(u, encode_file_to_base64(full_url))
        tag["style"] = style_content

    return soup

def rewrite_internal_links(soup, base_url, url_to_file):
    for link in soup.find_all("a", href=True):
        href = link["href"]
        full_url = urljoin(base_url, href)
        if full_url in url_to_file:
            link["href"] = url_to_file[full_url]

def save_page(soup, folder, filename):
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(str(soup))
    print(f"Saved: {path}")

def archive_site(start_url, output_folder="offline_site", max_pages=20):
    visited = set()
    url_to_file = {}
    q = Queue()
    q.put(start_url)

    while not q.empty() and len(visited) < max_pages:
        url = q.get()
        if url in visited:
            continue
        visited.add(url)
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            soup = embed_resources(soup, url)
            filename = sanitize_filename(url)
            url_to_file[url] = filename

            # Enqueue internal links first
            for link in soup.find_all("a", href=True):
                link_url = urljoin(url, link["href"])
                if urlparse(link_url).netloc == urlparse(start_url).netloc:
                    q.put(link_url)

            # Rewrite internal links to offline filenames
            rewrite_internal_links(soup, url, url_to_file)
            save_page(soup, output_folder, filename)

        except Exception as e:
            print(f"Failed to process {url}: {e}")

    print(f"Archived {len(visited)} pages to {output_folder}")

# Example usage
archive_site("https://example.com", "my_offline_site", max_pages=20)
