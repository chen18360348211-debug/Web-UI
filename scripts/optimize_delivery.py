"""Apply the responsive image manifest to the static page; retain PNG fallbacks.

Run after optimize_images.py (and after regenerating the Figma HTML). This
changes delivery only: the existing image classes and animation hooks survive.
"""
from html import escape
from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / 'dist'
IMAGES = json.loads((DIST / 'assets/optimized/image-manifest.json').read_text())['images']
NOVEMBER_MANIFEST = DIST / 'assets/optimized/november-art-manifest.json'
if NOVEMBER_MANIFEST.exists():
    IMAGES.update(json.loads(NOVEMBER_MANIFEST.read_text())['images'])
HERO_IMAGE = 'assets/uploads/hero-20261119.png'
FEATURED_BACKGROUND = 'assets/uploads/package-background-20261119.jpg'
CSS_FILES = ['fonts.css', 'styles.css', 'hover.css', 'controls.css', 'power-levels.css',
             'featured-art.css', 'customize-motion.css', 'weekly-bonus.css',
             'coupon-marquee.css', 'product-flip.css', 'product-controls.css',
             'product-entry.css', 'content-entry.css', 'campaign-sticky.css']
THUMBNAIL = IMAGES['assets/uploads/package-thumbnail.png']['default']


def set_attr(tag, key, value):
    tag = re.sub(r'\s' + re.escape(key) + r'(?:="[^"]*"|=\x27[^\x27]*\x27)?(?=[\s/>])', '', tag)
    end = tag.rfind('/>') if tag.endswith('/>') else tag.rfind('>')
    return tag[:end] + f' {key}="{escape(str(value), quote=True)}"' + tag[end:]


class PageImages(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=False)
        self.text = text
        self.lines = [0] + [m.end() for m in re.finditer('\n', text)]
        self.section = None
        self.picture = 0
        self.changes = []

    def handle_starttag(self, name, attributes):
        attrs = dict(attributes)
        raw = self.get_starttag_text()
        replacement = raw
        if name == 'section':
            self.section = attrs.get('id')
            if self.section == 'featured-packages':
                replacement = set_attr(raw, 'data-thumbnail-art', THUMBNAIL)
        if name == 'picture':
            self.picture += 1
        if name == 'source' and self.section == 'black-friday':
            replacement = set_attr(raw, 'srcset', IMAGES[HERO_IMAGE]['srcset'])
        if name == 'img':
            if self.section == 'black-friday':
                raw = set_attr(raw, 'src', HERO_IMAGE)
                raw = set_attr(raw, 'alt', 'Black Friday. Up to 30% off. Gift card savings plus up to 2X points. Nov 2–Nov 30.')
                attrs['src'] = HERO_IMAGE
            initial = self.section in ('announcement', 'main-navigation', 'black-friday', 'campaign-navigation')
            replacement = set_attr(raw, 'decoding', 'async')
            replacement = set_attr(replacement, 'loading', 'eager' if initial else 'lazy')
            info = IMAGES.get(attrs.get('src'))
            if info:
                replacement = set_attr(replacement, 'width', info['width'])
                replacement = set_attr(replacement, 'height', info['height'])
                if self.section == 'black-friday':
                    replacement = set_attr(replacement, 'fetchpriority', 'high')
                if not self.picture:
                    classes = attrs.get('class', '').split()
                    sizes = '17vw' if 'f144' in classes else '100vw'
                    if 'f80' in classes or self.section == 'weekly-bonus' and '4c963' in attrs.get('src', ''):
                        sizes = '83.333vw'
                    if self.section == 'customize' and attrs.get('src') == 'assets/uploads/package-thumbnail.png':
                        sizes = '23vw'
                    source = f'<source type="image/webp" srcset="{info["srcset"]}" sizes="{sizes}">'
                    replacement = f'<picture style="display:contents">{source}{replacement}</picture>'
        if name == 'video':
            replacement = set_attr(raw, 'data-src', 'assets/video/weekly-bonus-optimized.mp4')
            replacement = re.sub(r'\s(?:data-)?poster="[^"]*"', '', replacement)
            replacement = set_attr(replacement, 'data-poster', IMAGES['assets/figma/d11078bc-451f-4290-af94-a19b856a3430/de98c.png']['default'])
            replacement = set_attr(replacement, 'preload', 'none')
        original_tag = self.get_starttag_text()
        if replacement != original_tag:
            line, column = self.getpos()
            start = self.lines[line - 1] + column
            self.changes.append((start, start + len(original_tag), replacement))

    handle_startendtag = handle_starttag

    def handle_endtag(self, name):
        if name == 'section':
            self.section = None
        if name == 'picture':
            self.picture -= 1


page = (DIST / 'index.html').read_text(encoding='utf-8')
parser = PageImages(page)
parser.feed(page)
for start, end, replacement in reversed(parser.changes):
    page = page[:start] + replacement + page[end:]

# The new Banner includes its own copy; avoid painting the old live line twice.
page = page.replace('NOV 1 – NOV 30', 'NOV 2 – NOV 30')
background = IMAGES[FEATURED_BACKGROUND]
def background_picture(class_name, sizes):
    return (f'<picture style="display:contents"><source type="image/webp" srcset="{background["srcset"]}" sizes="{sizes}">'
            f'<img class="{class_name}" src="{FEATURED_BACKGROUND}" width="3840" height="2160" '
            'alt="" decoding="async" loading="lazy"></picture>')
if 'class="featured-background-art"' not in page:
    page = page.replace('<div class="featured-raster-scene">', '<div class="featured-raster-scene">' + background_picture('featured-background-art', '100vw'))
if 'class="featured-mini-background"' not in page:
    page = page.replace('<div class="f94" data-name="Frame 427324301 1">', '<div class="f94" data-name="Frame 427324301 1">' + background_picture('featured-mini-background', '23vw'))
if 'id="featured-preserved-cards"' not in page:
    definitions = ('<svg width="0" height="0" aria-hidden="true" style="position:absolute;pointer-events:none"><defs>'
                   '<clipPath id="featured-preserved-cards" clipPathUnits="objectBoundingBox">'
                   '<rect x="0.177083333333" y="0.555555555556" width="0.3" height="0.365740740741"/>'
                   '<rect x="0.536458333333" y="0.555555555556" width="0.3" height="0.365740740741"/>'
                   '</clipPath></defs></svg>')
    page = page.replace('<main id="design-canvas" aria-label="MIKOLO Black Friday">', '<main id="design-canvas" aria-label="MIKOLO Black Friday">' + definitions)
page = page.replace('y="0.488888888889" width="0.3" height="0.432407407407"', 'y="0.555555555556" width="0.3" height="0.365740740741"')
panels = '<div class="featured-card-panels" aria-hidden="true"><span></span><span></span></div>'
if page.count('class="featured-card-panels"') < 2:
    page = page.replace('<div class="featured-raster-scene">', '<div class="featured-raster-scene">' + panels)
    page = page.replace('<div class="f94" data-name="Frame 427324301 1">', '<div class="f94" data-name="Frame 427324301 1">' + panels)
    # Place backgrounds below the transparent panel gradients in paint order.
    for name in ('featured-background-art', 'featured-mini-background'):
        pattern = r'(<div class="(?:featured-raster-scene|f94)"[^>]*>)(' + re.escape(panels) + r')(<picture[^>]*><source[^>]*><img class="' + name + r'"[^>]*></picture>)'
        page = re.sub(pattern, r'\1\3\2', page)
if 'id="featured-mini-frame"' not in page:
    frame = ('<clipPath id="featured-mini-frame" clipPathUnits="objectBoundingBox">'
             '<path clip-rule="evenodd" fill-rule="evenodd" d="M0 0H1V1H0Z '
             'M.045833333 .002777778H.954166667V.081481481H.9984375V.918518519H.954166667V.997222222H.045833333V.918518519H.0015625V.081481481H.045833333Z"/>'
             '</clipPath>')
    page = page.replace('</clipPath></defs></svg>', '</clipPath>' + frame + '</defs></svg>', 1)
if 'class="featured-mini-outline"' not in page:
    thumb = IMAGES['assets/uploads/package-thumbnail.png']
    outline = (f'<picture style="display:contents"><source type="image/webp" srcset="{thumb["srcset"]}" sizes="23vw">'
               '<img class="featured-mini-outline" src="assets/uploads/package-thumbnail.png" alt="" '
               'width="3840" height="2160" loading="lazy" decoding="async"></picture>')
    mini_bg = background_picture('featured-mini-background', '23vw')
    page = page.replace(mini_bg, mini_bg + outline)
frame_svg = ('<svg class="featured-frame-art" viewBox="0 0 1920 1080" preserveAspectRatio="none" aria-hidden="true">'
             '<path d="M87 2H1833V87H1918V993H1833V1078H87V993H2V87H87Z"/></svg>')
if page.count('class="featured-frame-art"') < 2:
    page = page.replace('<div class="featured-raster-scene">', '<div class="featured-raster-scene">' + frame_svg)
    page = page.replace('<div class="f94" data-name="Frame 427324301 1">', '<div class="f94" data-name="Frame 427324301 1">' + frame_svg)

# The artwork stays in its original CSS slot; only the bytes it references change.
for name in CSS_FILES:
    text = (DIST / name).read_text(encoding='utf-8')
    for original, info in IMAGES.items():
        if original == 'assets/uploads/package-thumbnail.png':
            text = text.replace(f'url("{original}")', 'var(--package-thumbnail-art, none)')
        else:
            text = text.replace(original, info['default'])
    (DIST / name).write_text(text, encoding='utf-8', newline='\n')

# One render-blocking request, same cascade order and relative URL base.
bundle = '\n'.join(f'/* {name} */\n' + (DIST / name).read_text(encoding='utf-8') for name in CSS_FILES)
(DIST / 'site.css').write_text(bundle, encoding='utf-8', newline='\n')
page = re.sub(r'<link rel="stylesheet" href="(?:' + '|'.join(re.escape(n) for n in CSS_FILES + ['site.css']) + r')(?:\?[^\"]*)?">\s*', '', page)
page = re.sub(r'<!-- delivery hints -->.*?<!-- /delivery hints -->\s*', '', page, flags=re.S)
hero = IMAGES[HERO_IMAGE]
css_version = hashlib.sha256(bundle.encode()).hexdigest()[:12]
hints = f'''<!-- delivery hints -->
<link rel="preload" as="image" type="image/webp" href="{hero['default']}" imagesrcset="{hero['srcset']}" imagesizes="100vw" fetchpriority="high">
<link rel="preload" as="font" href="assets/fonts/barlow-500-latin.woff2" type="font/woff2" crossorigin>
<link rel="preload" as="font" href="assets/fonts/jersey-10-400-latin.woff2" type="font/woff2" crossorigin>
<link rel="stylesheet" href="site.css?v={css_version}">
<noscript><style>#featured-packages{{--package-thumbnail-art:url("{THUMBNAIL}")}}</style></noscript>
<!-- /delivery hints -->
'''
page = page.replace('</head>', hints + '</head>')
if 'src="media-loading.mjs"' not in page:
    page = page.replace('<script src="preview.js">', '<script type="module" src="media-loading.mjs"></script><script src="preview.js">')
video_version = hashlib.sha256((DIST / 'weekly-bonus.mjs').read_bytes()).hexdigest()[:12]
page = re.sub(r'src="weekly-bonus\.mjs(?:\?[^\"]*)?"', f'src="weekly-bonus.mjs?v={video_version}"', page)
(DIST / 'index.html').write_text(page, encoding='utf-8', newline='\n')
print(f'Updated {len(parser.changes)} image/media tags; bundled {len(CSS_FILES)} stylesheets.')
