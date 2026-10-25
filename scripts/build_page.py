"""Translate the retrieved Figma section references into dependency-free HTML/CSS.

The source of truth is Figma frame 541:1054. Images remain separate original
assets, text remains live HTML, and exported component geometry stays intact.
"""
from pathlib import Path
import argparse
import html
import json
import math
import re
from figma_css import declarations, UNKNOWN

ROOT = Path(__file__).resolve().parent.parent
PACKAGE_THUMBNAIL = 'assets/uploads/package-thumbnail.png'
PACKAGE_FULL = 'assets/uploads/package-full.png'
PACKAGE_OPTION_CHECK = 'assets/figma/bd6513f6-63af-4512-b2bf-839225f13cbc/0fcc0.svg'
PACKAGE_OPTION_IDS = {'1937', '1949', '1961', '1972', '1999', '2011', '2023', '2034'}
PRODUCT_CARD_IDS = {
    '1416', '1442', '1468', '1494', '1522', '1548', '1574', '1600',
    '1716', '1742', '1768', '1794', '1822', '1848', '1874', '1900',
    '1933', '1995',
}
# The two larger featured package configurators have their own Figma layout.
FLIP_PRODUCT_CARD_IDS = PRODUCT_CARD_IDS - {'1933', '1995'}
PRODUCT_ENTRY_PARTS = {
    str(int(card_id) + offset): part
    for card_id in FLIP_PRODUCT_CARD_IDS
    for offset, part in ((5, 'image'), (10, 'title'), (12, 'price'), (15, 'button'))
}
# One-time copy/media entries from the user's iPhone Duo recording. The
# raster thumbnail and product-card entry stages keep their own behavior.
CONTENT_ENTRY_DELAYS = {
    '1253': 0, '1254': 150, '1255': 150,
    '1317': 0, '1318': 150, '1319': 300,
    '1324': 0, '1322': 150, '1325': 300,
    '1331': 0, '1332': 150, '1333': 300,
    '1629': 0, '1630': 150, '1631': 300, '1669': 300,
    '1926': 0, '2060': 0, '2063': 150, '2064': 300,
    '2074': 0, '2071': 150, '2072': 225, '2073': 300,
    '2076': 0, '2080': 75, '2084': 150, '2088': 225,
}
PRODUCT_CART_IDS = {
    '1431', '1457', '1483', '1509', '1537', '1563', '1589', '1615',
    '1731', '1757', '1783', '1809', '1837', '1863', '1889', '1915',
}
VAULT_TAB_IDS = {'1670', '1678', '1683', '1688', '1693', '1698', '1703', '1708'}
HOVER_ASSETS = {
    '541:2092': 'assets/figma/081f3a89-1f90-46ab-9ccf-cdbe1cf85201/ba1d0.svg',
    '606:1649': 'assets/figma/a40dd691-8d56-4f0f-98ef-8273b5bdd5ce/4be99.svg',
    '541:2124': 'assets/figma/20abc727-8f1f-43e1-8f66-bdd70e715edc/69a1e.svg',
    '610:1657': 'assets/figma/ec99ad27-ee6d-472d-9a2b-4761ac35263e/203f5.svg',
    '619:1667': 'assets/figma/7eec6afd-30ab-4d36-9533-5527aca60aba/dc9b1.svg',
}
CONTROL_IDS = {
    '1056', '1058', '1063', '1177', '1187', '1188', '1189', '1190', '1191',
    '1193', '1198', '1203', '1208', '1221', '1229', '1234', '1239', '1245',
    '1431', '1457', '1483', '1509', '1537', '1563', '1589', '1615',
    '1670', '1678', '1683', '1688', '1693', '1698', '1703', '1708',
    '1731', '1757', '1783', '1809', '1837', '1863', '1889', '1915', '1926',
    '1937', '1949', '1961', '1972', '1987', '1999', '2011', '2023', '2034', '2049', '2064',
    '1073', '1080', '1082', '1084', '1086', '1088', '1090', '1092',
    '1097', '1099', '1101', '1103', '1105', '1107', '1109',
    '1114', '1116', '1118', '1120', '1122', '1127', '1129', '1131', '1133', '1135', '1140',
    '1145', '1148', '1150', '1153', '1156', '1158', '1160', '1173',
    '1334', '1356', '1378', '1400',
    '1632', '1644', '1656',
}
SECTIONS = [
    ('1055', 'announcement', 'Announcement', 0, 0, 1920, 48),
    ('1175', 'main-navigation', 'MIKOLO navigation', 0, 48, 1920, 64),
    ('1212', 'black-friday', 'Black Friday', 0, 112, 1920, 800),
    ('1215', 'campaign-navigation', 'Campaign navigation', 0, 912, 1920, 80),
    ('1250', 'early-access', 'Early access and power levels', 0, 992, 1920, 1747),
    ('1320', 'customize', 'Customize your package', 0, 2731, 1920, 1080),
    ('1931', 'featured-packages', 'Featured packages', 0, 3811, 1920, 1080),
    ('1329', 'package-offers', 'Package offers', 160, 4995, 1601, 344),
    ('1413', 'best-sellers', 'Best-selling packages', 160, 5395, 1601, 1212),
    ('1627', 'vault-heading', 'The vault collection', 160, 6711, 1601, 406.872),
    ('1668', 'vault-products', 'The vault products', 160, 7173.872, 1601, 1300),
    ('1926', 'see-more', 'See more products', 867, 8513.872, 187, 46),
    ('2057', 'weekly-bonus', 'Weekly bonus drop', 0, 8664, 1921, 1392),
    ('1064', 'footer', 'MIKOLO footer', 0, 10160, 1920, 599),
]

def power_level_reveal(fragment):
    """Use Figma's white frame as a tiled, scroll-driven reveal stencil."""
    start = re.search(r'<div\b[^>]*data-node-id="541:1279"[^>]*>', fragment)
    end = re.search(r'<div\b[^>]*data-node-id="541:1313"[^>]*>', fragment)
    if not start or not end:
        raise RuntimeError('Power-level artwork boundaries are missing.')
    white_asset = 'assets/figma/power-level-white/551-3475.png'
    if not (ROOT / 'dist' / white_asset).is_file():
        raise RuntimeError('Original Figma power-level white asset is missing.')
    pixels = []
    for row in range(12):
        for column in range(24):
            # A fixed spatial seed preserves the same stepped outline on reverse
            # scrolling. Only the mask changes; the original Figma layers stay put.
            distance = math.hypot((column + .5 - 12) / 12, (row + .5 - 6) / 6)
            jitter = (((column * 37 + row * 53 + column * row * 11) % 29) / 28 - .5) * .16
            threshold = min(1, max(0, (distance + jitter - .06) / 1.28))
            entry = 8 + threshold * 80
            starter = ' data-start-visible' if row in (5, 6) and column in (11, 12) else ''
            pixels.append(f'<image class="power-pixel"{starter} href="{white_asset}" '
                          f'x="{column * 80}" y="{row * 80}" width="{min(80.75, 1920 - column * 80)}" height="{min(80.75, 925 - row * 80)}" '
                          f'preserveAspectRatio="none" style="--pixel-entry:{entry:.2f}%;--pixel-end:{entry + .6:.2f}%"/>')
    stencil = ('<svg class="power-pixel-definitions" aria-hidden="true" width="0" height="0">'
               '<defs><mask id="power-level-pixel-mask" maskUnits="userSpaceOnUse" '
               'maskContentUnits="userSpaceOnUse" x="0" y="0" width="1920" height="925" style="mask-type:alpha">'
               + ''.join(pixels) + '</mask></defs></svg>')
    scene = ('<div class="power-level-reveal" data-node-id="551:3474" data-name="闯关板块">'
             + stencil + '<div class="power-level-art"><div class="power-level-source">'
             + fragment[start.start():end.start()]
             + '</div></div></div>')
    return fragment[:start.start()] + scene + fragment[end.start():]

def inline_style(match):
    body = match.group(1)
    props = []
    property_pattern = r'(\w+):\s*("(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\')'
    for item in re.finditer(property_pattern, body):
        name, quoted = item.groups()
        name = re.sub(r'[A-Z]', lambda m: '-' + m[0].lower(), name)
        value = quoted[1:-1].replace('\\"', '"').replace("\\'", "'")
        props.append(name + ':' + value)
    if re.sub(property_pattern, '', body).strip(' \t\r\n,'):
        raise RuntimeError('Unsupported JSX inline style: ' + body)
    return 'style="' + html.escape(';'.join(props), quote=True) + '"'

def featured_package_art(fragment):
    """Show the supplied composites while preserving the original hit areas."""
    for asset in (PACKAGE_THUMBNAIL, PACKAGE_FULL):
        if not (ROOT / 'dist' / asset).is_file() or not (ROOT / 'dist' / asset).stat().st_size:
            raise RuntimeError('Missing supplied package artwork: ' + asset)
    # The uploaded artwork already includes all text and buttons. Keep their
    # original HTML geometry as a transparent interaction/accessibility layer,
    # without loading or painting any of the superseded image assets.
    controls = re.sub(r'<img\b[^>]*>', '', fragment)
    return ('<div class="featured-raster-scene">'
            f'<img class="featured-full-art" src="{PACKAGE_FULL}" width="3840" height="2160" alt="" decoding="async">'
            '<div class="featured-preview-window" aria-hidden="true">'
            f'<img class="featured-preview-art" src="{PACKAGE_THUMBNAIL}" width="3840" height="2160" alt="" decoding="async">'
            '</div><div class="featured-interaction-layer">' + controls
            + '</div>' + package_option_controls()
            + '<!-- featured-shop-hover-art --></div>')

def package_option_controls():
    """Native, independent checkboxes over the original accessory artwork.

    The supplied thumbnail contains eight unchecked option tiles. Reuse those
    source windows without editing either PNG so baked-in checks can be removed.
    Source and target coordinates differ slightly between the two supplied PNGs.
    """
    if not (ROOT / 'dist' / PACKAGE_OPTION_CHECK).is_file():
        raise RuntimeError('Missing original Figma accessory check artwork.')
    groups = []
    title = '2-in-1 Leg Press Hack Squat Machine Combo DD10'
    for side, target_x, source_x, ids in [
        ('left', 364, 364, ['1937', '1949', '1961', '1972']),
        ('right', 1054, 1053, ['1999', '2011', '2023', '2034']),
    ]:
        options = []
        for index, node_id in enumerate(ids):
            column, row = index % 2, index // 2
            top = 89.2 if row else (1 if column else 0)
            height = 75.2 if index == 0 else 73.2
            source_y = 719 if row else 631
            source_column = source_x + column * 271
            checked = ' checked' if index == 0 else ''
            input_id = 'package-addon-' + node_id
            options.append(
                f'<label class="package-option" data-package-option="{node_id}" '
                f'data-ui-control for="{input_id}" '
                f'style="left:{column * 271}px;top:{top}px;height:{height}px;'
                f'--option-source-x:{source_column}px;--option-source-y:{source_y}px;'
                f'--option-source-scale:{height / 74:.12f}">'
                f'<input class="package-option-input" type="checkbox" id="{input_id}" '
                f'name="{side}_package_addons" value="{node_id}"{checked}>'
                f'<span class="package-option-label-text">{side.title()} package accessory {index + 1}: {title}</span>'
                '<span class="package-option-art" aria-hidden="true">'
                '<span class="package-option-base"></span>'
                f'<img class="package-option-check" src="{PACKAGE_OPTION_CHECK}" '
                'width="18" height="18" alt=""></span></label>')
        groups.append(f'<fieldset class="package-option-group" data-package-group="{side}" '
                      f'style="left:{target_x}px"><legend class="package-option-label-text">'
                      f'{side.title()} package accessories</legend>' + ''.join(options) + '</fieldset>')
    return '<div class="package-options">' + ''.join(groups) + '</div>'

def convert_reference(source, node_label, assets, style_index, css, audit):
    prefix = re.search(r'const assetPathPrefix = "([^"]+)";', source)[1]
    image_vars = {m[1]: prefix + '/' + m[2] for m in re.finditer(r'const (\w+) = `\$\{assetPathPrefix\}/([^`]+)`;', source)}
    fragment = source.split('  return (', 1)[1].split('\n  );', 1)[0].strip()
    def image_ref(match):
        name = match[1]
        url = image_vars[name]
        local = assets.get(url, url if url.startswith('assets/') else None)
        if local is None:
            raise RuntimeError('Unmapped Figma asset: ' + name)
        if not (ROOT / 'dist' / local).is_file() or not (ROOT / 'dist' / local).stat().st_size:
            raise RuntimeError('Missing original Figma asset: ' + local)
        audit.append({'node': node_label, 'variable': name, 'asset': local})
        return 'src="' + local + '"'
    fragment = re.sub(r'src=\{(\w+)\}', image_ref, fragment)
    fragment = re.sub(r'style=\{\{(.*?)\}\}', inline_style, fragment)
    fragment = re.sub(r'\{`([^`]*)`\}', lambda m: html.escape(m[1]), fragment)
    fragment = re.sub(r'\{"([^"}]*)"\}', lambda m: html.escape(m[1]), fragment)
    fragment = re.sub(r"\{'([^'}]*)'\}", lambda m: html.escape(m[1]), fragment)
    def class_ref(match):
        classes = match[1]
        if classes not in style_index:
            key = 'f' + str(len(style_index) + 1)
            style_index[classes] = key
            style = declarations(classes)
            tokens = set(classes.split())
            if {'text-ellipsis', 'h-[62px]'} <= tokens:
                style += 'display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:2;line-clamp:2;'
            css.append('.' + key + '{' + style + '}')
        return 'class="' + style_index[classes] + '"'
    fragment = re.sub(r'className="([^"]*)"', class_ref, fragment)
    # JSX permits self-closing containers; HTML requires their end tags.
    fragment = re.sub(r'<(div|p|span)(\s[^<>]*?)\s*/>', lambda m: '<' + m[1] + m[2] + '></' + m[1] + '>', fragment)
    fragment = re.sub(r'>[ \t]*\n[ \t]*', '>', fragment)
    fragment = re.sub(r'[ \t]*\n[ \t]*<', '<', fragment)
    fragment = re.sub(r'\n[ \t]+', ' ', fragment)
    return fragment

def native_button(fragment, node_id):
    """Keep the Figma subtree while giving a real action native semantics."""
    start = re.search(r'<div\b[^>]*data-node-id="' + re.escape(node_id) + r'"[^>]*>', fragment)
    if not start:
        raise RuntimeError('Missing action button: ' + node_id)
    depth = 1
    for end in re.finditer(r'<(/?)div\b[^>]*>', fragment[start.end():]):
        depth += -1 if end[1] else 1
        if depth == 0:
            closing_start = start.end() + end.start()
            closing_end = start.end() + end.end()
            return (fragment[:start.start()] + start[0].replace('<div', '<button type="button"', 1)
                    + fragment[start.end():closing_start] + '</button>' + fragment[closing_end:])
    raise RuntimeError('Unbalanced action button: ' + node_id)

def build(reference_dir):
    assets = json.loads((ROOT / 'scripts/asset-map.json').read_text(encoding='utf-8'))
    style_index = {}
    css = []
    fragments = []
    audit = []
    for node_id, asset in HOVER_ASSETS.items():
        if not (ROOT / 'dist' / asset).is_file() or not (ROOT / 'dist' / asset).stat().st_size:
            raise RuntimeError('Missing original Figma hover asset: ' + asset)
        audit.append({'node': node_id, 'variable': 'css-hover-artwork', 'asset': asset})
    for node, slug, label, x, y, width, height in SECTIONS:
        source = (reference_dir / f'figma-541-{node}.txt').read_text(encoding='utf-8')
        fragment = convert_reference(source, '541:' + node, assets, style_index, css, audit)
        if node == '1320':
            old_thumbnail = 'assets/figma/72e642b0-3b1e-4074-8734-3ec57f3fdac3/55950.png'
            fragment = fragment.replace(old_thumbnail, PACKAGE_THUMBNAIL)
            for placement in audit:
                if placement['node'] == '541:1320' and placement['asset'] == old_thumbnail:
                    placement.update(asset=PACKAGE_THUMBNAIL, source='user-provided')
        if node == '1931':
            fragment = featured_package_art(fragment)
            audit[:] = [placement for placement in audit if placement['node'] != '541:1931']
            audit.extend({'node': '541:1931', 'variable': variable, 'asset': asset, 'source': 'user-provided'}
                         for variable, asset in [('packageFull', PACKAGE_FULL), ('packagePreview', PACKAGE_THUMBNAIL)])
            audit.extend({'node': '541:' + option_id, 'variable': 'package-option-base', 'asset': PACKAGE_THUMBNAIL,
                          'source': 'user-provided'} for option_id in sorted(PACKAGE_OPTION_IDS))
            audit.extend({'node': '541:' + option_id, 'variable': 'package-option-check', 'asset': PACKAGE_OPTION_CHECK}
                         for option_id in sorted(PACKAGE_OPTION_IDS))
        if node == '1250':
            fragment = fragment.replace('data-node-id="541:1255"', 'data-node-id="541:1255" data-countdown')
            for number_id, unit in [('1259', 'days'), ('1265', 'hours'), ('1271', 'minutes'), ('1277', 'seconds')]:
                fragment = fragment.replace(f'data-node-id="541:{number_id}"', f'data-node-id="541:{number_id}" data-countdown-unit="{unit}"')
            fragment = power_level_reveal(fragment)
        if node == '1215':
            for button_id in ['1221', '1229', '1234', '1239', '1245']:
                fragment = fragment.replace(f'data-node-id="541:{button_id}"', f'data-node-id="541:{button_id}" tabindex="0"')
        if node in ('1329', '1627'):
            row_id = '1333' if node == '1329' else '1631'
            outline_asset = '268ac.svg' if node == '1329' else '1c658.svg'
            fragment = fragment.replace(f'data-node-id="541:{row_id}"', f'data-node-id="541:{row_id}" data-coupon-marquee')
            fragment = re.sub(r'(<img\b[^>]*src="[^"]+/' + re.escape(outline_asset) + '")',
                              r'\1 data-coupon-outline', fragment)
        if node == '2057':
            # Replace only the decorative art; the original gradient, title,
            # CTA, and following content keep their Figma positions.
            pattern = r'(<div[^>]*data-node-id="541:2060"[^>]*>)<img[^>]*src="([^"]+)"[^>]*>'
            def weekly_bonus_video(match):
                return (match[1] + '<video class="weekly-bonus-video" data-weekly-bonus-video '
                        'data-src="assets/video/weekly-bonus.mp4" width="1920" height="960" '
                        'poster="' + match[2] + '" autoplay muted loop playsinline '
                        'loading="lazy" preload="metadata" aria-hidden="true"></video>')
            fragment, count = re.subn(pattern, weekly_bonus_video, fragment)
            if count != 1:
                raise RuntimeError('Expected one weekly bonus illustration to replace.')
            fragment = native_button(fragment, '541:2064')
        def control_attributes(match):
            node_id = match[1]
            attributes = match[0]
            if node_id in CONTROL_IDS:
                attributes += ' data-ui-control'
            if node_id in PRODUCT_CARD_IDS:
                attributes += ' data-product-card'
            if node_id in FLIP_PRODUCT_CARD_IDS:
                attributes += ' data-product-flip'
            if node_id in PRODUCT_CART_IDS:
                attributes += ' data-product-cart'
            if node_id in PRODUCT_ENTRY_PARTS:
                attributes += f' data-product-entry-part="{PRODUCT_ENTRY_PARTS[node_id]}"'
            if node_id in CONTENT_ENTRY_DELAYS:
                attributes += f' data-content-entry="{CONTENT_ENTRY_DELAYS[node_id]}"'
                if node_id in {'1322', '1324', '1325'}:
                    attributes += ' data-content-entry-inner'
            if node_id in PACKAGE_OPTION_IDS:
                # The native labelled checkboxes own interaction and accessibility.
                # Keep the superseded source geometry without duplicate controls.
                attributes += ' inert aria-hidden="true"'
            if node_id == '1926':
                attributes += ' data-see-more-hover tabindex="0"'
            if node_id == '2064':
                attributes += ' data-bonus-enter-hover tabindex="0"'
            if node_id in {'1987', '2049'}:
                side = 'left' if node_id == '1987' else 'right'
                attributes += f' data-shop-now="{side}" tabindex="0"'
            if node_id in VAULT_TAB_IDS:
                state = 'selected' if node_id == '1670' else 'unselected'
                attributes += f' data-vault-tab="{state}" tabindex="0"'
            return attributes
        fragment = re.sub(r'data-node-id="541:(\d+)"', control_attributes, fragment)
        if re.search(r'=\s*\{|className=|\{(?:`|["\']|[A-Za-z_$]|\{)|export default', fragment):
            raise RuntimeError('Untranslated JSX in ' + node)
        section_x, section_y = (0, 0) if node == '1215' else (x, y)
        section_focus = ' tabindex="-1"' if node == '1931' else ''
        section = f'<section id="{slug}" aria-label="{label}" class="design-section"{section_focus} style="left:{section_x}px;top:{section_y}px;width:{width}px;height:{height}px">{fragment}</section>'
        if node == '1215':
            # The track spans the remaining artboard without occupying flow.
            # The original navigation can stick while every section keeps its
            # measured Figma coordinates and the canvas keeps its full height.
            section = (f'<div class="campaign-sticky-track" style="left:{x}px;top:{y}px;width:{width}px">'
                       + '<div class="campaign-sticky-sentinel" aria-hidden="true"></div>'
                       + section + '</div>')
        fragments.append(section)
    # Stable layout bounds for navigation state. The displayed product scene
    # transforms during scrolling, so it cannot be the observation target.
    featured_start = next(section[4] for section in SECTIONS if section[1] == 'customize')
    featured_end = next(section[4] + section[6] for section in SECTIONS
                        if section[1] == 'featured-packages')
    fragments.append('<div class="featured-navigation-region" aria-hidden="true" '
                     f'style="left:0px;top:{featured_start}px;width:1920px;'
                     f'height:{featured_end - featured_start}px"></div>')
    hover_source = (reference_dir / 'figma-594-1618.txt').read_text(encoding='utf-8')
    hover_fragment = convert_reference(hover_source, '594:1618', assets, style_index, css, audit)
    hover_fragment = hover_fragment.replace('data-node-id="594:1633"', 'data-node-id="594:1633" data-ui-control data-product-cart')
    for part_id, part in [('1623', 'image'), ('1628', 'title'), ('1630', 'price'), ('1633', 'button')]:
        hover_fragment = hover_fragment.replace(f'data-node-id="594:{part_id}"',
                                                f'data-node-id="594:{part_id}" data-product-entry-part="{part}"')
    shop_source = (reference_dir / 'figma-541-2108.txt').read_text(encoding='utf-8')
    shop_audit = []
    shop_fragment = convert_reference(shop_source, '541:2108', assets, style_index, css, shop_audit)
    # Visual copies live outside the transparent hit-area layer. They inherit
    # the same scene transform and never intercept the two original controls.
    shop_fragment = shop_fragment.replace('data-node-id=', 'data-source-node-id=')
    shop_overlays = ''.join('<div class="featured-shop-hover" data-shop-hover="' + side
                            + '" aria-hidden="true">' + shop_fragment + '</div>'
                            for side in ('left', 'right'))
    fragments = [fragment.replace('<!-- featured-shop-hover-art -->', shop_overlays)
                 for fragment in fragments]
    audit.extend(dict(placement, slot=side) for side in ('left', 'right') for placement in shop_audit)
    if UNKNOWN:
        raise RuntimeError('Unsupported Figma styles: ' + repr(sorted(UNKNOWN)))
    # Figma rounds auto-sized text boxes to full pixels; preserve those measured
    # dimensions so fractional browser font metrics cannot accumulate in grids.
    dimensions = json.loads((ROOT / 'scripts/text-dimensions.json').read_text(encoding='utf-8'))
    for node_id, size in dimensions.items():
        css.append(f'[data-node-id="{node_id}"]' + '{width:' + str(size['width']) + 'px;height:' + str(size['height']) + 'px;}')
    (ROOT / 'dist/styles.css').write_text(BASE_CSS + '\n'.join(css) + OVERRIDES, encoding='utf-8')
    document = '''<!doctype html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>MIKOLO | Black Friday Power Quest</title><meta name="description" content="MIKOLO Black Friday Power Quest — PC design preview.">
<link rel="icon" href="data:,"><link rel="stylesheet" href="fonts.css"><link rel="stylesheet" href="styles.css"><link rel="stylesheet" href="hover.css"><link rel="stylesheet" href="controls.css"><link rel="stylesheet" href="power-levels.css"><link rel="stylesheet" href="featured-art.css"><link rel="stylesheet" href="customize-motion.css"><link rel="stylesheet" href="weekly-bonus.css"><link rel="stylesheet" href="coupon-marquee.css"><link rel="stylesheet" href="product-flip.css">
<link rel="stylesheet" href="product-controls.css">
<link rel="stylesheet" href="product-entry.css">
<link rel="stylesheet" href="content-entry.css">
<link rel="stylesheet" href="campaign-sticky.css">
</head><body><main id="design-canvas" aria-label="MIKOLO Black Friday">''' + '\n'.join(fragments) + '''</main>
<template id="product-hover-template">''' + hover_fragment + '''</template>
<script src="preview.js"></script><script type="module" src="countdown.mjs"></script><script type="module" src="weekly-bonus.mjs"></script><script type="module" src="coupon-marquee.mjs"></script><script type="module" src="product-flip.mjs"></script><script type="module" src="product-entry.mjs"></script><script type="module" src="content-entry.mjs"></script><script type="module" src="campaign-actions.mjs"></script></body></html>'''
    (ROOT / 'dist/index.html').write_text(document, encoding='utf-8')
    (ROOT / 'scripts/asset-usage.json').write_text(json.dumps(audit, indent=2), encoding='utf-8')
    print(f'Built {len(SECTIONS)} sections, {len(style_index)} CSS rules, {len(audit)} asset placements.')

BASE_CSS = '''/* Exact desktop geometry from Figma frame 541:1054, 1920 x 10759. */
:root{--page-background:#030310;--font-body:"Barlow",sans-serif;--font-display:"Jersey 10",sans-serif}
*,*::before,*::after{box-sizing:border-box;border-width:0;border-style:solid}
html{margin:0;padding:0;scrollbar-width:none;background:var(--page-background)}
html::-webkit-scrollbar{display:none}
body{margin:0;padding:0;font-family:var(--font-body);font-size:16px;line-height:1.5;color:white}
p,h1,h2,h3,h4{margin:0;font-size:inherit;font-weight:inherit}
img{vertical-align:middle;max-width:100%;height:auto}
button,input{font:inherit;color:inherit;background:none;border:0;padding:0}
#design-canvas{position:relative;width:1920px;height:10759px;overflow:clip;background:var(--page-background);isolation:isolate}
.design-section{position:absolute}
'''

OVERRIDES = '''
/* Static desktop preview: buttons and tabs retain their exact default state. */
/* Figma 541:1322 contains an intentional leading space. */
[data-node-id="541:1322"]{white-space:pre}
[data-node-id="541:1320"]{overflow:clip}
/* Figma draws its text shadow behind the gradient glyph fill. */
[data-node-id="541:1259"],[data-node-id="541:1261"],
[data-node-id="541:1265"],[data-node-id="541:1267"],
[data-node-id="541:1271"],[data-node-id="541:1273"],
[data-node-id="541:1277"]{text-shadow:none;filter:drop-shadow(.8px .8px 3.2px #03784a)}
[data-node-id="541:1261"],[data-node-id="541:1267"],[data-node-id="541:1273"]{font-family:'Press Start 2P','Noto Sans SC',sans-serif;line-height:1;text-indent:17px}
/* Gradient strokes, read from the original frame rather than approximated assets. */
[data-node-id="541:1933"],[data-node-id="541:1995"]{border-image:linear-gradient(to bottom,rgba(167,237,208,0),#a7edd0) 1}
[data-node-id="541:1937"],[data-node-id="541:1999"]{border-image:linear-gradient(to bottom,#fff1a0,#f5d264 45%,#c99b36) 1}
/* Respect the original one-line and two-line ending truncation properties. */
#featured-packages [data-node-id="541:1945"],#featured-packages [data-node-id="541:1956"],
#featured-packages [data-node-id="541:1968"],#featured-packages [data-node-id="541:1979"],
#featured-packages [data-node-id="541:2007"],#featured-packages [data-node-id="541:2018"],
#featured-packages [data-node-id="541:2030"],#featured-packages [data-node-id="541:2041"]{width:124px;min-width:0;max-width:124px;white-space:nowrap;text-overflow:ellipsis}
[data-node-id="541:1062"] img{height:1px}
'''

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('reference_dir', nargs='?', type=Path, default=ROOT / 'source/figma')
    build(parser.parse_args().reference_dir)
