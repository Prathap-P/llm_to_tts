from playwright.sync_api import sync_playwright
import os


def get_webpage_content(url: str, cdp_url: str = "http://localhost:9222") -> dict:
    """
    Get web page content using Playwright connected to existing browser via CDP.
    
    Args:
        url: The URL to scrape
        cdp_url: Chrome DevTools Protocol endpoint (default: http://localhost:9222)
    
    Returns:
        dict containing:
            - url: The final URL after any redirects
            - title: Page title
            - content: Page text content
            - html: Page HTML content
    """
    with sync_playwright() as p:
        # Connect to existing browser via CDP
        browser = p.chromium.connect_over_cdp(cdp_url)
        
        # Get default context and pages
        context = browser.contexts[0]
        
        # Get the first page or create a new one
        if context.pages:
            page = context.pages[0]
        else:
            page = context.new_page()
        
        try:
            # Navigate to the URL
            page.goto(url, wait_until="networkidle")
            
            # Extract page information
            result = {
                "url": page.url,
                "title": page.title(),
                "content": page.inner_text("body"),
                "html": page.content()
            }
            
            return result
            
        finally:
            # Don't close the browser, just disconnect
            browser.close()


def get_webpage_content_with_selector(url: str, selector: str = None, cdp_url: str = "http://localhost:9222") -> dict:
    """
    Get specific elements from a web page using CSS selector.
    
    Args:
        url: The URL to scrape
        selector: CSS selector to extract specific content (optional)
        cdp_url: Chrome DevTools Protocol endpoint (default: http://localhost:9222)
    
    Returns:
        dict containing page data and selected content if selector provided
    """
    with sync_playwright() as p:
        # Connect to existing browser via CDP
        browser = p.chromium.connect_over_cdp(cdp_url)
        context = browser.contexts[0]
        
        if context.pages:
            page = context.pages[0]
        else:
            page = context.new_page()
        
        try:
            page.goto(url, wait_until="networkidle")
            
            result = {
                "url": page.url,
                "title": page.title(),
                "content": page.inner_text("body"),
            }
            
            # If selector provided, extract specific content
            if selector:
                elements = page.query_selector_all(selector)
                result["selected_content"] = [elem.inner_text() for elem in elements]
            
            return result
            
        finally:
            browser.close()


def navigate_and_extract_content(
    initial_url: str, 
    content_selector: str,
    cdp_url: str = "http://localhost:9222",
    wait_time: int = 5000,
    click_selector: str = None
) -> dict:
    """
    Navigate to a page, get a link from an element, open it in new tab, and extract content.
    
    Args:
        initial_url: The starting URL
        content_selector: CSS selector for the content container on the new page
        cdp_url: Chrome DevTools Protocol endpoint (default: http://localhost:9222)
        wait_time: Time to wait for elements in milliseconds (default: 5000)
        click_selector: Optional CSS selector for element to click before getting link
    
    Returns:
        dict containing extracted content with structure preserved
    """
    with sync_playwright() as p:
        # Connect to existing browser via CDP
        browser = p.chromium.connect_over_cdp(cdp_url)
        context = browser.contexts[0]
        
        if context.pages:
            page = context.pages[0]
        else:
            page = context.new_page()
        
        try:
            # Step 1: Navigate to initial URL
            print(f"Navigating to: {initial_url}")
            # Use domcontentloaded instead of networkidle for sites with lots of ongoing requests
            page.goto(initial_url, wait_until="domcontentloaded", timeout=60000)
            
            # Wait a bit for dynamic content to load
            page.wait_for_timeout(wait_time)
            
            # Step 1.5: Click on element if click_selector is provided
            if click_selector:
                print(f"Clicking element: {click_selector}")
                try:
                    page.wait_for_selector(click_selector, timeout=wait_time)
                    click_element = page.query_selector(click_selector)
                    if click_element:
                        click_element.click()
                        print("✓ Element clicked successfully")
                        # Wait for any animations or content to load after click
                        page.wait_for_timeout(2000)
                    else:
                        print("Warning: Click element not found")
                except Exception as e:
                    print(f"Warning: Could not click element: {e}")
            
            # Step 2: Get href link from the specified element
            print(f"Getting link using class name: group/notification-list-item")
            
            # Use JavaScript to find element by class name and get href from child <a> tag
            href = page.evaluate("""
                () => {
                    const element = document.getElementsByClassName('group/notification-list-item')[0];
                    if (!element) return null;
                    const anchor = element.querySelector('a');
                    if (!anchor) return null;
                    return anchor.href;
                }
            """)
            
            if not href:
                print("\nDEBUG: Could not find element or anchor tag")
                print("Page title:", page.title())
                print("Current URL:", page.url)
                
                # Try to debug what's available
                classes_found = page.evaluate("""
                    () => {
                        const elements = document.getElementsByClassName('group/notification-list-item');
                        return elements.length;
                    }
                """)
                print(f"Found {classes_found} elements with class 'group/notification-list-item'")
                
                raise Exception(f"Could not find element with class 'group/notification-list-item' or its child anchor tag")
            
            print(f"Found link: {href}")
            
            # Step 3: Open new tab with the link
            new_page = context.new_page()
            print(f"Opening new tab with: {href}")
            new_page.goto(href, wait_until="domcontentloaded", timeout=60000)
            new_page.wait_for_timeout(wait_time)
            
            # Step 4: Query the content container
            print(f"Extracting content from selector: {content_selector}")
            
            try:
                new_page.wait_for_selector(content_selector, timeout=wait_time)
            except Exception as e:
                print(f"Warning: Content element not found after {wait_time}ms wait")
            
            content_container = new_page.query_selector(content_selector)
            
            if not content_container:
                print("\nDEBUG: Could not find content container")
                print("Page title:", new_page.title())
                print("Current URL:", new_page.url)
                raise Exception(f"Could not find content element with selector: {content_selector}")
            
            # Step 5: Collect all text elements while preserving their original order
            # query_selector_all returns elements in document order (as they appear in the DOM)
            all_children = content_container.query_selector_all('p, h2, h3, h4, ul, ol, pre, code')
            
            collected_content = []
            for element in all_children:
                tag_name = element.evaluate('el => el.tagName.toLowerCase()')
                text = element.inner_text().strip()
                if text:
                    collected_content.append({
                        'tag': tag_name,
                        'text': text
                    })
            
            result = {
                'initial_url': initial_url,
                'target_url': href,
                'final_url': new_page.url,
                'title': new_page.title(),
                'content': collected_content,
                'full_text': '\n\n'.join([item['text'] for item in collected_content])
            }
            
            # Print the collected content
            print("\n" + "="*80)
            print("EXTRACTED CONTENT:")
            print("="*80 + "\n")
            for item in collected_content:
                print(f"[{item['tag'].upper()}]")
                print(item['text'])
                print()
            
            return result
            
        finally:
            browser.close()


def navigate_with_specific_selectors(initial_url: str, cdp_url: str = "http://localhost:9222") -> dict:
    """
    Convenience function with your specific selectors already configured.
    
    Args:
        initial_url: The starting URL
        cdp_url: Chrome DevTools Protocol endpoint (default: http://localhost:9222)
    
    Returns:
        dict containing extracted content
    """
    # Click this button first to reveal the link
    click_selector = "#root > div.border-subtlest.ring-subtlest.divide-subtlest.bg-base > div > div > div.group\\/sidebar.relative.z-10.hidden.min-h-0.flex-none.flex-row-reverse.md\\:flex.border-r.border-subtlest.ring-subtlest.divide-subtlest.bg-base > div.pb-md.scrollbar-none.relative.flex.h-full.flex-col.items-center.overflow-y-auto.overflow-x-hidden.border-subtlest.ring-subtlest.divide-subtlest.bg-transparent > div.gap-md.pt-sm.mt-auto.flex.w-full.min-w-0.flex-col.items-center.justify-center.\\[\\&\\>\\*\\]\\:w-full.pb-sm > div.relative.flex.flex-col.items-center.justify-center > span > div > div > button"
    
    # Extract content from this container
    content_selector = '#markdown-content-0 > div > div > div'
    
    return navigate_and_extract_content(
        initial_url=initial_url,
        content_selector=content_selector,
        cdp_url=cdp_url,
        wait_time=5000,
        click_selector=click_selector
    )


def test_cdp_connection(cdp_url: str = "http://localhost:9222") -> bool:
    """
    Test if CDP connection is working.
    
    Args:
        cdp_url: Chrome DevTools Protocol endpoint (default: http://localhost:9222)
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(cdp_url)
            context = browser.contexts[0]
            
            if context.pages:
                page = context.pages[0]
            else:
                page = context.new_page()
            
            # Try to navigate to a simple page
            page.goto("https://example.com", wait_until="networkidle")
            title = page.title()
            
            print(f"✓ CDP Connection successful!")
            print(f"  Page title: {title}")
            print(f"  URL: {page.url}")
            
            browser.close()
            return True
    except Exception as e:
        print(f"✗ CDP Connection failed: {e}")
        return False


