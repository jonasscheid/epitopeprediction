process NETMHCPAN {
    label 'process_single'
    tag "${metadata.sample}"

    container 'ghcr.io/jonasscheid/epitopeprediction-2:netmhc'

    input:
    tuple val(metadata), path(peptide_file), path(nonfree_tools)

    output:
    tuple val(metadata), path("*.tsv"), emit: predicted
    path "versions.yml", emit: versions

    script:
    if (metadata.mhc_class != "I") {
        error "NETMHCPAN only supports MHC class I. Use NETMHCIIPAN for MHC class II, or adjust the samplesheet accordingly."
    }

    """
    netmhcpan.py --input ${peptide_file} --alleles '${metadata.alleles}' --sample_id ${metadata.sample}

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        python \$(python --version | sed 's/Python //g')
        netmhcpan \$(echo 4.1)
        netmhcpan \$(cat data/version | sed -s 's/ version/:/g')
    END_VERSIONS
    """
    stub:
    """
    touch ${metadata.sample}_predicted_netmhcpan.tsv
    touch versions.yml
    """
}
