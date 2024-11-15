import argparse
import os

def main():
    parser = argparse.ArgumentParser(description="Process a file and output result")
    parser.add_argument("input_file", type=str, help="Path to the input file")

    args = parser.parse_args()

    print(args.input_file)

if __name__ == "__main__":
    main()