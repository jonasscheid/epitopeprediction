#!/usr/bin/env python

import sys
import argparse
import logging
import pandas as pd
import numpy as np
import typing
from functools import reduce
from epytope.Core import Allele, Peptide
from epytope.EpitopePrediction import EpitopePredictorFactory

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
    parser = argparse.ArgumentParser(description='Predicting epitopes using Syfpeithi with the epytope framework')
    parser.add_argument('--input', help='Input file containing the protein sequences')
    parser.add_argument('--alleles', help='Input string containing the alleles')
    parser.add_argument('--output', help='Output file containing the predicted epitopes')
    parser.add_argument('--min_peptide_length', type=int, default=8, help='Minimum length of the peptides')
    parser.add_argument('--max_peptide_length', type=int, default=12, help='Maximum length of the peptides')

    return parser.parse_args(argv)


def get_matrix_max_score(allele, length) -> float:
    """
    Get the maximum score of a Syfpeithi matrix
    :param allele: epytope Allele object
    :param length: length of the peptide
    :return: maximum score of the matrix
    """
    # Convert allele to epytope internal structure to load the matrix
    conv_allele = "%s_%s%s" % (allele.locus, allele.supertype, allele.subtype)
    allele_model = "%s_%i" % (conv_allele, length)
    try:
        pssm = getattr(
            __import__("epytope.Data.pssms.syfpeithi.mat." + allele_model, fromlist=[allele_model]), allele_model
        )
        return sum([max(scrs.values()) for pos, scrs in pssm.items()])
    except:
        return np.nan


def rel_max_score(row, allele, matrix_max_score_dict) -> float:
    """
    Compute the peptide score relative to the maximum matrix score for a given allele
    :param row: row of the input dataframe
    :param allele: allele for which the rel-max-score should be computed
    :param matrix_max_score_dict: dict containing the maximum scores of the Syfpeithi matrices
    :return: rel-max-score of the peptide for the allele
    """
    # Syfpeithi supports only specific peptide length and allele combinations
    logger.debug("row['sequence']", row['sequence'])
    logger.debug(matrix_max_score_dict)

    if len(row['sequence']) not in matrix_max_score_dict[allele].keys():
        return np.nan
    half_max_score = (row[allele] / matrix_max_score_dict[allele][len(row['sequence'])]) * 100
    return half_max_score



def main():
    args = parse_args()
    # Define MHC binding tool using the epytope framework
    predictor = EpitopePredictorFactory("Syfpeithi")
    min_length_given_by_syfpeithi = 8
    max_length_given_by_syfpeithi = 12

    input_file = pd.read_csv(args.input, sep='\t')

    # Build epytope Objects of peptides and alleles
    peptides = [Peptide(peptide) for peptide in input_file['sequence'] if len(peptide) >= args.min_peptide_length and len(peptide) <= args.max_peptide_length]
    print("peptides", peptides)
    # Check if alleles are supported by the predictor
    alleles = []
    for allele in args.alleles.split(';'):
        epytope_allele = Allele(allele)
        if epytope_allele not in predictor.supportedAlleles:
            logger.warning(f'Allele {allele} is not supported by syfpeithi. No prediction was made.')
            continue
        alleles.append(epytope_allele)

    # Fill a dict of dicts: {allele1: {length1: max_score_length1, length2:max_score_length1}, allele2:.. }
    matrix_max_score_dict = {}
    for allele in alleles:
        len_score_dict = {}

        for peptide_length in set(range(args.min_peptide_length, args.max_peptide_length+1)) & set(range(min_length_given_by_syfpeithi, max_length_given_by_syfpeithi+1)):
            matrix_max_score = get_matrix_max_score(allele, peptide_length)
            if matrix_max_score is np.nan:
                logger.warning(f'Out of scope of requested peptide length {peptide_length}. No prediction was made.')
                continue
            len_score_dict[peptide_length] = matrix_max_score
            matrix_max_score_dict[allele] = len_score_dict

    # Predict MHC binding using the epytope framework
    results = predictor.predict(peptides, alleles=alleles)

    # Compute Syfpeithi half-max-score per allele
    predictions_per_allele = []
    for allele in alleles:
        allele_df = results[allele]['syfpeithi']['Score'].reset_index()
        # Rename accordingly for downstream handling
        allele_df.rename({'Score': allele, 'Peptides': 'sequence'}, axis=1, inplace=True)
        # Compute half-max-score
        allele_df[allele] = allele_df.apply(lambda x: rel_max_score(x, allele, matrix_max_score_dict), axis=1)
        predictions_per_allele.append(allele_df)

    # Merge all allele specific predictions
    predictions_df = reduce(lambda left, right: pd.merge(left, right, on=['sequence'], how='outer'), predictions_per_allele)
    #change column name of df
    predictions_df.rename(columns={'sequence': 'peptide'}, inplace=True)
    # Write output
    predictions_df.to_csv(args.output, sep='\t', index=False)


if __name__ == '__main__':
    main()
