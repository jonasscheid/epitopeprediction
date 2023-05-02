#!/usr/bin/env python

import argparse
import pandas as pd
import typing
import sys
import re
import tempfile
import logging
from mhcnuggets.src.predict import predict
#import mhcgnomes


# Create a logger
logging.basicConfig(filename='mhcnuggets.log', filemode='w',level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

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
    parser.add_argument('--mhcclass', required=required, help='Get MHC Class of sample')
    parser.add_argument('--threshold', type=float, default=50, help='Threshold for the prediction')
    parser.add_argument('--version', action='store_true', help='Tool version')

    return parser.parse_args(argv)


def main():
    args = parse_args()
    #collect all alleles and peptide for the sample and collect them in a list
    alleles = args.alleles.split(';')
    peptides = pd.read_csv(args.input, sep='\t')['sequence']
    peptide_number = len(peptides)

    #convert id and peptide tsv into one peptide per line without header
    with open('mhcnuggets_peptides.tsv', 'w+') as input:
        peptides.to_csv(input, sep='\t', index=False, header=False)

    #temp file output of mhcnuggets tool, necessary information gets extracted and written to the actual output file
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_out:
        #re-routing stdout to temporary output file
        #if you want to see the direct output of the mhcnuggets tool, take out line 50 and 57, the output then will be printed to stdout
        sys.stdout = temp_out
        for a in alleles:
            #a = mhcgnomes.parse(a).to_string()
            #converted_a = a.replace("*", "")
            #Mhcnuggets prediction
            predict(class_=args.mhcclass, peptides_path = 'mhcnuggets_peptides.tsv', mhc=a, rank_output=True)
        #resetting stdout
        sys.stdout = sys.__stdout__

        #affinity scores for the alleles and peptides need to be extracted from the temporary mhcnuggets output
        allele_pattern = re.compile('Closest allele found .*')
        peptide_pattern = re.compile('.*,.*,.*')

        # Seek back to the beginning of the file to read its content
        temp_out.seek(0)
        #track the current allele for prediction tables
        allele = ""
        #iterator through table, max. length is number of peptides per a certain allele
        table_lines = 0
        allele_count = 0
        df = pd.DataFrame({"allele":[],"peptide":[],"ic50_affinity_score":[],"human_proteome_rank":[]}).reset_index(drop=True)
        # Read the content of the temporary file
        for line in temp_out.readlines():
            line_s = line.strip()
            #mhcnuggets output started prediction on specific allele
            if allele_pattern.match(line_s):
                allele = line_s.split(' ')[-1]
                if allele not in alleles:
                    logging.warning("The Mhcnuggets prediction was made with the allele name "+allele+" which is not the requested allele "+alleles[allele_count-1])
            #mhcnuggets peptide output belonging to specific allele above
            if (table_lines > 0) and (peptide_pattern.match(line_s)):
                line_list = line_s.split(',')
                #generate new df entry for peptide
                new_df = pd.DataFrame({"allele": allele, "peptide": line_list[0], "ic50_affinity_score": line_list[1], "human_proteome_rank": line_list[2]}, index=[0])
                df = pd.concat([df, new_df],ignore_index=True, axis=0)
                logging.debug("The mhcnuggets prediction in df format belonging to allele "+allele+" and the peptide "+str(line_list[0])+ " is: "+ new_df.to_string())

            if line_s == "peptide,ic50,human_proteome_rank":
                allele_count += 1
                table_lines = peptide_number + 1

            table_lines -= 1

    #join the information on one peptide into one row
    df = df.pivot(index='peptide', columns=['allele'], values=['ic50_affinity_score', 'human_proteome_rank'])
    #join the multiple columns
    df.columns = df.columns.map('_'.join).str.strip('_')
    #generate peptide column
    df = df.rename_axis('peptide').reset_index()
    #write joined df to output file
    df.to_csv(args.output, sep='\t', index=False)


if __name__ == '__main__':
    main()
