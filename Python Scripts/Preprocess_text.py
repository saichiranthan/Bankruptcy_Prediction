# use venv which has nltk installed in it!

from nltk.tokenize import sent_tokenize
from typing import List, Dict, Any, Set

import os
import re
import nltk
import argparse

nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)

# remove contractions from the input file
contractions_dict = { 
    "ain't": "are not", "'s":" is", "aren't": "are not", "can't": "cannot", "can't've": "cannot have", "'cause": "because", "could've": "could have", "couldn't": "could not", "couldn't've": "could not have", "didn't": "did not", "doesn't": "does not", "don't": "do not", "hadn't": "had not", "hadn't've": "had not have", "hasn't": "has not", "haven't": "have not", "he'd": "he would", "he'd've": "he would have", "he'll": "he will", "he'll've": "he will have", 
    "how'd": "how did", "how'd'y": "how do you", "how'll": "how will", "I'd": "I would", "I'd've": "I would have", "I'll": "I will", "I'll've": "I will have", "I'm": "I am", "I've": "I have", "isn't": "is not", "it'd": "it would", "it'd've": "it would have", "it'll": "it will", "it'll've": "it will have", "let's": "let us", "ma'am": "madam", "mayn't": "may not", "might've": "might have", "mightn't": "might not", "mightn't've": "might not have", "must've": "must have", 
    "mustn't": "must not", "mustn't've": "must not have", "needn't": "need not", "needn't've": "need not have", "o'clock": "of the clock", "oughtn't": "ought not", "oughtn't've": "ought not have", "shan't": "shall not", "sha'n't": "shall not", "shan't've": "shall not have", "she'd": "she would", "she'd've": "she would have", "she'll": "she will", "she'll've": "she will have", "should've": "should have", "shouldn't": "should not", "shouldn't've": "should not have", 
    "so've": "so have", "that'd": "that would", "that'd've": "that would have", "there'd": "there would", "there'd've": "there would have", "they'd": "they would", "they'd've": "they would have","they'll": "they will", "they'll've": "they will have", "they're": "they are", "they've": "they have", "to've": "to have", "wasn't": "was not", "we'd": "we would", "we'd've": "we would have", "we'll": "we will", "we'll've": "we will have", "we're": "we are", "we've": "we have", 
    "weren't": "were not","what'll": "what will", "what'll've": "what will have", "what're": "what are", "what've": "what have", "when've": "when have", "where'd": "where did", "where've": "where have", "who'll": "who will", "who'll've": "who will have", "who've": "who have", "why've": "why have", "will've": "will have", "won't": "will not", "won't've": "will not have", "would've": "would have", "wouldn't": "would not", "wouldn't've": "would not have", "y'all": "you all", 
    "y'all'd": "you all would", "y'all'd've": "you all would have", "y'all're": "you all are", "y'all've": "you all have", "you'd": "you would", "you'd've": "you would have", "you'll": "you will", "you'll've": "you will have", "you're": "you are", "you've": "you have"
 }

# groups the contractions into a regular expression like "(can't|won't)"
contractions_re = re.compile('(%s)'%'|'.join(contractions_dict.keys()))

def expand_contractions(text: str, contractions_dict: Dict[str, str] = contractions_dict) -> str:
    """
    Expand contractions in the text
    """
    def replace(match):
        return contractions_dict[match.group(0)]
    return contractions_re.sub(replace, text)

def process_data(file_path: str, token_size: int = 2000, generate_chunks: bool = False):
    """
    read a file and if need to chunk, then create chunks of text and
    rewrite it on the same file.
    """
    # not going to remove stopwords as they can change the meaning!
    with open(file_path, 'r', encoding='utf-8') as file:
        text = file.read()
        text = expand_contractions(text)
        sentences = sent_tokenize(text)
        sentences = [ " ".join(sentence.split('\n')) for sentence in sentences]
        sentences = " ".join(sentences)
        # convert to word tokenization to use it as tokens
        sentences = sentences.split()
        if(len(sentences) <= 50):
            print("removed invalid file")
            return 1
        # print(len(sentences))
        # if need to chunk the text
        os.makedirs("./processed_data", exist_ok=True)
        result_file_path = "./processed_data/" + os.path.basename(file_path)
        if(generate_chunks):
            chunks = []
            for i in range(0, len(sentences), token_size):
                chunk = " ".join(sentences[i:i+token_size])
                chunks.append(chunk)
            with open(result_file_path, 'w', encoding='utf-8') as file:
                multiline_text = "\n".join(chunks)
                file.write(multiline_text)
        else:
            with open(result_file_path, 'w', encoding='utf-8') as file:
                file.write(" ".join(sentences))
    return 0

def main():
    parser = argparse.ArgumentParser(description="Process a file and output result")
    parser.add_argument("input_file", type=str, help="Path to the input file")
    parser.add_argument("--generate_chunks", default=True, action='store_true', help="Generate chunks of text")
    parser.add_argument("--token_size", type=int, default=2000, help="Size of the chunks")

    args = parser.parse_args()

    flag = process_data(args.input_file, args.token_size, args.generate_chunks)
    if flag:
        print("Invalid file")
        os.remove(args.input_file)
    else:
        print("Processed the file!")
    
if __name__ == "__main__":
    main()