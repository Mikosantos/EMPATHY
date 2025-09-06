# in testing, run the app first by executing `python app.py` and then in another terminal, run `pytest -s -v tests/test_1.py`
import time
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "http://127.0.0.1:5000"

@pytest.fixture(scope="module")
def driver():
    driver = webdriver.Chrome()
    driver.maximize_window()
    yield driver
    driver.quit()

def login(driver):
    driver.get(BASE_URL)

    email_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "email"))
    )
    email_field.send_keys("garciareinaalthea@gmail.com")
    time.sleep(1)
    password_field = driver.find_element(By.NAME, "password")
    password_field.send_keys("qwerty12345")
    time.sleep(1)
    # Click submit
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'img[alt="Journal"]'))
    )

def test_dashboard_flow(driver):
    # --- Step 1: Login ---
    login(driver)
    print(f"✅ Logged in successfully.")

    time.sleep(3)

    # --- Step 2: Navigate to Dashboard ---
    dashboard_btn =  WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//img[@alt='Dashboard']"))
    )
    assert dashboard_btn.is_displayed()
    time.sleep(3)
    dashboard_btn.click()
    print(f"✅ Dashboard button found and clicked.")
    time.sleep(3)

    # --- Step 3: Open "New Entry" modal ---
    new_entry_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "new-entry-nav-icon"))
    )
    new_entry_btn.click()
    print("✅ New Entry button clicked.")

    modal = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "#newEntryModal.visible"))
    )
    assert modal.is_displayed()
    print("✅ New Entry modal is visible.")

    # --- Step 4: Fill in journal entry ---
    driver.find_element(By.NAME, "title").send_keys("Lucky :))")
    time.sleep(1)
    content = (
        "My dog passed away today. I can't stop crying. Everything feels empty without him. "
        "His bed is still in the corner, but he's not there anymore. I miss his bark, his paws "
        "tapping on the floor, everything. I keep replaying the last moments in my head. It hurts "
        "so much. The house feels cold and lonely now. I don't know how to handle this. I just "
        "want him back. I wasn't ready for this."
    )
    driver.find_element(By.NAME, "content").send_keys(content)
    time.sleep(3)
    print("✅ Inputted contents into the journal entry successfully.")

    # --- Step 5: Submit ---
    save_btn = driver.find_element(By.ID, "modal-save")
    assert save_btn.is_displayed()
    if save_btn:
        save_btn.click()
        print("✅ Save button found and clicked.")
    time.sleep(1)

    # --- Step 6: Validate ---
    first_entry = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".entry-item.selected"))
    )
    time.sleep(1)

    # Title check (left panel)
    entry_title = first_entry.find_element(By.CSS_SELECTOR, ".title").text
    assert entry_title == "Lucky :))", f"Expected title 'Lucky :))', got '{entry_title}'"
    print("✅ Matched title. (left panel)")
    time.sleep(1)

    # Snippet check (left panel)
    entry_content_snippet = first_entry.find_element(By.CSS_SELECTOR, ".content").text
    expected_full_content = content
    expected_snippet = expected_full_content[:150]
    time.sleep(1)
    assert entry_content_snippet.startswith(expected_snippet[:140]), (
        f"Snippet mismatch. Expected starting with '{expected_snippet[:140]}', "
        f"but got '{entry_content_snippet}'"
    )
    print("✅ Matched snippet. (left panel)")

    time.sleep(1)
    # Full content check (right panel)
    full_content = driver.find_element(By.ID, "entry-content").text
    assert full_content == expected_full_content, (
        "Full entry content does not match.\n"
        f"Expected:\n{expected_full_content}\nGot:\n{full_content}"
    )
    print("✅ Matched content. (right panel)")
    time.sleep(1)
    
    meme = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "#meme-image"))
    )
    assert meme.is_displayed(), "Meme image is not visible!"
    print("✅ Meme image is visible!")
    time.sleep(1)

    # Close the browser
    driver.quit()