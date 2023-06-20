#!/usr/bin/env python

import argparse
import pandas as pd
import typing
import sys
from mhcflurry import Class1PresentationPredictor
import logging
import subprocess

# instantiate global logger object
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

def parse_args(argv=None) -> typing.List[str]:
    """
    Parse command line arguments
    :param argv: list of arguments
    :return: parsed arguments
    """
    required = True if '--version' not in sys.argv else False
    parser = argparse.ArgumentParser(description='Predicting epitopes using Mhcflurry')
    parser.add_argument('--input', required=required, help='Input file containing the protein sequences')
    parser.add_argument('--alleles', required=required, help='Input string containing the alleles')
    parser.add_argument('--output', required=required, help='Output file containing the predicted epitopes')
    parser.add_argument('--min_peptide_length', type=int, default=8, help='Minimum length of the peptides')
    parser.add_argument('--max_peptide_length', type=int, default=12, help='Maximum length of the peptides')
    parser.add_argument('--threshold', type=float, default=50, help='Threshold for the prediction')
    parser.add_argument('--version', action='store_true', help='Tool version')

    return parser.parse_args(argv)


def main():
    args = parse_args()

    min_length_given_by_mhcflurry = 8
    max_length_given_by_mhcflurry = 15

    input_file = pd.read_csv(args.input, sep='\t')
    alleles = args.alleles.split(';')
    peptides = input_file['sequence'].to_list()
    # remove peptides that are too short or too long
    for peptide in peptides:
        if len(peptide) not in set(range(args.min_peptide_length, args.max_peptide_length+1))&set(range(min_length_given_by_mhcflurry, max_length_given_by_mhcflurry+1)):
            logger.warning(f'Peptide {peptide} does not have the right length. Skipping this peptide {peptide}.')
            peptides.remove(peptide)

    # fetch model if it's not already downloaded
    model_already_dowloaded = subprocess.call(['mhcflurry-downloads', 'path', 'models_class1_presentation'],stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if model_already_dowloaded != 0:
        download_model = subprocess.run(['mhcflurry-downloads', 'fetch', 'models_class1_presentation'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if download_model.returncode != 0:
            for line in download_model.stdout.decode().splitlines():
                logger.error(line)
            raise RuntimeError("mhcflurry failed to download model file")
    # load predictor and get supported alleles
    predictor_classI = Class1PresentationPredictor.load()
    supported_alleles = predictor_classI.supported_alleles

    # predict for each allele and peptide
    tmp_dfs = []
    for allele in alleles:
        if allele in supported_alleles:
            for peptide in peptides:
                tmp_df = predictor_classI.predict(peptides=[peptide],alleles=[allele]).reset_index(drop=True)
                tmp_dfs.append(tmp_df)
                logger.debug(f'Prediction was made for allele {allele} and peptide {peptide}.')
        else:
            logger.warning(f'Allele {allele} in combination with the peptide {peptide} is not supported by mhcflurry. No prediction was made.')

    df = pd.concat(tmp_dfs, ignore_index=True, axis=0).reset_index(drop=True)
    # clean up
    df = df.rename(columns={'best_allele': 'allele'})
    df = df.drop(columns=['peptide_num'])
    df = df.drop_duplicates(subset=['peptide', 'allele'])
    # join the information on one peptide into one row -> wide format
    df = df.pivot(index='peptide', columns='allele', values=['affinity', 'processing_score', 'presentation_score', 'presentation_percentile'])
    # join the multiple columns
    df.columns = df.columns.map('_'.join).str.strip('_')
    # generate peptide column
    df = df.rename_axis('peptide').reset_index()
    #write joined df to output file
    df.to_csv(args.output, sep='\t', index=False)


if __name__ == '__main__':
    main()
