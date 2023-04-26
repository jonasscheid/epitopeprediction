#!/usr/bin/env python

import argparse
import pandas as pd
import typing
import sys
from mhcflurry import Class1PresentationPredictor
import mhcgnomes
import logging
import subprocess

# Create a logger
logging.basicConfig(filename='mhcflurry.log', filemode='w',level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s', force=True)

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
    input_file = pd.read_csv(args.input, sep='\t')
    #collect all alleles and peptide for the sample
    alleles = args.alleles.split(';')
    peptides = input_file['sequence'].to_list()

    #fetch model if it's not already downloaded
    #saved in container at /root/.local/share/mhcflurry/4/2.0.0/models_class1/
    p = subprocess.call(['mhcflurry-downloads', 'path', 'models_class1'],stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if p == 0:
        subprocess.run(['mhcflurry-downloads', 'fetch', 'models_class1'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    #load predictor and get supported alleles
    predictor_classI = Class1PresentationPredictor.load()
    supported_alleles = predictor_classI.supported_alleles

    #generate head of dataframe
    df = pd.DataFrame({"peptide":[],"peptide_num":[],"sample_name":[],"affinity":[],"best_allele":[],"processing_score":[],"presentation_score":[],"presentation_percentile":[]}).reset_index(drop=True)

    for a in alleles:
        for p in peptides:
            #convert allele to MHC name standard with mhcgnomes
            converted_a = mhcgnomes.parse(a).to_string()
            #check if allele is supported
            if converted_a in supported_alleles:
                new_df = predictor_classI.predict(peptides=[p],alleles=[a]).reset_index(drop=True)
                df = pd.concat([df, new_df],ignore_index=True, axis=0)
                logging.debug("Prediction was made for allele " + a)
            else:
                logging.warning("Allele "+ a + " was converted by mhcgnomes to " + converted_a + " and is not supported by mhcflurry." )

    #make output pretty
    df = df.drop(columns=['sample_name'])
    df = df.drop(columns=['peptide_num'])
    df = df.rename(columns={"best_allele":"allele"})

    #join the information on one peptide into one row
    df = df.pivot(index='peptide', columns=['allele'], values=['affinity', 'processing_score', 'presentation_score', 'presentation_percentile'])
    #join the multiple columns
    df.columns = df.columns.map('_'.join).str.strip('_')
    #generate peptide column
    df = df.rename_axis('peptide').reset_index()
    #write joined df to output file
    df.to_csv(args.output, sep='\t', index=False)


if __name__ == '__main__':
    main()
