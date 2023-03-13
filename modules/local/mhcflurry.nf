process MHCFLURRY {
    label 'process_low'
    tag "${metadata.sample}"

    conda "bioconda::mhcflurry=2.0.6"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/mhcflurry:2.0.6--pyh7cba7a3_0' :
        'quay.io/biocontainers/mhcflurry:2.0.6--pyh7cba7a3_0' }"

    input:
    tuple val(metadata), path(peptide_file)

    output:
    tuple val(metadata), path("*.tsv"), emit: predicted
    path "versions.yml", emit: versions

    script:
    def min_length = (metadata.mhc_class == "I") ? params.min_peptide_length_mhc_I : params.min_peptide_length_mhc_II
    def max_length = (meta.mhcclass == "I") ? params.max_peptide_length_mhc_I : params.max_peptide_length_mhc_II

    // TODO: Threshold?
    """
    mhcflurry-prediction-placeholder

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        epytope: \$(python -c "import pkg_resources; print(pkg_resources.get_distribution('epytope').version)")
    END_VERSIONS
    """

    stub:
    """
    touch ${metadata.sample}_predicted_mhcflurry.tsv
    touch versions.yml
    """
}
