#!/usr/bin/env python3
"""Brand the OpenBot app bundle and page shell.

The app ships as a compiled single-page app whose brand name and sidebar are
baked into the JavaScript. This script applies the same edits we use, so a new
upstream image can be re-branded in seconds:

  python3 patch-app-bundle.py \
      --bundle  path/to/index-CbN6XavV.js \
      --html    path/to/index.html \
      --brand   "Your Brand" \
      --vault   https://vault.example.com/mybots/ \
      --graph   https://vault.example.com/mybots/graph.html

What it does:
  * sets the product name the app shows (it is a hard-coded default upstream)
  * adds sidebar links: Obsidian Graph, Obsidian Vault, OpenRouter, Help
  * leaves a cache-buster on the script tag so browsers pick the change up

Re-run it after every OpenBot update; see docs/updating-from-openbot.md.
"""
import argparse
import pathlib
import re
import sys

NAV_ITEM = (
    'c.jsx(oc,{{children:c.jsxs(td,{{className:"hover:bg-foreground/5 h-10",'
    'render:p=>c.jsx("a",{{...p,href:"{href}"{extra}}}),'
    'children:[c.jsx("div",{{className:"size-[28px] flex items-center justify-center",'
    'children:c.jsx(Cge,{{}})}}),'
    'c.jsx("span",{{className:"text-sm trackint-tight",children:"{label}"}})}}])}}),'
)


def patch_bundle(path: pathlib.Path, brand: str, links: list[tuple[str, str]]) -> None:
    text = path.read_text()

    # 1. the product name the app renders (upstream default: "OpenBot")
    text = text.replace('productName:"OpenBot"', f'productName:"{brand}"')

    # 2. sidebar links, inserted above Skills and below it as configured
    for label, href, where in links:
        if f'children:"{label}"' in text:
            continue
        item = NAV_ITEM.format(href=href, label=label, extra='')
        if where == "above-skills":
            anchor = ('children:[c.jsx(oc,{children:c.jsxs(td,{className:"hover:bg-foreground/5 h-10",'
                      'render:p=>c.jsx(er,{...p,to:"/skills"')
            if anchor not in text:
                print(f"  ! could not find the Skills item to insert {label} above")
                continue
            text = text.replace(anchor, "children:[" + item + anchor[len("children:["):], 1)
        elif where == "above-vault":
            anchor = ('children:[c.jsx(oc,{children:c.jsxs(td,{className:"hover:bg-foreground/5 h-10",'
                      'render:p=>c.jsx("a",{...p,href:"' + links[1][1] + '"})')
            if anchor not in text:
                print(f"  ! could not find the vault item to insert {label} above")
                continue
            text = text.replace(anchor, "children:[" + item + anchor[len("children:["):], 1)
        else:  # below OpenRouter / after a given marker
            anchor = 'children:"OpenRouter"})]})}),c.jsx(oc,{children:c.jsxs(o$,'
            if anchor not in text:
                print(f"  ! could not find the OpenRouter item to insert {label} after")
                continue
            text = text.replace(anchor, 'children:"OpenRouter"})]})}),' + item + 'c.jsx(oc,{children:c.jsxs(o$,', 1)

    path.write_text(text)
    print(f"  bundle patched: {path}")


def patch_html(path: pathlib.Path, brand: str) -> None:
    text = path.read_text()
    text = re.sub(r"<title>[^<]*</title>", f"<title>{brand}</title>", text, count=1)
    # cache-buster so a re-branded bundle is actually fetched
    text = re.sub(r'(/assets/index-[A-Za-z0-9]+\.js)(\?v=\d+)?', r"\1?v=1", text)
    path.write_text(text)
    print(f"  page shell patched: {path}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundle", required=True, type=pathlib.Path)
    ap.add_argument("--html", required=True, type=pathlib.Path)
    ap.add_argument("--brand", required=True)
    ap.add_argument("--vault", required=True, help="vault page URL, e.g. https://vault.example.com/mybots/")
    ap.add_argument("--graph", required=True, help="graph page URL, e.g. .../graph.html")
    ap.add_argument("--openrouter", default="https://openrouter.ai/")
    ap.add_argument("--help", default="/help/")
    args = ap.parse_args()

    links = [
        ("Obsidian Graph", args.graph, "above-vault"),
        ("Obsidian Vault", args.vault, "above-skills"),
        ("OpenRouter", args.openrouter, "above-help"),
        ("Help", args.help, "above-help"),
    ]
    if not args.bundle.exists() or not args.html.exists():
        print("bundle or html not found", file=sys.stderr)
        return 1
    patch_bundle(args.bundle, args.brand, links)
    patch_html(args.html, args.brand)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())