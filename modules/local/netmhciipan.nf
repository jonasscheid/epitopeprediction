process NETMHCIIPAN {
    label 'process_single'
    tag "${metadata.sample}"


    container 'ghcr.io/jonasscheid/epitopeprediction-2:netmhc'

    input:
    tuple val(metadata), path(peptide_file)

    output:
    tuple val(metadata), path("*.tsv"), emit: predicted
    path "versions.yml", emit: versions

    script:
    if (metadata.mhc_class != "II") {
        error "NETMHCIIPAN only supports MHC class II. Use NETMHCPAN for MHC class I, or adjust the samplesheet accordingly."
    }
    // TODO: Preprocess peptide input for netmhcpan input -> line-separated list of peptides, no header
    // TODO: Check allele support
    // TODO: Postprocess output for netmhcpan output -> See epytope

    """
    #!/bin/bash
    netMHCIIpan -f $peptide_file \\
        -inptype 1 \\
        -a DRB1_0101 \\
        -xls \\
        -xlsfile ${metadata.sample}_tmp_predicted.tsv

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        python \$(python --version | sed 's/Python //g')
        netmhciipan \$(cat data/version | sed -s 's/ version/:/g')
    END_VERSIONS
    """

    stub:
    """
    touch ${metadata.sample}_predicted_netmhcpan.tsv
    touch versions.yml
    """
}
