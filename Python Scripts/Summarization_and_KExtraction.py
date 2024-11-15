from dotenv import load_dotenv
from typing import List, Dict
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from difflib import SequenceMatcher
from tqdm import tqdm

import os
import re
import time
import json
import argparse

# Load the API key from the .env file
load_dotenv()

api_key = os.getenv("API_KEY1")

# create a schema for your json output
class Relation(BaseModel):
    source: str = Field(description="Source entity of the relation")
    target: str = Field(description="Target entity of the relation")
    relation: str = Field(description="Relation between the source and target entities")

class Entity(BaseModel):
    name: str = Field(description="Name of the entity", alias="entity")
    type: str = Field(description="Type of the entity")

class BankruptcyLevel(BaseModel):
    level: str = Field(description="Bankruptcy level of the company")

class Summary(BaseModel):
    summary: str = Field(description="Summary of the input text")
    bankruptcy_level: BankruptcyLevel = Field(description="Bankruptcy level of the company")
    entities: List[Entity] = Field(description="Entities extracted from the input text")
    relations: List[Relation] = Field(description="Relations extracted from the input text")

class EntityNormalizer:
    def __init__(self):
        self.company_suffixes = {
            'limited', 'ltd', 'llc', 'inc', 'incorporated', 'corporation', 'corp',
            'enterprise', 'enterprises', 'company', 'co', 'group', 'holdings',
            'plc', 'ag', 'sa', 'nv', 'private', 'pvt'
        }
        self.known_entities = {}  # Maps normalized names to canonical names

    def normalize_name(self, name: str) -> str:
        name = name.lower()
        name = ' '.join(name.split())
        name = re.sub(r'[^\w\s&0-]', '', name)
        words = name.split()
        cleaned_words = [w for w in words if w not in self.company_suffixes]

        if cleaned_words:
            return ' '.join(cleaned_words)
        return name
    
    def are_similar_entities(self, name1, name2, threshold = 0.95):
        norm1 = self.normalize_name(name1)
        norm2 = self.normalize_name(name2)

        if norm1 == norm2:
            return True
        
        similarity = SequenceMatcher(None, norm1, norm2).ratio()
        return similarity >= threshold
    
    def get_canonical_name(self, name: str) -> str:
        normalized = self.normalize_name(name)

        for known_norm, canonical in self.known_entities.items():
            if self.are_similar_entities(normalized, known_norm):
                return canonical
            
        self.known_entities[normalized] = name
        return name
    
class SnKExtractor:
    def __init__(self, api_key: str, model: str = "llama-3.1-70b-versatile"):
        os.environ["GROQ_API_KEY"] = api_key
        self.llm = ChatGroq(temperature=0.5, model_name = model)
        self.parser = PydanticOutputParser(pydantic_object=Summary)
        self.prompt = self._create_prompt()
        self.entity_normalizer = EntityNormalizer()

    def _create_prompt(self):
        template = """You are a financial Summarization and Knowledge Extraction System. Your task is to summarize and extract entities and relation from the given text and format them exactly according to the specified JSON structure. Only output the JSON structure, nothing else.

Extract the following information from the given financial text of a company:

Entities should be one of these types:
1. COMPANY
2. EVENT
3. PRODUCT

Relations should be one of these types:
1. PARTICIPATES_IN (COMPANY -> EVENT)
- Properties: Role (Organizer, Participant, Sponsor), Effect (-1 to 1)
2. PRODUCES (COMPANY -> PRODUCT)
- Properties: Production Volume, Production Start Date
3. MENTIONS (EVENTS -> COMPANY/PRODUCT)
- Properties: Sentiment (-1 to 1), Mention Count
4. OWNS (COMPANY -> COMPANY)
- Properties: Ownership Percentage, Acquisition Date
5. COMPETES_WITH (COMPANY -> COMPANY)
- Properties: Market Overlap Percentage
6. HAD_NEGATIVE_IMPACT_ON (EVENT -> COMPANY)
- Properties: Impact Level (0 to 1), Impact Type (Financial, Reputation, Legal), Reason
7. HAD_POSITIVE_IMPACT_ON (EVENT -> COMPANY)
- Properties: Impact Level (0 to 1), Impact Type (Financial, Reputation, Legal), Reason

Summary should be the main content of the whole text provided.
- Include the company's name and the bankruptcy level of the company.
- Include the reason for the bankruptcy and the impact of the bankruptcy on the company.
- Include the company's financial status and the company's future prospects.

Bankruptcy Level should be between (-1 to 1), where -1 is the lowest level of bankruptcy and 1 is the highest level of bankruptcy.
- Conclude corresponding to the sentiment of the company's financial status and future prospects.
- If the company would not be bankrupt, the bankruptcy level should be -1. (Healthy Company)
- If the comapny would be bankrupt, the bankruptcy level should be between 0.4 to 1. (Bankrupt Company)
- If the company is in a critical situation, the bankruptcy level should be between 0 to 0.4. (Critical Company)

Rules:
1. Use full Company names consistently 
2. Do not repeat the contents
3. Normalize company names (e.g., if "Apple Inc." and "Apple Corporation" refer to the same company, use one consistent name)
4. Output must be valid JSON format
5. Use only the predefined entities and relations type
6. The source and target have to be added as entities before forming a relation
7. Focus mainly on the impacts of events on the company in relation extractions
8. Impact level should be between 0 to 1 for both positive and negative impacts, 0 means no impact and 1 means the highest impact
9. Bankruptcy level should be between -1 to 1
10. Bankruptcy level should be concluded based on the sentiment of the company's financial status and future prospects
11. Bankruptcy level should be between 0.4 to 1 if the sentiment of the text is negative and -1 to 0 if the sentiment of the text is positive
12. Must create properties related to relations based on the given information in the text

Input text: {text}

{format_instructions}
"""
        return ChatPromptTemplate.from_template(template)

    def extract_summary_and_knowledge(self, financial_snippet: str, output_dir: str) -> Summary:
        retries = 0
        wait_time = 0
        while retries < 5:
            try:
                message = self.prompt.format_messages(
                    text=financial_snippet,
                    format_instructions=self.parser.get_format_instructions()
                )
                output = self.llm.invoke(message)
                retries = 0
                wait_time = 0
                return output
            except Exception as e:
                retries += 1
                wait_time += 120
                time.sleep(wait_time)
                print(F"Error during Summarization and Knowledge Extraction II: {str(e)}")
                return Summary(summary="Could not generate summary !", entities=[], relations=[], bankruptcy_level="0")
            
def main():
    parser = argparse.ArgumentParser(description="Summarize and Extract Knowledge from the input file and  a file and write the output to a json file")
    parser.add_argument("input_file", type=str, help="Path to the input MD&A section of a company's financial report")

    args = parser.parse_args()

    summary_extractor = SnKExtractor(api_key=api_key)

    with open(args.input_file, "r") as f:
        text = f.readline()
        os.makedirs("./output", exist_ok=True)
        output_path = "./output"
        try:
            result = summary_extractor.extract_summary_and_knowledge(text, output_path)
            output_path = os.path.join(output_path, os.path.basename(args.input_file).replace(".txt", ".json"))
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result.model_dump(), f, indent=4)
        except Exception as e:
            print(F"Error during Summarization and Knowledge Extraction: {str(e)}")

    with open(output_path, "r", encoding='utf-8') as f:
        extracted_text = json.load(f)
        try:
            start = extracted_text['content'].find("{")
            end = extracted_text['content'].rfind("}")
            if start == 1 or end == -1:
                raise ValueError("Invalid JSON format")
            json_str = extracted_text['content'][start:end+1]
            json_obj = json.loads(json_str)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(json_obj, f, indent=4)
        except Exception as e:
            print(F"Error during JSON extraction: {str(e)}")

if __name__ == "__main__":
    main()