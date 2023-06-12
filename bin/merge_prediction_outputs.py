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

    return parser.parse_args(argv)


def main():
    args = parse_args()
    #collect all files that entail the prediction outputs
    prediction_files = args.prediction_files.split(" ")
    sample_name = args.sample_id

    df = pd.DataFrame({"peptide":[]})
    for file in prediction_files:
        tmp_df = pd.read_csv(file, sep='\t')
        #get predictor name from folder name
        predictor = os.path.basename(file).split("_")[2][:-4]
        #add prefix to all columns except peptide
        tmp_df.columns = [f'{predictor}_{col}' if col != "peptide" else col for col in tmp_df.columns]
        df = pd.merge(df, tmp_df, on="peptide", how='outer')

    #write df to tsv
    df.to_csv(f'{sample_name}_predictions.tsv', sep='\t', index=False)

if __name__ == '__main__':
    main()
