#!/usr/bin/env python

import argparse
import pandas as pd
import typing
import sys
import logging
import mhcgnomes
from functools import reduce

# Create a logger
logging.basicConfig(filename='merge_prediction_outputs.log', filemode='w',level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s', force=True)

def parse_args(argv=None) -> typing.List[str]:
    """
    Parse command line arguments
    :param argv: list of arguments
    :return: parsed arguments
    """
    parser = argparse.ArgumentParser(description='Harmonize prediction outputs')
    parser.add_argument('--input', required=True, help='Lists of paths to prediction outputs')
    parser.add_argument('--original_file', required=True, help='Path to original input file contained in metadata')
    parser.add_argument('--output', required=True, help='Output file')
    parser.add_argument('--min_peptide_length', type=int, help='Minimum length of the peptides')
    parser.add_argument('--max_peptide_length', type=int, help='Maximum length of the peptides')
    parser.add_argument('--syfpeithi_threshold', type=int, help='Threshold for syfpeithis relativ max matrix score')
    parser.add_argument('--mhcflurry_threshold', type=int, help='Threshold for mhcflurry')
    parser.add_argument('--mhcnuggets_threshold', type=int, help='Threshold for mhcnuggets')
    parser.add_argument('--netmhcpan_threshold', type=int, help='Threshold for netmhcpan')
    parser.add_argument('--netmhciipan_threshold', type=int, help='Threshold for netmhciipan')

    return parser.parse_args(argv)


class PredictionResult():
    def __init__(self, predictor, prediction_df, threshold=None):
        self.predictor = predictor
        self.prediction_df = prediction_df
        self.threshold = threshold

    def get_prediction_df(self):
        return self.prediction_df

    def format_prediction_result(self):
        if self.predictor == 'syfpeithi':
            self.prediction_df = self._format_syfpeithi_prediction(self.threshold)
        elif self.predictor == 'mhcflurry':
            self.prediction_df = self._format_mhcflurry_prediction(self.threshold)
        elif self.predictor == 'mhcnuggets':
            self.prediction_df = self._format_mhcnuggets_prediction(self.threshold)
        elif self.predictor == 'netmhcpan':
            self.prediction_df = self._format_netmhcpan_prediction(self.threshold)
        elif self.predictor == 'netmhciipan':
            self.prediction_df = self._format_netmhciipan_prediction(self.threshold)
        else:
            logging.error(f'Predictor {self.predictor} not supported')
            sys.exit(1)

    def _format_syfpeithi_prediction(self, threshold=None):
        df = self.prediction_df
        df = df.rename(columns={'peptide': 'sequence'})
        df.columns = [f'syfpeithi_relMaxScore_{col}' if col != "sequence" else col for col in df.columns]
        if threshold:
            # keep peptide if at least one allele has a score >= threshold
            df = df[df.iloc[:, 1:].ge(threshold).any(1)]
        return df

    def _format_mhcflurry_prediction(self, threshold=None):
        df = self.prediction_df
        df = df.rename(columns={'peptide': 'sequence'})
        df = df[df.columns[df.columns.str.contains('presentation_percentile|sequence')]]
        # Get rid of the presentation_percentile prefix and obtain only allele names in columns
        df.columns = [col.replace('presentation_percentile_','') if col != "sequence" else col for col in df.columns]
        # Represent official allele names
        df.columns = [f'mhcflurry_percentile_{mhcgnomes.parse(col).to_string()}' if col != "sequence" else col for col in df.columns]
        if threshold:
            # keep peptide if at least one allele has a score <= threshold
            df = df[~df.iloc[:, 1:].gt(threshold).any(1)]
        return df

    def _format_mhcnuggets_prediction(self, threshold=None):
        df = self.prediction_df
        df = df.rename(columns={'peptide': 'sequence'})
        df = df[df.columns[df.columns.str.contains('human_proteome_rank|sequence')]]
        # Get rid of the human_proteome_rank prefix and obtain only allele names in columns
        df.columns = [col.replace('human_proteome_rank_','') if col != "sequence" else col for col in df.columns]
        # Represent official allele names
        df.columns = [f'mhcnuggets_rank_{mhcgnomes.parse(col).to_string()}' if col != "sequence" else col for col in df.columns]
        if threshold:
            # keep peptide if at least one allele has a score <= threshold
            df = df[~df.iloc[:, 1:].gt(threshold).any(1)]
        return df

    def _format_netmhcpan_prediction(self, threshold=None):
        df = self.prediction_df
        df = df.rename(columns={'Peptide': 'sequence'})
        df = df[df.columns[df.columns.str.contains('sequence|EL_Rank|allele')]]
        # We need to bring long format to wide format and need to get rid of duplicates
        df = df.drop_duplicates(subset=['sequence', 'allele'])
        df = df.pivot(index='sequence', columns='allele', values='EL_Rank')
        # Represent official allele names
        df.columns = [f'netmhcpan_rank_{mhcgnomes.parse(col).to_string()}' for col in df.columns]
        df = df.reset_index()
        if threshold:
            # keep peptide if at least one allele has a score <= threshold
            df = df[~df.iloc[:, 1:].gt(threshold).any(1)]
        return df

    def _format_netmhciipan_prediction(self, threshold=None):
        NotImplementedError()



def main():
    args = parse_args()
    #collect all files that entail the prediction outputs
    input = args.input.split(" ")

    tmp_dfs = []
    for file in input:
        tmp_df = pd.read_csv(file, sep='\t')
        if 'syfpeithi' in file:
            predictor = 'syfpeithi'
            threshold = args.syfpeithi_threshold
        elif 'mhcflurry' in file:
            predictor = 'mhcflurry'
            threshold = args.mhcflurry_threshold
        elif 'mhcnuggets' in file:
            predictor = 'mhcnuggets'
            threshold = args.mhcnuggets_threshold
        elif 'netmhcpan' in file:
            predictor = 'netmhcpan'
            threshold = args.netmhcpan_threshold
        elif 'netmhciipan' in file:
            predictor = 'netmhciipan'
            threshold = args.netmhciipan_threshold
        else:
            logging.error(f'Predictor not supported')
            sys.exit(1)

        # Refactor prediction output to only the necessary columns
        prediction_result = PredictionResult(predictor, tmp_df, threshold)
        prediction_result.format_prediction_result()
        tmp_df = prediction_result.get_prediction_df()

        tmp_dfs.append(tmp_df)

    #merge elements in tmp_dfs on one column of dataframe
    df = reduce(lambda left,right: pd.merge(left,right,on=['sequence'], how='outer', sort=True), tmp_dfs)
    original_input = pd.read_csv(args.original_file, sep='\t')
    df = pd.merge(original_input, df, on=['sequence'], how='outer', sort=True)

    #write df to tsv
    df.to_csv(f'{args.output}', sep='\t', index=False)

if __name__ == '__main__':
    main()
