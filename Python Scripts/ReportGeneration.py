import json
from fpdf import FPDF

class PDFReport(FPDF):
    def header(self):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "Bankruptcy Prediction Report", 0, 1, "C")
        self.ln(10)
    
    def chapter_title(self, title):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, title, 0, 1)
        self.ln(5)

    def chapter_body(self, body):
        self.set_font("Arial", "", 10)
        self.multi_cell(0, 10, body)
        self.ln()

def generate_pdf_report(json_file, output_file):
    # Step 1: Load JSON data
    with open(json_file, 'r') as file:
        data = json.load(file)

    # Step 2: Extract data fields
    summary = data.get("summary", "No summary available.")
    bankruptcy_prediction_level = data.get("bankruptcy_level", "Unknown")
    entities = data.get("entities", [])
    relations = data.get("relations", [])

    # Step 3: Initialize PDF
    pdf = PDFReport()
    pdf.add_page()

    # Step 4: Add content to PDF
    pdf.chapter_title("Summary")
    pdf.chapter_body(summary)

    pdf.chapter_title("Bankruptcy Prediction Level")
    level = f'Predicted bankruptcy level of this company is {bankruptcy_prediction_level["level"]}'
    if float(bankruptcy_prediction_level["level"]) > 0.4:
        pdf.chapter_body(level + ", this company is at risk of bankruptcy.")
    elif float(bankruptcy_prediction_level["level"]) < 0.4 and float(bankruptcy_prediction_level["level"]) > 0:
        pdf.chapter_body(level + ", the company is in it critical section, this may go bankrupt.")
    else:
        pdf.chapter_body(level + ",The company is not at risk of bankruptcy.")

    pdf.chapter_title("Entities")
    entity_text = "\n".join([f"  - {entity['entity']} ({entity['type']})" for entity in entities])
    pdf.chapter_body(entity_text)

    pdf.chapter_title("Relations")
    relation_text = "\n".join([
        f"  - {relation['source']} {relation['relation']} {relation['target']}"
        for relation in relations
    ])
    pdf.chapter_body(relation_text)

    # Step 5: Save PDF to file
    pdf.output(output_file)
    print(f"PDF report generated successfully: {output_file}")

# Example usage
generate_pdf_report(r"output\ABGSHIP_2013_MDA.json", r"output\bankruptcy_report.pdf")
