#!/usr/bin/env python

import argparse
import pandas as pd
import typing
import sys
import logging
import os

# Create a logger
logging.basicConfig(filename='merge_prediction_outputs.log', filemode='w',level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s', force=True)

def parse_args(argv=None) -> typing.List[str]:
    """
    Parse command line arguments
    :param argv: list of arguments
    :return: parsed arguments
    """
    required = True if '--version' not in sys.argv else False
    parser = argparse.ArgumentParser(description='Harmonize prediction outputs')
    parser.add_argument('--sample_id', required=required)
    parser.add_argument('--prediction_files', required=required, help='Lists of paths to prediction outputs')
    parser.add_argument('--input_file', required=required, help='Path to original input file')
    parser.add_argument('--file_type', required=required, help='One of 3 types: peptide, protein, or variant')

    return parser.parse_args(argv)


def main():
    args = parse_args()
    #collect all files that entail the prediction outputs
    prediction_files = args.prediction_files.split(" ")
    sample_name = args.sample_id
    file_type = args.file_type

    #TODO for meee: das ganze sieht für andere filetypen sehr anders aus (peptide hat eine sequence spalte die zu peptide umbenannt wurde)
    file_type = "peptide"
    identifier_of_file_type = "peptide"
    #open tsv file and get df
    input_file = pd.read_csv(args.input_file, sep='\t')
    #drop id column if it exists
    if "id" in input_file.columns:
        input_file = input_file.drop(columns=["id"])

    df = pd.DataFrame({"sequence":[]})
    for file in prediction_files:
        tmp_df = pd.read_csv(file, sep='\t')
        #rename peptide column to sequence
        tmp_df = tmp_df.rename(columns={"peptide":"sequence"})
        #get predictor name from folder name
        predictor = os.path.basename(file).split("_")[2][:-4]
        #add prefix to all columns except peptide
        tmp_df.columns = [f'{predictor}_{col}' if col != "sequence" else col for col in tmp_df.columns]
        df = pd.merge(df, tmp_df, on="sequence", how='outer')

    #merge input file with prediction df
    df = pd.merge(input_file, df, on="sequence", how='outer')
    #write df to tsv
    df.to_csv(f'{sample_name}_predictions.tsv', sep='\t', index=False)

if __name__ == '__main__':
    main()
