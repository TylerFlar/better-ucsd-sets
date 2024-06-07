import os
import csv
import re
from collections import defaultdict


def clean_header(header):
    header = [col.replace("\n", "").strip() for col in header]
    enrolled_resp_rate_index = header.index("ENROLLED/RESP RATE")
    header[enrolled_resp_rate_index] = "ENROLLED"
    header.insert(enrolled_resp_rate_index + 1, "RESP RATE")
    return header, enrolled_resp_rate_index


def clean_instructor_name(name):
    if "," in name:
        last_name, first_name = name.split(",", 1)
        return f"{first_name.strip()} {last_name.strip()}"
    return name


def split_enrolled_resp_rate(value):
    match = re.match(r"(\d+)\((\d+\.?\d*)%\)", value)
    if match:
        return int(match.group(1)), float(match.group(2))
    return value, 0


def clean_avg_grade_received(value):
    if "(N/A)" in value:
        return ""
    return float(value[:4].strip())


def clean_course_name(course_name):
    return course_name[:-6] if len(course_name) > 6 else course_name


def clean_row(row, indices):
    (
        instructor_index,
        enrolled_resp_rate_index,
        avg_grade_received_index,
        course_index,
        term_index,
    ) = indices
    row = [col.replace("\n", "").strip() for col in row]

    if instructor_index != -1:
        row[instructor_index] = clean_instructor_name(row[instructor_index])

    if enrolled_resp_rate_index != -1:
        enrolled, resp_rate = split_enrolled_resp_rate(row[enrolled_resp_rate_index])
        row[enrolled_resp_rate_index] = enrolled
        row.insert(enrolled_resp_rate_index + 1, resp_rate)

    if avg_grade_received_index != -1:
        row[avg_grade_received_index] = clean_avg_grade_received(
            row[avg_grade_received_index]
        )

    if course_index != -1:
        row[course_index] = clean_course_name(row[course_index])

    return row


def combine_rows(rows, indices):
    combined_data = defaultdict(lambda: defaultdict(list))
    (
        instructor_index,
        term_index,
        enrolled_index,
        resp_rate_index,
        avg_grade_received_index,
    ) = indices

    for row in rows:
        instructor_term = (row[instructor_index], row[term_index])
        combined_data[instructor_term]["rows"].append(row)
        combined_data[instructor_term]["ENROLLED"].append(row[enrolled_index])
        combined_data[instructor_term]["RESP_RATE"].append(row[resp_rate_index])

    combined_rows = []

    for (instructor, term), data in combined_data.items():
        combined_row = data["rows"][0].copy()
        total_enrolled = sum(data["ENROLLED"])
        weighted_resp_rate = (
            sum(e * r for e, r in zip(data["ENROLLED"], data["RESP_RATE"]))
            / total_enrolled
        )
        combined_row[enrolled_index] = total_enrolled
        combined_row[resp_rate_index] = round(weighted_resp_rate, 2)

        for i in range(len(data["rows"][0])):
            if (
                i != enrolled_index
                and i != resp_rate_index
                and isinstance(data["rows"][0][i], float)
            ):
                weighted_average = sum(
                    row[i] * row[enrolled_index] * row[resp_rate_index]
                    for row in data["rows"]
                ) / sum(
                    row[enrolled_index] * row[resp_rate_index] for row in data["rows"]
                )
                combined_row[i] = round(weighted_average, 2)

        combined_rows.append(combined_row)

    return combined_rows


def clean_data(input_file, output_file):
    with open(input_file, mode="r", newline="", encoding="utf-8-sig") as infile:
        reader = csv.reader(infile)
        rows = list(reader)

    if not rows:
        return

    header, enrolled_resp_rate_index = clean_header(rows[0])
    instructor_index = header.index("INSTRUCTOR")
    avg_grade_received_index = header.index("AVG GRADE RECEIVED")
    course_index = header.index("COURSE")
    term_index = header.index("TERM")

    cleaned_rows = [
        clean_row(
            row,
            (
                instructor_index,
                enrolled_resp_rate_index,
                avg_grade_received_index,
                course_index,
                term_index,
            ),
        )
        for row in rows[1:]
        if all(col != "N/A" and col != "" for col in row)
    ]

    if not cleaned_rows:
        return

    indices = (
        instructor_index,
        term_index,
        enrolled_resp_rate_index,
        enrolled_resp_rate_index + 1,
        avg_grade_received_index,
    )
    combined_rows = combine_rows(cleaned_rows, indices)

    if not combined_rows:
        return

    with open(output_file, mode="w", newline="", encoding="utf-8") as outfile:
        writer = csv.writer(outfile)
        writer.writerow(header)
        writer.writerows(combined_rows)


def process_directory(input_dir, output_dir):
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith(".csv"):
                input_file = os.path.join(root, file)
                relative_path = os.path.relpath(input_file, input_dir)
                output_file = os.path.join(output_dir, relative_path)
                os.makedirs(os.path.dirname(output_file), exist_ok=True)
                clean_data(input_file, output_file)
                print(f"Processed {input_file} -> {output_file}")


if __name__ == "__main__":
    input_directory = "csv"
    output_directory = "csv_cleaned"
    process_directory(input_directory, output_directory)
