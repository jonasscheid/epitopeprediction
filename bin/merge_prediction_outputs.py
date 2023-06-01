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
    parser = argparse.ArgumentParser(description='Predicting epitopes using Mhcflurry')
    parser.add_argument('--data', required=required, help='The metadata Object that holds all information about the sample, allele etc.')
    parser.add_argument('--pathlist', required=required, help='Lists of paths to prediction outputs')

    return parser.parse_args(argv)


def main():
    args = parse_args()
    #collect all files that entail the prediction outputs
    prediction_files = args.pathlist.split(" ")
    sample_name = args.data[0]

    df = pd.DataFrame({"peptide":[]})
    for file in prediction_files:
        new_df = pd.read_csv(file, sep='\t')
        #get prediction name from folder name
        prediction_name = os.path.basename(file).split("_")[2][:-4]
        #add prefix to all columns except peptide
        new_df.columns = [prediction_name +"_"+col if col != "peptide" else col for col in new_df.columns]
        df = pd.merge(df, new_df, on="peptide", how='outer')

    #write df to tsv
    df.to_csv("merged_prediction.tsv", sep='\t', index=False)

if __name__ == '__main__':
    main()
