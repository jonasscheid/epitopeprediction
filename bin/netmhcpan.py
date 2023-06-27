#!/opt/conda/bin/python

import argparse
import typing
import logging
import subprocess as sp
import pandas as pd
import sys
import os

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
    parser = argparse.ArgumentParser(description='Predicting epitopes using NetMHCpan')
    parser.add_argument('--input', required=True, help='Tab-separated input file containing the sequences')
    parser.add_argument('--alleles', required=True, help='Input string containing the alleles')
    parser.add_argument('--sample_id', required=True, help='Sample IDs to be used in the output file')
    parser.add_argument('--min_peptide_length', type=int, default=8, help='Minimum length of the peptides')
    parser.add_argument('--max_peptide_length', type=int, default=12, help='Maximum length of the peptides')

    return parser.parse_args(argv)


def main():
    args = parse_args()

    min_length_given_by_netmhcpan = 8
    max_length_given_by_netmhcpan = 56

    # Parse input file and write to netmhcpan input format
    peptides = pd.read_csv(args.input, sep='\t')['sequence'].tolist()
    netmhcpan_input = f'{args.input.split(".")[0]}.txt'
    with open(netmhcpan_input, 'w') as file:
        for peptide in peptides:
            # Hard length limits of netmhcpan
            if len(peptide) in set(range(args.min_peptide_length, args.max_peptide_length+1)) & set(range(min_length_given_by_netmhcpan, max_length_given_by_netmhcpan+1)):
                file.write(peptide + '\n')
            else:
                logger.warning(f'{peptide} does not have the right length. Skipping..')

    # Check if input alleles are supported by netmhcpan
    input_alleles = [allele.replace('*', '') for allele in args.alleles.split(';')]
    # For this we need to catch the stdout of netmhcpan
    sp.run(['netmhcpan/netMHCpan', '-listMHC'], stdout=open('supported_alleles.txt', 'w'))

    supported_alleles = []
    with open('supported_alleles.txt', 'r') as alleles_file:
        for allele in alleles_file.readlines():
            if allele.startswith('HLA') or allele.startswith('H-2'):
                supported_alleles.append(allele.strip())

    # Run netmhcpan for each allele
    for allele in input_alleles:
        if allele not in supported_alleles:
            logger.warning(f'{allele} is not supported by NetMHCpan')
        else:
            sp.call(['netmhcpan/netMHCpan', '-f', netmhcpan_input, '-inptype', '1','-a', allele, '-xls', '-xlsfile', f'{args.sample_id}_{allele}.xls'])

    # Combine allele-specific prediction files into one
    tmp_dfs = []
    for allele in input_alleles:
        if allele in supported_alleles:
            #if file with name f'{args.sample_id}_{allele}.xls' not found raise RuntimeError
            if f'{args.sample_id}_{allele}.xls' not in os.listdir():
                raise RuntimeError('No single prediction was made for whole sample. Please check the input file.')
            tmp_df = pd.read_csv(f'{args.sample_id}_{allele}.xls', sep='\t', skiprows=1, index_col=0)
            tmp_df['allele'] = allele
            tmp_dfs.append(tmp_df)
            # Clean up intermediate files
            sp.run(['rm', f'{args.sample_id}_{allele}.xls'])

    combined_df = pd.concat(tmp_dfs)
    combined_df.to_csv(f'{args.sample_id}_predicted_netmhcpan.tsv', sep='\t')



if __name__ == '__main__':
    main()
