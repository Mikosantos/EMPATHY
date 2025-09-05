# in testing, run the app first by executing `python app.py` and then in another terminal, run `pytest tests/test_full.py`

from playwright.sync_api import sync_playwright
import time

BASE_URL = "http://127.0.0.1:5000"

def login(page):
    page.goto(BASE_URL)
    page.fill('input[name="email"]', "garciareinaalthea@gmail.com")
    page.fill('input[name="password"]', "qwerty12345")
    page.click('button[type="submit"]')
    page.wait_for_selector('img[alt="Journal"]')  # wait until logged in

def test_dashboard_flow():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # --- Step 1: Login ---
        login(page)

        # --- Step 2: Navigate to Dashboard ---
        page.click('img[alt="Journal"]')
        page.wait_for_selector('#dashboard-nav-icon')
        assert page.is_visible('#dashboard-nav-icon')

        # --- Step 3: Open "New Entry" modal ---
        page.click('#new-entry-nav-icon')
        page.wait_for_selector('#newEntryModal.visible')

        # --- Step 4: Fill in journal entry ---
        page.fill('input[name="title"]', "Lucky :))")
        page.fill('textarea[name="content"]', (
            "My dog passed away today. I can't stop crying. Everything feels empty without him. "
            "His bed is still in the corner, but he's not there anymore. I miss his bark, his paws "
            "tapping on the floor, everything. I keep replaying the last moments in my head. It hurts "
            "so much. The house feels cold and lonely now. I don't know how to handle this. I just "
            "want him back. I wasn't ready for this."
        ))

        # --- Step 5: Submit ---
        page.click('#modal-save')

        # --- Step 6: Wait for redirect & DB(model) to update ---
        page.wait_for_selector('#dashboard-nav-icon')
        time.sleep(2)  # optional, ensure meme loads

        # --- Step 7: Validate ---
        meme = page.query_selector('#meme-image')
        assert meme is not None, "Meme image element not found!"
        assert meme.is_visible(), "Meme image is not visible!"

        browser.close()

if __name__ == "__main__":
    test_dashboard_flow()
