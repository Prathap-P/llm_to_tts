from playwright_scraper import test_cdp_connection, navigate_with_specific_selectors
from tts import generate_audio_file
from functools import reduce

if __name__ == "__main__":
    print("="*80)
    print("PLAYWRIGHT CDP SCRAPER")
    print("="*80)
    print("\nAttempting to connect to browser on http://localhost:9222")
    print("\nIf you see a connection error, start your browser with remote debugging:")
    print("  macOS: open -a 'Microsoft Edge' --args --remote-debugging-port=9222")
    print("  or: /Applications/Microsoft\\ Edge.app/Contents/MacOS/Microsoft\\ Edge --remote-debugging-port=9222")
    print("="*80 + "\n")
    
    # First test the CDP connection
    print("Testing CDP connection...")
    if not test_cdp_connection():
        print("\nPlease ensure:")
        print("  1. Your browser is running")
        print("  2. It was started with --remote-debugging-port=9222")
        print("  3. No other process is using port 9222")
        exit(1)
    
    print("\n" + "="*80)
    print("Starting main scraping task...")
    print("="*80 + "\n")
    
    try:
        initial_url = "https://www.perplexity.ai/"
        result = navigate_with_specific_selectors(initial_url)
        print(f"\n✓ Successfully extracted {len(result['content'])} elements")
        content = result['content']
        content = reduce(lambda x, y: x + y['text'], content, "")
        generate_audio_file(content, "content.wav")
        
        
    except Exception as e:
        print(f"\n✗ Error during scraping: {e}")
        print("\nNote: The selectors might need to be updated based on the current page structure.")
        print("You can modify the selectors in the navigate_with_specific_selectors() function.")
        exit(1)
