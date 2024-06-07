import csv
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time
import re


class SETsScraper:
    TIMEOUT_SECONDS = 60

    def __init__(self, username, password):
        self.username = username
        self.password = password

        options = webdriver.ChromeOptions()
        options.add_argument("--ignore-certificate-errors")

        self.driver = webdriver.Chrome(options=options)

    def scrape(self):
        self.driver.get(
            "https://academicaffairs.ucsd.edu/Modules/Evals/SET/Reports/Search.aspx"
        )

        dropdown_element = WebDriverWait(self.driver, self.TIMEOUT_SECONDS).until(
            EC.presence_of_element_located((By.ID, "authtype"))
        )

        select = Select(dropdown_element)
        select.select_by_value("_eventId_authn/PasswordKrb")

        username_field = self.driver.find_element(By.ID, "ssousername")
        username_field.send_keys(self.username)
        password_field = self.driver.find_element(By.ID, "ssopassword")
        password_field.send_keys(self.password)

        login_button = self.driver.find_element(By.NAME, "_eventId_proceed")
        login_button.click()

        input("Press Enter after completing Duo authentication...")

        unit_dropdown = WebDriverWait(self.driver, self.TIMEOUT_SECONDS).until(
            EC.presence_of_element_located(
                (By.ID, "ContentPlaceHolder1_EvalsContentPlaceHolder_ddlUnit")
            )
        )
        unit_select = Select(unit_dropdown)

        for index in range(1, len(unit_select.options)):
            unit_dropdown = WebDriverWait(self.driver, self.TIMEOUT_SECONDS).until(
                EC.presence_of_element_located(
                    (By.ID, "ContentPlaceHolder1_EvalsContentPlaceHolder_ddlUnit")
                )
            )
            unit_select = Select(unit_dropdown)
            unit_select.select_by_index(index)
            unit_name = unit_select.first_selected_option.text

            time.sleep(5)

            course_dropdown = WebDriverWait(self.driver, self.TIMEOUT_SECONDS).until(
                EC.presence_of_element_located(
                    (By.ID, "ContentPlaceHolder1_EvalsContentPlaceHolder_ddlCourse")
                )
            )
            course_select = Select(course_dropdown)
            for course_index in range(1, len(course_select.options)):
                course_dropdown = WebDriverWait(
                    self.driver, self.TIMEOUT_SECONDS
                ).until(
                    EC.presence_of_element_located(
                        (By.ID, "ContentPlaceHolder1_EvalsContentPlaceHolder_ddlCourse")
                    )
                )
                course_select = Select(course_dropdown)
                course_select.select_by_index(course_index)
                course_name = course_select.options[course_index].text.strip()
                course_code = course_select.options[course_index].get_attribute("value")

                sanitized_course_code = re.sub(r'[\\/*?:"<>|]', "", course_code)

                time.sleep(5)

                self.driver.find_element(
                    By.ID, "ContentPlaceHolder1_EvalsContentPlaceHolder_btnSubmit"
                ).click()

                time.sleep(5)

                try:
                    table = WebDriverWait(self.driver, self.TIMEOUT_SECONDS).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, ".table-responsive")
                        )
                    )

                    headers = [
                        header.text
                        for header in table.find_elements(By.CSS_SELECTOR, "thead th")
                    ]
                    rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")
                    data = [
                        [cell.text for cell in row.find_elements(By.CSS_SELECTOR, "td")]
                        for row in rows
                    ]

                    dir_path = f"csv/{unit_name}"
                    os.makedirs(dir_path, exist_ok=True)

                    with open(
                        f"{dir_path}/{sanitized_course_code}.csv", mode="w", newline=""
                    ) as file:
                        writer = csv.writer(file)
                        writer.writerow(headers)
                        writer.writerows(data)

                except Exception as e:
                    print(f"No table found for {unit_name} - {course_name}. Skipping.")
                    continue

                time.sleep(
                    5
                )  # Allow time for the page to reset before the next selection

    def close_browser(self):
        self.driver.quit()


if __name__ == "__main__":
    with open("creds.txt", "r") as f:
        username = f.readline().strip()
        password = f.readline().strip()

    scraper = SETsScraper(username, password)
    scraper.scrape()
    scraper.close_browser()
