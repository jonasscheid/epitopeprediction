//and also do the allele name

process PREPARE_PREDICTION_INPUT {
    label 'process_single'
    tag "${meta.sample}"

    conda "bioconda::mhcgnomes=1.8.4"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/mhcgnomes:1.8.4--pyh7cba7a3_0' :
        'quay.io/biocontainers/mhcgnomes:1.8.4--pyh7cba7a3_0' }"

    input:
    tuple val(meta), path(peptide_file)

    output:
    tuple val(meta), path("*.csv"), emit: prepared
    path "versions.yml", emit: versions

    script:
    def args       = task.ext.args ?: ''
    def prefix     = task.ext.prefix ?: meta.sample
    //TODO handle the thresholds (parse the --tools_thresholds and --use_affinity_thresholds)
    def min_length = (meta.mhc_class == "I") ? params.min_peptide_length : params.min_peptide_length_class2
    def max_length = (meta.mhc_class == "I") ? params.max_peptide_length : params.max_peptide_length_class2
    //tools über params.tools ziehen

    """
    """

    stub:
    def args       = task.ext.args ?: ''
    def prefix     = task.ext.prefix ?: meta.sample
    """
    touch ${prefix}_syfpeithi.csv
    touch ${prefix}_mhcflurry.csv
    touch ${prefix}_mhcnuggets.csv
    touch ${prefix}_netmhcpan.csv
    touch ${prefix}_netmhciipan.csv
    touch versions.yml
    """
}
