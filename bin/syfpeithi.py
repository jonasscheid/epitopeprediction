import sys
import argparse
import pandas as pd
import numpy as np
import typing
from functools import reduce
from epytope.Core import Allele, Peptide
from epytope.EpitopePrediction import EpitopePredictorFactory, Syfpeithi


def parse_args(argv=None) -> typing.List[str]:
    """
    Parse command line arguments
    :param argv: list of arguments
    :return: parsed arguments
    """
    parser = argparse.ArgumentParser(description='Predicting epitopes using Syfpeithi with the epytope framework')
    parser.add_argument('--input', required=True, help='Input file containing the protein sequences')
    parser.add_argument('--alleles', required=True, help='Input string containing the alleles')
    parser.add_argument('--output', required=True, help='Output file containing the predicted epitopes')
    parser.add_argument('--min_peptide_length', type=int, default=8, help='Minimum length of the peptides')
    parser.add_argument('--max_peptide_length', type=int, default=12, help='Maximum length of the peptides')
    parser.add_argument('--threshold', type=float, default=50, help='Threshold for the prediction')
    parser.add_argument('--version', action='store_true', default=1.0, help='Tool version')

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


def compute_half_max_score(row, allele, matrix_max_score_dict) -> float:
    """
    Compute the half-max-score of a peptide for a specific allele
    :param row: row of the input dataframe
    :param allele: allele for which the half-max-score should be computed
    :param matrix_max_score_dict: dict containing the maximum scores of the Syfpeithi matrices
    :return: half-max-score of the peptide for the allele
    """
    # Syfpeithi supports only specific peptide length and allele combinations
    if len(row['sequence']) not in matrix_max_score_dict[allele].keys():
        return np.nan
    half_max_score = (row[allele] / matrix_max_score_dict[allele][len(row['sequence'])]) * 100
    return half_max_score



def main():
    args = parse_args()
    # Define MHC binding tool using the epytope framework
    predictor = EpitopePredictorFactory("Syfpeithi")
    if args.version:
        sys.exit(f"{predictor.version}")

    input_file = pd.read_csv(args.input, sep='\t')

    # Build epytope Objects of peptides and alleles
    peptides = [Peptide(peptide) for peptide in input_file['sequence'] if len(peptide) >= args.min_peptide_length and len(peptide) <= args.max_peptide_length]
    alleles = [Allele(allele) for allele in args.alleles.split(';')]

    # Fill a dict of dicts: {allele1: {length1: max_score_length1, length2:max_score_length1}, allele2:.. }
    matrix_max_score_dict = {}
    for allele in alleles:
        len_score_dict = {}
        for peptide_length in range(args.min_peptide_length, args.max_peptide_length):
            matrix_max_score = get_matrix_max_score(allele, peptide_length)
            if matrix_max_score is np.nan:
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
        allele_df[allele] = allele_df.apply(lambda x: compute_half_max_score(x, allele, matrix_max_score_dict), axis=1)
        # Add column with boolean value if peptide is a binder
        allele_df[f"{allele}_binder"] = allele_df[allele] >= args.threshold
        predictions_per_allele.append(allele_df)

    # Merge all allele specific predictions
    predictions_df = reduce(lambda left, right: pd.merge(left, right, on=['sequence'], how='outer'), predictions_per_allele)

    # Write output
    predictions_df.to_csv(args.output, sep='\t', index=False)


if __name__ == '__main__':
    main()
