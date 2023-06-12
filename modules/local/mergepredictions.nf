process MERGEPREDICTIONS {
    label 'process_low'
    tag "${metadata.sample}"

    conda "bioconda::mhcgnomes=1.8.4"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/mhcgnomes:1.8.4--pyh7cba7a3_0' :
        'quay.io/biocontainers/mhcgnomes:1.8.4--pyh7cba7a3_0' }"

    input:
    tuple val(metadata), path(prediction_paths)

    output:
    tuple val(metadata), path("*.tsv"), emit: merged
    path "versions.yml", emit: versions

    script:
    """
    merge_prediction_outputs.py --data '${metadata}' --pathlist '${prediction_paths}'
    touch merged.tsv

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        python: \$(python --version | sed 's/Python //g')
    END_VERSIONS
    """
}
