#!/usr/bin/env python3
import os
import requests
import sys
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# --- CONFIG ---
#SITEMAP_URL = "https://www.rauhauser.net/sitemap.xml"
OUTPUT_DIR = "."
try:
    SITEMAP_URL = sys.argv[1]
except:
    print("Need a target like https://whatever.substack.com/sitemap.xml\n")
    exit()
# --------------

def get_urls_from_sitemap():
    print(f"Fetching sitemap: {SITEMAP_URL}")
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(SITEMAP_URL, headers=headers)
        soup = BeautifulSoup(response.content, "xml")
        urls = [loc.text.strip() for loc in soup.find_all("loc") if "/p/" in loc.text.strip()]
        print(f"Found {len(urls)} articles.")
        return urls
    except Exception as e:
        print(f"Error fetching sitemap: {e}")
        return []

def clean_page(page):
    print("  Cleaning page DOM...")
    page.evaluate("""() => {
        const selectorsToRemove = [
            '.modal',
            '.subscribe-popup',
            '#subscribe-modal',
            '.pencraft.pc-display-flex.pc-position-fixed',
            'div[data-testid="subscribe-modal"]', 
            '.frontend-pencraft-Box-module__flex-grow--F2g5', 
            'header',
            '.post-header',
            '.secondary-navigation',
            '.right-sidebar',
            '.ac-modal-overlay',
            '.navbar',
            '.post-footer',
            '.subscribe-footer'
        ];
        
        selectorsToRemove.forEach(selector => {
            document.querySelectorAll(selector).forEach(el => el.remove());
        });

        const article = document.querySelector('.single-post'); 
        if (article) {
            article.style.width = '100%';
            article.style.maxWidth = '100%';
            article.style.margin = '0 auto';
        }
        
        // Nuke fixed elements that float over text
        document.querySelectorAll('*').forEach(el => {
            if (window.getComputedStyle(el).position === 'fixed') {
                el.remove();
            }
        });
    }""")

def scroll_to_bottom(page):
    print("  Scrolling to load images...")
    # Fast initial scroll
    for i in range(5): 
        page.mouse.wheel(0, 4000)
        page.wait_for_timeout(200)
    
    # Precise scroll to bottom to catch stragglers
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(1500)

def save_as_pdf(url, output_dir):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # CRITICAL CHANGE: emulate a high-DPI screen for better quality
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            viewport={"width": 1400, "height": 1080}, # Wider viewport
            device_scale_factor=2  # High DPI for crisp text/images
        )
        page = context.new_page()

        try:
            slug = url.split("/p/")[-1].strip('/')
            filename = f"{slug}.pdf"
            filepath = os.path.join(output_dir, filename)

            if os.path.exists(filepath):
                print(f"Skipping (exists): {filename}")
                return

            print(f"Processing: {url}")
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # 1. Force "Screen" media type so it looks like a webpage, not a printout
            page.emulate_media(media="screen")
            
            scroll_to_bottom(page)
            clean_page(page)
            
            # 2. Save PDF with background enabled
            page.pdf(
                path=filepath, 
                format="Letter", 
                print_background=True,
                margin={"top": "0.3in", "bottom": "0.3in", "left": "0.3in", "right": "0.3in"},
                scale=0.85 # Slight scale down to fit wide content better
            )
            print(f"{filename}")

        except Exception as e:
            print(f"FAILED {url}: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    urls = get_urls_from_sitemap()
    
    for url in urls:
        save_as_pdf(url, OUTPUT_DIR)
