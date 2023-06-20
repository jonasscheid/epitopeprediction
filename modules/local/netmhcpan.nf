process NETMHCPAN {
    label 'process_low'
    tag "${metadata.sample}"


    container "pmccaffrey6/netmhcpan_i:4.1"

    input:
    tuple val(metadata), path(peptide_file)

    output:
    tuple val(metadata), path("*.tsv"), emit: predicted
    path "versions.yml", emit: versions

    script:
    if (metadata.mhc_class != "I") {
        error "NETMHCPAN only supports MHC class I. Use NETMHCIIPAN for MHC class II, or adjust the samplesheet accordingly."
    }
    // TODO: Preprocess peptide input for netmhcpan input -> line-separated list of peptides, no header
    // TODO: Check allele support
    // TODO: Postprocess output for netmhcpan output -> See epytope
    // https://github.com/KohlbacherLab/epytope/blob/4e3640459fe2aa95d779fae6c2163b3a92f1d2fd/epytope/EpitopePrediction/External.py#L880
    """
    #!/bin/bash

    netMHCpan -p $peptide_file \\
        -a HLA-A02:01 \\
        -xls \\
        -xlsfile ${metadata.sample}_tmp_predicted.tsv

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        python \$(python --version | sed 's/Python //g')
        netmhcpan \$(cat data/version | sed -s 's/ version/:/g')
    END_VERSIONS
    """

    stub:
    """
    touch ${metadata.sample}_predicted_netmhcpan.tsv
    touch versions.yml
    """
}
