process SYFPEITHI {
    label 'process_low'
    tag "${metadata.sample}"

    conda "bioconda::epytope=3.1.0"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/epytope:3.1.0--pyh5e36f6f_0' :
        'quay.io/biocontainers/epytope:3.1.0--pyh5e36f6f_0' }"

    input:
    tuple val(metadata), path(peptide_file)

    output:
    tuple val(metadata), path("*.tsv"), emit: predicted
    path "versions.yml", emit: versions

    script:
    def min_length = (metadata.mhc_class == "I") ? params.min_peptide_length_mhc_I : params.min_peptide_length_mhc_II
    def max_length = (metadata.mhcclass == "I") ? params.max_peptide_length_mhc_I : params.max_peptide_length_mhc_II

    // TODO: Threshold?
    """
    touch syfpeithi_prediction.log
    syfpeithi.py --input ${peptide_file} \\
        --alleles '${metadata.alleles}' \\
        --min_peptide_length ${min_length} \\
        --max_peptide_length ${max_length} \\
        --threshold 50 \\
        --output '${metadata.sample}_predicted_syfpeithi.tsv' \\

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        epytope: \$(python -c "import pkg_resources; print(pkg_resources.get_distribution('epytope').version)")
        syfpeithi: \$(python syfpeithi.py --version | tail -1)
    END_VERSIONS
    """

    stub:
    """
    touch ${metadata.sample}_predicted_syfpeithi.tsv
    touch versions.yml
    """
}
