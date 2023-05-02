process MHCNUGGETS {
    label 'process_low'
    tag "${metadata.sample}"

    conda "bioconda::mhcnuggets=2.4.0"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/mhcnuggets:2.4.0--pyh7cba7a3_0' :
        'quay.io/biocontainers/mhcnuggets:2.4.0--pyh7cba7a3_0' }"

    input:
    tuple val(metadata), path(peptide_file)

    output:
    tuple val(metadata), path("*.tsv"), emit: predicted
    path "versions.yml", emit: versions

    script:
    """
    touch mhcnuggets_prediction.log
    mhcnuggets_prediction.py --input ${peptide_file} --output '${metadata.sample}_predicted_mhcnuggets.tsv' --alleles '${metadata.alleles}' --mhcclass ${metadata.mhc_class}

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
    END_VERSIONS
    """

    //mhcgnomes: \$(python -c "from mhcgnomes import version; print(version.__version__)")
    //TODO mhcnuggets version hinzufügen -> mhcnuggets:  \$(echo "2.4.0")

    stub:
    """
    touch ${metadata.sample}_predicted_mhcnuggets.tsv
    touch versions.yml
    """
}
