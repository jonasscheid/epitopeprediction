process SAMPLESHEET_CHECK {
    tag "$samplesheet"
    label 'process_single'

    conda "bioconda::mhcgnomes=1.8.4"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/mhcgnomes:1.8.4--pyh7cba7a3_0' :
        'quay.io/biocontainers/mhcgnomes:1.8.4--pyh7cba7a3_0' }"

    input:
    path samplesheet

    output:
    path '*.tsv'       , emit: tsv
    path "versions.yml", emit: versions

    when:
    task.ext.when == null || task.ext.when

    script: // This script is bundled with the pipeline, in nf-core/epitopeprediction/bin/
    """
    check_samplesheet.py \\
        $samplesheet \\
        samplesheet.valid.tsv

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        python \$(python --version | sed 's/Python //g')
    END_VERSIONS
    """
}
