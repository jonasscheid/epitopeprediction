process SEQKIT_SPLIT2 {
    tag "${meta.sample}"
    label 'process_low'

    conda "bioconda::seqkit=2.4.0"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/seqkit:2.4.0--h9ee0642_0' :
        'quay.io/biocontainers/seqkit:2.4.0--h9ee0642_0' }"

    input:
    tuple val(meta), path(fasta)

    output:
    tuple val(meta), path("**/*.fasta"), emit: splitted
    path "versions.yml"             , emit: versions

    script:
    def args   = task.ext.args   ?: ''
    def prefix = task.ext.prefix ?: "${meta.id}"

    """
    seqkit split2 ${fasta} -s 100

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        seqkit \$(echo \$(seqkit 2>&1) | sed 's/^.*Version: //; s/ .*\$//')
    END_VERSIONS
    """
}

